import numpy as np
import torch
from pipeline_helpers import (
    get_device, safe_load, safe_predict, torch_predict_probs, load_timm_model, 
    load_timm_feature_extractor, calculate_ensemble_probs, decode_probs
)

_SEV_MAP = {"01-minor": "minor", "02-moderate": "moderate", "03-severe": "severe"}
S3_WEIGHTS = {"ViT": 0.40, "SVM": 0.35, "YOLO": 0.25}

def load(base_dir):
    dev = get_device()
    from ultralytics import YOLO
    import joblib

    d = base_dir / "models" / "damage severity" / "models"
    s = {"classes": ["01-minor", "02-moderate", "03-severe"]}

    s["vit"] = safe_load("S3 ViT", lambda: load_timm_model("vit_base_patch16_224", 3, d / "vit_model.pth", dev))
    s["yolo"] = safe_load("S3 YOLO", lambda: YOLO(str(d / "yolov8_classifier_best.pt")))
    s["feat_ext"] = safe_load("S3 Feature Extractor", lambda: load_timm_feature_extractor("efficientnet_b0", d / "efficientnet_model.pth", dev))
    s["svm"] = safe_load("S3 SVM", lambda: joblib.load(d / "svm_model.pkl"))
    s["scaler"] = safe_load("S3 Scaler", lambda: joblib.load(d / "feature_scaler.pkl"))

    return {k: v for k, v in s.items() if v is not None}

def predict(models, img_path, tensor):
    cls = models["classes"] # Safe as it's hardcoded in load()
    details, model_probs = {}, {}

    if "vit" in models:
        probs = safe_predict("S3-vit", lambda: torch_predict_probs(models["vit"], tensor))
        if probs is not None:
            model_probs["ViT"] = probs
            details["ViT"] = decode_probs(probs, cls, weight=S3_WEIGHTS["ViT"])

    if "yolo" in models:
        probs = safe_predict("S3-yolo", lambda: models["yolo"](img_path, verbose=False)[0].probs.data.cpu().numpy())
        if probs is not None and len(probs) == len(cls):
            model_probs["YOLO"] = probs
            details["YOLO"] = decode_probs(probs, cls, weight=S3_WEIGHTS["YOLO"])

    if "feat_ext" in models and "scaler" in models and "svm" in models:
        def _svm_probs():
            with torch.no_grad():
                feats = models["scaler"].transform(models["feat_ext"](tensor).cpu().numpy())
            raw = models["svm"].predict_proba(feats)[0]
            aligned = np.zeros(len(cls), dtype=float)
            for j, c in enumerate(models["svm"].classes_):
                idx = cls.index(str(c)) if str(c) in cls else (int(c) if str(c).isdigit() else -1)
                if 0 <= idx < len(cls): aligned[idx] = raw[j]
            return aligned / np.sum(aligned) if np.sum(aligned) > 0 else aligned

        probs = safe_predict("S3-svm", _svm_probs)
        if probs is not None and len(probs) == len(cls):
            model_probs["SVM"] = probs
            details["SVM"] = decode_probs(probs, cls, weight=S3_WEIGHTS["SVM"])

    final_probs = calculate_ensemble_probs(model_probs, S3_WEIGHTS, len(cls))
    final = cls[int(np.argmax(final_probs))] if final_probs is not None else cls[0]
    avg_c = float(np.max(final_probs)) if final_probs is not None else 0.5

    return {"severity": _SEV_MAP.get(final, "minor"), "severity_class": final, "confidence": avg_c, "details": details}