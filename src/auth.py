# SilkTrace — Authentication & Role-Based Access Control (Google OIDC)
import os
import json
import urllib.parse
import requests
import streamlit as st
from src.config import (
    GOOGLE_OIDC_DISCOVERY_URL,
    DEFAULT_ROLE_MAPPING,
    ROLE_PERMISSIONS,
    APP_NAME,
    APP_DESCRIPTION,
)

def _get_secret_or_env(key: str, default: str = "") -> str:
    """Retrieve secret from environment variables or st.secrets safely."""
    val = os.environ.get(key)
    if val:
        return val.strip()
    try:
        if key in st.secrets:
            return str(st.secrets[key]).strip()
    except Exception:
        pass
    return default

def get_google_credentials():
    """Returns Google Client ID, Secret, and Redirect URI."""
    client_id = _get_secret_or_env("GOOGLE_CLIENT_ID")
    client_secret = _get_secret_or_env("GOOGLE_CLIENT_SECRET")
    redirect_uri = _get_secret_or_env("GOOGLE_REDIRECT_URI", "http://localhost:8501/oauth2callback")
    return client_id, client_secret, redirect_uri

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
    """Render a high-converting, professional Google Cloud login interface."""
    client_id, client_secret, redirect_uri = get_google_credentials()

    st.markdown("""
    <div style="max-width: 580px; margin: 40px auto; padding: 40px; background: rgba(15, 23, 42, 0.95); border-radius: 24px; border: 1.5px solid rgba(96, 165, 250, 0.3); box-shadow: 0 25px 60px rgba(0,0,0,0.6); text-align: center;">
        <div style="font-size: 64px; margin-bottom: 8px;">🧵</div>
        <h1 style="color: #ffffff !important; font-size: 2.5rem; font-weight: 800; margin-bottom: 6px; letter-spacing: -0.5px;">SilkTrace</h1>
        <p style="color: #60a5fa !important; font-size: 1.05rem; font-weight: 500; margin-bottom: 24px;">AI-Powered Smart Textile Manufacturing Intelligence</p>
        
        <div style="background: rgba(30, 41, 59, 0.7); padding: 20px; border-radius: 16px; border: 1px solid rgba(255, 255, 255, 0.08); margin-bottom: 28px; text-align: left;">
            <p style="color: #f8fafc !important; font-weight: 600; margin-bottom: 10px; font-size: 0.95rem;">🔒 Authenticated Industrial Platform Access</p>
            <p style="color: #94a3b8 !important; font-size: 0.88rem; margin: 4px 0;">• Real-Time Industrial Energy Consumption Forecasting</p>
            <p style="color: #94a3b8 !important; font-size: 0.88rem; margin: 4px 0;">• Garment Worker Productivity Optimization</p>
            <p style="color: #94a3b8 !important; font-size: 0.88rem; margin: 4px 0;">• MobileNetV2 Fabric Defect Quality Control</p>
            <p style="color: #94a3b8 !important; font-size: 0.88rem; margin: 4px 0;">• Executive KPI Dashboard & PDF Report Exports</p>
        </div>
    """, unsafe_allow_html=True)

    if client_id and client_secret:
        auth_url = get_google_auth_url()
        st.markdown(f"""
        <div style="margin-top: 15px; margin-bottom: 20px;">
            <a href="{auth_url}" target="_self" style="display: inline-flex; align-items: center; justify-content: center; background-color: #ffffff; color: #0f172a !important; text-decoration: none; padding: 14px 32px; border-radius: 12px; font-weight: 700; font-size: 1.05rem; box-shadow: 0 8px 25px rgba(255, 255, 255, 0.15); transition: all 0.2s ease;">
                <svg style="width: 20px; height: 20px; margin-right: 12px;" viewBox="0 0 24 24">
                    <path fill="#4285F4" d="M22.56 12.25c0-.78-.07-1.53-.2-2.25H12v4.26h5.92c-.26 1.37-1.04 2.53-2.21 3.31v2.77h3.57c2.08-1.92 3.28-4.74 3.28-8.09z"/>
                    <path fill="#34A853" d="M12 23c2.97 0 5.46-.98 7.28-2.66l-3.57-2.77c-.98.66-2.23 1.06-3.71 1.06-2.86 0-5.29-1.93-6.16-4.53H2.18v2.84C3.99 20.53 7.7 23 12 23z"/>
                    <path fill="#FBBC05" d="M5.84 14.1c-.22-.66-.35-1.36-.35-2.1s.13-1.44.35-2.1V7.06H2.18C1.43 8.55 1 10.22 1 12s.43 3.45 1.18 4.94l2.85-2.22.81-.62z"/>
                    <path fill="#EA4335" d="M12 5.38c1.62 0 3.06.56 4.21 1.64l3.15-3.15C17.45 2.09 14.97 1 12 1 7.7 1 3.99 3.47 2.18 7.06l3.66 2.84c.87-2.6 3.3-4.52 6.16-4.52z"/>
                </svg>
                Continue with Google
            </a>
        </div>
        """, unsafe_allow_html=True)
    else:
        # Check if Streamlit's native st.login is configured via secrets
        if hasattr(st, "login"):
            try:
                if st.button("🔑 Continue with Google (Streamlit Auth)", use_container_width=True):
                    st.login("google")
            except Exception:
                pass

        st.info("💡 **Google OAuth Setup**: Configure `GOOGLE_CLIENT_ID` and `GOOGLE_CLIENT_SECRET` in environment variables or Render dashboard for live Google Cloud OIDC Login.")

    st.markdown("---")
    if st.button("🔐 Continue with Demo Access", use_container_width=True):
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

    st.markdown("</div>", unsafe_allow_html=True)

def handle_auth_gate():
    """Handle OAuth redirect callback and enforce session authentication."""
    # Check native Streamlit st.user if authenticated via st.login()
    if hasattr(st, "user") and getattr(st.user, "is_logged_in", False):
        st.session_state["authenticated"] = True
        st.session_state["user_info"] = {
            "name": getattr(st.user, "name", "Google User"),
            "email": getattr(st.user, "email", "user@gmail.com"),
            "picture": getattr(st.user, "picture", "")
        }
        st.session_state["user_role"] = get_user_role(getattr(st.user, "email", ""))

    # Check for OAuth callback code in query parameters
    if "code" in st.query_params and not st.session_state.get("authenticated"):
        auth_code = st.query_params["code"]
        client_id, client_secret, _ = get_google_credentials()
        try:
            if client_id and client_secret:
                user_info = exchange_code_for_user_info(auth_code)
                st.session_state["authenticated"] = True
                st.session_state["user_info"] = user_info
                st.session_state["user_role"] = get_user_role(user_info.get("email", ""))
                st.query_params.clear()
                st.rerun()
            else:
                st.warning("Google OAuth client configuration incomplete.")
        except Exception as e:
            st.error(f"Authentication Error: {str(e)}")
            st.query_params.clear()

    # Enforce authentication gate
    if not st.session_state.get("authenticated"):
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
        if hasattr(st, "logout"):
            try:
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
