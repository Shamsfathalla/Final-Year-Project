"""
Car Scoring Logic
=================
Translates pipeline stage outputs into a single numerical score (0–10).
"""

from __future__ import annotations
import numpy as np
from collections import Counter

CONDITION_RANGES: dict[str, tuple[float, float]] = {
    "poor":      (0.0, 2.9),
    "fair":      (3.0, 4.9),
    "good":      (5.0, 6.9),
    "very good": (7.0, 8.4),
    "excellent": (8.5, 10.0),
}

SEVERITY_SCORE_CEILING: dict[str, float] = {"minor": 4.0, "moderate": 2.0, "severe": 0.5}
SEVERITY_DEDUCTIONS: dict[str, float] = {"minor": 1.5, "moderate": 3.5, "severe": 6.0}

DAMAGE_TYPE_FACTOR: dict[str, float] = {
    "bumper_surface": 0.85, "fender_surface": 0.85, "door_surface": 0.90,
    "mirror_surface": 0.80, "hood_surface": 0.90,
    "bumper_body": 1.00, "fender_body": 1.00, "door_body": 1.15, "hood_body": 1.15,
    "glass": 1.25, "wheel": 1.25, "light": 1.05,
    "total_loss": 10.00,
}

_GRADES = [
    (8.5, "Excellent", "green"),
    (7.0, "Very Good", "teal"),
    (5.0, "Good",      "blue"),
    (3.0, "Fair",      "orange"),
    (0.0, "Poor",      "red"),
]

def _score_damaged(severity: str, damage_type: str | None) -> float:
    if damage_type and damage_type.lower() == "total_loss":
        return 0.0
    ceiling = SEVERITY_SCORE_CEILING.get(severity.lower(), 2.0)
    factor = DAMAGE_TYPE_FACTOR.get((damage_type or "").lower(), 1.0)
    adjusted = ceiling / factor if factor > 1.0 else ceiling + (1.0 - factor) * 1.5
    return round(max(0.0, min(ceiling + 1.5, adjusted)), 1)

def _deduction_for_damaged(severity: str, damage_type: str | None) -> float:
    base = SEVERITY_DEDUCTIONS.get(severity.lower(), 3.5)
    factor = DAMAGE_TYPE_FACTOR.get((damage_type or "").lower(), 1.0)
    return round(base * factor, 2)

def _grade_for(score: float) -> tuple[str, str]:
    for threshold, label, colour in _GRADES:
        if score >= threshold:
            return label, colour
    return "Poor", "red"

def _condition_score(condition: str, confidence: float = 0.7) -> float:
    lo, hi = CONDITION_RANGES.get(condition.lower(), (5.0, 6.9))
    return round(lo + (hi - lo) * max(0.0, min(1.0, confidence)), 1)

def score_image(image_result: dict) -> float:
    if image_result.get("damage_type") == "total_loss":
        return 0.0
    if "condition" in image_result:
        conf = image_result.get("confidence", 0.7)
        return _condition_score(image_result["condition"], conf)
    if "severity" in image_result and "damage_type" in image_result:
        return _score_damaged(image_result["severity"], image_result["damage_type"])
    return 6.0

def calculate_final_score(pipeline_results: dict) -> dict:
    if pipeline_results["total_loss_detected"]:
        return {
            "final_score": 0.0, "total_loss": True,
            "grade": "Total Loss", "grade_colour": "red",
            "summary": "Total Loss detected – the vehicle is a write-off.",
            "image_scores": [], "condition_summary": "Total Loss",
            "damage_summary": "Total Loss detected in one or more images.",
        }

    ext = pipeline_results["exterior_count"]
    if ext == 0:
        return {
            "final_score": 0.0, "total_loss": False,
            "grade": "N/A", "grade_colour": "grey",
            "summary": (f"All {pipeline_results['total_images']} images were "
                        "classified as interior views – no exterior images to assess."),
            "image_scores": [], "condition_summary": "No exterior images",
            "damage_summary": "N/A",
        }

    image_scores: list[dict] = []
    for rec in pipeline_results["image_results"]:
        if rec.get("score") is not None: sc = rec["score"]
        elif "condition" in rec or ("severity" in rec and "damage_type" in rec): sc = score_image(rec)
        else: continue
        
        rec["score"] = sc
        image_scores.append({"filename": rec["filename"], "label": rec["final_label"], "score": sc})

    undamaged_scores = [_condition_score(r["condition"], r.get("confidence", 0.7)) for r in pipeline_results["undamaged_images"] if "condition" in r]
    base = float(np.mean(undamaged_scores)) if undamaged_scores else 6.0

    total_deduction = sum(_deduction_for_damaged(r.get("severity", "moderate"), r.get("damage_type")) for r in pipeline_results["damaged_images"])
    spread = total_deduction * max(pipeline_results["damaged_count"] / ext, 0.6)
    final = round(max(0.0, min(10.0, base - spread)), 1)

    cond_counts = Counter(r.get("condition", "").title() for r in pipeline_results["undamaged_images"])
    condition_summary = ", ".join(f"{v} {k}" for k, v in cond_counts.items() if k) or "No undamaged images"

    dmg_parts = [f"{(r.get('damage_type') or 'unknown').replace('_', ' ').title()} ({(r.get('severity') or 'unknown').title()})" for r in pipeline_results["damaged_images"]]
    damage_summary = ", ".join(dmg_parts) or "No damage detected"

    n, ni = pipeline_results["total_images"], pipeline_results["interior_count"]
    nd, nu = pipeline_results["damaged_count"], pipeline_results["undamaged_count"]

    parts = [f"Processed {n} image{'s' if n != 1 else ''}."]
    if ni: parts.append(f"{ni} interior (discarded).")
    if nd: parts.append(f"{nd} contained damage ({damage_summary}).")
    if nu: parts.append(f"{nu} undamaged ({condition_summary}).")

    grade, colour = _grade_for(final)

    return {
        "final_score": final, "total_loss": False,
        "grade": grade, "grade_colour": colour,
        "summary": " ".join(parts),
        "image_scores": image_scores,
        "condition_summary": condition_summary,
        "damage_summary": damage_summary,
    }