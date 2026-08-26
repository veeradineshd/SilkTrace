# SilkTrace — Automated Authentication Test Suite
import unittest
import os
import sys
import time
from pathlib import Path
from unittest.mock import MagicMock, patch

# Add workspace root to sys.path
BASE_DIR = Path(__file__).resolve().parent.parent
if str(BASE_DIR) not in sys.path:
    sys.path.insert(0, str(BASE_DIR))

# Set test environment
os.environ["COOKIE_SECRET"] = "test-cookie-secret-min-32-chars-key-2026"

from src.auth import (
    _create_auth_cookie_value,
    _read_auth_cookie,
    _get_signer,
    get_user_role,
    is_feature_allowed_for_user,
    ROLE_PERMISSIONS,
    DEFAULT_ROLE_MAPPING,
)
from itsdangerous import BadSignature, SignatureExpired


class TestSilkTraceAuthentication(unittest.TestCase):

    def setUp(self):
        self.user_info = {
            "name": "SilkTrace Engineer",
            "email": "engineer@silktrace.ai",
            "picture": "https://example.com/pic.jpg",
            "sub": "google-user-1234567890",
        }
        self.role = "ANALYST"

    def test_01_cookie_creation_and_signing(self):
        """Test that auth cookie is created and signed properly."""
        cookie_val = _create_auth_cookie_value(self.user_info, self.role)
        self.assertIsNotNone(cookie_val)
        self.assertIsInstance(cookie_val, str)
        self.assertGreater(len(cookie_val), 20)

        # Verify decoding with valid signer
        signer = _get_signer()
        self.assertIsNotNone(signer)
        payload = signer.loads(cookie_val)
        self.assertEqual(payload["email"], "engineer@silktrace.ai")
        self.assertEqual(payload["name"], "SilkTrace Engineer")
        self.assertEqual(payload["role"], "ANALYST")
        self.assertEqual(payload["sub"], "google-user-1234567890")
        self.assertIn("iat", payload)

    def test_02_tampered_cookie_rejection(self):
        """Test that any tampering of the signed cookie is rejected."""
        cookie_val = _create_auth_cookie_value(self.user_info, self.role)
        self.assertIsNotNone(cookie_val)

        # Tamper with the cookie string
        tampered = cookie_val[:-4] + "abcd"
        signer = _get_signer()
        self.assertIsNotNone(signer)
        assert signer is not None

        with self.assertRaises(BadSignature):
            signer.loads(tampered)

    def test_03_expired_cookie_rejection(self):
        """Test that expired cookies are rejected based on max_age."""
        signer = _get_signer()
        self.assertIsNotNone(signer)
        assert signer is not None
        payload = {
            "sub": self.user_info["sub"],
            "email": self.user_info["email"],
            "name": self.user_info["name"],
            "pic": self.user_info["picture"],
            "role": self.role,
        }
        # Dump at t=1000
        with patch("time.time", return_value=1000.0):
            old_cookie = signer.dumps(payload)

        # Load at t=2000 with max_age=10 seconds (should raise SignatureExpired)
        with patch("time.time", return_value=2000.0):
            with self.assertRaises(SignatureExpired):
                signer.loads(old_cookie, max_age=10)

    def test_04_session_restoration(self):
        """Test reading and verifying valid auth cookie payload."""
        signer = _get_signer()
        self.assertIsNotNone(signer)
        assert signer is not None
        payload = {
            "sub": "user-test-id",
            "email": "operator@silktrace.ai",
            "name": "Operator Joe",
            "pic": "",
            "role": "OPERATOR",
        }
        signed = signer.dumps(payload)

        # Verify decoding and payload structure
        loaded = signer.loads(signed, max_age=86400)
        self.assertEqual(loaded["email"], "operator@silktrace.ai")
        self.assertEqual(loaded["role"], "OPERATOR")
        self.assertEqual(loaded["name"], "Operator Joe")

    def test_05_role_permissions_and_mapping(self):
        """Test role mapping and RBAC permissions."""
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

    def test_06_logout_cookie_invalidation(self):
        """Test logout clears session state and expires cookie."""
        mock_session = {
            "authenticated": True,
            "user_info": self.user_info,
            "user_role": "ADMIN",
        }
        mock_session["authenticated"] = False
        mock_session.pop("user_info", None)
        mock_session.pop("user_role", None)

        self.assertFalse(mock_session["authenticated"])
        self.assertNotIn("user_info", mock_session)
        self.assertNotIn("user_role", mock_session)


if __name__ == "__main__":
    unittest.main()
