import numpy as np
from pipeline_helpers import (
    get_torch, get_device, safe_load, safe_predict, torch_preprocess, 
    torch_predict_probs, load_timm_model, load_timm_feature_extractor
)

_SEV_MAP = {"01-minor": "minor", "02-moderate": "moderate", "03-severe": "severe"}
S3_WEIGHTS = {
    "ViT": 0.40,
    "SVM": 0.35,
    "YOLO": 0.25,
}

def load(base_dir):
    dev = get_device()
    from ultralytics import YOLO
    import joblib

    d = base_dir / "damage severity" / "models"
    s = {}
    
    s["classes"] = ["01-minor", "02-moderate", "03-severe"]

    # Stage 3 uses ViT + SVM + YOLO weighted ensemble.
    s["vit"] = safe_load("S3 ViT", lambda: load_timm_model("vit_base_patch16_224", 3, d / "vit_model.pth", dev))
    s["yolo"] = safe_load("S3 YOLO", lambda: YOLO(str(d / "yolov8_classifier_best.pt")))
    
    s["feat_ext"] = safe_load("S3 Feature Extractor", lambda: load_timm_feature_extractor("efficientnet_b0", d / "efficientnet_model.pth", dev))
    
    s["svm"] = safe_load("S3 SVM", lambda: joblib.load(d / "svm_model.pkl"))
    s["scaler"] = safe_load("S3 Scaler", lambda: joblib.load(d / "feature_scaler.pkl"))

    return {k: v for k, v in s.items() if v is not None}

def predict(models, img_path):
    cls = models.get("classes", ["01-minor", "02-moderate", "03-severe"])
    tensor = torch_preprocess(img_path)
    details = {}
    model_probs = {}

    def _decode(probs):
        idx = int(np.argmax(probs))
        return {"prediction": cls[idx], "confidence": float(np.max(probs))}

    if "vit" in models:
        probs = safe_predict("S3-vit", lambda: torch_predict_probs(models["vit"], tensor))
        if probs is not None:
            model_probs["ViT"] = probs
            d = _decode(probs)
            d["weight"] = S3_WEIGHTS["ViT"]
            details["ViT"] = d

    if "yolo" in models:
        def _yolo():
            res = models["yolo"](img_path, verbose=False)
            return res[0].probs.data.cpu().numpy()
        probs = safe_predict("S3-yolo", _yolo)
        if probs is not None and len(probs) == len(cls):
            model_probs["YOLO"] = probs
            d = _decode(probs)
            d["weight"] = S3_WEIGHTS["YOLO"]
            details["YOLO"] = d

    feats_s = None
    if "feat_ext" in models and "scaler" in models:
        def _get_feats():
            with get_torch().no_grad():
                x = models["feat_ext"](tensor)
                return models["scaler"].transform(x.cpu().numpy())
        feats_s = safe_predict("S3-feat", _get_feats)

    if feats_s is not None:
        if "svm" in models:
            def _svm_probs_aligned():
                raw = models["svm"].predict_proba(feats_s)[0]
                aligned = np.zeros(len(cls), dtype=float)
                for j, c in enumerate(models["svm"].classes_):
                    try:
                        idx = int(c)
                    except Exception:
                        idx = cls.index(str(c)) if str(c) in cls else -1
                    if 0 <= idx < len(cls):
                        aligned[idx] = raw[j]
                s = float(np.sum(aligned))
                return aligned / s if s > 0 else aligned

            probs = safe_predict("S3-svm", _svm_probs_aligned)
            if probs is not None and len(probs) == len(cls):
                model_probs["SVM"] = probs
                d = _decode(probs)
                d["weight"] = S3_WEIGHTS["SVM"]
                details["SVM"] = d

    agg = np.zeros(len(cls), dtype=float)
    used_w = 0.0
    for model_name, probs in model_probs.items():
        w = S3_WEIGHTS.get(model_name, 0.0)
        if w <= 0 or len(probs) != len(cls):
            continue
        agg += (probs * w)
        used_w += w

    if used_w > 0:
        final_probs = agg / used_w
        idx = int(np.argmax(final_probs))
        final = cls[idx]
        avg_c = float(np.max(final_probs))
    else:
        final = cls[0]
        avg_c = 0.5

    return {"severity": _SEV_MAP.get(final, "minor"), "severity_class": final, "confidence": avg_c, "details": details}