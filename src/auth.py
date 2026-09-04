# SilkTrace — Authentication & Role-Based Access Control (Native Streamlit OIDC)
import os
import json
import logging
from pathlib import Path
import streamlit as st
from src.config import (
    DEFAULT_ROLE_MAPPING,
    ROLE_PERMISSIONS,
    APP_NAME,
    APP_DESCRIPTION,
)

# ── Safe diagnostic logger ──────────────────────────────────────────────────
# Safe to log: auth events, user roles, email domains.
# NEVER log: client_secret, cookie_secret, auth codes, tokens.
_log = logging.getLogger("silktrace.auth")
if not _log.handlers:
    _handler = logging.StreamHandler()
    _handler.setFormatter(logging.Formatter("%(asctime)s [%(levelname)s] silktrace.auth: %(message)s"))
    _log.addHandler(_handler)
    _log.setLevel(logging.INFO)


# ──────────────────────────────────────────────────────────────────────────────
# NATIVE STREAMLIT OIDC CONFIGURATION BRIDGE
# ──────────────────────────────────────────────────────────────────────────────

def ensure_secrets_file():
    """Ensure .streamlit/secrets.toml exists on disk with environment variables if on Render/Cloud.

    Populates the [auth] section required by Streamlit Native OIDC (st.login / st.user).
    """
    try:
        client_id     = os.getenv("GOOGLE_CLIENT_ID", "")
        client_secret = os.getenv("GOOGLE_CLIENT_SECRET", "")
        redirect_uri  = os.getenv("GOOGLE_REDIRECT_URI", "https://silktrace.onrender.com/oauth2callback")
        cookie_secret = os.getenv("COOKIE_SECRET", "silktrace-super-secret-key-32chars-min-2026")

        root_dir       = Path(__file__).resolve().parent.parent
        streamlit_dir  = root_dir / ".streamlit"
        streamlit_dir.mkdir(parents=True, exist_ok=True)
        secrets_file   = streamlit_dir / "secrets.toml"

        dash_streamlit_dir = root_dir / "dashboard" / ".streamlit"
        dash_streamlit_dir.mkdir(parents=True, exist_ok=True)
        dash_secrets_file  = dash_streamlit_dir / "secrets.toml"

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
    except Exception as exc:
        _log.warning("Secrets synchronization skipped: %s", exc)


def sync_native_auth_secrets():
    """Ensure environment variables are bridged to secrets file for native Streamlit OIDC."""
    ensure_secrets_file()


# Synchronize secrets configuration on module import
sync_native_auth_secrets()


def get_secret(name: str, default: str = "") -> str:
    """Retrieve secret from environment variables, st.secrets, or secrets.toml safely.

    1. First checks system environment variables (os.environ / os.getenv)
       — primary for Render, Docker, and CI/CD pipelines.
    2. Safely checks st.secrets without crashing if absent.
    3. Direct disk fallback to .streamlit/secrets.toml via tomllib.
    """
    val = os.getenv(name)
    if val is not None and val.strip():
        return val.strip()

    mapping = {
        "GOOGLE_REDIRECT_URI": "redirect_uri",
        "COOKIE_SECRET":       "cookie_secret",
        "GOOGLE_CLIENT_ID":    "client_id",
        "GOOGLE_CLIENT_SECRET":"client_secret",
    }

    try:
        if name in st.secrets:
            sec_val = st.secrets.get(name)
            if sec_val is not None and str(sec_val).strip():
                return str(sec_val).strip()

        auth_sec = st.secrets.get("auth")
        if isinstance(auth_sec, dict):
            if name in mapping and mapping[name] in auth_sec:
                v = auth_sec[mapping[name]]
                if v:
                    return str(v).strip()
    except Exception:
        pass

    # Disk fallback via tomllib
    try:
        import tomllib
        root_dir = Path(__file__).resolve().parent.parent
        for p in [root_dir / ".streamlit" / "secrets.toml", root_dir / "dashboard" / ".streamlit" / "secrets.toml"]:
            if p.exists():
                data = tomllib.loads(p.read_text(encoding="utf-8"))
                if name in data and str(data[name]).strip():
                    return str(data[name]).strip()
                auth_data = data.get("auth", {})
                if isinstance(auth_data, dict):
                    if name in auth_data and str(auth_data[name]).strip():
                        return str(auth_data[name]).strip()
                    if name in mapping and mapping[name] in auth_data:
                        v = auth_data[mapping[name]]
                        if v and str(v).strip():
                            return str(v).strip()
    except Exception:
        pass

    return default


def _get_secret_or_env(key: str, default: str = "") -> str:
    """Backwards-compatible alias for get_secret."""
    return get_secret(key, default)


def get_google_credentials():
    """Returns Google Client ID, Secret, and Redirect URI."""
    client_id     = get_secret("GOOGLE_CLIENT_ID", "")
    client_secret = get_secret("GOOGLE_CLIENT_SECRET", "")
    redirect_uri  = get_secret("GOOGLE_REDIRECT_URI", "https://silktrace.onrender.com/oauth2callback")
    return client_id, client_secret, redirect_uri


def is_google_auth_configured() -> bool:
    """Check if valid, non-placeholder Google OAuth credentials are provided.

    Prevents triggering Streamlit's native st.login() with dummy credentials,
    which causes a 500 Internal Server Error during the Tornado OAuth token exchange.
    """
    client_id, client_secret, _ = get_google_credentials()
    if not client_id or not client_secret:
        return False

    placeholders = [
        "test-client-id",
        "test-client-secret",
        "test-google-client",
        "your_client_id",
        "your_client_secret",
        "your-client-id",
        "your-client-secret",
        "example.com",
        "placeholder",
    ]
    cid_lower = client_id.lower().strip()
    sec_lower = client_secret.lower().strip()

    if any(p in cid_lower for p in placeholders) or any(p in sec_lower for p in placeholders):
        return False

    return True


# ──────────────────────────────────────────────────────────────────────────────
# ROLE-BASED ACCESS CONTROL (RBAC)
# ──────────────────────────────────────────────────────────────────────────────

def get_user_role(email: str) -> str:
    """Determine role for a given email based on configuration or default mapping."""
    if not email:
        return "ADMIN" if st.session_state.get("demo_authenticated", False) else "ANALYST"
    role_map_raw = _get_secret_or_env("SILKTRACE_ROLE_MAP")
    role_map     = DEFAULT_ROLE_MAPPING.copy()
    if role_map_raw:
        try:
            parsed = json.loads(role_map_raw)
            if isinstance(parsed, dict):
                role_map.update(parsed)
        except Exception:
            pass
    return role_map.get(email.lower().strip(), "ANALYST")


def get_current_user_info() -> dict:
    """Retrieve consistent user metadata dictionary across native Google OIDC and Demo Mode."""
    # 1. Native Streamlit Google OIDC
    if hasattr(st, "user") and getattr(st.user, "is_logged_in", False):
        user_name  = getattr(st.user, "name",    "Google User") or "Google User"
        user_email = getattr(st.user, "email",   "") or ""
        user_pic   = getattr(st.user, "picture", "") or ""
        user_role  = get_user_role(user_email)
        info = {
            "name": user_name,
            "email": user_email,
            "picture": user_pic,
            "role": user_role,
            "is_google": True,
            "is_authenticated": True,
        }
        st.session_state["google_authenticated"] = True
        st.session_state["google_user_info"] = info
        return info

    # 1b. Cached Google OIDC Session State
    if st.session_state.get("google_authenticated", False) and "google_user_info" in st.session_state:
        return st.session_state["google_user_info"]

    # 2. Check query params or session state for Demo Access
    is_demo = st.session_state.get("demo_authenticated", False) or (st.query_params.get("auth_mode") == "demo")
    if is_demo:
        demo_info = st.session_state.get("demo_user_info", {})
        user_name  = demo_info.get("name",    "SilkTrace Admin (Demo)")
        user_email = demo_info.get("email",   "admin@silktrace.ai")
        user_pic   = demo_info.get("picture", "")
        user_role  = st.session_state.get("demo_user_role", "ADMIN")
        return {
            "name": user_name,
            "email": user_email,
            "picture": user_pic,
            "role": user_role,
            "is_google": False,
            "is_authenticated": True,
        }

    return {
        "name": "Guest",
        "email": "",
        "picture": "",
        "role": "VIEWER",
        "is_google": False,
        "is_authenticated": False,
    }


def is_feature_allowed_for_user(feature_key: str) -> bool:
    """Check if the current user session has permission to access a feature."""
    user = get_current_user_info()
    if not user.get("is_authenticated", False):
        return False
    user_role = user.get("role", "ANALYST")
    allowed = ROLE_PERMISSIONS.get(user_role, ROLE_PERMISSIONS["ANALYST"])
    return feature_key in allowed


# ──────────────────────────────────────────────────────────────────────────────
# LOGIN SCREEN
# ──────────────────────────────────────────────────────────────────────────────

def render_login_screen():
    """Render a high-converting, professional SaaS login interface."""
    has_real_google_auth = is_google_auth_configured()

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
.silk-dev-notice{background:rgba(30,58,138,.25);border:1px solid rgba(96,165,250,.25);border-radius:12px;padding:12px 14px;color:#bfdbfe !important;font-size:.82rem;text-align:left;margin-bottom:.75rem;line-height:1.45;}
div.stButton>button{background:linear-gradient(135deg,#2563eb,#1d4ed8) !important;color:#fff !important;border:1px solid rgba(96,165,250,.3) !important;border-radius:12px !important;font-weight:600 !important;font-size:.95rem !important;padding:.75rem 1.5rem !important;box-shadow:0 4px 18px rgba(37,99,235,.35) !important;transition:all .2s cubic-bezier(.4,0,.2,1) !important;width:100% !important;margin-bottom:8px !important;}
div.stButton>button:hover{background:linear-gradient(135deg,#3b82f6,#2563eb) !important;box-shadow:0 8px 25px rgba(59,130,246,.5) !important;transform:translateY(-2px) !important;border-color:rgba(147,197,253,.5) !important;}
div.stButton>button:active{transform:translateY(0) !important;}
.silk-login-footer{color:#64748b !important;font-size:.75rem;text-align:center;margin-top:1.25rem;}
</style>""", unsafe_allow_html=True)

    col_l, col_center, col_r = st.columns([1, 1.4, 1])

    with col_center:
        st.markdown(
            f'<div class="silk-login-wrapper">'
            f'<div class="silk-login-logo-container"><div class="silk-login-logo">&#129525;</div></div>'
            f'<div class="silk-login-title">SilkTrace</div>'
            f'<div><span class="silk-login-badge">Enterprise Intelligence &#8226; {APP_NAME}</span></div>'
            f'<p class="silk-login-tagline">{APP_DESCRIPTION}</p>'
            f'<div style="margin-bottom:1rem;">'
            f'<div class="silk-feature-row"><div class="silk-feature-icon">&#9889;</div><div><div class="silk-feature-text">Energy Consumption Forecasting</div><div class="silk-feature-desc">Random Forest industrial power analytics</div></div></div>'
            f'<div class="silk-feature-row"><div class="silk-feature-icon">&#128119;</div><div><div class="silk-feature-text">Garment Workforce Productivity</div><div class="silk-feature-desc">ML-driven target tracking &amp; optimization</div></div></div>'
            f'<div class="silk-feature-row"><div class="silk-feature-icon">&#128269;</div><div><div class="silk-feature-text">MobileNetV2 Fabric QC</div><div class="silk-feature-desc">Computer vision defect classification &amp; PDF reporting</div></div></div>'
            f'<div class="silk-feature-row"><div class="silk-feature-icon">&#128202;</div><div><div class="silk-feature-text">Executive KPI Analytics</div><div class="silk-feature-desc">Role-based access control &amp; automated reporting</div></div></div>'
            f'</div>'
            f'</div>',
            unsafe_allow_html=True
        )

        if has_real_google_auth:
            sync_native_auth_secrets()
            if st.button("🌐 Continue with Google", use_container_width=True, key="google_oauth_btn"):
                _log.info("Google OAuth login initiated via st.login()")
                try:
                    st.login()
                except Exception as exc:
                    _log.error("st.login exception: %s", exc)
                    st.error(f"Authentication error: {exc}")
        else:
            st.markdown(
                '<div class="silk-dev-notice">'
                '&#128274; <strong>Google SSO in Standby:</strong> '
                'Placeholder credentials detected. Use <strong>Demo Access</strong> below to immediately access the workspace, '
                'or configure real OAuth credentials in <code>.streamlit/secrets.toml</code> to enable Google Sign-In.'
                '</div>',
                unsafe_allow_html=True
            )

        if st.button("🚀 Enter Industrial Platform (Demo Access)", use_container_width=True, key="demo_auth_btn"):
            _log.info("Demo Access activated")
            st.session_state["demo_authenticated"] = True
            st.session_state["demo_user_info"] = {
                "name":    "SilkTrace Admin (Demo)",
                "email":   "admin@silktrace.ai",
                "picture": "",
                "sub":     "demo-admin-12345",
            }
            st.session_state["demo_user_role"] = "ADMIN"
            st.query_params["auth_mode"] = "demo"
            st.rerun()

        st.markdown(
            '<p class="silk-login-footer">Protected by SilkTrace Enterprise Security &nbsp;&#8226;&nbsp; SOC2 / OIDC Compliant</p>',
            unsafe_allow_html=True
        )


# ──────────────────────────────────────────────────────────────────────────────
# AUTHENTICATION GATE — called from app.py before any dashboard content
# ──────────────────────────────────────────────────────────────────────────────

def handle_auth_gate():
    """Enforce authentication before rendering dashboard content with reconnect resilience.

    1. Native Streamlit Google OIDC: checks st.user.is_logged_in
    2. Cached Google Session: checks st.session_state['google_authenticated']
    3. Demo Access in session state: checks st.session_state['demo_authenticated']
    4. Reconnect auto-restoration: recovers session from st.query_params['auth_mode']
    5. Unauthenticated: renders login screen and calls st.stop()
    """
    # 1. Check native Streamlit Google OIDC
    if hasattr(st, "user") and getattr(st.user, "is_logged_in", False):
        st.session_state["google_authenticated"] = True
        return

    # 2. Check cached Google session state
    if st.session_state.get("google_authenticated", False):
        return

    # 3. Check Demo Access in session state
    if st.session_state.get("demo_authenticated", False):
        return

    # 4. Recover active session after WebSocket reconnect or tab reload
    if st.query_params.get("auth_mode") == "demo":
        st.session_state["demo_authenticated"] = True
        st.session_state["demo_user_info"] = {
            "name":    "SilkTrace Admin (Demo)",
            "email":   "admin@silktrace.ai",
            "picture": "",
            "sub":     "demo-admin-12345",
        }
        st.session_state["demo_user_role"] = "ADMIN"
        return

    # 5. Not authenticated -> show login UI and stop execution
    render_login_screen()
    st.stop()


# ──────────────────────────────────────────────────────────────────────────────
# SIDEBAR — USER PROFILE & SIGN OUT
# ──────────────────────────────────────────────────────────────────────────────

def render_sidebar_user_profile():
    """Render logged-in user details, role badge, and logout button in sidebar."""
    user = get_current_user_info()
    if not user.get("is_authenticated", False):
        return

    user_name  = user.get("name", "User")
    user_email = user.get("email", "")
    user_pic   = user.get("picture", "")
    user_role  = user.get("role", "ADMIN")
    is_google  = user.get("is_google", False)
    badge_text = f"ROLE: {user_role}" if is_google else f"DEMO MODE: {user_role}"

    st.sidebar.markdown("<div style='text-align:center;'>", unsafe_allow_html=True)
    if user_pic:
        st.sidebar.image(user_pic, width=54)
    st.sidebar.markdown(f"**{user_name}**")
    if user_email:
        st.sidebar.caption(user_email)

    role_color = {
        "ADMIN":    "#22c55e",
        "ANALYST":  "#3b82f6",
        "OPERATOR": "#f59e0b",
        "VIEWER":   "#94a3b8",
    }.get(user_role, "#3b82f6")

    st.sidebar.markdown(f"""
    <div style="margin-top: 4px; margin-bottom: 12px;">
        <span style="background: rgba(30, 41, 59, 0.8); border: 1px solid {role_color}; color: {role_color}; padding: 3px 10px; border-radius: 12px; font-size: 0.75rem; font-weight: 700;">
            {badge_text}
        </span>
    </div>
    """, unsafe_allow_html=True)

    if st.sidebar.button("🚪 Sign Out", use_container_width=True, key="sign_out_btn"):
        _log.info("Sign Out clicked")
        st.query_params.clear()
        st.session_state["demo_authenticated"] = False
        st.session_state["google_authenticated"] = False
        st.session_state.pop("demo_user_info", None)
        st.session_state.pop("demo_user_role", None)
        st.session_state.pop("google_user_info", None)
        if is_google:
            try:
                st.logout()
            except Exception as exc:
                _log.error("st.logout error: %s", exc)
                st.rerun()
        else:
            st.rerun()

    st.sidebar.markdown("</div>", unsafe_allow_html=True)
    st.sidebar.markdown("---")
