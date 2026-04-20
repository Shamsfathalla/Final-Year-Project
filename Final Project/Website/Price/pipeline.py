import os
import logging
from pathlib import Path

import stage1, stage2, stage3, stage4
from pipeline_helpers import torch_preprocess

logger = logging.getLogger(__name__)

TL_MIN_RATIO = 0.4          
_GOOD_OR_BETTER = {"good", "very good", "excellent"}
DMG_OVERRIDE_UNDAMAGED_RATIO = 0.6   
DMG_OVERRIDE_S2_CONF = 0.65          

class CarAssessmentPipeline:
    def __init__(self, base_dir: str):
        self.base_dir = Path(base_dir)
        self.models: dict = {}
        self._loaded = False

    def load_all_models(self):
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
        self.load_all_models()

        results = {
            "total_images": len(image_paths),
            "interior_count": 0, "exterior_count": 0,
            "damaged_count": 0, "undamaged_count": 0,
            "total_loss_detected": False,
            "image_results": [], "damaged_images": [], "undamaged_images": [],
        }

        for img_path in image_paths:
            rec = {"filename": os.path.basename(img_path), "path": img_path, "stages": {}}

            try:
                # Preprocess tensor exactly ONCE per image
                tensor = torch_preprocess(img_path)
            except Exception as e:
                logger.error(f"Failed to preprocess {img_path}: {e}")
                continue

            # ---- Stage 1 ----
            s1 = stage1.predict(self.models["s1"], img_path, tensor)
            rec["stages"]["s1"] = s1
            if s1["label"] == "interior":
                rec["final_label"] = "Interior (Discarded)"
                rec["score"] = None
                results["interior_count"] += 1
                results["image_results"].append(rec)
                continue

            results["exterior_count"] += 1

            # ---- Stage 2 ----
            s2 = stage2.predict(self.models["s2"], img_path, tensor)
            rec["stages"]["s2"] = s2

            if s2["is_damaged"]:
                results["damaged_count"] += 1

                if s2["damage_type"] == "total_loss":
                    s3 = stage3.predict(self.models["s3"], img_path, tensor)
                    rec["stages"]["s3"] = s3

                    if s3["severity"] == "severe":
                        rec.update({
                            "final_label": "Total Loss", "damage_type": "total_loss",
                            "severity": "total_loss", "s3_severity": s3["severity"], "score": 0
                        })
                        results["damaged_images"].append(rec)
                        results["image_results"].append(rec)
                        continue
                    else:
                        rec.update({
                            "damage_type": "body", "severity": s3["severity"],
                            "final_label": f"Damaged – Body ({s3['severity'].title()}) [S2 predicted total-loss but S3 severity is {s3['severity']}]"
                        })
                        results["damaged_images"].append(rec)
                        results["image_results"].append(rec)
                        continue

                # ---- Stage 3 ----
                s3 = stage3.predict(self.models["s3"], img_path, tensor)
                rec.update({
                    "stages": {"s1": s1, "s2": s2, "s3": s3},
                    "damage_type": s2["damage_type"], "severity": s3["severity"],
                    "final_label": f"Damaged – {s2['damage_type'].replace('_', ' ').title()} ({s3['severity'].title()})"
                })
                results["damaged_images"].append(rec)
            else:
                results["undamaged_count"] += 1
                # ---- Stage 4 ----
                s4 = stage4.predict(self.models["s4"], img_path, tensor)
                rec.update({
                    "stages": {"s1": s1, "s2": s2, "s4": s4},
                    "condition": s4["condition"], "confidence": s4.get("confidence", 0.7),
                    "final_label": f"Undamaged – {s4['condition'].title()}"
                })
                results["undamaged_images"].append(rec)

            results["image_results"].append(rec)

        # ── Global Total-Loss Validation ────────────────────────────────
        tl_imgs = [r for r in results["damaged_images"] if r.get("damage_type") == "total_loss"]
        tl_severe = [r for r in tl_imgs if r.get("s3_severity", "").lower() == "severe"]
        good_undamaged = any(r.get("condition", "").lower() in _GOOD_OR_BETTER for r in results["undamaged_images"])
        ext = results["exterior_count"] or 1
        
        if good_undamaged: total_loss_confirmed = False
        elif results["exterior_count"] <= 1: total_loss_confirmed = len(tl_severe) > 0
        else: total_loss_confirmed = (len(tl_severe) / ext) >= TL_MIN_RATIO

        results["total_loss_detected"] = total_loss_confirmed

        if len(tl_imgs) > 0 and not total_loss_confirmed:
            for img in tl_imgs:
                sev = img.get("s3_severity", "severe")
                img.update({
                    "damage_type": "body", "severity": sev, "score": None,
                    "final_label": f"Damaged – Body ({sev.title()}) [Total-loss overridden by cross-image check]",
                    "reason": "Total Loss was predicted but overridden: " + ("Stage 3 severity was only " + f"'{sev}' (not severe)." if sev != "severe" else "other images contradict a write-off.")
                })

        # ── Global False-Damage Override ────────────────────────────────
        if ext and (results["undamaged_count"] / ext) >= DMG_OVERRIDE_UNDAMAGED_RATIO:
            to_override = [img for img in results["damaged_images"] if img.get("stages", {}).get("s2", {}).get("confidence", 1.0) < DMG_OVERRIDE_S2_CONF or img.get("severity", "moderate").lower() in ("minor", "moderate")]
            for img in to_override:
                # Recalculate tensor for overrides to avoid memory bloat of saving all tensors
                override_tensor = torch_preprocess(img["path"])
                s4 = stage4.predict(self.models["s4"], img["path"], override_tensor)
                old_label = img["final_label"]
                img.update({
                    "stages": {**img["stages"], "s4": s4}, "condition": s4["condition"],
                    "confidence": s4.get("confidence", 0.7), "score": None,
                    "final_label": f"Undamaged – {s4['condition'].title()} [damage overridden: most images are undamaged]",
                    "reason": f"Originally detected as damaged ({old_label}) but overridden because the majority of images show the car is in good condition."
                })
                img.pop("damage_type", None)
                img.pop("severity", None)
                
                results["damaged_images"].remove(img)
                results["undamaged_images"].append(img)
                results["damaged_count"] -= 1
                results["undamaged_count"] += 1

        return results