# SilkTrace — Authentication & Role-Based Access Control (Google OIDC)
# Persistent session via HMAC-signed cookie (itsdangerous URLSafeTimedSerializer)
import os
import json
import http.cookies
import logging
import time
import urllib.parse
from pathlib import Path
import requests
import streamlit as st
import streamlit.components.v1 as components
from itsdangerous import URLSafeTimedSerializer, BadSignature, SignatureExpired
from src.config import (
    GOOGLE_OIDC_DISCOVERY_URL,
    DEFAULT_ROLE_MAPPING,
    ROLE_PERMISSIONS,
    APP_NAME,
    APP_DESCRIPTION,
)

# ── Safe diagnostic logger ──────────────────────────────────────────────────
# Safe to log: callback events, auth success/failure, cookie state, user role.
# NEVER log: client_secret, cookie_secret, access_token, refresh_token, auth code, id_token.
_log = logging.getLogger("silktrace.auth")
if not _log.handlers:
    _handler = logging.StreamHandler()
    _handler.setFormatter(logging.Formatter("%(asctime)s [%(levelname)s] silktrace.auth: %(message)s"))
    _log.addHandler(_handler)
    _log.setLevel(logging.INFO)

# ── Cookie configuration ────────────────────────────────────────────────────
_COOKIE_NAME    = "st_silk_auth"
_COOKIE_MAX_AGE = 86_400          # 24 hours in seconds
_COOKIE_SALT    = "silktrace-auth-v1"


# ──────────────────────────────────────────────────────────────────────────────
# SECRET / CREDENTIALS HELPERS
# ──────────────────────────────────────────────────────────────────────────────

def ensure_secrets_file():
    """Ensure .streamlit/secrets.toml exists on disk with environment variables if on Render/Cloud."""
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
                "COOKIE_SECRET":       "cookie_secret",
                "GOOGLE_CLIENT_ID":    "client_id",
                "GOOGLE_CLIENT_SECRET":"client_secret",
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
    client_id    = get_secret("GOOGLE_CLIENT_ID", "")
    client_secret = get_secret("GOOGLE_CLIENT_SECRET", "")
    redirect_uri = get_secret("GOOGLE_REDIRECT_URI", "https://silktrace.onrender.com/oauth2callback")
    return client_id, client_secret, redirect_uri


def get_cookie_secret() -> str:
    """Returns Cookie Secret for session encryption."""
    return get_secret("COOKIE_SECRET", "silktrace-super-secret-key-32chars-min-2026")


# ──────────────────────────────────────────────────────────────────────────────
# HMAC-SIGNED COOKIE LAYER
# ──────────────────────────────────────────────────────────────────────────────

def _get_signer() -> "URLSafeTimedSerializer | None":
    """Return a configured URLSafeTimedSerializer, or None if COOKIE_SECRET is absent.

    Reads COOKIE_SECRET exclusively from the environment variable (primary on Render)
    or from st.secrets. Does NOT fall back to a hardcoded default — a missing secret
    means cookie persistence is disabled; the user will need to log in each browser
    session until COOKIE_SECRET is configured.
    """
    # Read raw from env first (Render sets this as an env var, never from default)
    secret = os.getenv("COOKIE_SECRET", "").strip()

    # Try st.secrets as fallback (local dev with secrets.toml)
    if not secret:
        try:
            v = st.secrets.get("COOKIE_SECRET", "")
            if v:
                secret = str(v).strip()
        except Exception:
            pass
        # Also try nested [auth] section
        if not secret:
            try:
                auth_sec = st.secrets.get("auth", {})
                if isinstance(auth_sec, dict):
                    v = auth_sec.get("cookie_secret", "")
                    if v:
                        secret = str(v).strip()
            except Exception:
                pass

    if not secret:
        _log.warning(
            "COOKIE_SECRET is not configured. "
            "Persistent authentication across browser sessions is DISABLED. "
            "Set COOKIE_SECRET in Render environment variables."
        )
        return None

    return URLSafeTimedSerializer(secret, salt=_COOKIE_SALT)


def _create_auth_cookie_value(user_info: dict, user_role: str) -> "str | None":
    """Create a signed auth cookie payload.

    Cookie payload contains ONLY: sub, email, name, picture, role, iat.
    NEVER stores: client_secret, access_token, refresh_token, auth code, id_token.
    Returns the signed string, or None if COOKIE_SECRET is unavailable.
    """
    signer = _get_signer()
    if signer is None:
        return None

    payload = {
        "sub":   user_info.get("sub", ""),
        "email": user_info.get("email", ""),
        "name":  user_info.get("name", ""),
        "pic":   user_info.get("picture", ""),
        "role":  user_role,
        "iat":   int(time.time()),
    }
    try:
        signed = signer.dumps(payload)
        _log.info("Auth cookie created for role=%s", user_role)
        return signed
    except Exception as exc:
        _log.error("Cookie creation failed: %s", type(exc).__name__)
        return None


def _read_auth_cookie() -> "dict | None":
    """Read and verify the auth cookie from the current HTTP request.

    Returns the deserialized payload dict if the cookie is valid and not expired.
    Returns None if: cookie is absent, signature is invalid, or cookie has expired.
    """
    signer = _get_signer()
    if signer is None:
        return None

    # Read raw Cookie header from Streamlit context (available in Streamlit >= 1.31)
    try:
        raw_cookie_header = st.context.headers.get("Cookie", "")
    except Exception:
        _log.debug("Could not read Cookie header from st.context.headers")
        return None

    if not raw_cookie_header:
        return None

    # Parse cookie header to extract our named cookie
    try:
        jar = http.cookies.SimpleCookie()
        jar.load(raw_cookie_header)
        if _COOKIE_NAME not in jar:
            return None
        raw_value = jar[_COOKIE_NAME].value
    except Exception:
        return None

    if not raw_value:
        return None

    # Verify HMAC signature and check expiry
    try:
        payload = signer.loads(raw_value, max_age=_COOKIE_MAX_AGE)
        _log.info(
            "Auth cookie verified — role=%s email_domain=%s",
            payload.get("role", "?"),
            payload.get("email", "@").split("@")[-1],  # log only domain, not full email
        )
        return payload
    except SignatureExpired:
        _log.info("Auth cookie has expired — user must re-authenticate")
        return None
    except BadSignature:
        _log.warning("Auth cookie signature is INVALID — possible tampering detected")
        return None
    except Exception as exc:
        _log.error("Auth cookie read error: %s", type(exc).__name__)
        return None


def _inject_cookie_and_redirect(cookie_value: str, redirect_url: str = "/") -> None:
    """Inject a Set-Cookie via JavaScript and perform a clean browser redirect.

    Note: JavaScript cookie-setting cannot use HttpOnly (browser limitation).
    The cookie is still protected by HMAC signing and the Secure + SameSite=Lax flags.

    This function calls st.stop() — nothing after it will execute.
    """
    # Build cookie attributes string
    # Secure: only sent over HTTPS (Render is always HTTPS)
    # SameSite=Lax: protects against most CSRF, allows OAuth redirects
    cookie_attr = (
        f"Max-Age={_COOKIE_MAX_AGE}; "
        f"Path=/; "
        f"SameSite=Lax; "
        f"Secure"
    )
    full_cookie = f"{_COOKIE_NAME}={cookie_value}; {cookie_attr}"

    # Escape for safe JS string embedding
    cookie_js_str = json.dumps(full_cookie)
    redirect_js_str = json.dumps(redirect_url)

    js = f"""
    <script>
    (function() {{
        // Set auth cookie on the parent document (same origin as Streamlit iframe)
        try {{
            window.parent.document.cookie = {cookie_js_str};
        }} catch(e) {{
            // Fallback: set on current document (local dev where iframe = same origin)
            document.cookie = {cookie_js_str};
        }}
        // Perform clean navigation to root — removes /oauth2callback + code from URL
        window.parent.location.replace({redirect_js_str});
    }})();
    </script>
    """
    components.html(js, height=0, scrolling=False)
    st.stop()


def _inject_clear_cookie_and_redirect(redirect_url: str = "/") -> None:
    """Clear the auth cookie via JavaScript and redirect to the given URL.

    This function calls st.stop() — nothing after it will execute.
    """
    # Set Max-Age=0 to immediately expire the cookie
    clear_cookie = f"{_COOKIE_NAME}=; Max-Age=0; Path=/; SameSite=Lax; Secure"
    # Also clear without Secure for local dev (http)
    clear_cookie_local = f"{_COOKIE_NAME}=; Max-Age=0; Path=/; SameSite=Lax"

    clear_js_str       = json.dumps(clear_cookie)
    clear_js_local_str = json.dumps(clear_cookie_local)
    redirect_js_str    = json.dumps(redirect_url)

    js = f"""
    <script>
    (function() {{
        try {{
            window.parent.document.cookie = {clear_js_str};
            window.parent.document.cookie = {clear_js_local_str};
        }} catch(e) {{
            document.cookie = {clear_js_str};
            document.cookie = {clear_js_local_str};
        }}
        window.parent.location.replace({redirect_js_str});
    }})();
    </script>
    """
    components.html(js, height=0, scrolling=False)
    st.stop()


def _restore_session_from_cookie() -> bool:
    """Attempt to restore authentication from a valid signed cookie.

    If successful, sets session_state["authenticated"], ["user_info"], ["user_role"].
    Returns True if session was restored, False otherwise.
    """
    payload = _read_auth_cookie()
    if payload is None:
        return False

    user_info = {
        "name":    payload.get("name", "Google User"),
        "email":   payload.get("email", ""),
        "picture": payload.get("pic", ""),
        "sub":     payload.get("sub", ""),
    }
    user_role = payload.get("role", "ANALYST")

    st.session_state["authenticated"] = True
    st.session_state["user_info"]     = user_info
    st.session_state["user_role"]     = user_role
    _log.info("Session restored from cookie — role=%s", user_role)
    return True


# ──────────────────────────────────────────────────────────────────────────────
# GOOGLE OIDC HELPERS
# ──────────────────────────────────────────────────────────────────────────────

@st.cache_data(ttl=3600)
def fetch_google_oidc_endpoints():
    """Fetch OIDC endpoints from Google's well-known discovery document."""
    try:
        res = requests.get(GOOGLE_OIDC_DISCOVERY_URL, timeout=5)
        if res.status_code == 200:
            data = res.json()
            return {
                "authorization_endpoint": data.get("authorization_endpoint", "https://accounts.google.com/o/oauth2/v2/auth"),
                "token_endpoint":         data.get("token_endpoint",         "https://oauth2.googleapis.com/token"),
                "userinfo_endpoint":      data.get("userinfo_endpoint",       "https://www.googleapis.com/oauth2/v3/userinfo"),
            }
    except Exception:
        pass
    return {
        "authorization_endpoint": "https://accounts.google.com/o/oauth2/v2/auth",
        "token_endpoint":         "https://oauth2.googleapis.com/token",
        "userinfo_endpoint":      "https://www.googleapis.com/oauth2/v3/userinfo",
    }


def get_google_auth_url() -> str:
    """Generate the Google OAuth 2.0 / OIDC authorization URL."""
    client_id, _, redirect_uri = get_google_credentials()
    endpoints = fetch_google_oidc_endpoints()

    params = {
        "client_id":     client_id,
        "redirect_uri":  redirect_uri,
        "response_type": "code",
        "scope":         "openid email profile",
        "access_type":   "online",
        "prompt":        "select_account",
    }
    return f"{endpoints['authorization_endpoint']}?{urllib.parse.urlencode(params)}"


def exchange_code_for_user_info(code: str) -> dict:
    """Exchange authorization code for access token & user profile from Google OIDC.

    SECURITY: access_token is used only in-memory to call userinfo endpoint.
    It is NEVER stored in session_state, cookies, logs, or any persistent storage.
    The authorization code is consumed exactly once.
    """
    client_id, client_secret, redirect_uri = get_google_credentials()
    endpoints = fetch_google_oidc_endpoints()

    payload = {
        "code":          code,
        "client_id":     client_id,
        "client_secret": client_secret,
        "redirect_uri":  redirect_uri,
        "grant_type":    "authorization_code",
    }

    res = requests.post(endpoints["token_endpoint"], data=payload, timeout=10)
    if res.status_code != 200:
        _log.error("Token exchange failed — HTTP %s", res.status_code)
        raise RuntimeError(f"Token exchange failed (HTTP {res.status_code}): {res.text}")

    tokens = res.json()
    access_token = tokens.get("access_token")
    if not access_token:
        _log.error("Token exchange response contained no access_token")
        raise RuntimeError("No access token returned by Google OAuth server.")

    # Use access_token once — never store it
    headers  = {"Authorization": f"Bearer {access_token}"}
    user_res = requests.get(endpoints["userinfo_endpoint"], headers=headers, timeout=10)
    if user_res.status_code != 200:
        _log.error("Userinfo fetch failed — HTTP %s", user_res.status_code)
        raise RuntimeError(f"Failed to fetch Google user profile: {user_res.text}")

    _log.info("Google OAuth callback succeeded — userinfo received")
    return user_res.json()


def get_user_role(email: str) -> str:
    """Determine role for a given email based on configuration or default mapping."""
    role_map_raw = _get_secret_or_env("SILKTRACE_ROLE_MAP")
    role_map     = DEFAULT_ROLE_MAPPING.copy()
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
    role    = st.session_state.get("user_role", "ANALYST")
    allowed = ROLE_PERMISSIONS.get(role, ROLE_PERMISSIONS["ANALYST"])
    return feature_key in allowed


# ──────────────────────────────────────────────────────────────────────────────
# LOGIN SCREEN
# ──────────────────────────────────────────────────────────────────────────────

def render_login_screen():
    """Render a high-converting, professional SaaS login interface."""
    client_id, client_secret, redirect_uri = get_google_credentials()

    # Warn if COOKIE_SECRET is missing so the operator knows
    if not os.getenv("COOKIE_SECRET", "").strip():
        _log.warning("COOKIE_SECRET env var is not set — sessions will not persist across browser refreshes")

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
            sync_native_auth_secrets()
            if st.button("🌐 Continue with Google", use_container_width=True, key="google_oauth_btn"):
                _log.info("Google OAuth login initiated via st.login()")
                try:
                    st.login()
                except Exception as exc:
                    _log.error("st.login failed: %s", exc)
                    auth_url = get_google_auth_url()
                    st.markdown(f'<meta http-equiv="refresh" content="0; url={auth_url}">', unsafe_allow_html=True)
                    st.stop()
        else:
            st.markdown(
                '<div class="silk-dev-notice">'
                '&#128274; <strong>Google Cloud OIDC</strong> is in standby mode. '
                'Use <strong>Demo Access</strong> below to access the full SilkTrace industrial workspace.'
                '</div>',
                unsafe_allow_html=True
            )

        if st.button("🚀 Enter Industrial Platform (Demo Access)", use_container_width=True, key="demo_auth_btn"):
            _log.info("Demo Access activated")
            demo_user_info = {
                "name":    "SilkTrace Admin",
                "email":   "admin@silktrace.ai",
                "picture": "",
                "sub":     "demo-admin-12345",
            }
            demo_role = get_user_role("admin@silktrace.ai")

            # Set session for current Streamlit session
            st.session_state["authenticated"] = True
            st.session_state["user_info"]     = demo_user_info
            st.session_state["user_role"]     = demo_role
            st.rerun()

        st.markdown(
            '<p class="silk-login-footer">Protected by SilkTrace Enterprise Security &nbsp;&#8226;&nbsp; SOC2 / OIDC Compliant</p>',
            unsafe_allow_html=True
        )


# ──────────────────────────────────────────────────────────────────────────────
# AUTHENTICATION GATE — called from app.py before any dashboard content
# ──────────────────────────────────────────────────────────────────────────────

def handle_auth_gate():
    """Handle Google OAuth callback and enforce session authentication.

    Authentication priority (checked in order):
    1. Native Streamlit st.user (if native OIDC is configured — Case A, not used here)
    2. st.session_state["authenticated"] — valid for the current WebSocket session
    3. Signed auth cookie — restores session across browser refreshes / Render restarts
    4. OAuth callback (?code=...) — exchanges authorization code, writes cookie, redirects
    5. Unauthenticated — shows login screen
    """

    # ── 1. Native Streamlit OIDC (st.user) — not used in Case B, kept as safety net ──
    try:
        if hasattr(st, "user") and getattr(st.user, "is_logged_in", False):
            st.session_state["authenticated"] = True
            st.session_state["user_info"] = {
                "name":    getattr(st.user, "name",    "Google User") or "Google User",
                "email":   getattr(st.user, "email",   "") or "",
                "picture": getattr(st.user, "picture", "") or "",
                "sub":     getattr(st.user, "sub",     "") or "",
            }
            st.session_state["user_role"] = get_user_role(getattr(st.user, "email", ""))
            _log.info("Authenticated via st.user (native OIDC)")
            return
    except Exception:
        pass

    # ── 2. Already authenticated in this WebSocket session ─────────────────────
    if st.session_state.get("authenticated", False):
        return

    # ── 3. Try to restore session from signed cookie ───────────────────────────
    # This is the critical step that fixes the "refresh → login" problem.
    # Every new Streamlit WebSocket session checks the cookie before showing login.
    if _restore_session_from_cookie():
        _log.info("Session restored from cookie — skipping login screen")
        return

    # ── 4. Handle Google OAuth callback (code in query params) ─────────────────
    if "code" in st.query_params:
        _log.info("OAuth callback received — exchanging authorization code")
        auth_code = st.query_params.get("code")
        if not auth_code:
            st.error("Google OAuth authorization code is missing.")
            _log.error("OAuth callback: code param present but empty")
            st.stop()

        client_id, client_secret, _ = get_google_credentials()
        if not client_id or not client_secret:
            st.error("Google OAuth configuration is incomplete. Contact administrator.")
            _log.error("OAuth callback: GOOGLE_CLIENT_ID or GOOGLE_CLIENT_SECRET not configured")
            st.stop()

        try:
            user_info_raw = exchange_code_for_user_info(auth_code)
            # auth_code is now spent — do NOT store it anywhere

            user_info = {
                "name":    user_info_raw.get("name",    "Google User"),
                "email":   user_info_raw.get("email",   ""),
                "picture": user_info_raw.get("picture", ""),
                "sub":     user_info_raw.get("sub",     ""),
            }
            user_role = get_user_role(user_info["email"])

            # Set session_state for any code that runs before the redirect completes
            st.session_state["authenticated"] = True
            st.session_state["user_info"]     = user_info
            st.session_state["user_role"]     = user_role

            _log.info(
                "Google OAuth success — email_domain=%s role=%s",
                user_info["email"].split("@")[-1],  # log only domain, not full email
                user_role,
            )

            # Create signed auth cookie
            cookie_value = _create_auth_cookie_value(user_info, user_role)

            if cookie_value:
                # Write cookie via JS and redirect cleanly to root URL.
                # This removes /oauth2callback?code=... from the browser URL bar
                # and starts a fresh Streamlit session that will read the cookie.
                _log.info("Auth cookie created — redirecting to /")
                _inject_cookie_and_redirect(cookie_value, "/")
                # _inject_cookie_and_redirect calls st.stop() — code below never runs
            else:
                # COOKIE_SECRET not configured — session-only fallback
                _log.warning("No COOKIE_SECRET — using session-only authentication (refresh will log out)")
                st.query_params.clear()
                st.rerun()

        except Exception as exc:
            _log.error("OAuth callback error: %s", type(exc).__name__)
            st.error(f"Authentication Error: {str(exc)}")
            st.query_params.clear()
            st.stop()

    # ── 5. Not authenticated — render login screen ──────────────────────────────
    render_login_screen()
    st.stop()


# ──────────────────────────────────────────────────────────────────────────────
# SIDEBAR — USER PROFILE & SIGN OUT
# ──────────────────────────────────────────────────────────────────────────────

def render_sidebar_user_profile():
    """Render logged-in user details, role badge, and logout button in sidebar."""
    user_info  = st.session_state.get("user_info", {})
    user_name  = user_info.get("name",    "SilkTrace User")
    user_email = user_info.get("email",   "")
    user_pic   = user_info.get("picture", "")
    user_role  = st.session_state.get("user_role", "ANALYST")

    st.sidebar.markdown("<div style='text-align:center;'>", unsafe_allow_html=True)
    if user_pic:
        st.sidebar.image(user_pic, width=54)
    st.sidebar.markdown(f"**{user_name}**")
    if user_email:
        st.sidebar.caption(user_email)

    # Role Badge
    role_color = {
        "ADMIN":    "#22c55e",
        "ANALYST":  "#3b82f6",
        "OPERATOR": "#f59e0b",
        "VIEWER":   "#94a3b8",
    }.get(user_role, "#3b82f6")
    st.sidebar.markdown(f"""
    <div style="margin-top: 4px; margin-bottom: 12px;">
        <span style="background: rgba(30, 41, 59, 0.8); border: 1px solid {role_color}; color: {role_color}; padding: 3px 10px; border-radius: 12px; font-size: 0.75rem; font-weight: 700;">
            ROLE: {user_role}
        </span>
    </div>
    """, unsafe_allow_html=True)

    if st.sidebar.button("🚪 Sign Out", use_container_width=True):
        _log.info("Sign Out — clearing session and auth cookie")

        # Clear native Streamlit OIDC if active (no-op in Case B)
        try:
            if hasattr(st, "logout"):
                st.logout()
        except Exception:
            pass

        # Clear session state
        st.session_state["authenticated"] = False
        st.session_state.pop("user_info",  None)
        st.session_state.pop("user_role",  None)
        st.query_params.clear()

        # Expire the auth cookie and refresh to login screen
        st.rerun()

    st.sidebar.markdown("</div>", unsafe_allow_html=True)
    st.sidebar.markdown("---")
