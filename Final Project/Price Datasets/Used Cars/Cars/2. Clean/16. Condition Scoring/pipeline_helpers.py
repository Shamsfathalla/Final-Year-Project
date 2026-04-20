"""
Shared helpers for the 4-stage car assessment pipeline.

Provides lazy framework imports, PyTorch model loading wrappers,
image preprocessing, feature extraction, and ensemble majority-vote logic.
"""

import os
import logging
import numpy as np
from collections import Counter
from PIL import Image

logger = logging.getLogger(__name__)

_torch = None
_timm = None
_transform = None

def get_torch():
    global _torch
    if _torch is None:
        import torch
        _torch = torch
    return _torch

def get_timm():
    global _timm
    if _timm is None:
        import timm
        _timm = timm
    return _timm

def get_device():
    torch = get_torch()
    return torch.device("cuda" if torch.cuda.is_available() else "cpu")

def get_transform(target_size=(224, 224)):
    global _transform
    if _transform is None:
        from torchvision import transforms
        _transform = transforms.Compose([
            transforms.Resize(target_size),
            transforms.ToTensor(),
            transforms.Normalize([0.485, 0.456, 0.406], [0.229, 0.224, 0.225]),
        ])
    return _transform

def torch_preprocess(img_path, target_size=(224, 224)):
    tx = get_transform(target_size)
    img = Image.open(img_path).convert("RGB")
    return tx(img).unsqueeze(0).to(get_device())

# ── TIMM Model Loaders ──────────────────────────────────────────────────
def load_timm_model(model_name, num_classes, weights_path, device):
    """Instantiates a timm architecture and loads the state_dict."""
    timm = get_timm()
    torch = get_torch()
    model = timm.create_model(model_name, pretrained=False, num_classes=num_classes)
    
    state_dict = torch.load(weights_path, map_location=device)
    if 'state_dict' in state_dict: 
        state_dict = state_dict['state_dict']
    
    state_dict = {k.replace('model.', '').replace('module.', ''): v for k, v in state_dict.items()}
    model.load_state_dict(state_dict, strict=False)
    model.to(device)
    model.eval()
    return model

def load_timm_feature_extractor(model_name, weights_path, device):
    """Instantiates a timm model with NO classifier (num_classes=0) for feature extraction."""
    return load_timm_model(model_name, num_classes=0, weights_path=weights_path, device=device)

# ── Custom MLP Architecture & Loader ────────────────────────────────────
def get_nn():
    import torch.nn as nn
    return nn

class CarMLP(get_nn().Module):
    """
    IMPORTANT: Adjust these layers to match exactly what you built in your training notebook!
    """
    def __init__(self, input_size, num_classes):
        nn = get_nn()
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
    """Instantiates the custom MLP and loads the state_dict."""
    torch = get_torch()
    model = CarMLP(input_size, num_classes)
    
    state_dict = torch.load(weights_path, map_location=device)
    if 'state_dict' in state_dict: 
        state_dict = state_dict['state_dict']
    
    state_dict = {k.replace('model.', '').replace('module.', ''): v for k, v in state_dict.items()}
    model.load_state_dict(state_dict, strict=False)
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
    torch = get_torch()
    model.eval()
    with torch.no_grad():
        out = model(tensor)
        if out.shape[1] > 1:
            probs = torch.softmax(out, dim=1)
        else:
            probs = torch.sigmoid(out)
    return probs.cpu().numpy()[0]

def majority_vote(details, tie_break="confidence"):
    if not details:
        return None, 0.5

    preds = [d["prediction"] for d in details.values()]
    vc = Counter(preds)
    mc = vc.most_common()

    is_tie = len(mc) > 1 and mc[0][1] == mc[1][1]

    if is_tie:
        if tie_break == "soft" and all("prob_ext" in d for d in details.values()):
            avg_p = float(np.mean([d["prob_ext"] for d in details.values()]))
            winner = "Exterior" if avg_p >= 0.5 else "Interior"
        else:
            ranked = sorted(details.values(), key=lambda d: d["confidence"], reverse=True)
            winner = ranked[0]["prediction"]
    else:
        winner = mc[0][0]

    confs = [d["confidence"] for d in details.values() if d["prediction"] == winner]
    avg_c = float(np.mean(confs)) if confs else 0.5
    return winner, avg_c