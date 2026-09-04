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
    ENERGY_DATASET_PATH,
    ENERGY_MODEL_URL,
    FABRIC_MODEL_URL,
    FABRIC_CLASSES,
)

def _download_file(url: str, destination_path: Path):
    """Download large model files from GitHub Release URL with high-speed 1MB streaming."""
    headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"}
    res = requests.get(url, headers=headers, stream=True, timeout=60)
    res.raise_for_status()
    with open(destination_path, "wb") as f:
        for chunk in res.iter_content(chunk_size=1048576):
            if chunk:
                f.write(chunk)

def ensure_energy_model():
    """Ensure energy model exists locally; self-heal from dataset or download if missing."""
    ENERGY_MODEL_PATH.parent.mkdir(parents=True, exist_ok=True)
    if not ENERGY_MODEL_PATH.exists() or ENERGY_MODEL_PATH.stat().st_size == 0:
        if ENERGY_DATASET_PATH.exists():
            try:
                from sklearn.ensemble import RandomForestRegressor
                df = pd.read_csv(ENERGY_DATASET_PATH)
                df_prep = df.copy()
                df_prep['date'] = list(range(len(df_prep)))
                df_prep['WeekStatus'] = df_prep['WeekStatus'].map({'Weekday': 0, 'Weekend': 1}).astype(int)
                day_map: dict[str, int] = {'Friday': 0, 'Monday': 1, 'Saturday': 2, 'Sunday': 3, 'Thursday': 4, 'Tuesday': 5, 'Wednesday': 6}
                df_prep['Day_of_week'] = df_prep['Day_of_week'].map(day_map).astype(int)
                load_map: dict[str, int] = {'Light_Load': 0, 'Maximum_Load': 1, 'Medium_Load': 2}
                df_prep['Load_Type'] = df_prep['Load_Type'].map(load_map).astype(int)

                X = df_prep[['date', 'Lagging_Current_Reactive.Power_kVarh', 'Leading_Current_Reactive_Power_kVarh', 'CO2(tCO2)', 'Lagging_Current_Power_Factor', 'Leading_Current_Power_Factor', 'NSM', 'WeekStatus', 'Day_of_week', 'Load_Type']]
                y = df_prep['Usage_kWh']

                rf = RandomForestRegressor(n_estimators=30, max_depth=14, min_samples_split=4, max_features='sqrt', random_state=42, n_jobs=-1)
                rf.fit(X, y)
                joblib.dump(rf, ENERGY_MODEL_PATH, compress=3)
                return
            except Exception:
                pass
        try:
            st.info("⬇️ Downloading Energy Prediction model from GitHub Releases...")
        except Exception:
            pass
        try:
            _download_file(ENERGY_MODEL_URL, ENERGY_MODEL_PATH)
        except Exception as e:
            if ENERGY_MODEL_PATH.exists():
                ENERGY_MODEL_PATH.unlink()
            raise RuntimeError(f"Failed to initialize Energy Prediction model: {str(e)}")

def ensure_fabric_model():
    """Ensure fabric defect model exists locally; download if missing or corrupt."""
    FABRIC_MODEL_PATH.parent.mkdir(parents=True, exist_ok=True)
    if not FABRIC_MODEL_PATH.exists() or FABRIC_MODEL_PATH.stat().st_size == 0:
        try:
            st.info("⬇️ Downloading Fabric Defect Detection model from GitHub Releases (~22 MB)...")
        except Exception:
            pass
        try:
            _download_file(FABRIC_MODEL_URL, FABRIC_MODEL_PATH)
        except Exception as e:
            if FABRIC_MODEL_PATH.exists():
                FABRIC_MODEL_PATH.unlink()
            raise RuntimeError(f"Failed to download Fabric Defect model: {str(e)}")

# Default fallback classes for encoders
DEFAULT_ENCODER_CLASSES = {
    "date": [
        "1/1/2015", "1/10/2015", "1/11/2015", "1/12/2015", "1/13/2015", "1/14/2015",
        "1/15/2015", "1/17/2015", "1/18/2015", "1/19/2015", "1/20/2015", "1/21/2015",
        "1/22/2015", "1/24/2015", "1/25/2015", "1/26/2015", "1/27/2015", "1/28/2015",
        "1/29/2015", "1/3/2015", "1/31/2015", "1/4/2015", "1/5/2015", "1/6/2015",
        "1/7/2015", "1/8/2015", "2/1/2015", "2/10/2015", "2/11/2015", "2/12/2015",
        "2/14/2015", "2/15/2015", "2/16/2015", "2/17/2015", "2/18/2015", "2/19/2015",
        "2/2/2015", "2/22/2015", "2/23/2015", "2/24/2015", "2/25/2015", "2/26/2015",
        "2/28/2015", "2/3/2015", "2/4/2015", "2/5/2015", "2/7/2015", "2/8/2015",
        "2/9/2015", "3/1/2015", "3/10/2015", "3/11/2015", "3/2/2015", "3/3/2015",
        "3/4/2015", "3/5/2015", "3/7/2015", "3/8/2015", "3/9/2015"
    ],
    "quarter": ["Quarter1", "Quarter2", "Quarter3", "Quarter4", "Quarter5"],
    "department": ["finishing", "sweing"],
    "day": ["Monday", "Saturday", "Sunday", "Thursday", "Tuesday", "Wednesday"],
}

@st.cache_resource
def load_encoders():
    """Load categorical feature encoders with caching and self-healing fallback."""
    encoder_specs = [
        ("date", DATE_ENCODER_PATH, "date"),
        ("quarter", QUARTER_ENCODER_PATH, "quarter"),
        ("department", DEPARTMENT_ENCODER_PATH, "department"),
        ("day", DAY_ENCODER_PATH, "day"),
    ]

    encoders = {}
    for key, path, _ in encoder_specs:
        if path.exists():
            try:
                enc = joblib.load(path)
                if enc is not None and hasattr(enc, "classes_") and hasattr(enc, "transform"):
                    encoders[key] = enc
            except Exception:
                pass

    if len(encoders) < 4:
        from sklearn.preprocessing import LabelEncoder
        from src.config import PRODUCTIVITY_DATASET_PATH
        df = None
        if PRODUCTIVITY_DATASET_PATH.exists():
            try:
                df = pd.read_csv(PRODUCTIVITY_DATASET_PATH)
                if "department" in df.columns:
                    df["department"] = df["department"].astype(str).str.strip()
            except Exception:
                df = None

        for key, path, col in encoder_specs:
            if key not in encoders:
                le = LabelEncoder()
                if df is not None and col in df.columns:
                    le.fit(df[col].dropna().astype(str))
                else:
                    le.fit(DEFAULT_ENCODER_CLASSES[key])
                encoders[key] = le
                try:
                    path.parent.mkdir(parents=True, exist_ok=True)
                    joblib.dump(le, path)
                except Exception:
                    pass

    return encoders

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
    confidence = probs[max_idx]

    return predicted_class, confidence, probs, elapsed
