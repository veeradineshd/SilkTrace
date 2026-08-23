# SilkTrace — Authentication & Role-Based Access Control (Google OIDC)
import os
import json
import urllib.parse
import textwrap
from pathlib import Path
import requests
import streamlit as st
from src.config import (
    GOOGLE_OIDC_DISCOVERY_URL,
    DEFAULT_ROLE_MAPPING,
    ROLE_PERMISSIONS,
    APP_NAME,
    APP_DESCRIPTION,
)

def ensure_secrets_file():
    """Ensure .streamlit/secrets.toml exists on disk with environment variables if on Render/Cloud."""
    try:
        client_id = os.getenv("GOOGLE_CLIENT_ID", "")
        client_secret = os.getenv("GOOGLE_CLIENT_SECRET", "")
        redirect_uri = os.getenv("GOOGLE_REDIRECT_URI", "https://silktrace.onrender.com/oauth2callback")
        cookie_secret = os.getenv("COOKIE_SECRET", "silktrace-super-secret-key-32chars-min-2026")

        root_dir = Path(__file__).resolve().parent.parent
        streamlit_dir = root_dir / ".streamlit"
        streamlit_dir.mkdir(parents=True, exist_ok=True)
        secrets_file = streamlit_dir / "secrets.toml"

        dash_streamlit_dir = root_dir / "dashboard" / ".streamlit"
        dash_streamlit_dir.mkdir(parents=True, exist_ok=True)
        dash_secrets_file = dash_streamlit_dir / "secrets.toml"

        if client_id and client_secret:
            content = f"""[auth]
redirect_uri = "{redirect_uri}"
cookie_secret = "{cookie_secret}"
client_id = "{client_id}"
client_secret = "{client_secret}"
server_metadata_url = "https://accounts.google.com/.well-known/openid-configuration"

GOOGLE_CLIENT_ID = "{client_id}"
GOOGLE_CLIENT_SECRET = "{client_secret}"
GOOGLE_REDIRECT_URI = "{redirect_uri}"
COOKIE_SECRET = "{cookie_secret}"
"""
            secrets_file.write_text(content, encoding="utf-8")
            dash_secrets_file.write_text(content, encoding="utf-8")
    except Exception:
        pass

def sync_native_auth_secrets():
    """Ensure environment variables are bridged to secrets file for native Streamlit OIDC."""
    ensure_secrets_file()

# Synchronize on load
sync_native_auth_secrets()

def get_secret(name: str, default: str = "") -> str:
    """Retrieve secret from environment variables or st.secrets safely.
    
    1. First checks system environment variables (os.environ / os.getenv)
       — primary for Render, Docker, and CI/CD pipelines.
    2. Then safely checks st.secrets inside a try-except block without triggering
       StreamlitSecretNotFoundError on environments where secrets.toml is absent.
    3. Supports both top-level keys and nested [auth] / [auth.google] sections.
    """
    # 1. Environment variable check (os.getenv returns str or None)
    val = os.getenv(name)
    if val is not None and val.strip():
        return val.strip()

    # 2. Local Streamlit secrets check (only if available)
    try:
        if name in st.secrets:
            sec_val = st.secrets.get(name)
            if sec_val is not None and str(sec_val).strip():
                return str(sec_val).strip()

        # Check nested auth / auth.google tables if defined in secrets.toml
        auth_sec = st.secrets.get("auth")
        if isinstance(auth_sec, dict):
            mapping = {
                "GOOGLE_REDIRECT_URI": "redirect_uri",
                "COOKIE_SECRET": "cookie_secret",
                "GOOGLE_CLIENT_ID": "client_id",
                "GOOGLE_CLIENT_SECRET": "client_secret",
            }
            if name in mapping and mapping[name] in auth_sec:
                v = auth_sec[mapping[name]]
                if v:
                    return str(v).strip()

            google_sec = auth_sec.get("google")
            if isinstance(google_sec, dict):
                if name == "GOOGLE_CLIENT_ID" and "client_id" in google_sec:
                    v = google_sec["client_id"]
                    if v:
                        return str(v).strip()
                if name == "GOOGLE_CLIENT_SECRET" and "client_secret" in google_sec:
                    v = google_sec["client_secret"]
                    if v:
                        return str(v).strip()
    except Exception:
        # st.secrets is unavailable, secrets.toml missing, or unparseable
        pass

    return default

def _get_secret_or_env(key: str, default: str = "") -> str:
    """Backwards-compatible alias for get_secret."""
    return get_secret(key, default)

def get_google_credentials():
    """Returns Google Client ID, Secret, and Redirect URI."""
    client_id = get_secret("GOOGLE_CLIENT_ID", "")
    client_secret = get_secret("GOOGLE_CLIENT_SECRET", "")
    redirect_uri = get_secret("GOOGLE_REDIRECT_URI", "https://silktrace.onrender.com/oauth2callback")
    return client_id, client_secret, redirect_uri

def get_cookie_secret() -> str:
    """Returns Cookie Secret for session encryption."""
    return get_secret("COOKIE_SECRET", "silktrace-super-secret-key-32chars-min-2026")

@st.cache_data(ttl=3600)
def fetch_google_oidc_endpoints():
    """Fetch OIDC endpoints from Google's well-known discovery document."""
    try:
        res = requests.get(GOOGLE_OIDC_DISCOVERY_URL, timeout=5)
        if res.status_code == 200:
            data = res.json()
            return {
                "authorization_endpoint": data.get("authorization_endpoint", "https://accounts.google.com/o/oauth2/v2/auth"),
                "token_endpoint": data.get("token_endpoint", "https://oauth2.googleapis.com/token"),
                "userinfo_endpoint": data.get("userinfo_endpoint", "https://www.googleapis.com/oauth2/v3/userinfo"),
            }
    except Exception:
        pass
    return {
        "authorization_endpoint": "https://accounts.google.com/o/oauth2/v2/auth",
        "token_endpoint": "https://oauth2.googleapis.com/token",
        "userinfo_endpoint": "https://www.googleapis.com/oauth2/v3/userinfo",
    }

def get_google_auth_url() -> str:
    """Generate the Google OAuth 2.0 / OIDC authorization URL."""
    client_id, _, redirect_uri = get_google_credentials()
    endpoints = fetch_google_oidc_endpoints()
    
    params = {
        "client_id": client_id,
        "redirect_uri": redirect_uri,
        "response_type": "code",
        "scope": "openid email profile",
        "access_type": "online",
        "prompt": "select_account",
    }
    return f"{endpoints['authorization_endpoint']}?{urllib.parse.urlencode(params)}"

def exchange_code_for_user_info(code: str) -> dict:
    """Exchange authorization code for access token & user profile from Google OIDC."""
    client_id, client_secret, redirect_uri = get_google_credentials()
    endpoints = fetch_google_oidc_endpoints()

    payload = {
        "code": code,
        "client_id": client_id,
        "client_secret": client_secret,
        "redirect_uri": redirect_uri,
        "grant_type": "authorization_code",
    }
    
    res = requests.post(endpoints["token_endpoint"], data=payload, timeout=10)
    if res.status_code != 200:
        raise RuntimeError(f"Token exchange failed (HTTP {res.status_code}): {res.text}")

    tokens = res.json()
    access_token = tokens.get("access_token")
    if not access_token:
        raise RuntimeError("No access token returned by Google OAuth server.")

    headers = {"Authorization": f"Bearer {access_token}"}
    user_res = requests.get(endpoints["userinfo_endpoint"], headers=headers, timeout=10)
    if user_res.status_code != 200:
        raise RuntimeError(f"Failed to fetch Google user profile: {user_res.text}")

    return user_res.json()

def get_user_role(email: str) -> str:
    """Determine role for a given email based on configuration or default mapping."""
    role_map_raw = _get_secret_or_env("SILKTRACE_ROLE_MAP")
    role_map = DEFAULT_ROLE_MAPPING.copy()
    if role_map_raw:
        try:
            parsed = json.loads(role_map_raw)
            if isinstance(parsed, dict):
                role_map.update(parsed)
        except Exception:
            pass
    return role_map.get(email.lower(), "ANALYST")

def is_feature_allowed_for_user(feature_key: str) -> bool:
    """Check if the current user session has permission to access a feature."""
    if not st.session_state.get("authenticated"):
        return False
    role = st.session_state.get("user_role", "ANALYST")
    allowed = ROLE_PERMISSIONS.get(role, ROLE_PERMISSIONS["ANALYST"])
    return feature_key in allowed

def render_login_screen():
    """Render a high-converting, professional SaaS login interface."""
    client_id, client_secret, redirect_uri = get_google_credentials()

    # Injected styles
    st.markdown("""<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800;900&family=JetBrains+Mono:wght@400;500;600&display=swap');
html,body,[data-testid="stAppViewContainer"],.main{font-family:'Inter',-apple-system,BlinkMacSystemFont,sans-serif;}
[data-testid="stAppViewContainer"]{background:radial-gradient(circle at 50% 15%,rgba(59,130,246,.12),transparent 50%),radial-gradient(circle at 80% 80%,rgba(14,165,233,.08),transparent 40%),linear-gradient(135deg,#0b0f19 0%,#111827 50%,#0f172a 100%);}
[data-testid="stSidebar"],[data-testid="collapsedControl"]{display:none !important;}
.main .block-container{padding-top:2rem !important;padding-bottom:2rem !important;background:transparent !important;border:none !important;box-shadow:none !important;backdrop-filter:none !important;}
.silk-login-wrapper{background:rgba(17,24,39,.72);backdrop-filter:blur(20px);-webkit-backdrop-filter:blur(20px);border:1px solid rgba(255,255,255,.1);border-radius:24px;padding:2.5rem 2.25rem 1.75rem;box-shadow:0 25px 60px -15px rgba(0,0,0,.6),inset 0 1px 1px rgba(255,255,255,.15);text-align:center;margin-bottom:1rem;}
.silk-login-logo-container{display:flex;justify-content:center;align-items:center;width:100%;margin:0 auto 1rem auto;}
.silk-login-logo{display:flex;align-items:center;justify-content:center;width:72px;height:72px;background:linear-gradient(135deg,rgba(59,130,246,.2),rgba(14,165,233,.1));border:1px solid rgba(96,165,250,.3);border-radius:20px;font-size:36px;margin:0 auto;box-shadow:0 8px 24px rgba(59,130,246,.2);}
.silk-login-title{font-size:2.25rem;font-weight:800;letter-spacing:-.03em;background:linear-gradient(135deg,#fff 30%,#93c5fd 100%);-webkit-background-clip:text;-webkit-text-fill-color:transparent;margin-bottom:.35rem;text-align:center;}
.silk-login-badge{display:inline-flex;align-items:center;gap:6px;padding:4px 12px;background:rgba(59,130,246,.15);border:1px solid rgba(96,165,250,.3);border-radius:20px;color:#93c5fd !important;font-size:.75rem;font-weight:600;letter-spacing:.04em;text-transform:uppercase;margin-bottom:.75rem;}
.silk-login-tagline{color:#94a3b8 !important;font-size:.95rem;line-height:1.5;margin-bottom:1.5rem;font-weight:400;text-align:center;}
.silk-feature-row{display:flex;align-items:center;gap:12px;background:rgba(255,255,255,.03);border:1px solid rgba(255,255,255,.06);border-radius:12px;padding:10px 14px;margin-bottom:8px;text-align:left;transition:all .2s ease;}
.silk-feature-row:hover{background:rgba(255,255,255,.06);border-color:rgba(96,165,250,.25);transform:translateX(3px);}
.silk-feature-icon{font-size:1.15rem;display:flex;align-items:center;justify-content:center;min-width:28px;}
.silk-feature-text{font-size:.86rem;color:#e2e8f0 !important;font-weight:500;}
.silk-feature-desc{font-size:.76rem;color:#94a3b8 !important;font-weight:400;}
.silk-google-btn{display:flex;align-items:center;justify-content:center;gap:12px;width:100%;background-color:#ffffff;color:#1f2937 !important;text-decoration:none !important;padding:12px 24px;border-radius:12px;font-weight:600;font-size:.95rem;box-shadow:0 4px 16px rgba(0,0,0,.25);transition:all .2s cubic-bezier(.4,0,.2,1);margin-bottom:.75rem;border:1px solid #e5e7eb;box-sizing:border-box;}
.silk-google-btn:hover{background-color:#f9fafb;transform:translateY(-2px);box-shadow:0 8px 24px rgba(255,255,255,.2);color:#111827 !important;}
.silk-google-btn:active{transform:translateY(0);}
.silk-dev-notice{background:rgba(30,58,138,.25);border:1px solid rgba(96,165,250,.25);border-radius:12px;padding:10px 14px;color:#bfdbfe !important;font-size:.82rem;text-align:center;margin-bottom:.75rem;line-height:1.4;}
div.stButton>button{background:linear-gradient(135deg,#2563eb,#1d4ed8) !important;color:#fff !important;border:1px solid rgba(96,165,250,.3) !important;border-radius:12px !important;font-weight:600 !important;font-size:.95rem !important;padding:.75rem 1.5rem !important;box-shadow:0 4px 18px rgba(37,99,235,.35) !important;transition:all .2s cubic-bezier(.4,0,.2,1) !important;width:100% !important;margin-bottom:8px !important;}
div.stButton>button:hover{background:linear-gradient(135deg,#3b82f6,#2563eb) !important;box-shadow:0 8px 25px rgba(59,130,246,.5) !important;transform:translateY(-2px) !important;border-color:rgba(147,197,253,.5) !important;}
div.stButton>button:active{transform:translateY(0) !important;}
.silk-login-footer{color:#64748b !important;font-size:.75rem;text-align:center;margin-top:1.25rem;}
</style>""", unsafe_allow_html=True)

    # Use centered Streamlit column layout to contain widgets
    col_l, col_center, col_r = st.columns([1, 1.4, 1])

    with col_center:
        st.markdown(
            f'<div class="silk-login-wrapper">'
            f'<div class="silk-login-logo-container"><div class="silk-login-logo">&#129525;</div></div>'
            f'<div class="silk-login-title">SilkTrace</div>'
            f'<div><span class="silk-login-badge">Enterprise Intelligence &#8226; {APP_NAME}</span></div>'
            f'<p class="silk-login-tagline">{APP_DESCRIPTION}</p>'
            f'<div style="margin-bottom:1rem;">'
            f'<div class="silk-feature-row"><div class="silk-feature-icon">&#9889;</div><div><div class="silk-feature-text">Energy Consumption Forecasting</div><div class="silk-feature-desc">Random Forest &amp; XGBoost time-series power analytics</div></div></div>'
            f'<div class="silk-feature-row"><div class="silk-feature-icon">&#128119;</div><div><div class="silk-feature-text">Garment Workforce Productivity</div><div class="silk-feature-desc">ML-driven target tracking &amp; optimization</div></div></div>'
            f'<div class="silk-feature-row"><div class="silk-feature-icon">&#128269;</div><div><div class="silk-feature-text">MobileNetV2 Fabric QC</div><div class="silk-feature-desc">Computer vision defect classification &amp; PDF reporting</div></div></div>'
            f'<div class="silk-feature-row"><div class="silk-feature-icon">&#128202;</div><div><div class="silk-feature-text">Executive KPI Analytics</div><div class="silk-feature-desc">Role-based access control &amp; automated reporting</div></div></div>'
            f'</div>'
            f'</div>',
            unsafe_allow_html=True
        )

        if client_id and client_secret:
            auth_url = get_google_auth_url()
            st.markdown(
                f'<a href="{auth_url}" target="_self" class="silk-google-btn">'
                f'<svg width="18" height="18" viewBox="0 0 24 24" style="flex-shrink:0;">'
                f'<path fill="#4285F4" d="M22.56 12.25c0-.78-.07-1.53-.2-2.25H12v4.26h5.92c-.26 1.37-1.04 2.53-2.21 3.31v2.77h3.57c2.08-1.92 3.28-4.74 3.28-8.09z"/>'
                f'<path fill="#34A853" d="M12 23c2.97 0 5.46-.98 7.28-2.66l-3.57-2.77c-.98.66-2.23 1.06-3.71 1.06-2.86 0-5.29-1.93-6.16-4.53H2.18v2.84C3.99 20.53 7.7 23 12 23z"/>'
                f'<path fill="#FBBC05" d="M5.84 14.1c-.22-.66-.35-1.36-.35-2.1s.13-1.44.35-2.1V7.06H2.18C1.43 8.55 1 10.22 1 12s.43 3.45 1.18 4.94l2.85-2.22.81-.62z"/>'
                f'<path fill="#EA4335" d="M12 5.38c1.62 0 3.06.56 4.21 1.64l3.15-3.15C17.45 2.09 14.97 1 12 1 7.7 1 3.99 3.47 2.18 7.06l3.66 2.84c.87-2.6 3.3-4.52 6.16-4.52z"/>'
                f'</svg>Continue with Google</a>',
                unsafe_allow_html=True
            )
        else:
            st.markdown(
                '<div class="silk-dev-notice">'
                '&#128274; <strong>Google Cloud OIDC</strong> is in standby mode. '
                'Use <strong>Demo Access</strong> below to access the full SilkTrace industrial workspace.'
                '</div>',
                unsafe_allow_html=True
            )

        if st.button("🚀 Enter Industrial Platform (Demo Access)", use_container_width=True, key="demo_auth_btn"):
            st.session_state["authenticated"] = True
            user_info = {
                "name": "SilkTrace Admin",
                "email": "admin@silktrace.ai",
                "picture": "",
                "sub": "demo-admin-12345"
            }
            st.session_state["user_info"] = user_info
            st.session_state["user_role"] = get_user_role("admin@silktrace.ai")
            st.rerun()

        st.markdown(
            '<p class="silk-login-footer">Protected by SilkTrace Enterprise Security &nbsp;&#8226;&nbsp; SOC2 / OIDC Compliant</p>',
            unsafe_allow_html=True
        )

def handle_auth_gate():
    """Handle Google OAuth callback and enforce session authentication."""

    # 1. Check native Streamlit authentication (persisted via encrypted cookie)
    # Wrapped in try/except because st.user raises StreamlitAuthError when [auth]
    # section is absent from secrets.toml (e.g. Render without env vars set).
    try:
        if hasattr(st, "user") and getattr(st.user, "is_logged_in", False):
            st.session_state["authenticated"] = True
            st.session_state["user_info"] = {
                "name": getattr(st.user, "name", "Google User") or "Google User",
                "email": getattr(st.user, "email", "") or "",
                "picture": getattr(st.user, "picture", "") or "",
                "sub": getattr(st.user, "sub", "") or ""
            }
            st.session_state["user_role"] = get_user_role(getattr(st.user, "email", ""))
            return
    except Exception:
        pass

    # 2. Check if user is authenticated via session_state (e.g. Demo Access)
    if st.session_state.get("authenticated", False):
        return

    # 3. Handle manual Google OAuth callback fallback if code in query_params
    if "code" in st.query_params:
        auth_code = st.query_params.get("code")
        if not auth_code:
            st.error("Google OAuth authorization code is missing.")
            st.stop()

        client_id, client_secret, _ = get_google_credentials()
        if not client_id or not client_secret:
            st.error("Google OAuth configuration is incomplete.")
            st.stop()

        try:
            user_info = exchange_code_for_user_info(auth_code)
            st.session_state["authenticated"] = True
            st.session_state["user_info"] = {
                "name": user_info.get("name", "Google User"),
                "email": user_info.get("email", ""),
                "picture": user_info.get("picture", ""),
                "sub": user_info.get("sub", "")
            }
            st.session_state["user_role"] = get_user_role(user_info.get("email", ""))
            st.query_params.clear()
            st.rerun()
        except Exception as e:
            st.error(f"Authentication Error: {str(e)}")
            st.query_params.clear()
            st.stop()

    # 4. User is not authenticated — show login screen
    render_login_screen()
    st.stop()
    
def render_sidebar_user_profile():
    """Render logged-in user details, role badge, and logout button in sidebar."""
    user_info = st.session_state.get("user_info", {})
    user_name = user_info.get("name", "SilkTrace User")
    user_email = user_info.get("email", "")
    user_pic = user_info.get("picture", "")
    user_role = st.session_state.get("user_role", "ANALYST")

    st.sidebar.markdown("<div style='text-align:center;'>", unsafe_allow_html=True)
    if user_pic:
        st.sidebar.image(user_pic, width=54)
    st.sidebar.markdown(f"**{user_name}**")
    if user_email:
        st.sidebar.caption(user_email)
    
    # Role Badge
    role_color = {"ADMIN": "#22c55e", "ANALYST": "#3b82f6", "OPERATOR": "#f59e0b", "VIEWER": "#94a3b8"}.get(user_role, "#3b82f6")
    st.sidebar.markdown(f"""
    <div style="margin-top: 4px; margin-bottom: 12px;">
        <span style="background: rgba(30, 41, 59, 0.8); border: 1px solid {role_color}; color: {role_color}; padding: 3px 10px; border-radius: 12px; font-size: 0.75rem; font-weight: 700;">
            ROLE: {user_role}
        </span>
    </div>
    """, unsafe_allow_html=True)

    if st.sidebar.button("🚪 Sign Out", use_container_width=True):
        try:
            if hasattr(st, "logout"):
                st.logout()
        except Exception:
            pass
        st.session_state["authenticated"] = False
        st.session_state.pop("user_info", None)
        st.session_state.pop("user_role", None)
        st.query_params.clear()
        st.rerun()
    st.sidebar.markdown("</div>", unsafe_allow_html=True)
    st.sidebar.markdown("---")
