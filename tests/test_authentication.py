import os
from pathlib import Path
import tomllib
import unittest
from unittest.mock import patch

import pandas as pd
from streamlit.testing.v1 import AppTest

from src.ui.authentication import (
    has_valid_oidc_settings,
    is_authorized_user,
    parse_allowed_emails,
)


ROOT = Path(__file__).resolve().parents[1]


class AuthenticationPolicyTest(unittest.TestCase):
    def test_email_allowlist_is_normalized_and_exact(self):
        self.assertEqual(
            parse_allowed_emails(" Person@Example.org,other@example.org "),
            {"person@example.org", "other@example.org"},
        )

    def test_identity_requires_login_verified_email_and_allowlist(self):
        allowlist = {"operator@example.org"}
        authorized = {"is_logged_in": True, "email_verified": True, "email": "OPERATOR@example.org"}
        self.assertTrue(is_authorized_user(authorized, allowlist))
        self.assertFalse(is_authorized_user({**authorized, "email_verified": False}, allowlist))
        self.assertFalse(is_authorized_user({**authorized, "is_logged_in": False}, allowlist))
        self.assertFalse(is_authorized_user({**authorized, "email": "other@example.org"}, allowlist))
        self.assertFalse(is_authorized_user({"is_logged_in": True}, allowlist))

    def test_oidc_configuration_rejects_placeholders_and_accepts_complete_values(self):
        settings = {
            "redirect_uri": "https://shopping.test/oauth2callback",
            "cookie_secret": "a" * 48,
            "client_id": "registered-client-id",
            "client_secret": "registered-client-secret",
            "server_metadata_url": "https://identity.test/.well-known/openid-configuration",
        }
        self.assertTrue(has_valid_oidc_settings(settings))
        self.assertFalse(has_valid_oidc_settings({**settings, "client_secret": "REPLACE_ME"}))
        self.assertFalse(has_valid_oidc_settings({**settings, "cookie_secret": "short"}))
        self.assertFalse(has_valid_oidc_settings({**settings, "redirect_uri": "http://public.test/oauth2callback"}))

    def test_checked_in_secret_example_is_not_treated_as_live_configuration(self):
        example = tomllib.loads(
            (ROOT / ".streamlit/secrets.toml.example").read_text(encoding="utf-8")
        )
        self.assertFalse(has_valid_oidc_settings(example.get("auth")))

    def test_app_startup_fails_closed_before_any_data_read(self):
        def forbidden_read(*args, **kwargs):
            raise AssertionError("A data file was read before authentication")

        with patch.dict(os.environ, {"APP_ALLOWED_EMAILS": ""}):
            with patch("pandas.read_csv", side_effect=forbidden_read):
                app = AppTest.from_file(str(ROOT / "app.py"), default_timeout=20).run()
        self.assertEqual(app.exception, [])
        self.assertTrue(any("access is disabled" in str(error.value).casefold() for error in app.error))

    def test_mock_oidc_authorized_identity_reaches_only_sign_out_control(self):
        import streamlit as st

        settings = {
            "redirect_uri": "https://shopping.test/oauth2callback",
            "cookie_secret": "a" * 48,
            "client_id": "registered-client-id",
            "client_secret": "registered-client-secret",
            "server_metadata_url": "https://identity.test/.well-known/openid-configuration",
        }
        identity = {"is_logged_in": True, "email_verified": True, "email": "operator@example.org"}
        with patch("src.ui.authentication._configured_auth", return_value=settings), \
             patch("src.ui.authentication.parse_allowed_emails", return_value={"operator@example.org"}), \
             patch.object(st, "user", identity, create=True), \
             patch.object(st.sidebar, "button") as sidebar_button, \
             patch.object(st, "stop") as stop:
            from src.ui.authentication import require_authenticated_user
            require_authenticated_user()

        sidebar_button.assert_called_once()
        self.assertEqual(sidebar_button.call_args.args[0], "Sign out")
        stop.assert_not_called()

    def test_mock_oidc_unverified_or_unlisted_identity_is_denied(self):
        import streamlit as st

        settings = {
            "redirect_uri": "https://shopping.test/oauth2callback",
            "cookie_secret": "a" * 48,
            "client_id": "registered-client-id",
            "client_secret": "registered-client-secret",
            "server_metadata_url": "https://identity.test/.well-known/openid-configuration",
        }
        identities = [
            {"is_logged_in": True, "email_verified": False, "email": "operator@example.org"},
            {"is_logged_in": True, "email_verified": True, "email": "other@example.org"},
        ]
        for identity in identities:
            with self.subTest(identity=identity), \
                 patch("src.ui.authentication._configured_auth", return_value=settings), \
                 patch("src.ui.authentication.parse_allowed_emails", return_value={"operator@example.org"}), \
                 patch.object(st, "user", identity, create=True), \
                 patch.object(st, "button") as button, \
                 patch.object(st, "stop") as stop:
                from src.ui.authentication import require_authenticated_user
                require_authenticated_user()
                button.assert_called_once()
                self.assertEqual(button.call_args.args[0], "Sign out")
                stop.assert_called_once()


if __name__ == "__main__":
    unittest.main()
