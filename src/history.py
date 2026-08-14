# SilkTrace — History Tracking & CSV Logger Module
from pathlib import Path
from datetime import datetime
import pandas as pd
from src.config import (
    HISTORY_DIR,
    ENERGY_HISTORY_PATH,
    PRODUCTIVITY_HISTORY_PATH,
    INSPECTION_HISTORY_PATH,
)

def log_energy_prediction(date: int, week_status: str, day: str, load_type: str, predicted_kwh: float, user_email: str = "System"):
    """Persist an energy prediction record to CSV history."""
    HISTORY_DIR.mkdir(parents=True, exist_ok=True)
    
    new_record = pd.DataFrame([{
        "Date": date,
        "WeekStatus": week_status,
        "Day": day,
        "Load_Type": load_type,
        "Predicted_Energy_kWh": round(float(predicted_kwh), 2),
        "User": user_email,
        "Timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    }])

    if ENERGY_HISTORY_PATH.exists() and ENERGY_HISTORY_PATH.stat().st_size > 0:
        existing = pd.read_csv(ENERGY_HISTORY_PATH)
        df = pd.concat([existing, new_record], ignore_index=True)
    else:
        df = new_record

    df.to_csv(ENERGY_HISTORY_PATH, index=False)

def log_productivity_prediction(date: str, department: str, day: str, team: int, predicted_prod: float, user_email: str = "System"):
    """Persist a worker productivity prediction record to CSV history."""
    HISTORY_DIR.mkdir(parents=True, exist_ok=True)

    new_record = pd.DataFrame([{
        "Date": str(date),
        "Department": str(department),
        "Day": str(day),
        "Team": int(team),
        "Predicted_Productivity": round(float(predicted_prod), 4),
        "User": user_email,
        "Timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    }])

    if PRODUCTIVITY_HISTORY_PATH.exists() and PRODUCTIVITY_HISTORY_PATH.stat().st_size > 0:
        existing = pd.read_csv(PRODUCTIVITY_HISTORY_PATH)
        df = pd.concat([existing, new_record], ignore_index=True)
    else:
        df = new_record

    df.to_csv(PRODUCTIVITY_HISTORY_PATH, index=False)

def log_fabric_inspection(defect_class: str, confidence: float, user_email: str = "System"):
    """Persist a fabric defect inspection record to CSV history."""
    HISTORY_DIR.mkdir(parents=True, exist_ok=True)

    timestamp_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    new_record = pd.DataFrame([{
        "Date": timestamp_str,
        "Detected Defect": str(defect_class),
        "Confidence (%)": round(float(confidence), 2),
        "User": user_email,
        "Timestamp": timestamp_str
    }])

    if INSPECTION_HISTORY_PATH.exists() and INSPECTION_HISTORY_PATH.stat().st_size > 0:
        existing = pd.read_csv(INSPECTION_HISTORY_PATH)
        df = pd.concat([existing, new_record], ignore_index=True)
    else:
        df = new_record

    df.to_csv(INSPECTION_HISTORY_PATH, index=False)

def load_energy_history() -> pd.DataFrame:
    """Retrieve energy prediction history."""
    if ENERGY_HISTORY_PATH.exists() and ENERGY_HISTORY_PATH.stat().st_size > 0:
        return pd.read_csv(ENERGY_HISTORY_PATH)
    return pd.DataFrame(columns=["Date", "WeekStatus", "Day", "Load_Type", "Predicted_Energy_kWh", "User", "Timestamp"])

def load_productivity_history() -> pd.DataFrame:
    """Retrieve productivity prediction history."""
    if PRODUCTIVITY_HISTORY_PATH.exists() and PRODUCTIVITY_HISTORY_PATH.stat().st_size > 0:
        return pd.read_csv(PRODUCTIVITY_HISTORY_PATH)
    return pd.DataFrame(columns=["Date", "Department", "Day", "Team", "Predicted_Productivity", "User", "Timestamp"])

def load_inspection_history() -> pd.DataFrame:
    """Retrieve fabric inspection history."""
    if INSPECTION_HISTORY_PATH.exists() and INSPECTION_HISTORY_PATH.stat().st_size > 0:
        return pd.read_csv(INSPECTION_HISTORY_PATH)
    return pd.DataFrame(columns=["Date", "Detected Defect", "Confidence (%)", "User", "Timestamp"])
