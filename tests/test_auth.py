# SilkTrace — Automated Authentication Test Suite (Native Streamlit OIDC)
import unittest
import os
import sys
from pathlib import Path
from unittest.mock import MagicMock, patch
import streamlit as st

# Add workspace root to sys.path
BASE_DIR = Path(__file__).resolve().parent.parent
if str(BASE_DIR) not in sys.path:
    sys.path.insert(0, str(BASE_DIR))

# Set test environment variables
os.environ["GOOGLE_CLIENT_ID"] = "test-google-client-id-123.apps.googleusercontent.com"
os.environ["GOOGLE_CLIENT_SECRET"] = "test-google-client-secret-xyz"
os.environ["GOOGLE_REDIRECT_URI"] = "https://silktrace.onrender.com/oauth2callback"
os.environ["COOKIE_SECRET"] = "test-cookie-secret-min-32-chars-key-2026"

from src.auth import (
    ensure_secrets_file,
    sync_native_auth_secrets,
    get_secret,
    get_google_credentials,
    get_user_role,
    is_feature_allowed_for_user,
    handle_auth_gate,
    render_sidebar_user_profile,
    ROLE_PERMISSIONS,
    DEFAULT_ROLE_MAPPING,
)


class TestSilkTraceNativeOIDCAuthentication(unittest.TestCase):

    def setUp(self):
        # Clear test session state
        st.session_state.clear()

    def test_01_secrets_bridge_configuration(self):
        """Test that ensure_secrets_file generates valid [auth] section for Native Streamlit OIDC."""
        ensure_secrets_file()
        secrets_path = BASE_DIR / ".streamlit" / "secrets.toml"
        self.assertTrue(secrets_path.exists())

        content = secrets_path.read_text(encoding="utf-8")
        self.assertIn("[auth]", content)
        self.assertIn('redirect_uri = "https://silktrace.onrender.com/oauth2callback"', content)
        self.assertIn('server_metadata_url = "https://accounts.google.com/.well-known/openid-configuration"', content)
        self.assertIn('client_id = "test-google-client-id-123.apps.googleusercontent.com"', content)
        self.assertIn('client_secret = "test-google-client-secret-xyz"', content)
        self.assertIn('cookie_secret = "test-cookie-secret-min-32-chars-key-2026"', content)

    def test_02_credentials_loading(self):
        """Test reading Google credentials from environment."""
        cid, csecret, redirect_uri = get_google_credentials()
        self.assertEqual(cid, "test-google-client-id-123.apps.googleusercontent.com")
        self.assertEqual(csecret, "test-google-client-secret-xyz")
        self.assertEqual(redirect_uri, "https://silktrace.onrender.com/oauth2callback")

    def test_03_role_mapping_rbac(self):
        """Test role mapping and RBAC matrix permissions."""
        admin_role = get_user_role("admin@silktrace.ai")
        self.assertEqual(admin_role, "ADMIN")

        unknown_role = get_user_role("random@external.org")
        self.assertEqual(unknown_role, "ANALYST")

        # Test permissions directly against ROLE_PERMISSIONS
        self.assertIn("system_health", ROLE_PERMISSIONS["ADMIN"])
        self.assertIn("reports", ROLE_PERMISSIONS["ADMIN"])
        self.assertNotIn("system_health", ROLE_PERMISSIONS["VIEWER"])
        self.assertNotIn("reports", ROLE_PERMISSIONS["VIEWER"])
        self.assertIn("analytics", ROLE_PERMISSIONS["VIEWER"])

    def test_04_native_user_feature_permissions(self):
        """Test is_feature_allowed_for_user with simulated native st.user."""
        mock_user = MagicMock()
        mock_user.is_logged_in = True
        mock_user.email = "admin@silktrace.ai"
        mock_user.name = "SilkTrace Admin"

        with patch.object(st, "user", mock_user, create=True):
            self.assertTrue(is_feature_allowed_for_user("system_health"))
            self.assertTrue(is_feature_allowed_for_user("reports"))
            self.assertTrue(is_feature_allowed_for_user("analytics"))

    def test_05_demo_access_permissions(self):
        """Test is_feature_allowed_for_user in isolated Demo Access mode."""
        # When unauthenticated and not demo
        mock_user = MagicMock()
        mock_user.is_logged_in = False
        with patch.object(st, "user", mock_user, create=True):
            self.assertFalse(is_feature_allowed_for_user("analytics"))

            # Activate Demo Access
            st.session_state["demo_authenticated"] = True
            st.session_state["demo_user_role"] = "ADMIN"
            self.assertTrue(is_feature_allowed_for_user("system_health"))
            self.assertTrue(is_feature_allowed_for_user("analytics"))

    def test_06_auth_gate_logged_in_user(self):
        """Test handle_auth_gate passes cleanly when native st.user is logged in."""
        mock_user = MagicMock()
        mock_user.is_logged_in = True
        mock_user.email = "user@silktrace.ai"

        with patch.object(st, "user", mock_user, create=True):
            # Should return without calling st.stop or render_login_screen
            with patch("src.auth.render_login_screen") as mock_render:
                handle_auth_gate()
                mock_render.assert_not_called()

    def test_07_auth_gate_unauthenticated_stops(self):
        """Test handle_auth_gate renders login and stops when unauthenticated."""
        mock_user = MagicMock()
        mock_user.is_logged_in = False

        with patch.object(st, "user", mock_user, create=True):
            with patch("src.auth.render_login_screen") as mock_render, \
                 patch("streamlit.stop", side_effect=SystemExit) as mock_stop:
                with self.assertRaises(SystemExit):
                    handle_auth_gate()
                mock_render.assert_called_once()
                mock_stop.assert_called_once()


if __name__ == "__main__":
    unittest.main()
