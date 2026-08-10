import joblib
import pandas as pd
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
PRODUCTIVITY_MODEL_PATH = BASE_DIR / "models" / "productivity_model.pkl"
ENERGY_MODEL_PATH = BASE_DIR / "models" / "energy_model.pkl"

_productivity_model = None
_energy_model = None

def get_productivity_model():
    global _productivity_model
    if _productivity_model is None:
        if not PRODUCTIVITY_MODEL_PATH.exists():
            raise FileNotFoundError(f"Productivity model not found at {PRODUCTIVITY_MODEL_PATH}")
        _productivity_model = joblib.load(PRODUCTIVITY_MODEL_PATH)
    return _productivity_model

def get_energy_model():
    global _energy_model
    if _energy_model is None:
        if not ENERGY_MODEL_PATH.exists():
            raise FileNotFoundError(f"Energy model not found at {ENERGY_MODEL_PATH}")
        _energy_model = joblib.load(ENERGY_MODEL_PATH)
    return _energy_model

def predict_productivity(data):
    model = get_productivity_model()
    df = pd.DataFrame([data]) if isinstance(data, dict) else data
    prediction = model.predict(df)
    return prediction[0]

def predict_energy(data):
    model = get_energy_model()
    df = pd.DataFrame([data]) if isinstance(data, dict) else data
    prediction = model.predict(df)
    return prediction[0]

def load_resources():
    """Load and return productivity and energy models."""
    return get_productivity_model(), get_energy_model()