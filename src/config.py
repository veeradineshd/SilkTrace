# SilkTrace — Centralized Configuration & Constants
from pathlib import Path
import os

# ==================== PATH DEFINITIONS ====================
# All paths derived from project root — fully compatible with Windows & Render Linux
BASE_DIR = Path(__file__).resolve().parent.parent

# Assets & Media
ASSETS_DIR = BASE_DIR / "assets"
LOGO_PATH = BASE_DIR / "dashboard" / "silktrace_logo.png"

# Models & Encoders
MODELS_DIR = BASE_DIR / "models"
PRODUCTIVITY_MODEL_PATH = MODELS_DIR / "productivity_model.pkl"
ENERGY_MODEL_PATH = MODELS_DIR / "energy_model.pkl"
FABRIC_MODEL_PATH = MODELS_DIR / "fabric_defect_model.keras"

DATE_ENCODER_PATH = MODELS_DIR / "date_encoder.pkl"
QUARTER_ENCODER_PATH = MODELS_DIR / "quarter_encoder.pkl"
DEPARTMENT_ENCODER_PATH = MODELS_DIR / "department_encoder.pkl"
DAY_ENCODER_PATH = MODELS_DIR / "day_encoder.pkl"
PRODUCTIVITY_ENCODER_PATH = MODELS_DIR / "productivity_encoder.pkl"

# Datasets
DATASETS_DIR = BASE_DIR / "datasets"
PRODUCTIVITY_DATASET_PATH = DATASETS_DIR / "productivity" / "garments_worker_productivity.csv"
ENERGY_DATASET_PATH = DATASETS_DIR / "energy" / "Steel_industry_data.csv"

# History & Reports
REPORTS_DIR = BASE_DIR / "reports"
HISTORY_DIR = BASE_DIR / "history"

ENERGY_HISTORY_PATH = HISTORY_DIR / "energy_history.csv"
PRODUCTIVITY_HISTORY_PATH = HISTORY_DIR / "productivity_history.csv"
INSPECTION_HISTORY_PATH = HISTORY_DIR / "inspection_history.csv"

# Ensure runtime directories exist
REPORTS_DIR.mkdir(parents=True, exist_ok=True)
HISTORY_DIR.mkdir(parents=True, exist_ok=True)

# ==================== APP METADATA ====================
APP_NAME = "SilkTrace"
APP_VERSION = "v1.0.0"
APP_DESCRIPTION = "AI-Powered Smart Textile Manufacturing Intelligence Platform"
DEVELOPER_NAME = "Veera Dinesh D"
DEVELOPER_INSTITUTION = "Sri Eshwar College of Engineering"

# ==================== MODEL RELEASE URLS ====================
# Fallback downloads for models larger than GitHub git limits
ENERGY_MODEL_URL = (
    "https://github.com/veeradineshd/SilkTrace/releases/download/"
    "v1.0.0/energy_model.pkl"
)

FABRIC_MODEL_URL = (
    "https://github.com/veeradineshd/SilkTrace/releases/download/"
    "v1.0.0/fabric_defect_model.keras"
)

# ==================== GOOGLE OIDC AUTH CONFIG ====================
GOOGLE_OIDC_DISCOVERY_URL = "https://accounts.google.com/.well-known/openid-configuration"

# Default Role Mappings (Email -> Role)
# Overrideable via environment variable SILKTRACE_ROLE_MAP (JSON string) or secrets
DEFAULT_ROLE_MAPPING = {
    "admin@silktrace.ai": "ADMIN",
    "analyst@silktrace.ai": "ANALYST",
    "operator@silktrace.ai": "OPERATOR",
    "viewer@silktrace.ai": "VIEWER",
}

# Role Descriptions
ROLE_PERMISSIONS = {
    "ADMIN": ["home", "productivity", "energy", "defect", "analytics", "reports", "system_health", "about"],
    "ANALYST": ["home", "productivity", "energy", "defect", "analytics", "reports", "about"],
    "OPERATOR": ["home", "productivity", "energy", "defect", "about"],
    "VIEWER": ["home", "analytics", "about"],
}

# ==================== FABRIC DEFECT CLASSES ====================
FABRIC_CLASSES = ["Hole", "Horizontal", "Vertical"]

FABRIC_RECOMMENDATIONS = {
    "Hole": "🔴 Action Required: Repair or replace the damaged fabric section immediately. Inspect needle tension and loom feeder mechanism.",
    "Horizontal": "🟠 Maintenance Alert: Check loom alignment, take-up roller speed, and yarn tension settings to resolve horizontal line defects.",
    "Vertical": "🟠 Inspection Needed: Inspect warp yarns, reed spacing, and verify machine calibration to clear vertical streak defects.",
}
