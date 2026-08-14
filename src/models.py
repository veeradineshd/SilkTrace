# SilkTrace — Machine Learning Models & Inference Pipelines
from pathlib import Path
import time
import requests
import joblib
import pandas as pd
import numpy as np
import streamlit as st
from PIL import Image

from src.config import (
    PRODUCTIVITY_MODEL_PATH,
    ENERGY_MODEL_PATH,
    FABRIC_MODEL_PATH,
    DATE_ENCODER_PATH,
    QUARTER_ENCODER_PATH,
    DEPARTMENT_ENCODER_PATH,
    DAY_ENCODER_PATH,
    ENERGY_MODEL_URL,
    FABRIC_MODEL_URL,
    FABRIC_CLASSES,
)

def _download_file(url: str, destination_path: Path):
    """Download large model files from GitHub Release URL with progress and streaming."""
    headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"}
    res = requests.get(url, headers=headers, stream=True, timeout=120)
    res.raise_for_status()
    with open(destination_path, "wb") as f:
        for chunk in res.iter_content(chunk_size=65536):
            if chunk:
                f.write(chunk)

def ensure_energy_model():
    """Ensure energy model exists locally; download if missing or corrupt."""
    ENERGY_MODEL_PATH.parent.mkdir(parents=True, exist_ok=True)
    if not ENERGY_MODEL_PATH.exists() or ENERGY_MODEL_PATH.stat().st_size == 0:
        st.info("⬇️ Downloading Energy Prediction model from GitHub Releases (~193 MB)...")
        try:
            _download_file(ENERGY_MODEL_URL, ENERGY_MODEL_PATH)
        except Exception as e:
            if ENERGY_MODEL_PATH.exists():
                ENERGY_MODEL_PATH.unlink()
            raise RuntimeError(f"Failed to download Energy Prediction model: {str(e)}")

def ensure_fabric_model():
    """Ensure fabric defect model exists locally; download if missing or corrupt."""
    FABRIC_MODEL_PATH.parent.mkdir(parents=True, exist_ok=True)
    if not FABRIC_MODEL_PATH.exists() or FABRIC_MODEL_PATH.stat().st_size == 0:
        st.info("⬇️ Downloading Fabric Defect Detection model from GitHub Releases (~47 MB)...")
        try:
            _download_file(FABRIC_MODEL_URL, FABRIC_MODEL_PATH)
        except Exception as e:
            if FABRIC_MODEL_PATH.exists():
                FABRIC_MODEL_PATH.unlink()
            raise RuntimeError(f"Failed to download Fabric Defect model: {str(e)}")

@st.cache_resource
def load_encoders():
    """Load categorical feature encoders with caching."""
    for name, path in [
        ("Date encoder", DATE_ENCODER_PATH),
        ("Quarter encoder", QUARTER_ENCODER_PATH),
        ("Department encoder", DEPARTMENT_ENCODER_PATH),
        ("Day encoder", DAY_ENCODER_PATH),
    ]:
        if not path.exists():
            raise FileNotFoundError(f"Required encoder file missing: {path} ({name})")

    return {
        "date": joblib.load(DATE_ENCODER_PATH),
        "quarter": joblib.load(QUARTER_ENCODER_PATH),
        "department": joblib.load(DEPARTMENT_ENCODER_PATH),
        "day": joblib.load(DAY_ENCODER_PATH),
    }

@st.cache_resource
def load_productivity_model():
    """Lazy-load worker productivity prediction Random Forest model."""
    if not PRODUCTIVITY_MODEL_PATH.exists():
        raise FileNotFoundError(f"Productivity model file not found at: {PRODUCTIVITY_MODEL_PATH}")
    return joblib.load(PRODUCTIVITY_MODEL_PATH)

@st.cache_resource
def load_energy_model():
    """Lazy-load industrial energy prediction Random Forest model."""
    ensure_energy_model()
    if not ENERGY_MODEL_PATH.exists():
        raise FileNotFoundError(f"Energy model file not found at: {ENERGY_MODEL_PATH}")
    return joblib.load(ENERGY_MODEL_PATH)

@st.cache_resource
def load_fabric_model():
    """Lazy-load MobileNetV2 fabric defect classification model."""
    ensure_fabric_model()
    if not FABRIC_MODEL_PATH.exists():
        raise FileNotFoundError(f"Fabric defect model file not found at: {FABRIC_MODEL_PATH}")

    try:
        from tensorflow.keras.models import load_model  # type: ignore[import-not-found]
    except ImportError:
        try:
            from keras.models import load_model  # type: ignore[import-not-found]
        except ImportError:
            raise RuntimeError("TensorFlow/Keras is required for Fabric Defect Detection but is not installed.")

    return load_model(FABRIC_MODEL_PATH, compile=False)

def predict_productivity(data_dict: dict) -> tuple[float, float, str]:
    """
    Predict worker productivity given encoded feature dictionary.
    Returns: (predicted_productivity, elapsed_time_seconds, status_text)
    """
    model = load_productivity_model()
    
    expected_cols = [
        "date", "quarter", "department", "day", "team",
        "targeted_productivity", "smv", "wip", "over_time",
        "incentive", "idle_time", "idle_men", "no_of_style_change", "no_of_workers"
    ]
    
    df = pd.DataFrame([data_dict])[expected_cols]
    
    t0 = time.time()
    pred = float(model.predict(df)[0])
    elapsed = time.time() - t0

    if pred >= 0.80:
        status = "Excellent / High Productivity"
    elif pred >= 0.60:
        status = "Average Productivity"
    else:
        status = "Low Productivity / Needs Attention"

    return pred, elapsed, status

def predict_energy(data_dict: dict) -> tuple[float, float, str]:
    """
    Predict energy usage given feature dictionary.
    Returns: (predicted_kWh, elapsed_time_seconds, status_text)
    """
    model = load_energy_model()
    
    expected_cols = [
        "date",
        "Lagging_Current_Reactive.Power_kVarh",
        "Leading_Current_Reactive_Power_kVarh",
        "CO2(tCO2)",
        "Lagging_Current_Power_Factor",
        "Leading_Current_Power_Factor",
        "NSM",
        "WeekStatus",
        "Day_of_week",
        "Load_Type"
    ]
    
    df = pd.DataFrame([data_dict])[expected_cols]
    
    t0 = time.time()
    pred = float(model.predict(df)[0])
    elapsed = time.time() - t0

    if pred > 1000:
        status = "High Energy Consumption"
    elif pred > 600:
        status = "Moderate Energy Consumption"
    else:
        status = "Efficient Energy Usage"

    return pred, elapsed, status

def predict_fabric_defect(image: Image.Image) -> tuple[str, float, list[float], float]:
    """
    Classify fabric defect from PIL Image using MobileNetV2 model.
    Returns: (predicted_class, confidence_percentage, class_probabilities_list, elapsed_time_seconds)
    """
    model = load_fabric_model()
    
    # Preprocess image for MobileNetV2 (224x224 float32 array normalized to [0, 1])
    img_resized = image.convert("RGB").resize((224, 224))
    img_array = np.array(img_resized, dtype=np.float32) / 255.0
    img_tensor = np.expand_dims(img_array, axis=0)

    t0 = time.time()
    predictions = model.predict(img_tensor, verbose=0)
    elapsed = time.time() - t0

    probs = [float(p * 100) for p in predictions[0]]
    max_idx = int(np.argmax(predictions[0]))
    predicted_class = FABRIC_CLASSES[max_idx]
    confidence = float(probs[max_idx])

    return predicted_class, confidence, probs, elapsed
