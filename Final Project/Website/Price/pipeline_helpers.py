"""
Shared helpers for the 4-stage car assessment pipeline.
"""
import os
import logging
import numpy as np
from PIL import Image
import torch
import torch.nn as nn
import timm
from torchvision import transforms

logger = logging.getLogger(__name__)

def get_device():
    return torch.device("cuda" if torch.cuda.is_available() else "cpu")

_transform = transforms.Compose([
    transforms.Resize((224, 224)),
    transforms.ToTensor(),
    transforms.Normalize([0.485, 0.456, 0.406], [0.229, 0.224, 0.225]),
])

def torch_preprocess(img_path):
    """Preprocess the image once to be used by all PyTorch models."""
    img = Image.open(img_path).convert("RGB")
    return _transform(img).unsqueeze(0).to(get_device())

def clean_state_dict(weights_path, device):
    """Loads and standardizes PyTorch state dictionaries."""
    state_dict = torch.load(weights_path, map_location=device)
    if 'state_dict' in state_dict: 
        state_dict = state_dict['state_dict']
    return {k.replace('model.', '').replace('module.', ''): v for k, v in state_dict.items()}

# ── Model Loaders ───────────────────────────────────────────────────────
def load_timm_model(model_name, num_classes, weights_path, device):
    model = timm.create_model(model_name, pretrained=False, num_classes=num_classes)
    model.load_state_dict(clean_state_dict(weights_path, device), strict=False)
    model.to(device)
    model.eval()
    return model

def load_timm_feature_extractor(model_name, weights_path, device):
    return load_timm_model(model_name, num_classes=0, weights_path=weights_path, device=device)

class CarMLP(nn.Module):
    def __init__(self, input_size, num_classes):
        super().__init__()
        self.network = nn.Sequential(
            nn.Linear(input_size, 256), 
            nn.ReLU(),
            nn.Dropout(0.3),
            nn.Linear(256, num_classes)
        )

    def forward(self, x):
        return self.network(x)

def load_mlp_model(input_size, num_classes, weights_path, device):
    model = CarMLP(input_size, num_classes)
    model.load_state_dict(clean_state_dict(weights_path, device), strict=False)
    model.to(device)
    model.eval()
    return model

# ── Safeload & Prediction Wrappers ──────────────────────────────────────
def safe_load(label, loader):
    try:
        m = loader()
        if isinstance(m, dict) and 'state_dict' not in m:
            logger.warning("%s ✗ Loaded object is a dict/OrderedDict, not a model instance.", label)
            return None
        logger.info("%s ✓", label)
        return m
    except Exception as e:
        logger.warning("%s ✗  %s", label, e)
        return None

def safe_predict(tag, fn):
    try:
        return fn()
    except Exception as e:
        logger.warning("%s  %s", tag, e)
        return None

def torch_predict_probs(model, tensor):
    model.eval()
    with torch.no_grad():
        out = model(tensor)
        probs = torch.softmax(out, dim=1) if out.shape[1] > 1 else torch.sigmoid(out)
    return probs.cpu().numpy()[0]

def calculate_ensemble_probs(model_probs, weights, num_classes):
    """Calculates weighted average probabilities across multiple models."""
    agg = np.zeros(num_classes, dtype=float)
    used_w = 0.0
    for name, probs in model_probs.items():
        w = weights.get(name, 0.0)
        if w > 0 and len(probs) == num_classes:
            agg += (probs * w)
            used_w += w
    return (agg / used_w) if used_w > 0 else None

def decode_probs(probs, classes, le=None, weight=None):
    """Shared helper to decode predictions across stages."""
    idx = int(np.argmax(probs))
    lbl = le.inverse_transform([idx])[0] if le else (classes[idx] if idx < len(classes) else classes[0])
    res = {"prediction": lbl, "confidence": float(np.max(probs))}
    if weight is not None:
        res["weight"] = weight
    return res