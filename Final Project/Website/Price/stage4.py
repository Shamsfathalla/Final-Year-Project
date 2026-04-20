import numpy as np
from pipeline_helpers import (
    get_device, safe_load, safe_predict, torch_predict_probs, load_timm_model, decode_probs
)

def load(base_dir):
    dev = get_device()
    import joblib

    d = base_dir / "models" / "undamaged condition" / "models"
    s = {}

    s["le"] = safe_load("S4 LabelEncoder", lambda: joblib.load(d / "label_encoder.pkl"))
    s["classes"] = list(s["le"].classes_) if s["le"] else ["excellent", "fair", "good", "poor", "very good"]
    num_classes = len(s["classes"])

    s["vit"] = safe_load("S4 ViT", lambda: load_timm_model("vit_base_patch16_224", num_classes, d / "vit_model.pth", dev))

    return {k: v for k, v in s.items() if v is not None}

def predict(models, img_path, tensor):
    cls = models.get("classes", ["excellent", "fair", "good", "poor", "very good"])
    le = models.get("le")
    details = {}

    if "vit" in models:
        probs = safe_predict("S4-vit", lambda: torch_predict_probs(models["vit"], tensor))
        if probs is not None:
            details["ViT"] = decode_probs(probs, cls, le)

    vit = details.get("ViT")
    if vit:
        condition = vit["prediction"]
        avg_c = float(vit["confidence"])
    else:
        condition = "good"
        avg_c = 0.5

    return {"condition": condition, "confidence": avg_c, "details": details}