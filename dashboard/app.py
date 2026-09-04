# SilkTrace — Production Streamlit Application Entrypoint
import os
import time
import sys
import platform
from datetime import datetime
from pathlib import Path
from PIL import Image
import pandas as pd
import numpy as np
import plotly.express as px
import streamlit as st
from streamlit_option_menu import option_menu

# Ensure src module is in path
BASE_DIR = Path(__file__).resolve().parent.parent
if str(BASE_DIR) not in sys.path:
    sys.path.insert(0, str(BASE_DIR))

# Import modular components
from src.config import (
    APP_NAME,
    APP_VERSION,
    APP_DESCRIPTION,
    DEVELOPER_NAME,
    DEVELOPER_INSTITUTION,
    LOGO_PATH,
    PRODUCTIVITY_MODEL_PATH,
    ENERGY_MODEL_PATH,
    FABRIC_MODEL_PATH,
    DATE_ENCODER_PATH,
    QUARTER_ENCODER_PATH,
    DEPARTMENT_ENCODER_PATH,
    DAY_ENCODER_PATH,
    PRODUCTIVITY_DATASET_PATH,
    ENERGY_DATASET_PATH,
    FABRIC_RECOMMENDATIONS,
)
from src.auth import (
    handle_auth_gate,
    render_sidebar_user_profile,
    is_feature_allowed_for_user,
    get_current_user_info,
)
from src.models import (
    load_encoders,
    load_productivity_model,
    load_energy_model,
    load_fabric_model,
    predict_productivity,
    predict_energy,
    predict_fabric_defect,
)
from src.reports import create_pdf_report
from src.history import (
    log_energy_prediction,
    log_productivity_prediction,
    log_fabric_inspection,
    load_energy_history,
    load_productivity_history,
    load_inspection_history,
)
from src.analytics import (
    load_analytics_datasets,
    compute_executive_kpis,
    generate_operational_alerts,
    create_department_productivity_chart,
    create_quarterly_productivity_trend_chart,
    create_energy_load_pie_chart,
    create_power_factor_analysis_chart,
)

# Page Configuration
st.set_page_config(
    page_title=f"{APP_NAME} — AI Textile Intelligence",
    page_icon="🧵",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ==================== DESIGN SYSTEM & STYLING ====================
def inject_custom_css():
    """Inject standard SilkTrace dark-theme glassmorphism CSS design tokens."""
    st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800;900&family=JetBrains+Mono:wght@400;500;600&display=swap');

    :root {
        --color-primary: #3b82f6;
        --color-primary-hover: #2563eb;
        --color-primary-dark: #1d4ed8;
        --color-primary-light: #60a5fa;
        --color-bg-deep: #0f172a;
        --color-bg-base: #1a1f35;
        --color-bg-surface: rgba(25, 35, 65, 0.95);
        --color-bg-card: rgba(20, 35, 60, 0.7);
        --color-green: #22c55e;
        --color-amber: #f59e0b;
        --color-red: #ef4444;
        --color-cyan: #0ea5e9;
        --color-text-primary: #ffffff;
        --color-text-secondary: #e2e8f0;
        --color-text-tertiary: #94a3b8;
        --color-border: rgba(96, 165, 250, 0.25);
        --radius-md: 12px;
        --radius-lg: 16px;
        --radius-xl: 20px;
        --shadow-card: 0 8px 32px rgba(0, 0, 0, 0.3);
        --shadow-card-hover: 0 20px 48px rgba(59, 130, 246, 0.25);
        --font-body: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif;
    }

    * { box-sizing: border-box; }
    html, body, [data-testid="stAppViewContainer"], .main { font-family: var(--font-body); }

    [data-testid="stAppViewContainer"] {
        background: linear-gradient(135deg, var(--color-bg-base) 0%, #2d3748 50%, var(--color-bg-base) 100%);
    }

    .main .block-container {
        background: linear-gradient(135deg, var(--color-bg-surface), rgba(45, 55, 90, 0.95));
        backdrop-filter: blur(8px);
        padding: 2.5rem;
        border-radius: var(--radius-lg);
        border: 1.5px solid var(--color-border);
        box-shadow: 0 20px 60px rgba(0, 0, 0, 0.4);
        margin-top: 1rem;
        margin-bottom: 1.5rem;
    }

    h1, h2, h3, h4 { color: var(--color-text-primary) !important; font-weight: 700; }
    p, span, div, label { color: var(--color-text-secondary) !important; }

    section[data-testid="stSidebar"] {
        background: linear-gradient(180deg, #1a2847 0%, #2d3e5f 100%);
        border-right: 1.5px solid rgba(96, 165, 250, 0.2);
    }
    section[data-testid="stSidebar"] * { color: #ffffff !important; }

    [data-testid="metric-container"] {
        background: linear-gradient(135deg, rgba(30, 58, 95, 0.8), rgba(20, 45, 75, 0.8));
        border: 1.5px solid var(--color-border);
        border-radius: var(--radius-md);
        padding: 1.25rem;
        box-shadow: var(--shadow-card);
    }
    [data-testid="metric-container"] label { color: #bfdbfe !important; font-weight: 600; text-transform: uppercase; }
    [data-testid="metric-container"] [data-testid="stMetricValue"] { color: #60a5fa !important; font-weight: 800; }

    .stButton > button {
        background: linear-gradient(135deg, var(--color-primary), var(--color-primary-hover));
        color: white !important;
        border: none;
        border-radius: var(--radius-md);
        font-weight: 600;
        padding: 0.75rem 1.5rem;
        box-shadow: 0 6px 20px rgba(59, 130, 246, 0.3);
    }
    .stButton > button:hover {
        background: linear-gradient(135deg, var(--color-primary-hover), var(--color-primary-dark));
        transform: translateY(-2px);
    }

    .stDownloadButton > button {
        background: linear-gradient(135deg, rgba(30, 58, 95, 0.9), rgba(20, 45, 75, 0.9));
        color: white !important;
        border: 1.5px solid var(--color-border);
        border-radius: var(--radius-md);
        font-weight: 600;
        padding: 0.7rem 1.25rem;
    }
    .stDownloadButton > button:hover {
        border-color: var(--color-primary-light);
        transform: translateY(-2px);
    }

    .silk-card {
        background: linear-gradient(135deg, rgba(20, 35, 65, 0.85), rgba(15, 30, 55, 0.85));
        border: 1.5px solid var(--color-border);
        border-radius: var(--radius-lg);
        padding: 1.75rem;
        box-shadow: var(--shadow-card);
    }

    .silk-hero {
        background: linear-gradient(135deg, rgba(15, 23, 42, 0.95), rgba(30, 58, 138, 0.6), rgba(15, 23, 42, 0.95));
        border: 1.5px solid var(--color-border);
        border-radius: var(--radius-xl);
        padding: 3rem 2.5rem;
        text-align: center;
        box-shadow: 0 24px 64px rgba(0, 0, 0, 0.4);
    }
    .silk-hero-title {
        font-size: 3rem; font-weight: 800;
        color: #e0f2fe !important;
        margin-bottom: 0.5rem;
    }
    .silk-hero-subtitle {
        font-size: 1.15rem; color: #94a3b8 !important;
        letter-spacing: 1px; margin-bottom: 1.5rem;
    }

    .silk-module-card {
        background: linear-gradient(135deg, rgba(20, 35, 65, 0.9), rgba(15, 30, 55, 0.9));
        border: 1.5px solid var(--color-border);
        border-radius: var(--radius-lg);
        padding: 1.75rem;
        min-height: 200px;
    }

    .silk-result-card {
        background: linear-gradient(135deg, rgba(15, 23, 42, 0.95), rgba(30, 58, 95, 0.95));
        border: 1.5px solid var(--color-border);
        border-radius: var(--radius-lg);
        padding: 2rem;
        text-align: center;
    }
    .silk-result-value { font-size: 2.75rem; font-weight: 800; margin: 0.75rem 0; }

    .silk-page-header {
        background: linear-gradient(135deg, rgba(15, 23, 42, 0.9), rgba(30, 58, 95, 0.7));
        border: 1.5px solid var(--color-border);
        border-radius: var(--radius-lg);
        padding: 2rem;
        margin-bottom: 1.5rem;
    }

    .silk-badge {
        display: inline-flex; align-items: center; gap: 6px;
        padding: 4px 12px; border-radius: 20px; font-size: 0.75rem; font-weight: 600;
    }
    .silk-badge.green { background: rgba(34, 197, 94, 0.15); color: #86efac !important; border: 1px solid rgba(34, 197, 94, 0.3); }
    .silk-badge.amber { background: rgba(245, 158, 11, 0.15); color: #fde68a !important; border: 1px solid rgba(245, 158, 11, 0.3); }
    .silk-badge.blue  { background: rgba(59, 130, 246, 0.15); color: #93c5fd !important; border: 1px solid rgba(59, 130, 246, 0.3); }
    .silk-badge.red   { background: rgba(239, 68, 68, 0.15); color: #fca5a5 !important; border: 1px solid rgba(239, 68, 68, 0.3); }

    .silk-footer {
        background: linear-gradient(135deg, rgba(15, 23, 42, 0.95), var(--color-bg-deep));
        border: 1.5px solid var(--color-border);
        border-radius: var(--radius-lg);
        padding: 2rem; text-align: center; margin-top: 2rem;
    }
    </style>
    """, unsafe_allow_html=True)

# Helper UI components
def render_page_header(title: str, subtitle: str, icon: str = ""):
    st.markdown(f"""
    <div class="silk-page-header">
        <h2 style="margin:0 0 0.25rem 0 !important;">{icon} {title}</h2>
        <p style="color:#94a3b8 !important; margin:0; font-size:1rem;">{subtitle}</p>
    </div>
    """, unsafe_allow_html=True)

def render_footer():
    st.markdown(f"""
    <div class="silk-footer">
        <div style="font-size:1.25rem; font-weight:700; color:#60a5fa !important; margin-bottom:0.5rem;">
            🧵 {APP_NAME} {APP_VERSION}
        </div>
        <p style="color:#94a3b8 !important; font-size:0.95rem;">
            {APP_DESCRIPTION}
        </p>
        <p style="color:#64748b !important; font-size:0.85rem; margin-top:8px;">
            🤖 3 AI Models &nbsp;•&nbsp; ⚡ Industrial Energy &nbsp;•&nbsp; 👷 Workforce Productivity &nbsp;•&nbsp; 🧵 Quality Control
        </p>
        <p style="color:#475569 !important; font-size:0.8rem; margin-top:4px;">
            Engineered by <strong>{DEVELOPER_NAME}</strong> &nbsp;•&nbsp; {DEVELOPER_INSTITUTION}
        </p>
    </div>
    """, unsafe_allow_html=True)

def render_timing_badge(elapsed_seconds: float):
    st.markdown(f"""
    <div style="display:inline-flex; align-items:center; gap:6px; background:rgba(59, 130, 246, 0.1); border:1px solid rgba(96, 165, 250, 0.3); border-radius:8px; padding:6px 14px; font-size:0.85rem; color:#bfdbfe !important; font-family:monospace; margin-top:0.5rem; margin-bottom:1rem;">
        ⏱️ Inference completed in {elapsed_seconds:.3f}s
    </div>
    """, unsafe_allow_html=True)

# ==================== OAUTH & SESSION GATE ====================
# Enforce authentication before rendering app
handle_auth_gate()

# Apply CSS
inject_custom_css()

# Pre-load resources safely
_encoder_load_error: str | None = None
try:
    encoders = load_encoders()
except Exception as e:
    _encoder_load_error = str(e)
    encoders = {}

try:
    prod_df, eng_df = load_analytics_datasets()
except Exception as e:
    st.error(f"Error loading analytics datasets: {str(e)}")
    prod_df = pd.DataFrame()
    eng_df = pd.DataFrame()

# ==================== SIDEBAR NAVIGATION ====================
if LOGO_PATH.exists():
    st.sidebar.image(str(LOGO_PATH), width=180)

# Render User Profile & Role Badge in Sidebar
render_sidebar_user_profile()

with st.sidebar:
    st.markdown("""
    <div style="text-align:center; margin-bottom:10px;">
        <h2 style="color:white; margin:0;">SilkTrace</h2>
        <p style="color:#94a3b8; font-size:0.85rem; margin:0;">AI Textile Intelligence</p>
    </div>
    """, unsafe_allow_html=True)

    page = option_menu(
        menu_title="📂 Navigation",
        options=[
            "Home",
            "Productivity Prediction",
            "Energy Prediction",
            "Fabric Defect Detection",
            "Analytics",
            "System Health",
            "About Project"
        ],
        icons=[
            "house-fill",
            "people-fill",
            "lightning-charge-fill",
            "grid-3x3-gap-fill",
            "bar-chart-fill",
            "activity",
            "info-circle-fill"
        ],
        menu_icon="cpu-fill",
        default_index=0,
        styles={
            "container": {"padding": "5px", "background-color": "#0f172a"},
            "icon": {"color": "#60a5fa", "font-size": "18px"},
            "nav-link": {"font-size": "15px", "text-align": "left", "margin": "4px", "padding": "10px", "border-radius": "8px"},
            "nav-link-selected": {"background-color": "#2563eb", "color": "white", "font-weight": "bold"}
        }
    )

st.sidebar.markdown("---")
st.sidebar.markdown("### 📊 System Status")
s1, s2 = st.sidebar.columns(2)
with s1:
    st.metric("Models", "3", "Active")
with s2:
    st.metric("Status", "Online", "✅")
st.sidebar.caption(f"{APP_NAME} {APP_VERSION} | Python 3.12")

# ==================== ROUTE RENDERING ====================

# ── 1. HOME PAGE ──────────────────────────────────────────
if page == "Home":
    st.markdown("""
    <div class="silk-hero">
        <div class="silk-hero-title">🧵 SilkTrace</div>
        <div class="silk-hero-subtitle">AI-Powered Smart Textile Manufacturing Intelligence Platform</div>
        <div style="display:inline-flex; align-items:center; gap:8px; background:rgba(34, 197, 94, 0.12); border:1px solid rgba(34, 197, 94, 0.3); border-radius:20px; padding:6px 16px; font-size:0.85rem; color:#86efac !important; font-weight:600;">
            <span style="width:8px; height:8px; background:#22c55e; border-radius:50%;"></span>
            Production System Online &nbsp;•&nbsp; All AI Models Ready
        </div>
    </div>
    """, unsafe_allow_html=True)

    st.caption(f"🕒 System Timestamp: {datetime.now().strftime('%d %B %Y | %I:%M %p')}")
    st.markdown("---")

    # Overview KPI Cards
    st.markdown("### 📈 Industrial KPI Overview")
    kpis = compute_executive_kpis(prod_df, eng_df, load_energy_history(), load_productivity_history(), load_inspection_history())
    
    c1, c2, c3, c4 = st.columns(4)
    with c1:
        st.metric("Avg Actual Productivity", f"{kpis['avg_actual_prod']:.2%}")
    with c2:
        st.metric("Avg Industrial Energy", f"{kpis['avg_energy_kwh']:.2f} kWh")
    with c3:
        st.metric("Total Predictions Executed", f"{kpis['total_predictions']:,}")
    with c4:
        st.metric("Defect Inspection Rate", f"{kpis['defect_rate']:.1f}%")

    st.markdown("---")

    # Core Module Highlights
    st.markdown("### 🎯 Core Intelligence Modules")
    col1, col2, col3 = st.columns(3)
    with col1:
        st.markdown("""
        <div class="silk-module-card">
            <h4 style="color:#86efac !important; margin-bottom:0.75rem;">👷 Productivity Prediction</h4>
            <p style="font-size:0.9rem;">Predict worker productivity using Random Forest machine learning based on workforce, SMV, and department features.</p>
            <span class="silk-badge green">Random Forest</span>
        </div>
        """, unsafe_allow_html=True)
    with col2:
        st.markdown("""
        <div class="silk-module-card">
            <h4 style="color:#fde68a !important; margin-bottom:0.75rem;">⚡ Energy Forecasting</h4>
            <p style="font-size:0.9rem;">Forecast factory energy usage in kWh using reactive power, power factor, and load status parameters.</p>
            <span class="silk-badge amber">Random Forest</span>
        </div>
        """, unsafe_allow_html=True)
    with col3:
        st.markdown("""
        <div class="silk-module-card">
            <h4 style="color:#7dd3fc !important; margin-bottom:0.75rem;">🧵 Fabric Defect Detection</h4>
            <p style="font-size:0.9rem;">Classify fabric defects (Hole, Horizontal, Vertical) automatically using MobileNetV2 Deep Learning.</p>
            <span class="silk-badge blue">MobileNetV2</span>
        </div>
        """, unsafe_allow_html=True)

    st.markdown("---")
    render_footer()

# ── 2. PRODUCTIVITY PREDICTION PAGE ────────────────────────
elif page == "Productivity Prediction":
    render_page_header("Worker Productivity Prediction", "AI-powered workforce planning and productivity optimization", "👷")

    st.markdown("""
    <div class="silk-card">
        <h4 style="color:#86efac !important; margin-bottom:0.5rem;">🤖 Random Forest Productivity Model</h4>
        <p style="font-size:0.9rem;">Predict garment worker actual productivity from workforce allocation, department, targeted productivity, SMV, overtime, and incentive parameters.</p>
    </div>
    """, unsafe_allow_html=True)
    st.markdown("---")

    date_enc = encoders.get("date") if isinstance(encoders, dict) else None
    quarter_enc = encoders.get("quarter") if isinstance(encoders, dict) else None
    dept_enc = encoders.get("department") if isinstance(encoders, dict) else None
    day_enc = encoders.get("day") if isinstance(encoders, dict) else None

    # Safe extraction of categorical classes with defaults to prevent any NoneType attribute errors
    default_dates = [
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
    ]
    default_quarters = ["Quarter1", "Quarter2", "Quarter3", "Quarter4", "Quarter5"]
    default_depts = ["finishing", "sweing"]
    default_days = ["Monday", "Saturday", "Sunday", "Thursday", "Tuesday", "Wednesday"]

    date_options = list(date_enc.classes_) if (date_enc is not None and hasattr(date_enc, "classes_")) else default_dates
    quarter_options = list(quarter_enc.classes_) if (quarter_enc is not None and hasattr(quarter_enc, "classes_")) else default_quarters
    dept_options = list(dept_enc.classes_) if (dept_enc is not None and hasattr(dept_enc, "classes_")) else default_depts
    day_options = list(day_enc.classes_) if (day_enc is not None and hasattr(day_enc, "classes_")) else default_days

    c1, c2 = st.columns(2)
    with c1:
        date_val = st.selectbox("📅 Select Date", date_options)
        quarter_val = st.selectbox("📊 Select Quarter", quarter_options)
        dept_val = st.selectbox("🏭 Department", dept_options)
        day_val = st.selectbox("📆 Day of Week", day_options)
        team_num = st.number_input("👥 Team Number", min_value=1, max_value=30, value=1)
        num_workers = st.number_input("👷 Number of Workers", min_value=1, max_value=200, value=50)
        target_prod = st.number_input("🎯 Targeted Productivity", min_value=0.0, max_value=1.0, value=0.80, step=0.05)
    
    with c2:
        smv_val = st.number_input("⏱️ SMV (Standard Minute Value)", min_value=0.0, max_value=100.0, value=20.0, step=0.5)
        wip_val = st.number_input("📦 WIP (Work In Progress)", min_value=0.0, max_value=10000.0, value=100.0, step=10.0)
        overtime_val = st.number_input("⏰ Overtime (minutes)", min_value=0, max_value=50000, value=0, step=100)
        incentive_val = st.number_input("💰 Incentive Amount", min_value=0, max_value=5000, value=50, step=10)
        idle_time_val = st.number_input("⏸️ Idle Time", min_value=0.0, max_value=500.0, value=0.0, step=0.5)
        idle_men_val = st.number_input("👤 Idle Workers", min_value=0, max_value=100, value=0, step=1)
        style_changes = st.number_input("🔄 Style Changes", min_value=0, max_value=10, value=0, step=1)

    st.markdown("---")

    if st.button("🚀 Predict Productivity", use_container_width=True):
        # Re-fetch encoders at click time
        _live_encoders = load_encoders()
        date_enc = _live_encoders.get("date")
        quarter_enc = _live_encoders.get("quarter")
        dept_enc = _live_encoders.get("department")
        day_enc = _live_encoders.get("day")

        def _safe_encode(encoder, val, options_list):
            if encoder is not None and hasattr(encoder, "transform"):
                try:
                    return int(encoder.transform([val])[0])
                except Exception:
                    pass
            return int(options_list.index(val)) if val in options_list else 0

        try:
            input_data = {
                "date": _safe_encode(date_enc, date_val, date_options),
                "quarter": _safe_encode(quarter_enc, quarter_val, quarter_options),
                "department": _safe_encode(dept_enc, dept_val, dept_options),
                "day": _safe_encode(day_enc, day_val, day_options),
                "team": team_num,
                "targeted_productivity": target_prod,
                "smv": smv_val,
                "wip": wip_val,
                "over_time": overtime_val,
                "incentive": incentive_val,
                "idle_time": idle_time_val,
                "idle_men": idle_men_val,
                "no_of_style_change": style_changes,
                "no_of_workers": num_workers
            }

            with st.spinner("🤖 Executing Random Forest Productivity Inference..."):
                pred, elapsed, status = predict_productivity(input_data)

            st.success("✅ Prediction Completed Successfully!")
            render_timing_badge(elapsed)

            # Record in history with verified active user
            active_user = get_current_user_info()
            user_email = active_user.get("email") or "admin@silktrace.ai"
            log_productivity_prediction(date_val, dept_val, day_val, team_num, pred, user_email)

            # Display Result Card
            is_on_target = pred >= target_prod
            badge_class = "green" if is_on_target else "amber"
            badge_text = "✅ On Target" if is_on_target else "⚠️ Below Target"

            c1, c2, c3 = st.columns([1, 2, 1])
            with c2:
                st.markdown(f"""
                <div class="silk-result-card">
                    <p style="color:#86efac !important; font-weight:600; text-transform:uppercase;">👷 Worker Productivity Prediction</p>
                    <div class="silk-result-value" style="color:{'#22c55e' if is_on_target else '#f59e0b'} !important;">{pred:.4f} ({pred:.1%})</div>
                    <p style="color:#94a3b8 !important;">Target Productivity: <strong>{target_prod:.1%}</strong></p>
                    <span class="silk-badge {badge_class}">{badge_text}</span>
                </div>
                """, unsafe_allow_html=True)
        except Exception as e:
            st.error(f"❌ Error during productivity prediction: {str(e)}")

    st.markdown("---")
    render_footer()

# ── 3. ENERGY PREDICTION PAGE ─────────────────────────────
elif page == "Energy Prediction":
    render_page_header("Industrial Energy Consumption Prediction", "Forecast electrical usage to reduce energy overhead", "⚡")

    st.markdown("""
    <div class="silk-card">
        <h4 style="color:#fde68a !important; margin-bottom:0.5rem;">🤖 Random Forest Energy Model</h4>
        <p style="font-size:0.9rem;">Predict factory energy usage (kWh) based on electrical reactive power, power factor, CO2 emissions, and load type.</p>
    </div>
    """, unsafe_allow_html=True)
    st.markdown("---")

    c1, c2 = st.columns(2)
    with c1:
        date_num = st.number_input("📅 Date Index", min_value=0, value=1)
        lagging_react = st.number_input("⚡ Lagging Reactive Power (kVarh)", min_value=0.0, value=4.5, step=0.5)
        leading_react = st.number_input("⚡ Leading Reactive Power (kVarh)", min_value=0.0, value=0.0, step=0.5)
        co2_val = st.number_input("💨 CO2 Emissions (tCO2)", min_value=0.0, value=0.0, step=0.01)
        lagging_pf = st.number_input("📊 Lagging Power Factor", min_value=0.0, max_value=100.0, value=85.0, step=1.0)
    with c2:
        leading_pf = st.number_input("📊 Leading Power Factor", min_value=0.0, max_value=100.0, value=100.0, step=1.0)
        nsm_val = st.number_input("⏱️ NSM (Number of Seconds from Midnight)", min_value=0, max_value=86400, value=30000, step=900)
        week_status_str = st.selectbox("📅 Weekday Status", ["Weekday", "Weekend"])
        day_name = st.selectbox("📆 Day of Week", ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"])
        load_type_str = st.selectbox("📦 Load Type", ["Light_Load", "Medium_Load", "Maximum_Load"])

    week_status_enc = 0 if week_status_str == "Weekday" else 1
    day_map = {"Friday": 0, "Monday": 1, "Saturday": 2, "Sunday": 3, "Thursday": 4, "Tuesday": 5, "Wednesday": 6}
    load_map = {"Light_Load": 0, "Maximum_Load": 1, "Medium_Load": 2}

    st.markdown("---")

    if st.button("🚀 Predict Energy Consumption", use_container_width=True):
        input_data = {
            "date": date_num,
            "Lagging_Current_Reactive.Power_kVarh": lagging_react,
            "Leading_Current_Reactive_Power_kVarh": leading_react,
            "CO2(tCO2)": co2_val,
            "Lagging_Current_Power_Factor": lagging_pf,
            "Leading_Current_Power_Factor": leading_pf,
            "NSM": nsm_val,
            "WeekStatus": week_status_enc,
            "Day_of_week": day_map[day_name],
            "Load_Type": load_map[load_type_str]
        }

        try:
            with st.spinner("🤖 Executing Random Forest Energy Inference..."):
                pred, elapsed, status = predict_energy(input_data)

            st.success("✅ Prediction Completed Successfully!")
            render_timing_badge(elapsed)

            # Log history with verified active user
            active_user = get_current_user_info()
            user_email = active_user.get("email") or "admin@silktrace.ai"
            log_energy_prediction(date_num, week_status_str, day_name, load_type_str, pred, user_email)

            # Result card
            c1, c2, c3 = st.columns([1, 2, 1])
            with c2:
                st.markdown(f"""
                <div class="silk-result-card">
                    <p style="color:#fde68a !important; font-weight:600; text-transform:uppercase;">⚡ Predicted Energy Usage</p>
                    <div class="silk-result-value" style="color:#f59e0b !important;">{pred:.2f} kWh</div>
                    <p style="color:#94a3b8 !important;">Status: <strong>{status}</strong></p>
                </div>
                """, unsafe_allow_html=True)
        except Exception as e:
            st.error(f"❌ Error executing energy prediction: {str(e)}")

    st.markdown("---")
    render_footer()

# ── 4. FABRIC DEFECT DETECTION PAGE ───────────────────────
elif page == "Fabric Defect Detection":
    render_page_header("Fabric Defect Detection & Quality Control", "Automated MobileNetV2 Deep Learning fabric inspection", "🧵")

    st.markdown("""
    <div class="silk-card">
        <h4 style="color:#7dd3fc !important; margin-bottom:0.5rem;">🤖 MobileNetV2 Deep Learning Classifier</h4>
        <p style="font-size:0.9rem;">Upload a fabric sample photo to automatically identify structural fabric defects (Hole, Horizontal, Vertical).</p>
    </div>
    """, unsafe_allow_html=True)
    st.markdown("---")

    uploaded_file = st.file_uploader("Choose a fabric image for inspection", type=["jpg", "jpeg", "png"])

    if uploaded_file is not None:
        try:
            image = Image.open(uploaded_file).convert("RGB")
            c1, c2 = st.columns([2, 1])
            with c1:
                st.image(image, caption="Uploaded Fabric Sample", use_container_width=True)
            with c2:
                st.markdown("### 🖼️ Image Details")
                st.metric("Width", f"{image.width} px")
                st.metric("Height", f"{image.height} px")
                st.metric("Color Space", image.mode)

            st.markdown("---")

            with st.spinner("🤖 MobileNetV2 Neural Network Analyzing Fabric Image..."):
                pred_class, confidence, probs, elapsed = predict_fabric_defect(image)

            st.success("✅ Quality Inspection Complete!")
            render_timing_badge(elapsed)

            active_user = get_current_user_info()
            user_email = active_user.get("email") or "admin@silktrace.ai"
            log_fabric_inspection(pred_class, confidence, user_email)

            # Results Cards
            c1, c2, c3 = st.columns(3)
            with c1:
                st.metric("Detected Fabric Status", pred_class)
            with c2:
                st.metric("Confidence Score", f"{confidence:.2f}%")
            with c3:
                conf_badge = "green" if confidence >= 85 else ("amber" if confidence >= 60 else "red")
                st.markdown(f"<div style='padding-top:15px;'><span class='silk-badge {conf_badge}'>Confidence Rating: {confidence:.1f}%</span></div>", unsafe_allow_html=True)

            st.markdown("---")
            st.markdown("### 📊 Defect Class Probabilities")
            prob_df = pd.DataFrame({"Defect Class": ["Hole", "Horizontal", "Vertical"], "Probability (%)": probs})
            
            fig = px.bar(
                prob_df,
                x="Defect Class",
                y="Probability (%)",
                text="Probability (%)",
                color="Defect Class",
                title="MobileNetV2 Output Probability Distribution",
                color_discrete_sequence=["#ef4444", "#f59e0b", "#0ea5e9"]
            )
            fig.update_traces(texttemplate="%{text:.2f}%", textposition="outside")
            fig.update_layout(height=350, plot_bgcolor="rgba(15, 23, 42, 0.5)", paper_bgcolor="rgba(0,0,0,0)", font=dict(color="#e2e8f0"))
            st.plotly_chart(fig, use_container_width=True)

            # AI Recommendations
            st.markdown("### 💡 AI Operational Recommendation")
            recommendation_msg = FABRIC_RECOMMENDATIONS.get(pred_class, "Inspect warp/weft yarns and perform standard loom calibration.")
            st.info(recommendation_msg)

            st.markdown("---")
            st.markdown("### 📥 Export Reports & Summaries")
            
            inspection_time_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            active_user = get_current_user_info()
            user_name_str = active_user.get("name", "SilkTrace Operator")
            user_email = active_user.get("email") or "admin@silktrace.ai"

            c1, c2 = st.columns(2)
            with c1:
                summary_table_df = pd.DataFrame({
                    "Attribute": ["Detected Condition", "Confidence Level", "Inspection Time", "Model Architecture", "Dimensions"],
                    "Value": [pred_class, f"{confidence:.2f}%", inspection_time_str, "MobileNetV2 Deep Learning", f"{image.width}x{image.height}"]
                })
                
                pdf_path = create_pdf_report(
                    summary_table_df,
                    pred_class,
                    confidence,
                    inspection_time_str,
                    user_name=user_name_str,
                    user_email=user_email,
                    recommendation=recommendation_msg
                )

                with open(pdf_path, "rb") as pdf_file:
                    st.download_button(
                        label="📄 Download Inspection Report (PDF)",
                        data=pdf_file,
                        file_name="SilkTrace_Inspection_Report.pdf",
                        mime="application/pdf",
                        use_container_width=True
                    )

            with c2:
                csv_bytes = summary_table_df.to_csv(index=False).encode("utf-8")
                st.download_button(
                    label="📊 Download Summary (CSV)",
                    data=csv_bytes,
                    file_name="inspection_summary.csv",
                    mime="text/csv",
                    use_container_width=True
                )

        except Exception as e:
            st.error(f"Error executing fabric defect inspection: {str(e)}")

    st.markdown("---")
    render_footer()

# ── 5. ANALYTICS & EXECUTIVE DASHBOARD PAGE ───────────────
elif page == "Analytics":
    render_page_header("SilkTrace Executive Analytics Dashboard", "Real-time industrial manufacturing intelligence & alert center", "📊")

    # Operational Alert Center
    alerts = generate_operational_alerts(prod_df, eng_df)
    if alerts:
        st.markdown("### 🚨 Operational Insights & Alert Center")
        for alert in alerts:
            alert_type = st.error if alert["severity"] == "CRITICAL" else (st.warning if alert["severity"] == "WARNING" else st.info)
            alert_type(f"**[{alert['category']}] {alert['message']}**\n\n*Reason:* {alert['reason']} | *Suggested Action:* {alert['suggested_action']}")

    st.markdown("---")

    # Analytics Charts
    c1, c2 = st.columns(2)
    with c1:
        if not prod_df.empty:
            st.plotly_chart(create_department_productivity_chart(prod_df), use_container_width=True)
    with c2:
        if not prod_df.empty:
            st.plotly_chart(create_quarterly_productivity_trend_chart(prod_df), use_container_width=True)

    c1, c2 = st.columns(2)
    with c1:
        if not eng_df.empty:
            st.plotly_chart(create_energy_load_pie_chart(eng_df), use_container_width=True)
    with c2:
        if not eng_df.empty:
            st.plotly_chart(create_power_factor_analysis_chart(eng_df), use_container_width=True)

    st.markdown("---")
    st.markdown("### 📋 Prediction History Logs")
    t1, t2, t3 = st.tabs(["⚡ Energy History", "👷 Productivity History", "🧵 Inspection History"])
    with t1:
        st.dataframe(load_energy_history(), use_container_width=True)
    with t2:
        st.dataframe(load_productivity_history(), use_container_width=True)
    with t3:
        st.dataframe(load_inspection_history(), use_container_width=True)

    st.markdown("---")
    render_footer()

# ── 6. SYSTEM HEALTH PAGE ──────────────────────────────────
elif page == "System Health":
    render_page_header("System Health & Diagnostic Status", "Real-time model file integrity and environment diagnostics", "🩺")

    health_records = [
        ("Productivity Model (Random Forest)", PRODUCTIVITY_MODEL_PATH.exists(), f"{PRODUCTIVITY_MODEL_PATH.stat().st_size / (1024*1024):.2f} MB" if PRODUCTIVITY_MODEL_PATH.exists() else "Missing"),
        ("Energy Model (Random Forest)", ENERGY_MODEL_PATH.exists(), f"{ENERGY_MODEL_PATH.stat().st_size / (1024*1024):.2f} MB" if ENERGY_MODEL_PATH.exists() else "Download on demand"),
        ("Fabric Model (MobileNetV2)", FABRIC_MODEL_PATH.exists(), f"{FABRIC_MODEL_PATH.stat().st_size / (1024*1024):.2f} MB" if FABRIC_MODEL_PATH.exists() else "Download on demand"),
        ("Date Encoder", DATE_ENCODER_PATH.exists(), "OK" if DATE_ENCODER_PATH.exists() else "Missing"),
        ("Quarter Encoder", QUARTER_ENCODER_PATH.exists(), "OK" if QUARTER_ENCODER_PATH.exists() else "Missing"),
        ("Department Encoder", DEPARTMENT_ENCODER_PATH.exists(), "OK" if DEPARTMENT_ENCODER_PATH.exists() else "Missing"),
        ("Day Encoder", DAY_ENCODER_PATH.exists(), "OK" if DAY_ENCODER_PATH.exists() else "Missing"),
        ("Productivity Dataset", PRODUCTIVITY_DATASET_PATH.exists(), "OK" if PRODUCTIVITY_DATASET_PATH.exists() else "Missing"),
        ("Energy Dataset", ENERGY_DATASET_PATH.exists(), "OK" if ENERGY_DATASET_PATH.exists() else "Missing"),
    ]

    health_df = pd.DataFrame(health_records, columns=["Component", "Status", "Details"])
    health_df["Status"] = health_df["Status"].map({True: "✅ Ready / Available", False: "⚠️ Download / Missing"})

    st.dataframe(health_df, use_container_width=True, hide_index=True)

    st.markdown("---")
    st.markdown("### 🖥️ Environment Diagnostics")
    c1, c2, c3 = st.columns(3)
    with c1:
        st.metric("App Version", APP_VERSION)
    with c2:
        st.metric("Python Runtime", platform.python_version())
    with c3:
        st.metric("Operating System", platform.system())

    st.markdown("---")
    render_footer()

# ── 7. ABOUT PROJECT PAGE ──────────────────────────────────
elif page == "About Project":
    render_page_header("About SilkTrace", "AI-powered decision support system for textile manufacturing", "ℹ️")

    st.markdown(f"""
    <div class="silk-card">
        <h3 style="color:#e0f2fe !important; margin-bottom:0.75rem;">🧵 Project Overview</h3>
        <p style="font-size:1rem; line-height:1.7;">
            <strong>SilkTrace</strong> is an AI/Data Analytics platform engineered for textile manufacturing units and handloom/power-loom micro-clusters. 
            It integrates machine learning for worker productivity forecasting, industrial energy consumption optimization, and deep-learning fabric defect detection.
        </p>
    </div>
    """, unsafe_allow_html=True)
    st.markdown("---")

    c1, c2 = st.columns(2)
    with c1:
        st.markdown("""
        <div class="silk-card" style="border-left: 4px solid #ef4444;">
            <h4 style="color:#fca5a5 !important;">🎯 Problem Statement</h4>
            <p style="font-size:0.9rem;">Textile manufacturers face production losses due to manual productivity records, unpredictable electrical energy spikes, and slow manual fabric defect inspection processes.</p>
        </div>
        """, unsafe_allow_html=True)
    with c2:
        st.markdown("""
        <div class="silk-card" style="border-left: 4px solid #22c55e;">
            <h4 style="color:#86efac !important;">💡 Proposed Solution</h4>
            <p style="font-size:0.9rem;">SilkTrace unifies predictive ML models and MobileNetV2 computer vision into an authenticated industrial dashboard with executive analytics and automated PDF reporting.</p>
        </div>
        """, unsafe_allow_html=True)

    st.markdown("---")
    st.markdown(f"""
    <div class="silk-card" style="text-align:center;">
        <h3 style="color:#e0f2fe !important;">👨‍💻 Developer Information</h3>
        <p style="color:#60a5fa !important; font-size:1.1rem; font-weight:700;">{DEVELOPER_NAME}</p>
        <p style="color:#94a3b8 !important;">{DEVELOPER_INSTITUTION}</p>
        <span class="silk-badge blue">{APP_NAME} {APP_VERSION}</span>
    </div>
    """, unsafe_allow_html=True)

    st.markdown("---")
    render_footer()
