import numpy as np
import torch
from pipeline_helpers import (
    get_device, safe_load, safe_predict, torch_predict_probs, load_timm_model, 
    load_timm_feature_extractor, load_mlp_model, calculate_ensemble_probs, decode_probs
)

S2_WEIGHTS = {"ViT": 0.45, "YOLO": 0.35, "MLP": 0.20}

def _normalise_damage_type(class_name):
    cn = class_name.strip().lower()
    if cn in ("undamaged", "total_loss"): return cn
    parts = cn.split()
    return f"{parts[0]}_{parts[1].replace('_damage', '')}" if len(parts) == 2 else cn.replace("_damage", "")

def load(base_dir):
    dev = get_device()
    from ultralytics import YOLO
    import joblib

    d = base_dir / "models" / "damage detection" / "models"
    s = {}

    s["le"] = safe_load("S2 LabelEncoder", lambda: joblib.load(d / "label_encoder.pkl"))
    s["classes"] = list(s["le"].classes_) if s["le"] else []
    s["scaler"] = safe_load("S2 Scaler", lambda: joblib.load(d / "scaler.pkl"))

    num_classes = len(s["classes"]) if s["classes"] else 15

    s["vit"] = safe_load("S2 ViT", lambda: load_timm_model("vit_base_patch16_224", num_classes, d / "vit_model.pth", dev))
    s["yolo"] = safe_load("S2 YOLO", lambda: YOLO(str(d / "yolov8_classifier_best.pt")))
    
    if s["yolo"] and not s["classes"]:
        s["classes"] = [s["yolo"].names[i] for i in sorted(s["yolo"].names)]

    s["feat_ext"] = safe_load("S2 Feature Extractor", lambda: load_timm_feature_extractor("efficientnet_b0", d / "efficientnet_model.pth", dev))
    s["mlp"] = safe_load("S2 MLP", lambda: load_mlp_model(1280, num_classes, d / "mlp_model.pth", dev))

    return {k: v for k, v in s.items() if v is not None}

def predict(models, img_path, tensor):
    if not models:
        return {"is_damaged": False, "damage_type": None, "class_name": "undamaged", "confidence": 0.5, "details": {}}

    classes, le = models.get("classes", []), models.get("le")
    details, model_probs = {}, {}

    if "vit" in models and classes:
        probs = safe_predict("S2-vit", lambda: torch_predict_probs(models["vit"], tensor))
        if probs is not None:
            model_probs["ViT"] = probs
            details["ViT"] = decode_probs(probs, classes, le, S2_WEIGHTS["ViT"])

    if "yolo" in models and classes:
        probs = safe_predict("S2-yolo", lambda: models["yolo"](img_path, verbose=False)[0].probs.data.cpu().numpy())
        if probs is not None:
            model_probs["YOLO"] = probs
            details["YOLO"] = decode_probs(probs, classes, le, S2_WEIGHTS["YOLO"])

    if "feat_ext" in models and "scaler" in models and "mlp" in models and classes:
        def _mlp_probs():
            with torch.no_grad():
                feats = models["scaler"].transform(models["feat_ext"](tensor).cpu().numpy())
            return torch_predict_probs(models["mlp"], torch.tensor(feats).to(get_device()).float())
        
        probs = safe_predict("S2-mlp", _mlp_probs)
        if probs is not None:
            model_probs["MLP"] = probs
            details["MLP"] = decode_probs(probs, classes, le, S2_WEIGHTS["MLP"])

    final_probs = calculate_ensemble_probs(model_probs, S2_WEIGHTS, len(classes))
    
    if final_probs is not None:
        idx = int(np.argmax(final_probs))
        final = le.inverse_transform([idx])[0] if le else classes[idx]
        avg_c = float(np.max(final_probs))
    else:
        final, avg_c = "undamaged", 0.5

    is_damaged = final.lower() != "undamaged"
    return {
        "is_damaged": is_damaged, 
        "damage_type": _normalise_damage_type(final) if is_damaged else None, 
        "class_name": final, 
        "confidence": avg_c, 
        "details": details
    }