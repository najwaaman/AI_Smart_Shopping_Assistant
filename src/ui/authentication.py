"""Google OIDC authentication and verified email verification for Streamlit."""

from collections.abc import Mapping
import os
import re
from urllib.parse import urlparse

import streamlit as st


OIDC_REQUIRED_KEYS = {
    "redirect_uri",
    "cookie_secret",
    "client_id",
    "client_secret",
    "server_metadata_url",
}
EMAIL_PATTERN = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")


def parse_allowed_emails(raw_value=None):
    """Return a normalized exact-email allowlist (legacy/optional compatibility)."""
    raw_value = os.environ.get("APP_ALLOWED_EMAILS", "") if raw_value is None else raw_value
    return {
        email.strip().casefold()
        for email in str(raw_value).split(",")
        if EMAIL_PATTERN.fullmatch(email.strip())
    }


def has_valid_oidc_settings(auth_settings):
    """Reject missing and obvious template OIDC values before offering login."""
    if not isinstance(auth_settings, Mapping):
        return False
    values = {key: auth_settings.get(key) for key in OIDC_REQUIRED_KEYS}
    if any(not isinstance(value, str) or not value.strip() for value in values.values()):
        return False
    normalized = {key: value.strip().casefold() for key, value in values.items()}
    placeholder_tokens = ("replace_me", "replace with", "placeholder", "your-", "your_", "<", ">", ".example", ".invalid")
    if any(any(token in value for token in placeholder_tokens) for value in normalized.values()):
        return False
    if len(values["cookie_secret"]) < 32:
        return False

    redirect = urlparse(values["redirect_uri"])
    local_http = redirect.scheme == "http" and redirect.hostname in {"localhost", "127.0.0.1"}
    if redirect.scheme != "https" and not local_http:
        return False
    if not redirect.hostname or not redirect.path.endswith("/oauth2callback"):
        return False

    metadata = urlparse(values["server_metadata_url"])
    return metadata.scheme == "https" and bool(metadata.hostname)


def _claim(user, name):
    if isinstance(user, Mapping):
        return user.get(name)
    try:
        return user.get(name)
    except (AttributeError, TypeError):
        return getattr(user, name, None)


def is_verified_user(user):
    """Verify that identity is logged in with a verified email address."""
    if _claim(user, "is_logged_in") is not True:
        return False
    if _claim(user, "email_verified") is not True:
        return False
    email = _claim(user, "email")
    return isinstance(email, str) and bool(EMAIL_PATTERN.fullmatch(email.strip()))


def is_authorized_user(user, allowed_emails=None):
    """Authorize any logged-in identity with a verified email address (allowlist optional)."""
    if not is_verified_user(user):
        return False
    if allowed_emails:
        email = _claim(user, "email")
        return isinstance(email, str) and email.strip().casefold() in allowed_emails
    return True


def _configured_auth():
    try:
        auth_settings = st.secrets.get("auth", {})
    except Exception:
        return {}
    return auth_settings if isinstance(auth_settings, Mapping) else {}


def require_authenticated_user():
    """Stop every application run unless Google OIDC authentication passes."""
    auth_settings = _configured_auth()
    if not has_valid_oidc_settings(auth_settings):
        st.error(
            "Application access is disabled: configure valid Google OIDC secrets "
            "in the deployment secret/environment settings."
        )
        st.stop()

    user = st.user
    if not is_verified_user(user):
        if _claim(user, "is_logged_in") is True:
            st.error("A verified email address is required to access this application.")
            st.button("Sign out", on_click=st.logout, key="auth_sign_out_unverified")
        else:
            st.info("Sign in with your Google account to access the shopping assistant demo.")
            st.button("Sign in with Google", on_click=st.login, key="auth_sign_in")
        st.stop()

    email = _claim(user, "email")
    if email:
        st.sidebar.caption(f"Signed in as: {email}")
    st.sidebar.button("Sign out", on_click=st.logout, key="auth_sign_out")
