import numpy as np
from pipeline_helpers import (
    get_torch, get_device, safe_load, safe_predict, torch_preprocess, 
    torch_predict_probs, load_timm_model
)

def load(base_dir):
    dev = get_device()

    d = base_dir / "exterior detection" / "models"
    s = {}

    # Stage 1 uses ViT only.
    s["vit"] = safe_load("S1 ViT", lambda: load_timm_model("vit_base_patch16_224", 2, d / "vit_model.pth", dev))

    return {k: v for k, v in s.items() if v is not None}

def predict(models, img_path):
    if not models:
        return {"label": "exterior", "confidence": 0.5, "details": {}}

    tensor = torch_preprocess(img_path)
    details = {}

    def _binary(probs):
        p_ext = float(probs[1]) if len(probs) > 1 else float(probs[0])
        lbl = "Exterior" if p_ext >= 0.5 else "Interior"
        return {"prob_ext": p_ext, "prediction": lbl, "confidence": p_ext if p_ext >= 0.5 else 1.0 - p_ext}

    if "vit" in models:
        r = safe_predict("S1-vit", lambda: _binary(torch_predict_probs(models["vit"], tensor)))
        if r: details["ViT"] = r
    vit = details.get("ViT")
    if not vit:
        return {"label": "exterior", "confidence": 0.5, "details": details}

    label = vit["prediction"].lower()
    final_conf = float(vit["confidence"])

    return {"label": label, "confidence": final_conf, "details": details}