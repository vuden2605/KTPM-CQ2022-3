"""
services/predictor.py
Load models và dự đoán UP/DOWN/NEUTRAL
"""

import joblib
import json
import os
import numpy as np
import pandas as pd
from typing import Optional, Dict

# Paths
MODELS_DIR = os.path.join(os.path.dirname(__file__), "..", "models")
MODEL_1H = os.path.join(MODELS_DIR, "model_1h.pkl")
MODEL_24H = os.path.join(MODELS_DIR, "model_24h.pkl")
INFO_1H = os.path.join(MODELS_DIR, "model_info_1h.json")
INFO_24H = os.path.join(MODELS_DIR, "model_info_24h.json")

# Global models
models = {}
infos = {}


def load_models():
    """Load models at startup"""
    global models, infos
    
    print("=" * 70)
    print("LOADING AI MODELS...")
    print("=" * 70)
    
    # Load 1H model
    try:
        models['1h'] = joblib.load(MODEL_1H)
        with open(INFO_1H, 'r') as f:
            infos['1h'] = json.load(f)
        
        acc = infos['1h'].get('test_accuracy', 0)
        model_name = infos['1h'].get('model_name', 'Unknown')
        print(f"✓ Model 1H loaded: {model_name} (accuracy: {acc:.2%})")
        print(f"  Features: {len(infos['1h']['feature_cols'])}")
        
    except Exception as e:
        print(f"✗ Failed to load model 1H: {e}")
        models['1h'] = None
    
    # Load 24H model
    try:
        models['24h'] = joblib.load(MODEL_24H)
        with open(INFO_24H, 'r') as f:
            infos['24h'] = json.load(f)
        
        acc = infos['24h'].get('test_accuracy', 0)
        model_name = infos['24h'].get('model_name', 'Unknown')
        print(f"✓ Model 24H loaded: {model_name} (accuracy: {acc:.2%})")
        print(f"  Features: {len(infos['24h']['feature_cols'])}")
        
    except Exception as e:
        print(f"✗ Failed to load model 24H: {e}")
        models['24h'] = None
    
    print("=" * 70)

def predict(features: Dict, horizon: str = '1h') -> Optional[Dict]:
    """
    Predict UP/DOWN/NEUTRAL
    
    Args:
        features: dict of feature values
        horizon: '1h' or '24h'
    
    Returns:
        {
            'prediction': 'UP',
            'confidence': 0.85,
            'probabilities': {'DOWN': 0.05, 'NEUTRAL': 0.10, 'UP': 0.85}
        }
    """
    if horizon not in models or models[horizon] is None:
        print(f"❌ Model {horizon} not available")
        return None
    
    model = models[horizon]
    feature_cols = infos[horizon]['feature_cols']
    
    # Prepare feature vector (fill missing với 0)
    X = pd.DataFrame([{col: features.get(col, 0) for col in feature_cols}])
    
    try:
        # Predict
        prediction_raw = model.predict(X)[0]
        proba = model.predict_proba(X)[0]
        confidence = float(proba.max())
        
        # Get class labels
        classes = model.classes_  # e.g. ['DOWN', 'NEUTRAL', 'UP']
        
        # ===== FIX: DECODE PREDICTION (NẾU LÀ INT) =====
        if isinstance(prediction_raw, (int, np.integer)):
            # XGBoost với LabelEncoder → trả về int (0, 1, 2)
            # Cần decode: 0 → 'DOWN', 1 → 'NEUTRAL', 2 → 'UP'
            prediction = str(classes[int(prediction_raw)])
        else:
            # RF/GB → trả về string trực tiếp
            prediction = str(prediction_raw)
        # ===== END FIX =====
        
        proba_dict = {str(classes[i]): float(proba[i]) for i in range(len(classes))}
        
        return {
            'prediction': prediction,  # ← BẢO ĐẢM LÀ STRING
            'confidence': confidence,
            'probabilities': proba_dict
        }
        
    except Exception as e:
        print(f"❌ Prediction error: {e}")
        import traceback
        traceback.print_exc()
        return None

# Load models khi module được import
load_models()