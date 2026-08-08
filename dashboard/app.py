import streamlit as st
import joblib
import time
import pandas as pd
from pathlib import Path
from PIL import Image

try:
    from tensorflow.keras.models import load_model  # type: ignore[import-not-found]
except ImportError:
    def load_model(*args, **kwargs):
        raise ImportError(
            "TensorFlow/Keras is required for fabric defect detection but is not available in this environment."
        )
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime
from reportlab.platypus import (
    SimpleDocTemplate,
    Table,
    TableStyle,
    Paragraph
)
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet
from streamlit_option_menu import option_menu

st.set_page_config(
    page_title="SilkTrace",
    page_icon="🧵",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ==================== CUSTOM STYLING ====================
def inject_custom_css():
    """Inject professional custom CSS styling with design-system variables"""
    st.markdown("""
    <style>
    /* ===========================
       GOOGLE FONTS
    =========================== */
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800;900&family=JetBrains+Mono:wght@400;500;600&display=swap');

    /* ===========================
       DESIGN SYSTEM — CSS VARIABLES
    =========================== */
    :root {
        /* — Primary Palette — */
        --color-primary: #3b82f6;
        --color-primary-hover: #2563eb;
        --color-primary-dark: #1d4ed8;
        --color-primary-light: #60a5fa;
        --color-primary-glow: rgba(59, 130, 246, 0.35);

        /* — Surface / Background — */
        --color-bg-deep: #0f172a;
        --color-bg-base: #1a1f35;
        --color-bg-surface: rgba(25, 35, 65, 0.95);
        --color-bg-card: rgba(20, 35, 60, 0.7);
        --color-bg-card-hover: rgba(20, 35, 60, 0.92);
        --color-bg-input: rgba(20, 35, 60, 0.7);

        /* — Accent Colors — */
        --color-green: #22c55e;
        --color-green-dark: #16a34a;
        --color-amber: #f59e0b;
        --color-amber-dark: #d97706;
        --color-red: #ef4444;
        --color-cyan: #0ea5e9;

        /* — Text — */
        --color-text-primary: #ffffff;
        --color-text-secondary: #e2e8f0;
        --color-text-tertiary: #94a3b8;
        --color-text-accent: #bfdbfe;
        --color-text-heading: #e0f2fe;

        /* — Borders — */
        --color-border: rgba(96, 165, 250, 0.25);
        --color-border-hover: rgba(96, 165, 250, 0.55);
        --color-border-subtle: rgba(96, 165, 250, 0.12);

        /* — Sizing — */
        --radius-sm: 8px;
        --radius-md: 12px;
        --radius-lg: 16px;
        --radius-xl: 20px;

        /* — Shadows — */
        --shadow-card: 0 8px 32px rgba(0, 0, 0, 0.3), inset 0 1px 0 rgba(255, 255, 255, 0.06);
        --shadow-card-hover: 0 20px 48px rgba(59, 130, 246, 0.25), inset 0 1px 0 rgba(255, 255, 255, 0.1);
        --shadow-button: 0 6px 20px rgba(59, 130, 246, 0.3);

        /* — Transitions — */
        --transition-fast: 0.2s cubic-bezier(0.4, 0, 0.2, 1);
        --transition-base: 0.3s cubic-bezier(0.4, 0, 0.2, 1);
        --transition-slow: 0.5s cubic-bezier(0.4, 0, 0.2, 1);

        /* — Typography — */
        --font-body: 'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;
        --font-mono: 'JetBrains Mono', 'Fira Code', monospace;
    }

    /* ===========================
       RESET & BASE
    =========================== */
    * {
        margin: 0;
        padding: 0;
        box-sizing: border-box;
    }

    html, body, [data-testid="stAppViewContainer"], .main {
        font-family: var(--font-body);
    }

    /* ===========================
       KEYFRAME ANIMATIONS
    =========================== */
    @keyframes fadeInUp {
        from { opacity: 0; transform: translateY(24px); }
        to   { opacity: 1; transform: translateY(0); }
    }

    @keyframes fadeIn {
        from { opacity: 0; }
        to   { opacity: 1; }
    }

    @keyframes pulseGlow {
        0%, 100% { box-shadow: 0 0 8px rgba(34, 197, 94, 0.4); }
        50%      { box-shadow: 0 0 20px rgba(34, 197, 94, 0.7); }
    }

    @keyframes gradientShift {
        0%   { background-position: 0% 50%; }
        50%  { background-position: 100% 50%; }
        100% { background-position: 0% 50%; }
    }

    @keyframes shimmer {
        0%   { background-position: -200% 0; }
        100% { background-position: 200% 0; }
    }

    /* ===========================
       MAIN BACKGROUND & CONTAINER
    =========================== */
    html, body {
        background: linear-gradient(135deg, var(--color-bg-base) 0%, #2d3748 50%, var(--color-bg-base) 100%);
        min-height: 100vh;
    }

    [data-testid="stAppViewContainer"] {
        background: linear-gradient(135deg, var(--color-bg-base) 0%, #2d3748 50%, var(--color-bg-base) 100%);
        padding-top: 1rem;
    }

    .main {
        background: transparent;
    }

    .main .block-container {
        background: linear-gradient(135deg, var(--color-bg-surface), rgba(45, 55, 90, 0.95));
        backdrop-filter: blur(8px);
        -webkit-backdrop-filter: blur(8px);
        padding: 2.5rem;
        border-radius: var(--radius-lg);
        border: 1.5px solid var(--color-border);
        box-shadow: 0 20px 60px rgba(0, 0, 0, 0.4), inset 0 1px 0 rgba(255, 255, 255, 0.08);
        margin-top: 1.5rem;
        margin-bottom: 1.5rem;
        animation: fadeIn 0.6s ease-out;
    }

    /* ===========================
       HEADINGS & TEXT
    =========================== */
    h1, h2, h3, h4, h5, h6 {
        color: var(--color-text-primary) !important;
        font-family: var(--font-body);
        font-weight: 700;
        letter-spacing: -0.5px;
        line-height: 1.3;
    }

    h1 {
        font-size: 2.5rem;
        margin-bottom: 1.5rem;
        color: var(--color-text-heading) !important;
    }

    h2 {
        font-size: 1.875rem;
        margin-top: 2rem;
        margin-bottom: 1rem;
        color: #f0f9ff !important;
    }

    h3 {
        font-size: 1.5rem;
        margin-top: 1.5rem;
        margin-bottom: 0.75rem;
        color: var(--color-text-heading) !important;
    }

    h4 {
        font-size: 1.25rem;
        color: #f0f9ff !important;
    }

    p, span, div, label {
        color: var(--color-text-secondary) !important;
    }

    .stMarkdown, .stMarkdown p {
        color: var(--color-text-secondary) !important;
    }

    /* ===========================
       SIDEBAR (UNCHANGED THEME/COLORS)
    =========================== */
    section[data-testid="stSidebar"] {
        background: linear-gradient(180deg, #1a2847 0%, #2d3e5f 100%);
        border-right: 1.5px solid rgba(96, 165, 250, 0.2);
    }

    section[data-testid="stSidebar"] * {
        color: #ffffff !important;
    }

    section[data-testid="stSidebar"] p,
    section[data-testid="stSidebar"] span,
    section[data-testid="stSidebar"] div {
        color: #e2e8f0 !important;
    }

    section[data-testid="stSidebar"] .stMarkdown h1,
    section[data-testid="stSidebar"] .stMarkdown h2,
    section[data-testid="stSidebar"] .stMarkdown h3 {
        color: #ffffff !important;
    }

    section[data-testid="stSidebar"] label {
        color: var(--color-text-heading) !important;
    }

    /* ===========================
       METRIC CARDS
    =========================== */
    [data-testid="metric-container"] {
        background: linear-gradient(135deg, rgba(30, 58, 95, 0.8), rgba(20, 45, 75, 0.8));
        border: 1.5px solid var(--color-border);
        border-radius: var(--radius-md);
        padding: 1.5rem;
        box-shadow: var(--shadow-card);
        transition: all var(--transition-base);
    }

    [data-testid="metric-container"]:hover {
        transform: translateY(-4px);
        border-color: var(--color-border-hover);
        box-shadow: var(--shadow-card-hover);
        background: linear-gradient(135deg, rgba(30, 58, 95, 0.95), rgba(20, 45, 75, 0.95));
    }

    [data-testid="metric-container"] label {
        color: var(--color-text-accent) !important;
        font-weight: 600;
        font-size: 0.875rem;
        text-transform: uppercase;
        letter-spacing: 0.5px;
    }

    [data-testid="metric-container"] [data-testid="stMetricValue"] {
        color: var(--color-primary-light) !important;
        font-weight: 700;
        font-size: 1.75rem;
    }

    [data-testid="metric-container"] span {
        color: var(--color-text-accent) !important;
    }

    /* ===========================
       BUTTONS
    =========================== */
    .stButton > button {
        background: linear-gradient(135deg, var(--color-primary), var(--color-primary-hover));
        color: white !important;
        border: none;
        border-radius: var(--radius-md);
        font-family: var(--font-body);
        font-weight: 600;
        font-size: 0.95rem;
        padding: 0.75rem 1.5rem;
        transition: all var(--transition-base);
        box-shadow: var(--shadow-button);
        text-transform: none;
        letter-spacing: 0.2px;
    }

    .stButton > button:hover {
        background: linear-gradient(135deg, var(--color-primary-hover), var(--color-primary-dark));
        transform: translateY(-2px);
        box-shadow: 0 12px 28px rgba(59, 130, 246, 0.4);
        color: white !important;
    }

    .stButton > button:active {
        transform: translateY(0);
    }

    .stDownloadButton > button {
        background: linear-gradient(135deg, rgba(30, 58, 95, 0.9), rgba(20, 45, 75, 0.9));
        color: white !important;
        border: 1.5px solid var(--color-border);
        border-radius: var(--radius-md);
        font-family: var(--font-body);
        font-weight: 600;
        font-size: 0.9rem;
        padding: 0.7rem 1.25rem;
        transition: all var(--transition-base);
    }

    .stDownloadButton > button:hover {
        border-color: var(--color-primary-light);
        background: linear-gradient(135deg, rgba(30, 58, 95, 1), rgba(20, 45, 75, 1));
        box-shadow: 0 8px 24px rgba(59, 130, 246, 0.25);
        transform: translateY(-2px);
        color: white !important;
    }

    /* ===========================
       INPUT FIELDS
    =========================== */
    .stTextInput input,
    .stNumberInput input,
    .stTextArea textarea {
        background: var(--color-bg-input) !important;
        border: 1.5px solid var(--color-border) !important;
        border-radius: var(--radius-md) !important;
        color: var(--color-text-primary) !important;
        font-family: var(--font-body);
        font-size: 0.95rem;
        padding: 0.75rem 1rem !important;
        transition: all var(--transition-base);
    }

    .stTextInput input:focus,
    .stNumberInput input:focus,
    .stTextArea textarea:focus {
        background: rgba(20, 35, 60, 0.9) !important;
        border-color: var(--color-primary-light) !important;
        box-shadow: 0 0 0 3px rgba(96, 165, 250, 0.2) !important;
        color: var(--color-text-primary) !important;
    }

    .stTextInput input::placeholder,
    .stNumberInput input::placeholder,
    .stTextArea textarea::placeholder {
        color: #64748b !important;
    }

    .stSelectbox label,
    .stTextInput label,
    .stNumberInput label,
    .stTextArea label {
        color: var(--color-text-heading) !important;
        font-weight: 500;
        font-size: 0.9rem;
    }

    /* Selectbox dropdown styling */
    [data-baseweb="select"] {
        background: var(--color-bg-input);
        border-radius: var(--radius-md);
    }

    [data-baseweb="select"] > div {
        background: var(--color-bg-input) !important;
        border: 1.5px solid var(--color-border) !important;
        border-radius: var(--radius-md) !important;
        color: var(--color-text-primary) !important;
        transition: all var(--transition-base);
    }

    [data-baseweb="select"] > div:hover {
        border-color: var(--color-border-hover) !important;
    }

    /* ===========================
       CHECKBOX & RADIO
    =========================== */
    .stCheckbox label,
    .stRadio label {
        color: var(--color-text-heading) !important;
        font-weight: 500;
    }

    /* ===========================
       ALERTS — SUCCESS / INFO / WARNING / ERROR
    =========================== */
    [data-testid="stAlert"] {
        border-radius: var(--radius-md);
        padding: 1rem 1.25rem;
        font-size: 0.95rem;
        backdrop-filter: blur(4px);
    }

    /* Success */
    .stSuccess, div[data-testid="stAlert"]:has(> div[role="alert"][data-baseweb="notification"][kind="positive"]) {
        background: rgba(34, 197, 94, 0.12);
        border-left: 4px solid var(--color-green);
        border-radius: var(--radius-md);
        padding: 1rem 1.25rem;
    }
    .stSuccess p, .stSuccess span, .stSuccess div { color: #d1fae5 !important; }

    /* Info */
    .stInfo, div[data-testid="stAlert"]:has(> div[role="alert"][data-baseweb="notification"][kind="info"]) {
        background: rgba(59, 130, 246, 0.12);
        border-left: 4px solid var(--color-primary);
        border-radius: var(--radius-md);
        padding: 1rem 1.25rem;
    }
    .stInfo p, .stInfo span, .stInfo div { color: var(--color-text-accent) !important; }

    /* Warning */
    .stWarning, div[data-testid="stAlert"]:has(> div[role="alert"][data-baseweb="notification"][kind="warning"]) {
        background: rgba(245, 158, 11, 0.12);
        border-left: 4px solid var(--color-amber);
        border-radius: var(--radius-md);
        padding: 1rem 1.25rem;
    }
    .stWarning p, .stWarning span, .stWarning div { color: #fde68a !important; }

    /* Error */
    .stError, div[data-testid="stAlert"]:has(> div[role="alert"][data-baseweb="notification"][kind="negative"]) {
        background: rgba(239, 68, 68, 0.12);
        border-left: 4px solid var(--color-red);
        border-radius: var(--radius-md);
        padding: 1rem 1.25rem;
    }
    .stError p, .stError span, .stError div { color: #fecaca !important; }

    /* ===========================
       DIVIDER
    =========================== */
    hr {
        border: none;
        height: 1px;
        background: linear-gradient(90deg, transparent, rgba(96, 165, 250, 0.2), transparent);
        margin: 2rem 0;
    }

    /* ===========================
       TABLES & DATAFRAMES
    =========================== */
    [data-testid="stDataFrame"] {
        border: 1.5px solid var(--color-border);
        border-radius: var(--radius-md);
        overflow: hidden;
        background: linear-gradient(135deg, var(--color-bg-card), rgba(20, 35, 60, 0.6));
    }

    .dataframe {
        border-radius: var(--radius-md);
    }

    tbody tr {
        border-color: var(--color-border-subtle);
        transition: background var(--transition-fast);
    }

    tbody tr:hover {
        background: rgba(59, 130, 246, 0.12) !important;
    }

    tbody td {
        color: var(--color-text-secondary) !important;
        border-color: var(--color-border-subtle);
    }

    thead th {
        background: rgba(15, 35, 65, 0.85);
        color: var(--color-text-heading) !important;
        font-weight: 700;
        border-color: rgba(96, 165, 250, 0.2);
        text-transform: uppercase;
        font-size: 0.8rem;
        letter-spacing: 0.5px;
    }

    /* ===========================
       EXPANDER
    =========================== */
    details {
        background: linear-gradient(135deg, var(--color-bg-card), rgba(15, 30, 55, 0.7));
        border: 1.5px solid var(--color-border);
        border-radius: var(--radius-md);
        padding: 1rem;
        transition: all var(--transition-base);
    }

    details:hover {
        background: linear-gradient(135deg, var(--color-bg-card-hover), rgba(15, 30, 55, 0.85));
        border-color: rgba(96, 165, 250, 0.4);
    }

    details summary {
        cursor: pointer;
        color: var(--color-text-heading) !important;
        font-weight: 600;
        user-select: none;
    }

    /* ===========================
       FILE UPLOADER
    =========================== */
    [data-testid="stFileUploader"] {
        background: linear-gradient(135deg, var(--color-bg-card), rgba(15, 30, 55, 0.7));
        border: 2px dashed rgba(96, 165, 250, 0.35);
        border-radius: var(--radius-lg);
        padding: 2rem;
        transition: all var(--transition-base);
    }

    [data-testid="stFileUploader"] label,
    [data-testid="stFileUploader"] p,
    [data-testid="stFileUploader"] span,
    [data-testid="stFileUploader"] div {
        color: var(--color-text-heading) !important;
    }

    [data-testid="stFileUploader"]:hover {
        background: linear-gradient(135deg, var(--color-bg-card-hover), rgba(15, 30, 55, 0.85));
        border-color: var(--color-primary-light);
        box-shadow: 0 0 24px rgba(59, 130, 246, 0.15);
    }

    /* ===========================
       PROGRESS BAR
    =========================== */
    .stProgress > div > div {
        background: linear-gradient(90deg, var(--color-primary), var(--color-cyan));
        border-radius: 10px;
    }

    /* ===========================
       CAPTIONS & SMALL TEXT
    =========================== */
    .streamlit-caption, .small-text {
        color: var(--color-text-accent) !important;
        font-size: 0.85rem;
        margin-top: 1.5rem;
        padding-top: 1rem;
        border-top: 1px solid var(--color-border-subtle);
    }

    /* ===========================
       SCROLLBAR
    =========================== */
    ::-webkit-scrollbar { width: 8px; height: 8px; }
    ::-webkit-scrollbar-track { background: rgba(15, 30, 55, 0.5); }
    ::-webkit-scrollbar-thumb { background: rgba(96, 165, 250, 0.5); border-radius: 10px; }
    ::-webkit-scrollbar-thumb:hover { background: rgba(96, 165, 250, 0.7); }

    /* ===========================
       CODE BLOCKS
    =========================== */
    pre, code {
        background: rgba(15, 30, 55, 0.8);
        border: 1px solid var(--color-border);
        border-radius: var(--radius-sm);
        color: var(--color-text-accent) !important;
        font-family: var(--font-mono);
        padding: 0.5rem 0.75rem;
    }

    pre {
        padding: 1rem;
    }

    /* ===========================
       LINKS
    =========================== */
    a {
        color: var(--color-primary-light);
        text-decoration: none;
        transition: color var(--transition-base);
        font-weight: 500;
    }

    a:hover {
        color: #93c5fd;
        text-decoration: underline;
    }

    /* ===========================
       TABS
    =========================== */
    .stTabs [data-baseweb="tab-list"] button {
        color: var(--color-text-secondary) !important;
        font-weight: 600;
        font-family: var(--font-body);
        transition: all var(--transition-fast);
    }

    .stTabs [data-baseweb="tab-list"] button[aria-selected="true"] {
        color: var(--color-primary-light) !important;
        border-bottom-color: var(--color-primary-light) !important;
    }

    /* ===========================
       ADDITIONAL TEXT ELEMENTS
    =========================== */
    .stText, .element-container, .stSelectbox, .stMultiSelect {
        color: var(--color-text-secondary) !important;
    }

    /* ===========================
       REUSABLE COMPONENT CLASSES
    =========================== */

    /* — Glassmorphic Card — */
    .silk-card {
        background: linear-gradient(135deg, rgba(20, 35, 65, 0.85), rgba(15, 30, 55, 0.85));
        border: 1.5px solid var(--color-border);
        border-radius: var(--radius-lg);
        padding: 1.75rem;
        box-shadow: var(--shadow-card);
        backdrop-filter: blur(10px);
        -webkit-backdrop-filter: blur(10px);
        transition: all var(--transition-base);
        animation: fadeInUp 0.5s ease-out;
    }

    .silk-card:hover {
        transform: translateY(-4px);
        border-color: var(--color-border-hover);
        box-shadow: var(--shadow-card-hover);
    }

    /* — Hero Section — */
    .silk-hero {
        background: linear-gradient(135deg, rgba(15, 23, 42, 0.95), rgba(30, 58, 138, 0.6), rgba(15, 23, 42, 0.95));
        border: 1.5px solid var(--color-border);
        border-radius: var(--radius-xl);
        padding: 3rem 2.5rem;
        text-align: center;
        box-shadow: 0 24px 64px rgba(0, 0, 0, 0.4);
        position: relative;
        overflow: hidden;
        animation: fadeInUp 0.6s ease-out;
    }

    .silk-hero::before {
        content: '';
        position: absolute;
        top: 0; left: 0; right: 0; bottom: 0;
        background: linear-gradient(135deg, transparent 30%, rgba(59, 130, 246, 0.05) 50%, transparent 70%);
        background-size: 200% 200%;
        animation: gradientShift 8s ease infinite;
        pointer-events: none;
    }

    .silk-hero-title {
        font-size: 3rem;
        font-weight: 800;
        letter-spacing: -1px;
        background: linear-gradient(135deg, #e0f2fe, #60a5fa, #e0f2fe);
        background-size: 200% auto;
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        background-clip: text;
        animation: shimmer 4s linear infinite;
        margin-bottom: 0.5rem;
    }

    .silk-hero-subtitle {
        font-size: 1.15rem;
        color: #94a3b8 !important;
        font-weight: 400;
        letter-spacing: 2px;
        text-transform: uppercase;
        margin-bottom: 1.5rem;
    }

    .silk-hero-status {
        display: inline-flex;
        align-items: center;
        gap: 8px;
        background: rgba(34, 197, 94, 0.12);
        border: 1px solid rgba(34, 197, 94, 0.3);
        border-radius: 20px;
        padding: 6px 16px;
        font-size: 0.85rem;
        color: #86efac !important;
        font-weight: 600;
    }

    .silk-hero-status-dot {
        width: 8px;
        height: 8px;
        background: #22c55e;
        border-radius: 50%;
        animation: pulseGlow 2s ease-in-out infinite;
    }

    /* — Module Cards — */
    .silk-module-card {
        background: linear-gradient(135deg, rgba(20, 35, 65, 0.9), rgba(15, 30, 55, 0.9));
        border: 1.5px solid var(--color-border);
        border-radius: var(--radius-lg);
        padding: 1.75rem;
        box-shadow: var(--shadow-card);
        transition: all var(--transition-base);
        position: relative;
        overflow: hidden;
        min-height: 200px;
    }

    .silk-module-card::before {
        content: '';
        position: absolute;
        top: 0; left: 0; right: 0;
        height: 3px;
        border-radius: var(--radius-lg) var(--radius-lg) 0 0;
    }

    .silk-module-card:hover {
        transform: translateY(-6px);
        border-color: var(--color-border-hover);
        box-shadow: var(--shadow-card-hover);
    }

    .silk-module-card.green::before  { background: linear-gradient(90deg, #22c55e, #16a34a); }
    .silk-module-card.amber::before  { background: linear-gradient(90deg, #f59e0b, #d97706); }
    .silk-module-card.blue::before   { background: linear-gradient(90deg, #0ea5e9, #0284c7); }

    .silk-module-icon {
        width: 48px;
        height: 48px;
        border-radius: var(--radius-md);
        display: flex;
        align-items: center;
        justify-content: center;
        font-size: 1.5rem;
        margin-bottom: 1rem;
    }

    .silk-module-icon.green  { background: rgba(34, 197, 94, 0.15); }
    .silk-module-icon.amber  { background: rgba(245, 158, 11, 0.15); }
    .silk-module-icon.blue   { background: rgba(14, 165, 233, 0.15); }

    /* — Result Cards — */
    .silk-result-card {
        background: linear-gradient(135deg, rgba(15, 23, 42, 0.95), rgba(30, 58, 95, 0.95));
        border: 1.5px solid var(--color-border);
        border-radius: var(--radius-lg);
        padding: 2rem;
        text-align: center;
        box-shadow: var(--shadow-card);
        animation: fadeInUp 0.4s ease-out;
        transition: all var(--transition-base);
    }

    .silk-result-card:hover {
        border-color: var(--color-border-hover);
        box-shadow: var(--shadow-card-hover);
    }

    .silk-result-value {
        font-size: 2.75rem;
        font-weight: 800;
        margin: 0.75rem 0;
        letter-spacing: -1px;
    }

    .silk-result-label {
        font-size: 0.9rem;
        text-transform: uppercase;
        letter-spacing: 1px;
        font-weight: 600;
    }

    /* — Page Header — */
    .silk-page-header {
        background: linear-gradient(135deg, rgba(15, 23, 42, 0.9), rgba(30, 58, 95, 0.7));
        border: 1.5px solid var(--color-border);
        border-radius: var(--radius-lg);
        padding: 2rem;
        margin-bottom: 1.5rem;
        animation: fadeInUp 0.5s ease-out;
    }

    .silk-page-header h2 {
        margin: 0 0 0.25rem 0 !important;
        padding: 0;
    }

    .silk-page-header p {
        color: var(--color-text-tertiary) !important;
        margin: 0;
    }

    /* — Badge — */
    .silk-badge {
        display: inline-flex;
        align-items: center;
        gap: 6px;
        padding: 4px 12px;
        border-radius: 20px;
        font-size: 0.75rem;
        font-weight: 600;
        letter-spacing: 0.5px;
    }

    .silk-badge.green  { background: rgba(34, 197, 94, 0.15); color: #86efac !important; border: 1px solid rgba(34, 197, 94, 0.3); }
    .silk-badge.amber  { background: rgba(245, 158, 11, 0.15); color: #fde68a !important; border: 1px solid rgba(245, 158, 11, 0.3); }
    .silk-badge.blue   { background: rgba(59, 130, 246, 0.15); color: #93c5fd !important; border: 1px solid rgba(59, 130, 246, 0.3); }
    .silk-badge.red    { background: rgba(239, 68, 68, 0.15); color: #fca5a5 !important; border: 1px solid rgba(239, 68, 68, 0.3); }

    /* — Footer — */
    .silk-footer {
        background: linear-gradient(135deg, rgba(15, 23, 42, 0.95), var(--color-bg-deep));
        border: 1.5px solid var(--color-border);
        border-radius: var(--radius-lg);
        padding: 2rem;
        text-align: center;
        margin-top: 2rem;
    }

    .silk-footer-brand {
        font-size: 1.25rem;
        font-weight: 700;
        color: var(--color-primary-light) !important;
        margin-bottom: 0.5rem;
    }

    .silk-footer-divider {
        height: 1px;
        background: linear-gradient(90deg, transparent, var(--color-border), transparent);
        margin: 1rem auto;
        max-width: 300px;
    }

    .silk-footer-meta {
        font-size: 0.8rem;
        color: var(--color-text-tertiary) !important;
    }

    /* — Step Cards — */
    .silk-step {
        background: linear-gradient(135deg, var(--color-bg-card), rgba(15, 30, 55, 0.7));
        border: 1.5px solid var(--color-border);
        border-radius: var(--radius-lg);
        padding: 1.5rem;
        text-align: center;
        transition: all var(--transition-base);
        position: relative;
    }

    .silk-step:hover {
        transform: translateY(-4px);
        border-color: var(--color-border-hover);
        box-shadow: var(--shadow-card-hover);
    }

    .silk-step-number {
        width: 36px;
        height: 36px;
        background: linear-gradient(135deg, var(--color-primary), var(--color-primary-hover));
        border-radius: 50%;
        display: inline-flex;
        align-items: center;
        justify-content: center;
        font-weight: 700;
        font-size: 0.9rem;
        color: white !important;
        margin-bottom: 0.75rem;
    }

    /* — Info Model Card — */
    .silk-model-info {
        background: linear-gradient(135deg, rgba(20, 35, 65, 0.85), rgba(15, 30, 55, 0.85));
        border: 1.5px solid var(--color-border);
        border-left: 4px solid var(--color-primary-light);
        border-radius: var(--radius-md);
        padding: 1.5rem;
        animation: fadeInUp 0.4s ease-out;
    }

    /* — Feature Grid — */
    .silk-feature-item {
        display: flex;
        align-items: center;
        gap: 10px;
        padding: 8px 0;
        color: var(--color-text-secondary) !important;
        font-size: 0.95rem;
    }

    .silk-feature-check {
        color: var(--color-green) !important;
        font-weight: 700;
    }

    /* — Timing Badge — */
    .silk-timing {
        display: inline-flex;
        align-items: center;
        gap: 6px;
        background: rgba(59, 130, 246, 0.1);
        border: 1px solid var(--color-border);
        border-radius: var(--radius-sm);
        padding: 6px 14px;
        font-size: 0.85rem;
        color: var(--color-text-accent) !important;
        font-family: var(--font-mono);
        margin-top: 0.5rem;
    }

    </style>
    """, unsafe_allow_html=True)

# Call custom styling on app start
inject_custom_css()

# ==================== REUSABLE UI HELPERS ====================

def render_page_header(title, subtitle, icon=""):
    """Render a styled page header with icon, title and subtitle"""
    st.markdown(f"""
    <div class="silk-page-header">
        <h2 style="margin:0 0 0.25rem 0 !important;">{icon} {title}</h2>
        <p style="color:#94a3b8 !important; margin:0; font-size:1rem;">{subtitle}</p>
    </div>
    """, unsafe_allow_html=True)

def render_footer():
    """Render a professional footer with branding"""
    st.markdown("""
    <div class="silk-footer">
        <div class="silk-footer-brand">🧵 SilkTrace v1.0</div>
        <p style="color:#94a3b8 !important; font-size:0.95rem;">
            AI-Powered Smart Textile Monitoring & Prediction System
        </p>
        <div class="silk-footer-divider"></div>
        <p style="color:#64748b !important; font-size:0.85rem; margin-bottom:4px;">
            🤖 3 AI Models &nbsp;•&nbsp; ⚡ Energy Prediction &nbsp;•&nbsp; 👷 Productivity &nbsp;•&nbsp; 🧵 Defect Detection
        </p>
        <p style="color:#475569 !important; font-size:0.8rem; margin-bottom:4px;">
            Built with <strong>Python</strong> • <strong>Streamlit</strong> • <strong>TensorFlow</strong> •
            <strong>Scikit-learn</strong> • <strong>Plotly</strong>
        </p>
        <div class="silk-footer-divider"></div>
        <p class="silk-footer-meta">
            Developed by <strong style="color:#e2e8f0 !important;">Veera Dinesh D</strong> &nbsp;•&nbsp; Sri Eshwar College of Engineering
        </p>
        <p style="color:#475569 !important; font-size:0.75rem; margin-top:6px;">
            © 2026 SilkTrace &nbsp;|&nbsp; All Rights Reserved
        </p>
        <span class="silk-badge blue" style="margin-top:8px;">v1.0 • Production</span>
    </div>
    """, unsafe_allow_html=True)

def render_timing_badge(elapsed_seconds):
    """Render execution time badge"""
    st.markdown(f"""
    <div class="silk-timing">
        ⏱️ Completed in {elapsed_seconds:.2f}s
    </div>
    """, unsafe_allow_html=True)

def create_pdf_report(summary_df, predicted_class, confidence, inspection_time):
    pdf_file = str(BASE_DIR / "inspection_report.pdf")

    doc = SimpleDocTemplate(pdf_file)
    styles = getSampleStyleSheet()
    elements = []

    elements.append(
        Paragraph("<b>SilkTrace</b>", styles["Title"])
    )

    elements.append(
        Paragraph(
            "<b>AI-Powered Smart Textile Monitoring &amp; Prediction System</b>",
            styles["Heading2"]
        )
    )

    elements.append(
        Paragraph("<br/>", styles["Normal"])
    )

    elements.append(
        Paragraph("<b>FABRIC INSPECTION REPORT</b>", styles["Title"])
    )

    elements.append(
        Paragraph("<br/>", styles["Normal"])
    )

    elements.append(
        Paragraph("<b>Inspection Details</b>", styles["Heading2"])
    )

    elements.append(
        Paragraph(f"<b>Inspection Date &amp; Time:</b> {inspection_time}", styles["Normal"])
    )

    elements.append(
        Paragraph(f"<b>Detected Defect:</b> {predicted_class}", styles["Normal"])
    )

    elements.append(
        Paragraph(f"<b>Confidence:</b> {confidence:.2f}%", styles["Normal"])
    )

    elements.append(
        Paragraph("<b>Model Used:</b> MobileNetV2", styles["Normal"])
    )

    elements.append(
        Paragraph("<br/>", styles["Normal"])
    )
    
    # Recommendation based on detected defect
    if predicted_class == "Hole":
        recommendation = "Repair or replace the damaged fabric section immediately."
    elif predicted_class == "Horizontal":
        recommendation = "Check loom alignment and yarn tension before production."
    else:
        recommendation = "Inspect warp yarns and machine calibration."

    elements.append(
        Paragraph("<b>AI Recommendation</b>", styles["Heading2"])
    )

    elements.append(
        Paragraph(recommendation, styles["Normal"])
    )

    elements.append(
        Paragraph("<br/>", styles["Normal"])
    )
    
    if summary_df is not None and not summary_df.empty:
        raw_data = [summary_df.columns.tolist()] + summary_df.values.tolist()
        data = [[str(cell) for cell in row] for row in raw_data]
    else:
        data = [["Field", "Value"], ["Status", "No Data Available"]]
    
    table = Table(data)

    table.setStyle(
        TableStyle([
            ("BACKGROUND", (0,0), (-1,0), colors.darkblue),
            ("TEXTCOLOR", (0,0), (-1,0), colors.white),
            ("GRID", (0,0), (-1,-1), 1, colors.black),
            ("BACKGROUND", (0,1), (-1,-1), colors.beige),
            ("ALIGN", (0,0), (-1,-1), "CENTER"),
            ("BOTTOMPADDING", (0,0), (-1,0), 10),
        ])
    )

    elements.append(table)

    doc.build(elements)

    return pdf_file

# ---------------- Load Models & Datasets ----------------

BASE_DIR = Path(__file__).resolve().parent.parent

LOGO_PATH = Path(__file__).resolve().parent / "silktrace_logo.png"

PRODUCTIVITY_MODEL_PATH = BASE_DIR / "models" / "productivity_model.pkl"
ENERGY_MODEL_PATH = BASE_DIR / "models" / "energy_model.pkl"
FABRIC_MODEL_PATH = BASE_DIR / "models" / "fabric_defect_model.keras"


# ==================== DOWNLOAD LARGE MODELS IF MISSING ====================

import urllib.request


ENERGY_MODEL_URL = (
    "https://github.com/veeradineshd/SilkTrace/releases/download/"
    "v1.0.0/energy_model.pkl"
)

FABRIC_MODEL_URL = (
    "https://github.com/veeradineshd/SilkTrace/releases/download/"
    "v1.0.0/fabric_defect_model.keras"
)


def ensure_large_models():
    """Download large ML models from the GitHub Release if they are missing."""

    ENERGY_MODEL_PATH.parent.mkdir(parents=True, exist_ok=True)

    if not ENERGY_MODEL_PATH.exists():
        st.info("⬇️ Downloading Energy Prediction model...")
        urllib.request.urlretrieve(
            ENERGY_MODEL_URL,
            ENERGY_MODEL_PATH
        )

    if not FABRIC_MODEL_PATH.exists():
        st.info("⬇️ Downloading Fabric Defect Detection model...")
        urllib.request.urlretrieve(
            FABRIC_MODEL_URL,
            FABRIC_MODEL_PATH
        )


DATE_ENCODER_PATH = BASE_DIR / "models" / "date_encoder.pkl"
QUARTER_ENCODER_PATH = BASE_DIR / "models" / "quarter_encoder.pkl"
DEPARTMENT_ENCODER_PATH = BASE_DIR / "models" / "department_encoder.pkl"
DAY_ENCODER_PATH = BASE_DIR / "models" / "day_encoder.pkl"

@st.cache_resource
def load_resources():
    ensure_large_models()
    for name, path in [
        ("Productivity model", PRODUCTIVITY_MODEL_PATH),
        ("Energy model", ENERGY_MODEL_PATH),
        ("Fabric defect model", FABRIC_MODEL_PATH),
        ("Date encoder", DATE_ENCODER_PATH),
        ("Quarter encoder", QUARTER_ENCODER_PATH),
        ("Department encoder", DEPARTMENT_ENCODER_PATH),
        ("Day encoder", DAY_ENCODER_PATH),
    ]:
        if not path.exists():
            raise FileNotFoundError(f"Required model/encoder resource file not found: {path} ({name})")

    productivity_model = joblib.load(PRODUCTIVITY_MODEL_PATH)
    energy_model = joblib.load(ENERGY_MODEL_PATH)
    fabric_model = load_model(FABRIC_MODEL_PATH)

    date_encoder = joblib.load(DATE_ENCODER_PATH)
    quarter_encoder = joblib.load(QUARTER_ENCODER_PATH)
    department_encoder = joblib.load(DEPARTMENT_ENCODER_PATH)
    day_encoder = joblib.load(DAY_ENCODER_PATH)

    return (
        productivity_model,
        energy_model,
        fabric_model,
        date_encoder,
        quarter_encoder,
        department_encoder,
        day_encoder
    )

(
    productivity_model,
    energy_model,
    fabric_model,
    date_encoder,
    quarter_encoder,
    department_encoder,
    day_encoder,
) = load_resources()

# ---------------- Load Datasets ----------------

@st.cache_data
def load_datasets():
    prod_path = BASE_DIR / "datasets" / "productivity" / "garments_worker_productivity.csv"
    eng_path = BASE_DIR / "datasets" / "energy" / "Steel_industry_data.csv"

    if not prod_path.exists():
        raise FileNotFoundError(f"Productivity dataset file not found at: {prod_path}")
    if not eng_path.exists():
        raise FileNotFoundError(f"Energy dataset file not found at: {eng_path}")

    productivity_data = pd.read_csv(prod_path)
    energy_data = pd.read_csv(eng_path)

    return productivity_data, energy_data


productivity_data, energy_data = load_datasets()

# ==================== SIDEBAR NAVIGATION ====================
 
# SilkTrace Logo
if LOGO_PATH.exists():
    st.sidebar.image(str(LOGO_PATH), width=180)
elif (Path(__file__).resolve().parent / "silktrace_logo.png.png").exists():
    st.sidebar.image(str(Path(__file__).resolve().parent / "silktrace_logo.png.png"), width=180)

# SilkTrace Branding
st.sidebar.markdown("""
<div style="text-align:center;">
    <h2 style="color:white; margin:5px 0;">SilkTrace</h2>
    <p style="color:#dbeafe; margin:0;">
        AI-Powered Textile Intelligence
    </p>
</div>
""", unsafe_allow_html=True)
 
with st.sidebar:

    page = option_menu(
        menu_title="📂 Navigation",

        options=[
            "Home",
            "Productivity Prediction",
            "Energy Prediction",
            "Fabric Defect Detection",
            "Analytics",
            "About Project"
        ],

        icons=[
            "house-fill",
            "people-fill",
            "lightning-charge-fill",
            "grid-3x3-gap-fill",
            "bar-chart-fill",
            "info-circle-fill"
        ],

        menu_icon="cpu-fill",

        default_index=0,

        styles={
            "container": {
                "padding": "5px",
                "background-color": "#0f172a"
            },

            "icon": {
                "color": "#60a5fa",
                "font-size": "18px"
            },

            "nav-link": {
                "font-size": "16px",
                "text-align": "left",
                "margin": "5px",
                "padding": "12px",
                "border-radius": "10px",
                "--hover-color": "#1e3a8a",
            },

            "nav-link-selected": {
                "background-color": "#2563eb",
                "color": "white",
                "font-weight": "bold"
            },

            "menu-title": {
                "color": "white",
                "font-size": "20px",
                "font-weight": "bold"
            }
        }
    )

st.sidebar.markdown("---")
st.sidebar.markdown("### 📊 System Status")
col1, col2 = st.sidebar.columns(2)
with col1:
    st.metric("Models", "3", "Active")
with col2:
    st.metric("Status", "Online", "✅")

st.sidebar.markdown("---")
st.sidebar.markdown("---")

st.sidebar.success("🟢 All AI Models Loaded")

st.sidebar.caption("""
Version : 1.0

Random Forest × 2

MobileNetV2

Developed by

Veera Dinesh D
""")

# ==================== HELPER FUNCTION FOR METRIC CARDS ====================

def display_metric_card(label, value, icon="", delta=None):
    """Display professional metric cards"""
    st.metric(label=f"{icon} {label}" if icon else label, value=value, delta=delta)

# ==================== HOME PAGE ==================== 
 
if page == "Home":

    # — Hero Section —
    st.markdown("""
    <div class="silk-hero">
        <div class="silk-hero-title">🧵 SilkTrace</div>
        <div class="silk-hero-subtitle">AI-Powered Smart Textile Monitoring & Prediction System</div>
        <div class="silk-hero-status">
            <div class="silk-hero-status-dot"></div>
            All AI Models Online
        </div>
    </div>
    """, unsafe_allow_html=True)

    from datetime import datetime

    st.caption(f"🕒 Dashboard Loaded : {datetime.now().strftime('%d %B %Y  |  %I:%M %p')}")
    
    st.markdown("---")

    st.markdown("""
    <div class="silk-model-info">
        <p style="color:#bfdbfe !important; font-size:1rem;">
            🚀 <strong>Transform Your Textile Manufacturing</strong> — SilkTrace integrates advanced AI to
            improve productivity, optimize energy, and automate quality inspection.
        </p>
    </div>
    """, unsafe_allow_html=True)

    st.markdown("---")

    # — KPI Cards —
    st.markdown("### 📈 System Overview")
    col1, col2, col3, col4 = st.columns(4)

    with col1:
        display_metric_card("AI Models", "3", "🤖")

    with col2:
        display_metric_card("Productivity Records", f"{len(productivity_data):,}", "👷")

    with col3:
        display_metric_card("Energy Records", f"{len(energy_data):,}", "⚡")

    with col4:
        display_metric_card("Fabric Classes", "3", "🧵")

    col1, col2, col3 = st.columns(3)

    with col1:
        st.metric("Accuracy", "95.8%")

    with col2:
        st.metric("Predictions", "50K+")

    with col3:
        st.metric("Processing Time", "<1 sec")

    st.markdown("---")

    # — Core Modules —
    st.markdown("### 🎯 Core Modules")

    col1, col2, col3 = st.columns(3)

    with col1:
        st.markdown("""
        <div class="silk-module-card green">
            <div class="silk-module-icon green">👷</div>
            <h4 style="color:#86efac !important; margin-bottom:0.75rem;">Productivity Prediction</h4>
            <p style="color:#d1fae5 !important; font-size:0.9rem;"><strong>Predict</strong> Worker Productivity</p>
            <p style="color:#d1fae5 !important; font-size:0.9rem;"><strong>Improve</strong> Workforce Planning</p>
            <p style="color:#6ee7b7 !important; font-size:0.85rem; margin-top:0.75rem;">
                <span class="silk-badge green">Random Forest</span>
            </p>
        </div>
        """, unsafe_allow_html=True)


    with col2:
        st.markdown("""
        <div class="silk-module-card amber">
            <div class="silk-module-icon amber">⚡</div>
            <h4 style="color:#fde68a !important; margin-bottom:0.75rem;">Energy Prediction</h4>
            <p style="color:#fef3c7 !important; font-size:0.9rem;"><strong>Forecast</strong> Energy Consumption</p>
            <p style="color:#fef3c7 !important; font-size:0.9rem;"><strong>Reduce</strong> Electricity Cost</p>
            <p style="color:#fcd34d !important; font-size:0.85rem; margin-top:0.75rem;">
                <span class="silk-badge amber">Random Forest</span>
            </p>
        </div>
        """, unsafe_allow_html=True)


    with col3:
        st.markdown("""
        <div class="silk-module-card blue">
            <div class="silk-module-icon blue">🧵</div>
            <h4 style="color:#7dd3fc !important; margin-bottom:0.75rem;">Fabric Defect Detection</h4>
            <p style="color:#bae6fd !important; font-size:0.9rem;"><strong>Detect</strong> Fabric Defects</p>
            <p style="color:#bae6fd !important; font-size:0.9rem;"><strong>Deep Learning</strong> Inspection</p>
            <p style="color:#38bdf8 !important; font-size:0.85rem; margin-top:0.75rem;">
                <span class="silk-badge blue">MobileNetV2</span>
            </p>
        </div>
        """, unsafe_allow_html=True)
    
    st.markdown("---")

    # — System Workflow —
    st.markdown("### 🔄 System Workflow")

    workflow_col1, workflow_col2, workflow_col3 = st.columns(3)

    with workflow_col1:
        st.markdown("""
        <div class="silk-step">
            <div class="silk-step-number">1</div>
            <h4 style="color:#e0f2fe !important; margin-bottom:0.5rem;">📥 Input</h4>
            <p style="font-size:0.9rem;">• Worker Data</p>
            <p style="font-size:0.9rem;">• Energy Parameters</p>
            <p style="font-size:0.9rem;">• Fabric Images</p>
        </div>
        """, unsafe_allow_html=True)

    with workflow_col2:
        st.markdown("""
        <div class="silk-step">
            <div class="silk-step-number">2</div>
            <h4 style="color:#e0f2fe !important; margin-bottom:0.5rem;">🤖 AI Processing</h4>
            <p style="font-size:0.9rem;">• Random Forest</p>
            <p style="font-size:0.9rem;">• MobileNetV2</p>
            <p style="font-size:0.9rem;">• Data Analysis</p>
        </div>
        """, unsafe_allow_html=True)

    with workflow_col3:
        st.markdown("""
        <div class="silk-step">
            <div class="silk-step-number">3</div>
            <h4 style="color:#e0f2fe !important; margin-bottom:0.5rem;">📊 Output</h4>
            <p style="font-size:0.9rem;">• Predictions</p>
            <p style="font-size:0.9rem;">• Analytics</p>
            <p style="font-size:0.9rem;">• PDF Reports</p>
        </div>
        """, unsafe_allow_html=True)

    st.markdown("---")

    # — Technology Stack —
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("### 🛠 Technology Stack")
        st.markdown("""
        - **Language:** Python
        - **ML Framework:** Scikit-learn
        - **DL Framework:** TensorFlow/Keras
        - **Dashboard:** Streamlit
        - **Visualization:** Plotly
        - **Data:** Pandas & NumPy
        """)
    
    st.markdown("---")

    # — Project Highlights —
    st.markdown("### ⭐ Project Highlights")

    col1, col2 = st.columns(2)

    with col1:
        st.markdown("""
        <div class="silk-card">
            <div class="silk-feature-item"><span class="silk-feature-check">✅</span> Three AI Models</div>
            <div class="silk-feature-item"><span class="silk-feature-check">✅</span> Interactive Dashboard</div>
            <div class="silk-feature-item"><span class="silk-feature-check">✅</span> PDF Report Generation</div>
            <div class="silk-feature-item"><span class="silk-feature-check">✅</span> CSV Export</div>
            <div class="silk-feature-item"><span class="silk-feature-check">✅</span> Real-Time Prediction</div>
        </div>
        """, unsafe_allow_html=True)

    with col2:
        st.markdown("""
        <div class="silk-card">
            <div class="silk-feature-item"><span class="silk-feature-check">✅</span> Analytics Dashboard</div>
            <div class="silk-feature-item"><span class="silk-feature-check">✅</span> TensorFlow Integration</div>
            <div class="silk-feature-item"><span class="silk-feature-check">✅</span> Scikit-learn Models</div>
            <div class="silk-feature-item"><span class="silk-feature-check">✅</span> Modern UI/UX</div>
            <div class="silk-feature-item"><span class="silk-feature-check">✅</span> Responsive Layout</div>
        </div>
        """, unsafe_allow_html=True)
    
    st.markdown("---")

    # — Key Features —
    st.markdown("### 📊 Key Features")

    st.markdown("""
    - Worker Productivity Prediction
    - Energy Consumption Forecasting
    - Deep Learning Fabric Inspection
    - Interactive Analytics Dashboard
    - PDF & CSV Report Generation
    - Real-time Inspection History
    """)

    st.markdown("---")

    # — Why SilkTrace —
    st.markdown("## 🚀 Why SilkTrace?")

    col1, col2, col3 = st.columns(3)

    with col1:
        st.markdown("""
        <div class="silk-module-card blue">
            <div class="silk-module-icon blue">⚡</div>
            <h4 style="color:#7dd3fc !important;">Faster Decisions</h4>
            <p style="font-size:0.9rem; margin-top:0.5rem;">AI predicts productivity and energy usage instantly.</p>
        </div>
        """, unsafe_allow_html=True)

    with col2:
        st.markdown("""
        <div class="silk-module-card green">
            <div class="silk-module-icon green">📈</div>
            <h4 style="color:#86efac !important;">Better Productivity</h4>
            <p style="font-size:0.9rem; margin-top:0.5rem;">Monitor workers and improve manufacturing efficiency.</p>
        </div>
        """, unsafe_allow_html=True)

    with col3:
        st.markdown("""
        <div class="silk-module-card amber">
            <div class="silk-module-icon amber">🧵</div>
            <h4 style="color:#fde68a !important;">Better Quality</h4>
            <p style="font-size:0.9rem; margin-top:0.5rem;">Automatically detect fabric defects using Deep Learning.</p>
        </div>
        """, unsafe_allow_html=True)
    
    st.markdown("")
    st.success("👉 **Get Started** | Select a module from the sidebar to begin analyzing textile data with AI.")

    st.markdown("---")

    # — Footer —
    render_footer()

# ==================== ENERGY PREDICTION PAGE ====================
 
elif page == "Energy Prediction":
 
    render_page_header(
        "Energy Consumption Prediction",
        "Forecast energy usage to optimize costs and efficiency",
        "⚡"
    )
    
    st.markdown("""
    <div class="silk-model-info">
        <h4 style="color:#fde68a !important; margin-bottom:0.75rem;">🤖 AI Model Information</h4>
        <p style="font-size:0.9rem;"><strong>Algorithm:</strong> Random Forest Regressor</p>
        <p style="font-size:0.9rem;"><strong>Dataset:</strong> Steel Industry Energy Consumption</p>
        <p style="font-size:0.9rem;"><strong>Purpose:</strong> Predict factory energy usage to reduce electricity cost.</p>
        <p style="font-size:0.9rem;"><strong>Input Features:</strong> 10</p>
    </div>
    """, unsafe_allow_html=True)

    st.markdown("---")

    col1, col2 = st.columns([2, 1])
    
    with col1:
        st.markdown("### ⚙️ Input Parameters")
    
    with col2:
        st.info("💡 **Tip:** Enter realistic values for accurate predictions")

    col1, col2 = st.columns(2)
    
    with col1:
        date = st.number_input("📅 Date", value=0)
        lagging_reactive = st.number_input("⚡ Lagging Current Reactive Power (kVarh)", value=0.0)
        leading_reactive = st.number_input("⚡ Leading Current Reactive Power (kVarh)", value=0.0)
        co2 = st.number_input("💨 CO2 (tCO2)", value=0.0)
    
    with col2:
        lagging_pf = st.number_input("📊 Lagging Current Power Factor", value=0.0)
        leading_pf = st.number_input("📊 Leading Current Power Factor", value=0.0)
        nsm = st.number_input("⏱️ NSM", value=0)
        week_status = st.selectbox("📅 Week Status", ["Weekday", "Weekend"])

    col1, col2, col3 = st.columns(3)
    
    with col1:
        day_name = st.selectbox(
            "📆 Day of Week",
            [
                "Monday",
                "Tuesday",
                "Wednesday",
                "Thursday",
                "Friday",
                "Saturday",
                "Sunday"
            ]
        )
    
    with col2:
        load_type = st.selectbox(
            "📦 Load Type",
            [
                "Light_Load",
                "Medium_Load",
                "Maximum_Load"
            ]
        )
    
    with col3:
        st.empty()

    week = 0 if week_status == "Weekday" else 1

    day_mapping = {
        "Friday": 0,
        "Monday": 1,
        "Saturday": 2,
        "Sunday": 3,
        "Thursday": 4,
        "Tuesday": 5,
        "Wednesday": 6
    }
 
    day = day_mapping[day_name]

    load_mapping = {
        "Light_Load": 0,
        "Maximum_Load": 1,
        "Medium_Load": 2
    }
 
    load = load_mapping[load_type]

    st.markdown("---")

    if st.button("🚀 Predict Energy Usage", use_container_width=True):
 
        input_df = pd.DataFrame([{
            "date": date,
            "Lagging_Current_Reactive.Power_kVarh": lagging_reactive,
            "Leading_Current_Reactive_Power_kVarh": leading_reactive,
            "CO2(tCO2)": co2,
            "Lagging_Current_Power_Factor": lagging_pf,
            "Leading_Current_Power_Factor": leading_pf,
            "NSM": nsm,
            "WeekStatus": week,
            "Day_of_week": day,
            "Load_Type": load
        }])
 
        start_time = time.time()
        with st.spinner("🤖 AI is predicting energy consumption..."):
            prediction = energy_model.predict(input_df)
        elapsed = time.time() - start_time

        st.success("✅ Prediction Completed Successfully!")
        render_timing_badge(elapsed)
        st.balloons()
        from pathlib import Path

        history_file = BASE_DIR / "history" / "energy_history.csv"
        history_file.parent.mkdir(parents=True, exist_ok=True)

        history = pd.DataFrame([{
            "Date": date,
            "WeekStatus": week_status,
            "Day": day_name,
            "Load_Type": load_type,
            "Predicted_Energy_kWh": prediction[0]
        }])

        if history_file.exists() and history_file.stat().st_size > 0:
            old = pd.read_csv(history_file)
            history = pd.concat([old, history], ignore_index=True)

        history.to_csv(history_file, index=False)
        
        # Intelligent Feedback
        if prediction[0] > 1000:
            st.error("⚠ High Energy Consumption")

        elif prediction[0] > 600:
            st.warning("⚠ Moderate Energy Consumption")

        else:
            st.success("✅ Efficient Energy Consumption")
        
        st.markdown("---")
        
        col1, col2, col3 = st.columns([1, 1, 1])
        
        with col2:
            st.markdown("""
            <div class="silk-result-card">
                <p style="color:#fde68a !important; font-size:0.85rem; text-transform:uppercase; letter-spacing:1px; font-weight:600;">⚡ Energy Prediction</p>
                <div class="silk-result-value" style="color:#f59e0b !important;">{:.2f} kWh</div>
                <p class="silk-result-label" style="color:#94a3b8 !important;">Predicted Energy Usage</p>
            </div>
            """.format(prediction[0]), unsafe_allow_html=True)

        st.markdown("---")
        render_footer()
 
# ==================== PRODUCTIVITY PREDICTION PAGE ====================
 
elif page == "Productivity Prediction":
    
    render_page_header(
        "Worker Productivity Prediction",
        "Predict productivity to optimize workforce planning and efficiency",
        "👷"
    )

    st.markdown("""
    <div class="silk-model-info">
        <h4 style="color:#86efac !important; margin-bottom:0.75rem;">🤖 AI Model Information</h4>
        <p style="font-size:0.9rem;"><strong>Algorithm:</strong> Random Forest Regressor</p>
        <p style="font-size:0.9rem;"><strong>Dataset:</strong> Garments Worker Productivity</p>
        <p style="font-size:0.9rem;"><strong>Purpose:</strong> Predict worker productivity before production.</p>
        <p style="font-size:0.9rem;"><strong>Input Features:</strong> 14</p>
    </div>
    """, unsafe_allow_html=True)

    st.markdown("---")

    col1, col2 = st.columns([2, 1])
    
    with col1:
        st.markdown("### 📋 Worker & Production Data")
    
    with col2:
        st.info("💡 **Tip:** Provide accurate workforce metrics for precise predictions")

    # Categorical inputs
    col1, col2 = st.columns(2)
    
    with col1:
        date = st.selectbox(
            "📅 Select Date",
            date_encoder.classes_
        )

    with col2:
        quarter = st.selectbox(
            "📊 Select Quarter",
            quarter_encoder.classes_
        )

    col1, col2 = st.columns(2)
    
    with col1:
        department = st.selectbox(
            "🏭 Select Department",
            department_encoder.classes_
        )

    with col2:
        day = st.selectbox(
            "📆 Select Day",
            day_encoder.classes_
        )

    st.markdown("### 👥 Workforce Information")

    col1, col2, col3 = st.columns(3)

    with col1:
        team = st.number_input("👥 Team Number", min_value=1, value=1)

    with col2:
        no_of_workers = st.number_input("👷 Number of Workers", min_value=0, value=50)

    with col3:
        targeted_productivity = st.number_input(
            "🎯 Targeted Productivity",
            min_value=0.0,
            max_value=1.0,
            value=0.8
        )

    st.markdown("### ⚙️ Production Parameters")

    col1, col2, col3 = st.columns(3)

    with col1:
        smv = st.number_input("⏱️ SMV (Standard Minute Value)", min_value=0.0, value=20.0)
        wip = st.number_input("📦 WIP (Work In Progress)", min_value=0.0, value=100.0)
        over_time = st.number_input("⏰ Over Time (hours)", min_value=0, value=0)

    with col2:
        incentive = st.number_input("💰 Incentive", min_value=0, value=50)
        idle_time = st.number_input("⏸️ Idle Time", min_value=0.0, value=0.0)
        idle_men = st.number_input("👤 Idle Men", min_value=0, value=0)

    with col3:
        no_of_style_change = st.number_input("🔄 Number of Style Changes", min_value=0, value=0)

    st.markdown("---")

    if st.button("🚀 Predict Productivity", use_container_width=True):

        input_data = pd.DataFrame([{

            "date": date_encoder.transform([date])[0],
            "quarter": quarter_encoder.transform([quarter])[0],
            "department": department_encoder.transform([department])[0],
            "day": day_encoder.transform([day])[0],

            "team": team,
            "targeted_productivity": targeted_productivity,
            "smv": smv,
            "wip": wip,
            "over_time": over_time,
            "incentive": incentive,
            "idle_time": idle_time,
            "idle_men": idle_men,
            "no_of_style_change": no_of_style_change,
            "no_of_workers": no_of_workers

        }])

        start_time = time.time()
        with st.spinner("🤖 AI is predicting worker productivity..."):
            prediction = productivity_model.predict(input_data)
        elapsed = time.time() - start_time

        st.success("✅ Prediction Completed Successfully!")
        render_timing_badge(elapsed)
        st.balloons()
        
        history_file = BASE_DIR / "history" / "productivity_history.csv"
        history_file.parent.mkdir(parents=True, exist_ok=True)

        history = pd.DataFrame([{
            "Date": date,
            "Department": department,
            "Day": day,
            "Team": team,
            "Predicted_Productivity": prediction[0]
        }])

        if history_file.exists() and history_file.stat().st_size > 0:
            old = pd.read_csv(history_file)
            history = pd.concat([old, history], ignore_index=True)

        history.to_csv(history_file, index=False)
        
        # Intelligent Feedback
        if prediction[0] >= 0.80:
            st.success("✅ Excellent Productivity")

        elif prediction[0] >= 0.60:
            st.warning("⚠ Average Productivity")

        else:
            st.error("❌ Low Productivity")
        
        st.markdown("---")
        
        col1, col2, col3 = st.columns([1, 1, 1])
        
        with col2:
            if prediction[0] >= targeted_productivity:
                status_color = "#22c55e"
                status_icon = "✅"
                status = "On Target"
            else:
                status_color = "#f59e0b"
                status_icon = "⚠️"
                status = "Below Target"

            # Determine badge class
            badge_class = "green" if prediction[0] >= targeted_productivity else "amber"

            st.markdown(f"""
            <div class="silk-result-card">
                <p style="color:#86efac !important; font-size:0.85rem; text-transform:uppercase; letter-spacing:1px; font-weight:600;">👷 Productivity Result</p>
                <div class="silk-result-value" style="color:{status_color} !important;">{prediction[0]:.2f}</div>
                <p class="silk-result-label" style="color:#94a3b8 !important;">Actual Productivity</p>
                <div style="margin-top:0.75rem;">
                    <span class="silk-badge {badge_class}">{status_icon} {status}</span>
                </div>
            </div>
            """, unsafe_allow_html=True)

        st.markdown("---")
        render_footer()
 
# ==================== FABRIC DEFECT DETECTION PAGE ====================

elif page == "Fabric Defect Detection":

    render_page_header(
        "Fabric Defect Detection",
        "AI-Powered Deep Learning for Automated Quality Inspection",
        "🧵"
    )

    st.markdown("""
    <div class="silk-model-info">
        <h4 style="color:#7dd3fc !important; margin-bottom:0.75rem;">🤖 Deep Learning Model</h4>
        <p style="font-size:0.9rem;"><strong>Architecture:</strong> MobileNetV2</p>
        <p style="font-size:0.9rem;"><strong>Classes:</strong> Hole • Horizontal • Vertical</p>
        <p style="font-size:0.9rem;"><strong>Input Size:</strong> 224 × 224 pixels</p>
    </div>
    """, unsafe_allow_html=True)

    st.markdown("---")

    with st.expander("ℹ️ Model Information", expanded=False):

        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown("""
            **Model Architecture:** MobileNetV2
            
            **Framework:** TensorFlow / Keras
            
            **Input Size:** 224 × 224 pixels
            
            **Processing:** Real-time inference
            """)
        
        with col2:
            st.markdown("""
            **Defect Classes:**
            - 🕳️ **Hole** - Fabric damage or punctures
            - ↔️ **Horizontal** - Horizontal line defects
            - ↕️ **Vertical** - Vertical line defects
            
            **Accuracy:** Production-grade AI model
            """)

    st.markdown("### 📸 Upload Fabric Image")

    uploaded_file = st.file_uploader(
        "Choose a fabric image for inspection",
        type=["jpg", "jpeg", "png"],
        help="Supported formats: JPG, JPEG, PNG. Recommended size: 224x224 pixels"
    )

    if uploaded_file is not None:

        image = Image.open(uploaded_file).convert("RGB")

        col1, col2 = st.columns([2, 1])
        
        with col1:
            st.image(
                image,
                caption="Uploaded Fabric Image",
                use_container_width=True
            )
        
        with col2:
            st.markdown("### 🖼️ Image Details")
            st.metric("Width", f"{image.width}px")
            st.metric("Height", f"{image.height}px")
            st.metric("Format", image.mode)

        st.divider()

        # Resize and preprocess
        img = image.resize((224, 224))
        img = np.array(img, dtype=np.float32)
        img = img / 255.0
        img = np.expand_dims(img, axis=0)

        # Predict
        start_time = time.time()
        with st.spinner("🤖 AI is analyzing the fabric image..."):
            prediction = fabric_model.predict(img)
        elapsed = time.time() - start_time

        class_names = [
            "Hole",
            "Horizontal",
            "Vertical"
        ]

        predicted_class = class_names[np.argmax(prediction)]
        confidence = float(np.max(prediction) * 100)
        probabilities = prediction[0] * 100
        
        # ==================== PREDICTION RESULTS ====================
        
        st.markdown("### 🤖 AI Prediction Result")
        render_timing_badge(elapsed)
        
        col1, col2, col3 = st.columns(3)
        
        with col1:
            if confidence >= 90:
                st.success(f"✅ High Confidence Detection")
            elif confidence >= 70:
                st.info(f"ℹ️ Moderate Confidence Detection")
            else:
                st.warning(f"⚠️ Low Confidence - Manual Review Recommended")

        with col2:
            st.metric("Detected Defect", predicted_class)

        with col3:
            st.metric("Confidence Score", f"{confidence:.2f}%")

        st.markdown("---")

        # Confidence indicator
        st.markdown("### 📊 Confidence Analysis")
        
        col1, col2 = st.columns([3, 1])
        
        with col1:
            st.progress(float(confidence) / 100)
        
        with col2:
            if confidence >= 80:
                st.success("✅ Reliable")
            elif confidence >= 60:
                st.warning("⚠️ Moderate")
            else:
                st.error("❌ Low")

        st.markdown("---")
        
        # Probability distribution
        st.markdown("### 📈 Defect Type Probabilities")

        probability_df = pd.DataFrame({
            "Defect Type": class_names,
            "Probability (%)": probabilities.round(2)
        })

        st.dataframe(probability_df, use_container_width=True, hide_index=True)

        # Chart
        chart_df = pd.DataFrame({
            "Defect Type": class_names,
            "Probability (%)": probabilities
        })

        fig = px.bar(
            chart_df,
            x="Defect Type",
            y="Probability (%)",
            text="Probability (%)",
            color="Defect Type",
            title="Prediction Confidence Distribution",
            color_discrete_sequence=["#ef4444", "#f59e0b", "#0ea5e9"]
        )
        
        fig.update_traces(texttemplate="%{text:.2f}%", textposition="outside")
        fig.update_layout(
            xaxis_title="Defect Type",
            yaxis_title="Confidence (%)",
            yaxis=dict(range=[0, 100]),
            height=400,
            showlegend=False,
            plot_bgcolor="rgba(15, 23, 42, 0.5)",
            paper_bgcolor="rgba(0,0,0,0)",
            font=dict(color="#e2e8f0")
        )
        
        st.plotly_chart(fig, use_container_width=True)
        
        st.divider()
        
        # ==================== INSPECTION SUMMARY ====================
        
        st.markdown("### 📋 Inspection Summary")

        inspection_time = datetime.now().strftime("%d-%m-%Y %I:%M %p")

        summary = pd.DataFrame({

            "Field":[
                "Detected Defect",
                "Confidence Level",
                "Inspection Time",
                "Model Used",
                "Image Dimensions"
            ],

            "Value":[
                predicted_class,
                f"{confidence:.2f}%",
                inspection_time,
                "MobileNetV2",
                f"{image.width} × {image.height}"
            ]

        })

        st.dataframe(summary, use_container_width=True, hide_index=True)
        
        st.divider()

        # ==================== EXPORT OPTIONS ====================
        
        st.markdown("### 📥 Export & Download")
        
        col1, col2 = st.columns(2)

        with col1:
            report_df = summary.copy()
            pdf_file = create_pdf_report(
                report_df,
                predicted_class,
                confidence,
                inspection_time
            )

            with open(pdf_file, "rb") as pdf:
                st.download_button(
                    label="📄 Download Inspection Report (PDF)",
                    data=pdf,
                    file_name="SilkTrace_Inspection_Report.pdf",
                    mime="application/pdf",
                    use_container_width=True
            )

        with col2:
            csv = summary.to_csv(index=False).encode("utf-8")
            st.download_button(
                label="📊 Download Report (CSV)",
                data=csv,
                file_name="inspection_report.csv",
                mime="text/csv",
                use_container_width=True
            )
        
        # ==================== HISTORY MANAGEMENT ====================
        
        st.divider()
        st.markdown("### 📂 Inspection History")

        history = pd.DataFrame({
            "Date": [inspection_time],
            "Detected Defect": [predicted_class],
            "Confidence (%)": [round(confidence, 2)]
        })

        history_file = BASE_DIR / "history" / "inspection_history.csv"
        history_file.parent.mkdir(parents=True, exist_ok=True)

        if history_file.exists() and history_file.stat().st_size > 0:
            old_history = pd.read_csv(history_file)
            history = pd.concat([old_history, history], ignore_index=True)

        history.to_csv(history_file, index=False)
        
        history_df = pd.read_csv(history_file)
        
        st.dataframe(
            history_df.sort_values("Date", ascending=False),
            use_container_width=True,
            hide_index=True
        )
        
        # ==================== RECOMMENDATIONS ====================
        
        st.divider()
        st.markdown("### 💡 AI Recommendation")
        
        if predicted_class == "Hole":
            st.warning("🔴 **Action Required:** Repair or replace the damaged fabric section before proceeding to production. This defect affects product quality significantly.")

        elif predicted_class == "Horizontal":
            st.info("🟠 **Maintenance Alert:** Check loom alignment and yarn tension settings. Horizontal defects indicate mechanical alignment issues.")

        elif predicted_class == "Vertical":
            st.info("🟠 **Inspection Needed:** Inspect warp yarns and verify machine calibration. Vertical defects suggest warp-related issues.")

        st.markdown("---")
        render_footer()

# ==================== ANALYTICS DASHBOARD ====================
 
elif page == "Analytics":

    render_page_header(
        "SilkTrace Analytics Dashboard",
        "Real-time insights for textile manufacturing optimization",
        "📊"
    )

    st.markdown("""
    <div class="silk-model-info">
        <h4 style="color:#bfdbfe !important; margin-bottom:0.75rem;">📊 Analytics Dashboard</h4>
        <p style="font-size:0.9rem;">This dashboard provides real-time insights into:</p>
        <p style="font-size:0.9rem;">• Worker Productivity Prediction &nbsp;• Energy Consumption Prediction</p>
        <p style="font-size:0.9rem;">• Historical Prediction Records &nbsp;• Manufacturing Performance &nbsp;• AI-driven Decision Support</p>
    </div>
    """, unsafe_allow_html=True)
    
    st.markdown("---")

    energy_history_file = BASE_DIR / "history" / "energy_history.csv"
    productivity_history_file = BASE_DIR / "history" / "productivity_history.csv"
    
    if not energy_history_file.exists() or energy_history_file.stat().st_size == 0:
        energy_history = pd.DataFrame(columns=["Date", "WeekStatus", "Day", "Load_Type", "Predicted_Energy_kWh"])
    else:
        energy_history = pd.read_csv(energy_history_file)

    if not productivity_history_file.exists() or productivity_history_file.stat().st_size == 0:
        productivity_history = pd.DataFrame(columns=["Date", "Department", "Day", "Team", "Predicted_Productivity"])
    else:
        productivity_history = pd.read_csv(productivity_history_file)
    
    # ================= KPI OVERVIEW =================

    st.markdown("### 📈 System Metrics")

    col1, col2, col3, col4 = st.columns(4)

    with col1:
        st.metric(
            "⚡ Energy Predictions",
            len(energy_history)
        )

    with col2:
        st.metric(
            "👷 Productivity Predictions",
            len(productivity_history)
        )

    with col3:
        avg_energy = round(energy_history["Predicted_Energy_kWh"].mean(), 2) if not energy_history.empty and "Predicted_Energy_kWh" in energy_history.columns and not energy_history["Predicted_Energy_kWh"].dropna().empty else 0.0
        st.metric(
            "⚡ Average Energy",
            avg_energy
        )

    with col4:
        avg_productivity = round(productivity_history["Predicted_Productivity"].mean(), 2) if not productivity_history.empty and "Predicted_Productivity" in productivity_history.columns and not productivity_history["Predicted_Productivity"].dropna().empty else 0.0
        st.metric(
            "👷 Average Productivity",
            avg_productivity
        )

    st.markdown("---")

    st.markdown("### ⚡ Energy Consumption Trend")
    if not energy_history.empty and "Date" in energy_history.columns and "Predicted_Energy_kWh" in energy_history.columns:
        energy_chart = energy_history.set_index("Date")
        st.line_chart(energy_chart["Predicted_Energy_kWh"])
    else:
        st.info("No energy prediction history available yet.")

    st.markdown("### 👷 Productivity Trend")
    if not productivity_history.empty and "Date" in productivity_history.columns and "Predicted_Productivity" in productivity_history.columns:
        productivity_chart = productivity_history.set_index("Date")
        st.line_chart(productivity_chart["Predicted_Productivity"])
    else:
        st.info("No productivity prediction history available yet.")
    
    # ================= PREDICTION HISTORY =================

    st.markdown("### 📋 Recent Prediction History")

    col1, col2 = st.columns(2)

    with col1:
        st.markdown("### ⚡ Energy Prediction History")
        st.dataframe(energy_history.tail(10), use_container_width=True)

    with col2:
        st.subheader("👷 Productivity Prediction History")
        st.dataframe(productivity_history.tail(10), use_container_width=True)

    st.markdown("---")
    
    st.subheader("⬇ Download Prediction History")

    col1, col2 = st.columns(2)

    with col1:
        if energy_history_file.exists() and energy_history_file.stat().st_size > 0:
            with open(energy_history_file, "rb") as file:
                st.download_button(
                    label="⬇ Download Energy History",
                    data=file,
                    file_name="energy_history.csv",
                    mime="text/csv",
                    use_container_width=True
                )
        else:
            st.download_button(
                label="⬇ Download Energy History",
                data=energy_history.to_csv(index=False).encode("utf-8"),
                file_name="energy_history.csv",
                mime="text/csv",
                use_container_width=True
            )

    with col2:
        if productivity_history_file.exists() and productivity_history_file.stat().st_size > 0:
            with open(productivity_history_file, "rb") as file:
                st.download_button(
                    label="⬇ Download Productivity History",
                    data=file,
                    file_name="productivity_history.csv",
                    mime="text/csv",
                    use_container_width=True
                )
        else:
            st.download_button(
                label="⬇ Download Productivity History",
                data=productivity_history.to_csv(index=False).encode("utf-8"),
                file_name="productivity_history.csv",
                mime="text/csv",
                use_container_width=True
            )

    st.markdown("---")

    # ================= PRODUCTIVITY ANALYSIS =================

    st.markdown("### 👷 Productivity Analysis")

    col1, col2 = st.columns(2)

    with col1:
        dept_productivity = productivity_data.groupby("department")["actual_productivity"].mean().reset_index()
        
        fig = px.bar(
            dept_productivity,
            x="department",
            y="actual_productivity",
            title="Average Productivity by Department",
            labels={"actual_productivity": "Avg Productivity", "department": "Department"},
            color="actual_productivity",
            color_continuous_scale="Blues"
        )
        fig.update_layout(
            height=400,
            showlegend=False,
            plot_bgcolor="rgba(15, 23, 42, 0.5)",
            paper_bgcolor="rgba(0,0,0,0)",
            font=dict(color="#e2e8f0")
        )
        st.plotly_chart(fig, use_container_width=True)

    with col2:
        quarter_productivity = productivity_data.groupby("quarter")["actual_productivity"].mean().reset_index()
        
        fig = px.line(
            quarter_productivity,
            x="quarter",
            y="actual_productivity",
            title="Productivity Trend by Quarter",
            labels={"actual_productivity": "Avg Productivity", "quarter": "Quarter"},
            markers=True,
            line_shape="spline"
        )
        fig.update_layout(
            height=400,
            plot_bgcolor="rgba(15, 23, 42, 0.5)",
            paper_bgcolor="rgba(0,0,0,0)",
            font=dict(color="#e2e8f0"),
            hovermode="x unified"
        )
        st.plotly_chart(fig, use_container_width=True)

    st.markdown("---")

    # ================= ENERGY ANALYSIS =================

    st.markdown("### ⚡ Energy Consumption Analysis")

    col1, col2 = st.columns(2)

    with col1:
        energy_stats = energy_data.groupby("Load_Type")["Usage_kWh"].sum().reset_index()

        fig = px.pie(
            energy_stats,
            names="Load_Type",
            values="Usage_kWh",
            title="Energy Usage by Load Type",
            color_discrete_sequence=["#ef4444", "#f59e0b", "#0ea5e9"]
        )
        fig.update_layout(
            height=400,
            paper_bgcolor="rgba(0,0,0,0)",
            font=dict(color="#e2e8f0")
        )
        st.plotly_chart(fig, use_container_width=True)

    with col2:
        load_counts = energy_data["Load_Type"].value_counts().reset_index()
        load_counts.columns = ["Load Type","Count"]

        fig = px.bar(
            load_counts,
            x="Load Type",
            y="Count",
            title="Load Type Distribution",
            color="Load Type",
            color_discrete_sequence=["#ef4444", "#f59e0b", "#0ea5e9"]
        )
        fig.update_layout(
            height=400,
            showlegend=False,
            plot_bgcolor="rgba(15, 23, 42, 0.5)",
            paper_bgcolor="rgba(0,0,0,0)",
            font=dict(color="#e2e8f0")
        )
        st.plotly_chart(fig, use_container_width=True)

    st.markdown("---")

    st.markdown("### 📊 Prediction Distribution")

    col1, col2 = st.columns(2)

    with col1:
        if not energy_history.empty and "Predicted_Energy_kWh" in energy_history.columns:
            fig = px.histogram(
                energy_history,
                x="Predicted_Energy_kWh",
                nbins=10,
                title="Energy Prediction Distribution",
                color_discrete_sequence=["#f59e0b"]
            )
            fig.update_layout(
                plot_bgcolor="rgba(15, 23, 42, 0.5)",
                paper_bgcolor="rgba(0,0,0,0)",
                font=dict(color="#e2e8f0")
            )
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("No energy distribution data available yet.")

    with col2:
        if not productivity_history.empty and "Predicted_Productivity" in productivity_history.columns:
            fig = px.histogram(
                productivity_history,
                x="Predicted_Productivity",
                nbins=10,
                title="Productivity Prediction Distribution",
                color_discrete_sequence=["#22c55e"]
            )
            fig.update_layout(
                plot_bgcolor="rgba(15, 23, 42, 0.5)",
                paper_bgcolor="rgba(0,0,0,0)",
                font=dict(color="#e2e8f0")
            )
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("No productivity distribution data available yet.")

    st.markdown("---")
    
    # ================= SUMMARY STATISTICS =================

    st.markdown("### 📊 Summary Statistics")

    col1, col2 = st.columns(2)

    with col1:
        st.markdown("#### 👷 Productivity Dataset")
        st.dataframe(
            productivity_data.describe(),
            use_container_width=True
        )

    with col2:
        st.markdown("#### ⚡ Energy Dataset")
        st.dataframe(
            energy_data.describe(),
            use_container_width=True
        )

    st.markdown("---")

    st.success(
        "📊 **Dashboard Insights:** SilkTrace Analytics provides comprehensive AI-driven intelligence for productivity improvement, energy optimization, and manufacturing excellence."
    )
    
    st.markdown("---")

    st.markdown("""
    <div class="silk-card">
        <h4 style="color:#e0f2fe !important; margin-bottom:0.75rem;">📌 Dashboard Summary</h4>
        <div class="silk-feature-item"><span class="silk-feature-check">✅</span> Historical Predictions</div>
        <div class="silk-feature-item"><span class="silk-feature-check">✅</span> AI Performance Monitoring</div>
        <div class="silk-feature-item"><span class="silk-feature-check">✅</span> Productivity Analysis</div>
        <div class="silk-feature-item"><span class="silk-feature-check">✅</span> Energy Consumption Analysis</div>
        <div class="silk-feature-item"><span class="silk-feature-check">✅</span> Downloadable Reports</div>
        <div class="silk-feature-item"><span class="silk-feature-check">✅</span> Business Intelligence Dashboard</div>
    </div>
    """, unsafe_allow_html=True)

    st.markdown("")
    render_footer()
    
# ==================== ABOUT PAGE ====================
 
elif page == "About Project":

    render_page_header(
        "About SilkTrace",
        "AI-Powered Smart Textile Monitoring & Prediction System",
        "ℹ️"
    )

    st.markdown("""
    <div class="silk-card">
        <h3 style="color:#e0f2fe !important; margin-bottom:0.75rem;">🧵 Project Overview</h3>
        <p style="font-size:1rem; line-height:1.7;">
            SilkTrace is an advanced Artificial Intelligence-based decision support system engineered to
            revolutionize textile manufacturing through intelligent productivity predictions, energy consumption
            forecasting, and automated fabric quality inspection.
        </p>
    </div>
    """, unsafe_allow_html=True)

    st.markdown("---")

    col1, col2 = st.columns(2)

    with col1:

        st.markdown("### 🎯 Problem Statement")

        st.markdown("""
        <div class="silk-card" style="border-left: 4px solid #ef4444;">
            <h4 style="color:#fca5a5 !important; margin-bottom:0.75rem;">Current Challenges in Textile Industry</h4>
            <div class="silk-feature-item"><span style="color:#ef4444 !important;">🔴</span> Manual monitoring of worker productivity</div>
            <div class="silk-feature-item"><span style="color:#ef4444 !important;">🔴</span> Inefficient energy consumption management</div>
            <div class="silk-feature-item"><span style="color:#ef4444 !important;">🔴</span> Slow fabric quality inspection processes</div>
            <div class="silk-feature-item"><span style="color:#ef4444 !important;">🔴</span> High production losses and waste</div>
            <div class="silk-feature-item"><span style="color:#ef4444 !important;">🔴</span> Lack of data-driven decision support</div>
        </div>
        """, unsafe_allow_html=True)

    with col2:

        st.markdown("### 💡 Proposed Solution")

        st.markdown("""
        <div class="silk-card" style="border-left: 4px solid #22c55e;">
            <h4 style="color:#86efac !important; margin-bottom:0.75rem;">SilkTrace Capabilities</h4>
            <div class="silk-feature-item"><span class="silk-feature-check">✅</span> Intelligent Productivity Prediction</div>
            <div class="silk-feature-item"><span class="silk-feature-check">✅</span> Smart Energy Forecasting</div>
            <div class="silk-feature-item"><span class="silk-feature-check">✅</span> Automated Fabric Defect Detection</div>
            <div class="silk-feature-item"><span class="silk-feature-check">✅</span> AI-Powered Analytics Dashboard</div>
            <div class="silk-feature-item"><span class="silk-feature-check">✅</span> Instant Report Generation</div>
        </div>
        """, unsafe_allow_html=True)

    st.markdown("---")

    st.markdown("### 🤖 Artificial Intelligence Modules")

    col1, col2, col3 = st.columns(3)

    with col1:
        st.markdown("""
        <div class="silk-module-card green">
            <div class="silk-module-icon green">👷</div>
            <h4 style="color:#86efac !important; margin-bottom:0.75rem;">Productivity Prediction</h4>
            <p style="font-size:0.9rem;"><strong>Algorithm:</strong> Random Forest Regressor</p>
            <p style="font-size:0.9rem;"><strong>Purpose:</strong> Predict worker productivity to optimize workforce planning and increase efficiency.</p>
            <p style="font-size:0.9rem;"><strong>Input Features:</strong> 14+ parameters</p>
        </div>
        """, unsafe_allow_html=True)

    with col2:
        st.markdown("""
        <div class="silk-module-card amber">
            <div class="silk-module-icon amber">⚡</div>
            <h4 style="color:#fde68a !important; margin-bottom:0.75rem;">Energy Prediction</h4>
            <p style="font-size:0.9rem;"><strong>Algorithm:</strong> Random Forest Regressor</p>
            <p style="font-size:0.9rem;"><strong>Purpose:</strong> Forecast factory energy usage to reduce electricity costs and carbon footprint.</p>
            <p style="font-size:0.9rem;"><strong>Input Features:</strong> 10+ parameters</p>
        </div>
        """, unsafe_allow_html=True)

    with col3:
        st.markdown("""
        <div class="silk-module-card blue">
            <div class="silk-module-icon blue">🧵</div>
            <h4 style="color:#7dd3fc !important; margin-bottom:0.75rem;">Fabric Defect Detection</h4>
            <p style="font-size:0.9rem;"><strong>Model:</strong> MobileNetV2 (Deep Learning)</p>
            <p style="font-size:0.9rem;"><strong>Purpose:</strong> Automatically classify fabric defects from images with high accuracy.</p>
            <p style="font-size:0.9rem;"><strong>Classes:</strong> Hole, Horizontal, Vertical</p>
        </div>
        """, unsafe_allow_html=True)

    st.markdown("---")

    st.markdown("### 🛠 Technology Stack")

    col1, col2, col3 = st.columns(3)

    with col1:
        st.markdown("""
        <div class="silk-card">
            <h4 style="color:#e0f2fe !important; margin-bottom:0.5rem;">💻 Programming & Data</h4>
            <div class="silk-feature-item"><span class="silk-feature-check">▸</span> Python 3.x</div>
            <div class="silk-feature-item"><span class="silk-feature-check">▸</span> Pandas</div>
            <div class="silk-feature-item"><span class="silk-feature-check">▸</span> NumPy</div>
            <div class="silk-feature-item"><span class="silk-feature-check">▸</span> Scikit-learn</div>
        </div>
        """, unsafe_allow_html=True)

    with col2:
        st.markdown("""
        <div class="silk-card">
            <h4 style="color:#e0f2fe !important; margin-bottom:0.5rem;">🧠 Deep Learning</h4>
            <div class="silk-feature-item"><span class="silk-feature-check">▸</span> TensorFlow</div>
            <div class="silk-feature-item"><span class="silk-feature-check">▸</span> Keras</div>
            <div class="silk-feature-item"><span class="silk-feature-check">▸</span> MobileNetV2</div>
        </div>
        """, unsafe_allow_html=True)

    with col3:
        st.markdown("""
        <div class="silk-card">
            <h4 style="color:#e0f2fe !important; margin-bottom:0.5rem;">📊 Dashboard & Visualization</h4>
            <div class="silk-feature-item"><span class="silk-feature-check">▸</span> Streamlit</div>
            <div class="silk-feature-item"><span class="silk-feature-check">▸</span> Plotly</div>
            <div class="silk-feature-item"><span class="silk-feature-check">▸</span> ReportLab</div>
            <div class="silk-feature-item"><span class="silk-feature-check">▸</span> Pillow</div>
        </div>
        """, unsafe_allow_html=True)

    st.markdown("---")

    st.markdown("### 📊 Project Features")

    features = [
        "✅ Real-time Worker Productivity Prediction",
        "✅ Accurate Energy Consumption Forecasting",
        "✅ AI-Powered Fabric Defect Detection",
        "✅ Interactive Analytics Dashboard",
        "✅ PDF Inspection Report Generation",
        "✅ CSV Data Export Capabilities",
        "✅ Inspection History Tracking",
        "✅ AI-Based Decision Support System"
    ]
    
    for feature in features:
        st.markdown(f"**{feature}**")

    st.markdown("---")

    st.markdown("### 🌍 Industrial Impact & Benefits")

    col1, col2 = st.columns(2)

    with col1:
        st.markdown("""
        <div class="silk-card">
            <h4 style="color:#86efac !important; margin-bottom:0.5rem;">⚡ Operational Efficiency</h4>
            <div class="silk-feature-item"><span class="silk-feature-check">▸</span> Reduce manual inspection time by up to 80%</div>
            <div class="silk-feature-item"><span class="silk-feature-check">▸</span> Improve workforce productivity prediction accuracy</div>
            <div class="silk-feature-item"><span class="silk-feature-check">▸</span> Optimize energy consumption and reduce costs</div>
            <br/>
            <h4 style="color:#7dd3fc !important; margin-bottom:0.5rem;">🔍 Quality Assurance</h4>
            <div class="silk-feature-item"><span class="silk-feature-check">▸</span> Automated fabric defect detection</div>
            <div class="silk-feature-item"><span class="silk-feature-check">▸</span> Consistent quality standards</div>
            <div class="silk-feature-item"><span class="silk-feature-check">▸</span> Reduced production losses</div>
        </div>
        """, unsafe_allow_html=True)

    with col2:
        st.markdown("""
        <div class="silk-card">
            <h4 style="color:#fde68a !important; margin-bottom:0.5rem;">📈 Data-Driven Decision Making</h4>
            <div class="silk-feature-item"><span class="silk-feature-check">▸</span> Real-time analytics and insights</div>
            <div class="silk-feature-item"><span class="silk-feature-check">▸</span> AI-powered recommendations</div>
            <div class="silk-feature-item"><span class="silk-feature-check">▸</span> Historical performance tracking</div>
            <br/>
            <h4 style="color:#86efac !important; margin-bottom:0.5rem;">🌿 Sustainability</h4>
            <div class="silk-feature-item"><span class="silk-feature-check">▸</span> Reduce energy consumption</div>
            <div class="silk-feature-item"><span class="silk-feature-check">▸</span> Minimize production waste</div>
            <div class="silk-feature-item"><span class="silk-feature-check">▸</span> Support sustainable manufacturing practices</div>
        </div>
        """, unsafe_allow_html=True)

    st.markdown("---")

    st.markdown("### 👨‍💻 Developer Information")

    st.markdown("""
    <div class="silk-card" style="text-align:center; max-width:500px; margin: 0 auto;">
        <div style="width:64px; height:64px; background:linear-gradient(135deg, #3b82f6, #2563eb); border-radius:50%; display:flex; align-items:center; justify-content:center; font-size:1.75rem; margin: 0 auto 1rem auto;">👨‍💻</div>
        <h3 style="color:#e0f2fe !important; margin-bottom:0.25rem;">Veera Dinesh D</h3>
        <p style="color:#94a3b8 !important; font-size:0.9rem; margin-bottom:1rem;">25AD236 &nbsp;•&nbsp; AI & Data Science</p>
        <div class="silk-footer-divider"></div>
        <p style="color:#94a3b8 !important; font-size:0.9rem; margin-top:1rem;">🎓 Sri Eshwar College of Engineering</p>
        <p style="color:#64748b !important; font-size:0.85rem; margin-top:0.25rem;">SilkTrace – AI-Powered Smart Textile Monitoring & Prediction System</p>
        <p style="color:#64748b !important; font-size:0.8rem; margin-top:0.5rem;">📧 Contact through Sri Eshwar College of Engineering</p>
    </div>
    """, unsafe_allow_html=True)

    st.markdown("---")

    st.markdown("""
    <div class="silk-card" style="text-align:center; border-color: rgba(14, 165, 233, 0.4);">
        <h3 style="color:#7dd3fc !important; margin-bottom:0.5rem;">🚀 Transform Your Textile Manufacturing with AI</h3>
        <p style="color:#94a3b8 !important; font-size:1rem;">SilkTrace combines cutting-edge artificial intelligence with industry expertise to revolutionize textile production.</p>
        <p style="color:#64748b !important; font-style:italic; margin-top:0.5rem;">Making textile manufacturing smarter, more efficient, and more sustainable through AI innovation.</p>
    </div>
    """, unsafe_allow_html=True)

    st.markdown("---")
    render_footer()
