"""
4-Stage Car Condition Assessment Pipeline
==========================================
Stage 1: Interior/Exterior Classification  →  stage1.py
Stage 2: Damage Detection                  →  stage2.py
Stage 3: Damage Severity Analysis           →  stage3.py
Stage 4: Undamaged Condition Grading        →  stage4.py

Shared helpers live in pipeline_helpers.py.
"""

import os
import logging
from pathlib import Path

import stage1, stage2, stage3, stage4

logger = logging.getLogger(__name__)

# ── Total-loss validation thresholds ────────────────────────────────────
TL_MIN_RATIO = 0.4          # ≥40 % of exterior images must be TL to confirm
_GOOD_OR_BETTER = {"good", "very good", "excellent"}

# ── False-damage override thresholds ───────────────────────────────────
DMG_OVERRIDE_UNDAMAGED_RATIO = 0.6   # if ≥60 % of exterior images are undamaged …
DMG_OVERRIDE_S2_CONF = 0.65          # … override damaged images below this S2 confidence


class CarAssessmentPipeline:
    """
    Runs every uploaded image through four sequential stages:

    1. Interior / Exterior filter
    2. Damage identification (multi-class → binary)
    3. Severity analysis   (for damaged images only)
    4. Condition grading   (for undamaged images only)
    """

    def __init__(self, base_dir: str):
        self.base_dir = Path(base_dir)
        self.models: dict = {}
        self._loaded = False

    def load_all_models(self):
        """Load every model for every stage (called once, lazily)."""
        if self._loaded:
            return
        logger.info("Loading all pipeline models …")
        self.models["s1"] = stage1.load(self.base_dir)
        self.models["s2"] = stage2.load(self.base_dir)
        self.models["s3"] = stage3.load(self.base_dir)
        self.models["s4"] = stage4.load(self.base_dir)
        self._loaded = True
        logger.info("All pipeline models loaded.")

    def process_images(self, image_paths: list[str]) -> dict:
        """Run *all* uploaded images through the 4-stage pipeline."""
        self.load_all_models()

        results = {
            "total_images": len(image_paths),
            "interior_count": 0,
            "exterior_count": 0,
            "damaged_count": 0,
            "undamaged_count": 0,
            "total_loss_detected": False,
            "image_results": [],
            "damaged_images": [],
            "undamaged_images": [],
        }

        for img_path in image_paths:
            rec = {
                "filename": os.path.basename(img_path),
                "path": img_path,
                "stages": {},
            }

            # ---- Stage 1 ----
            s1 = stage1.predict(self.models["s1"], img_path)
            rec["stages"]["s1"] = s1
            if s1["label"] == "interior":
                rec["final_label"] = "Interior (Discarded)"
                rec["score"] = None
                results["interior_count"] += 1
                results["image_results"].append(rec)
                continue

            results["exterior_count"] += 1

            # ---- Stage 2 ----
            s2 = stage2.predict(self.models["s2"], img_path)
            rec["stages"]["s2"] = s2

            if s2["is_damaged"]:
                results["damaged_count"] += 1

                if s2["damage_type"] == "total_loss":
                    # Run through Stage 3 as a severity sanity-check
                    s3 = stage3.predict(self.models["s3"], img_path)
                    rec["stages"]["s3"] = s3

                    if s3["severity"] == "severe":
                        # Stage 3 agrees → keep as TL candidate
                        rec["final_label"] = "Total Loss"
                        rec["damage_type"] = "total_loss"
                        rec["severity"] = "total_loss"
                        rec["s3_severity"] = s3["severity"]
                        rec["score"] = 0
                        results["damaged_images"].append(rec)
                        results["image_results"].append(rec)
                        continue
                    else:
                        # Stage 3 contradicts TL → downgrade to body damage
                        rec["damage_type"] = "body"
                        rec["severity"] = s3["severity"]
                        rec["final_label"] = (
                            f"Damaged – Body ({s3['severity'].title()})  "
                            f"[S2 predicted total-loss but S3 severity "
                            f"is {s3['severity']}]"
                        )
                        results["damaged_images"].append(rec)
                        results["image_results"].append(rec)
                        continue

                # ---- Stage 3 ----
                s3 = stage3.predict(self.models["s3"], img_path)
                rec["stages"]["s3"] = s3
                rec["damage_type"] = s2["damage_type"]
                rec["severity"] = s3["severity"]
                rec["final_label"] = (
                    f"Damaged – {s2['damage_type'].replace('_', ' ').title()} "
                    f"({s3['severity'].title()})"
                )
                results["damaged_images"].append(rec)
            else:
                results["undamaged_count"] += 1
                # ---- Stage 4 ----
                s4 = stage4.predict(self.models["s4"], img_path)
                rec["stages"]["s4"] = s4
                rec["condition"] = s4["condition"]
                rec["confidence"] = s4.get("confidence", 0.7)
                rec["final_label"] = f"Undamaged – {s4['condition'].title()}"
                results["undamaged_images"].append(rec)

            results["image_results"].append(rec)

        # ── Global Total-Loss Validation ────────────────────────────────
        tl_imgs = [r for r in results["damaged_images"]
                   if r.get("damage_type") == "total_loss"]
        tl_count = len(tl_imgs)

        # 1. Severity sanity-check: only keep TL images where Stage 3
        #    also says "severe" (minor/moderate contradicts total loss)
        tl_severe = [r for r in tl_imgs
                     if r.get("s3_severity", "").lower() == "severe"]

        # 2. Contradicting undamaged evidence
        good_undamaged = any(
            r.get("condition", "").lower() in _GOOD_OR_BETTER
            for r in results["undamaged_images"]
        )

        # 3. Ratio check
        ext = results["exterior_count"] or 1
        tl_ratio = len(tl_severe) / ext

        # Decision
        if good_undamaged:
            total_loss_confirmed = False
        elif results["exterior_count"] <= 1:
            total_loss_confirmed = len(tl_severe) > 0
        elif tl_ratio >= TL_MIN_RATIO:
            total_loss_confirmed = True
        else:
            total_loss_confirmed = False

        results["total_loss_detected"] = total_loss_confirmed

        # Downgrade false-positive TL images → severe damaged
        if tl_count > 0 and not total_loss_confirmed:
            for img in tl_imgs:
                sev = img.get("s3_severity", "severe")
                img["damage_type"] = "body"
                img["severity"] = sev
                img["score"] = None
                img["final_label"] = (
                    f"Damaged – Body ({sev.title()})  "
                    f"[Total-loss overridden by cross-image check]"
                )
                img["reason"] = (
                    "Total Loss was predicted but overridden: "
                    + ("Stage 3 severity was only "
                       + f"'{sev}' (not severe)."
                       if sev != "severe"
                       else "other images contradict a write-off.")
                )

        # ── Global False-Damage Override ────────────────────────────────
        # If most exterior images are undamaged (good+ condition), then
        # isolated low-confidence or minor-severity damage detections are
        # likely false positives → reclassify them as undamaged via S4.
        undamaged_ratio = (results["undamaged_count"] / ext) if ext else 0
        if undamaged_ratio >= DMG_OVERRIDE_UNDAMAGED_RATIO:
            to_override = []
            for img in results["damaged_images"]:
                s2_conf = img.get("stages", {}).get("s2", {}).get("confidence", 1.0)
                sev = img.get("severity", "moderate").lower()
                if s2_conf < DMG_OVERRIDE_S2_CONF or sev in ("minor", "moderate"):
                    to_override.append(img)

            for img in to_override:
                # Run through Stage 4 to get condition
                s4 = stage4.predict(self.models["s4"], img["path"])
                img["stages"]["s4"] = s4
                img["condition"] = s4["condition"]
                img["confidence"] = s4.get("confidence", 0.7)
                old_label = img["final_label"]
                img["final_label"] = (
                    f"Undamaged – {s4['condition'].title()}  "
                    f"[damage overridden: most images are undamaged]"
                )
                img["score"] = None
                img.pop("damage_type", None)
                img.pop("severity", None)
                img["reason"] = (
                    f"Originally detected as damaged ({old_label}) but "
                    f"overridden because the majority of images show the "
                    f"car is in good condition."
                )
                # Move from damaged → undamaged lists
                results["damaged_images"].remove(img)
                results["undamaged_images"].append(img)
                results["damaged_count"] -= 1
                results["undamaged_count"] += 1

        return results
