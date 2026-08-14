# SilkTrace — Prediction API Bridge
import pandas as pd
from src.models import (
    load_productivity_model,
    load_energy_model,
    predict_productivity as _predict_productivity_impl,
    predict_energy as _predict_energy_impl,
)

def get_productivity_model():
    """Retrieve cached productivity model."""
    return load_productivity_model()

def get_energy_model():
    """Retrieve cached energy model."""
    return load_energy_model()

def predict_productivity(data):
    """Predict productivity for single dictionary or DataFrame input."""
    model = get_productivity_model()
    df = pd.DataFrame([data]) if isinstance(data, dict) else data
    prediction = model.predict(df)
    return prediction[0]

def predict_energy(data):
    """Predict energy usage for single dictionary or DataFrame input."""
    model = get_energy_model()
    df = pd.DataFrame([data]) if isinstance(data, dict) else data
    prediction = model.predict(df)
    return prediction[0]

def load_resources():
    """Load and return productivity and energy models."""
    return get_productivity_model(), get_energy_model()