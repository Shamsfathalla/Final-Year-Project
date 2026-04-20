import numpy as np
from pipeline_helpers import (
    get_torch, get_device, safe_load, safe_predict, torch_preprocess, 
    torch_predict_probs, load_timm_model, load_timm_feature_extractor,
    load_mlp_model
)

S2_WEIGHTS = {
    "ViT": 0.45,
    "YOLO": 0.35,
    "MLP": 0.20,
}

def _normalise_damage_type(class_name):
    cn = class_name.strip().lower()
    if cn in ("undamaged", "total_loss"):
        return cn
    parts = cn.split()
    if len(parts) == 2:
        part, cat = parts
        return f"{part}_{cat.replace('_damage', '')}"
    return cn.replace("_damage", "")

def load(base_dir):
    dev = get_device()
    from ultralytics import YOLO
    import joblib

    d = base_dir / "damage detection" / "models"
    s = {}

    s["le"] = safe_load("S2 LabelEncoder", lambda: joblib.load(d / "label_encoder.pkl"))
    s["classes"] = list(s["le"].classes_) if s["le"] else []
    s["scaler"] = safe_load("S2 Scaler", lambda: joblib.load(d / "scaler.pkl"))

    num_classes = len(s["classes"]) if s["classes"] else 15

    # Stage 2 uses ViT + YOLO + MLP weighted ensemble.
    s["vit"] = safe_load("S2 ViT", lambda: load_timm_model("vit_base_patch16_224", num_classes, d / "vit_model.pth", dev))
    s["yolo"] = safe_load("S2 YOLO", lambda: YOLO(str(d / "yolov8_classifier_best.pt")))
    
    if s["yolo"] and not s["classes"]:
        s["classes"] = [s["yolo"].names[i] for i in sorted(s["yolo"].names)]

    s["feat_ext"] = safe_load("S2 Feature Extractor", lambda: load_timm_feature_extractor("efficientnet_b0", d / "efficientnet_model.pth", dev))
    
    # MLP expects 1280 inputs and outputs num_classes
    s["mlp"] = safe_load("S2 MLP", lambda: load_mlp_model(1280, num_classes, d / "mlp_model.pth", dev))

    return {k: v for k, v in s.items() if v is not None}

def predict(models, img_path):
    if not models:
        return {"is_damaged": False, "damage_type": None, "class_name": "undamaged", "confidence": 0.5, "details": {}}

    classes = models.get("classes", [])
    le = models.get("le")
    tensor = torch_preprocess(img_path)
    details = {}
    model_probs = {}

    def _decode(probs):
        idx = int(np.argmax(probs))
        lbl = le.inverse_transform([idx])[0] if le else (classes[idx] if idx < len(classes) else "unknown")
        return {"prediction": lbl, "confidence": float(np.max(probs))}

    if "vit" in models and classes:
        probs = safe_predict("S2-vit", lambda: torch_predict_probs(models["vit"], tensor))
        if probs is not None:
            model_probs["ViT"] = probs
            d = _decode(probs)
            d["weight"] = S2_WEIGHTS["ViT"]
            details["ViT"] = d

    if "yolo" in models:
        def _yolo():
            res = models["yolo"](img_path, verbose=False)
            return res[0].probs.data.cpu().numpy()
        probs = safe_predict("S2-yolo", _yolo)
        if probs is not None and classes:
            model_probs["YOLO"] = probs
            d = _decode(probs)
            d["weight"] = S2_WEIGHTS["YOLO"]
            details["YOLO"] = d

    feats_s = None
    if "feat_ext" in models and "scaler" in models:
        def _get_feats():
            with get_torch().no_grad():
                x = models["feat_ext"](tensor)
                return models["scaler"].transform(x.cpu().numpy())
        feats_s = safe_predict("S2-feat", _get_feats)

    if feats_s is not None and classes:
        if "mlp" in models and hasattr(models["mlp"], 'eval'):
            probs = safe_predict("S2-mlp", lambda: torch_predict_probs(models["mlp"], get_torch().tensor(feats_s).to(get_device()).float()))
            if probs is not None:
                model_probs["MLP"] = probs
                d = _decode(probs)
                d["weight"] = S2_WEIGHTS["MLP"]
                details["MLP"] = d

    agg = np.zeros(len(classes), dtype=float)
    used_w = 0.0
    for model_name, probs in model_probs.items():
        if len(probs) != len(classes):
            continue
        w = S2_WEIGHTS.get(model_name, 0.0)
        if w <= 0:
            continue
        agg += (probs * w)
        used_w += w

    if used_w > 0:
        final_probs = agg / used_w
        idx = int(np.argmax(final_probs))
        final = le.inverse_transform([idx])[0] if le else classes[idx]
        avg_c = float(np.max(final_probs))
    else:
        final = "undamaged"
        avg_c = 0.5

    is_damaged = final.lower() != "undamaged"
    dtype = _normalise_damage_type(final) if is_damaged else None

    return {"is_damaged": is_damaged, "damage_type": dtype, "class_name": final, "confidence": avg_c, "details": details}