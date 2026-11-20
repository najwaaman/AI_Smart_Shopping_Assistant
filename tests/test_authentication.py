import os
from pathlib import Path
import tomllib
import unittest
from unittest.mock import MagicMock, patch

from src.ui.authentication import (
    has_valid_oidc_settings,
    is_authorized_user,
    is_verified_user,
    parse_allowed_emails,
    require_authenticated_user,
)
from src.ui.public_aggregate_pages import PUBLIC_AGGREGATES_RELEASED


ROOT = Path(__file__).resolve().parents[1]


class GoogleAuthenticationPolicyTest(unittest.TestCase):
    def setUp(self):
        self.valid_settings = {
            "redirect_uri": "https://aismartshoppingassistant-xuv64fejngmem9mphns2l9.streamlit.app/oauth2callback",
            "cookie_secret": "a" * 48,
            "client_id": "google-client-id.apps.googleusercontent.com",
            "client_secret": "google-client-secret-key",
            "server_metadata_url": "https://accounts.google.com/.well-known/openid-configuration",
        }

    def test_legacy_email_allowlist_parsing_remains_optional(self):
        self.assertEqual(
            parse_allowed_emails(" Person@Example.org,other@example.org "),
            {"person@example.org", "other@example.org"},
        )
        self.assertEqual(parse_allowed_emails(""), set())
        self.assertEqual(parse_allowed_emails(None), set())

    def test_identity_requires_login_and_verified_email(self):
        verified_account = {"is_logged_in": True, "email_verified": True, "email": "shopper@gmail.com"}
        self.assertTrue(is_verified_user(verified_account))
        self.assertTrue(is_authorized_user(verified_account))

        # Rejection cases
        self.assertFalse(is_verified_user({**verified_account, "email_verified": False}))
        self.assertFalse(is_verified_user({**verified_account, "is_logged_in": False}))
        self.assertFalse(is_verified_user({**verified_account, "email": "invalid-email-format"}))
        self.assertFalse(is_verified_user({"is_logged_in": True, "email_verified": True}))
        self.assertFalse(is_verified_user(None))

    def test_any_valid_verified_google_account_can_authenticate_without_allowlist(self):
        """No email allowlist is required; any verified account is accepted."""
        diverse_accounts = [
            {"is_logged_in": True, "email_verified": True, "email": "first.visitor@gmail.com"},
            {"is_logged_in": True, "email_verified": True, "email": "analyst@retailcompany.com"},
            {"is_logged_in": True, "email_verified": True, "email": "student@university.edu"},
            {"is_logged_in": True, "email_verified": True, "email": "user+shopping@custom-domain.org"},
        ]
        for account in diverse_accounts:
            with self.subTest(email=account["email"]):
                self.assertTrue(is_verified_user(account))
                self.assertTrue(is_authorized_user(account))

    def test_oidc_configuration_rejects_placeholders_and_accepts_complete_values(self):
        self.assertTrue(has_valid_oidc_settings(self.valid_settings))
        self.assertFalse(has_valid_oidc_settings({**self.valid_settings, "client_secret": "REPLACE_ME"}))
        self.assertFalse(has_valid_oidc_settings({**self.valid_settings, "cookie_secret": "short"}))
        self.assertFalse(has_valid_oidc_settings({**self.valid_settings, "redirect_uri": "http://public.test/oauth2callback"}))
        self.assertFalse(has_valid_oidc_settings({**self.valid_settings, "server_metadata_url": "http://insecure.test"}))
        self.assertFalse(has_valid_oidc_settings(None))

    def test_checked_in_secret_example_is_not_treated_as_live_configuration(self):
        example = tomllib.loads(
            (ROOT / ".streamlit/secrets.toml.example").read_text(encoding="utf-8")
        )
        self.assertFalse(has_valid_oidc_settings(example.get("auth")))

    def test_unauthenticated_visitor_prompted_for_google_sign_in_and_stopped(self):
        """Unauthenticated visitors are stopped with 'Sign in with Google' button."""
        import streamlit as st

        class FakeStop(Exception):
            pass

        with patch("src.ui.authentication._configured_auth", return_value=self.valid_settings), \
             patch.object(st, "user", None, create=True), \
             patch.object(st, "info") as info, \
             patch.object(st, "button") as button, \
             patch.object(st, "stop", side_effect=FakeStop) as stop:
            with self.assertRaises(FakeStop):
                require_authenticated_user()

        info.assert_called_once()
        self.assertIn("Google", info.call_args.args[0])
        button.assert_called_once()
        self.assertEqual(button.call_args.args[0], "Sign in with Google")
        self.assertEqual(button.call_args.kwargs.get("on_click"), st.login)
        stop.assert_called_once()

    def test_authenticated_identity_grants_access_and_renders_sign_out(self):
        """Any verified identity proceeds past gate and receives sign-out control."""
        import streamlit as st

        identity = {"is_logged_in": True, "email_verified": True, "email": "visitor@gmail.com"}
        with patch("src.ui.authentication._configured_auth", return_value=self.valid_settings), \
             patch.object(st, "user", identity, create=True), \
             patch.object(st.sidebar, "button") as sidebar_button, \
             patch.object(st.sidebar, "caption") as sidebar_caption, \
             patch.object(st, "stop") as stop:
            require_authenticated_user()

        stop.assert_not_called()
        sidebar_button.assert_called_once()
        self.assertEqual(sidebar_button.call_args.args[0], "Sign out")
        self.assertEqual(sidebar_button.call_args.kwargs.get("on_click"), st.logout)
        sidebar_caption.assert_called_once()
        self.assertIn("visitor@gmail.com", sidebar_caption.call_args.args[0])

    def test_unverified_identity_is_denied_with_sign_out(self):
        """Logged in accounts with unverified email claims are denied with sign out."""
        import streamlit as st

        class FakeStop(Exception):
            pass

        unverified = {"is_logged_in": True, "email_verified": False, "email": "unverified@gmail.com"}
        with patch("src.ui.authentication._configured_auth", return_value=self.valid_settings), \
             patch.object(st, "user", unverified, create=True), \
             patch.object(st, "error") as error, \
             patch.object(st, "button") as button, \
             patch.object(st, "stop", side_effect=FakeStop) as stop:
            with self.assertRaises(FakeStop):
                require_authenticated_user()

        error.assert_called_once()
        self.assertIn("verified email", error.call_args.args[0].lower())
        button.assert_called_once()
        self.assertEqual(button.call_args.args[0], "Sign out")
        self.assertEqual(button.call_args.kwargs.get("on_click"), st.logout)
        stop.assert_called_once()

    def test_unconfigured_oidc_fails_closed_before_any_data_read(self):
        """Missing OIDC settings fails closed with error and stops execution."""
        import streamlit as st

        class FakeStop(Exception):
            pass

        def forbidden_read(*args, **kwargs):
            raise AssertionError("A data file was read before authentication")

        with patch("src.ui.authentication._configured_auth", return_value={}), \
             patch("pandas.read_csv", side_effect=forbidden_read), \
             patch.object(st, "error") as error, \
             patch.object(st, "stop", side_effect=FakeStop) as stop:
            with self.assertRaises(FakeStop):
                require_authenticated_user()

        error.assert_called_once()
        self.assertIn("access is disabled", error.call_args.args[0].lower())
        stop.assert_called_once()

    def test_all_seven_pages_configured_and_privacy_safeguards_intact(self):
        """Verify all seven pages exist and privacy safeguards remain closed."""
        pages_dir = ROOT / "pages"
        expected_pages = [
            "01_Overview.py",
            "02_Product_Classification.py",
            "03_Product_Recommendations.py",
            "04_Customer_Intelligence.py",
            "05_Predictions.py",
            "06_Customer_Segments.py",
            "07_Model_Insights.py",
        ]
        for page_name in expected_pages:
            page_path = pages_dir / page_name
            self.assertTrue(page_path.is_file(), f"Missing page: {page_name}")

        # Reconfirm privacy release gate remains disabled
        self.assertFalse(PUBLIC_AGGREGATES_RELEASED, "PUBLIC_AGGREGATES_RELEASED must remain False")


if __name__ == "__main__":
    unittest.main()
