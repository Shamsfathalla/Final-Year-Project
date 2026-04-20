import numpy as np
from pipeline_helpers import (
    get_torch, get_device, safe_load, safe_predict, torch_preprocess, 
    torch_predict_probs, load_timm_model
)

def load(base_dir):
    dev = get_device()
    import joblib

    d = base_dir / "undamaged condition" / "models"
    s = {}

    s["le"] = safe_load("S4 LabelEncoder", lambda: joblib.load(d / "label_encoder.pkl"))
    s["classes"] = list(s["le"].classes_) if s["le"] else ["excellent", "fair", "good", "poor", "very good"]
    num_classes = len(s["classes"])

    # Stage 4 uses ViT only.
    s["vit"] = safe_load("S4 ViT", lambda: load_timm_model("vit_base_patch16_224", num_classes, d / "vit_model.pth", dev))

    return {k: v for k, v in s.items() if v is not None}

def predict(models, img_path):
    cls = models.get("classes", ["excellent", "fair", "good", "poor", "very good"])
    le = models.get("le")
    tensor = torch_preprocess(img_path)
    details = {}

    def _decode(probs):
        idx = int(np.argmax(probs))
        lbl = le.inverse_transform([idx])[0] if le else (cls[idx] if idx < len(cls) else cls[0])
        return {"prediction": lbl, "confidence": float(np.max(probs))}

    if "vit" in models:
        r = safe_predict("S4-vit", lambda: _decode(torch_predict_probs(models["vit"], tensor)))
        if r: details["ViT"] = r

    vit = details.get("ViT")
    if vit:
        condition = vit["prediction"]
        avg_c = float(vit["confidence"])
    else:
        condition = "good"
        avg_c = 0.5

    return {"condition": condition, "confidence": avg_c, "details": details}