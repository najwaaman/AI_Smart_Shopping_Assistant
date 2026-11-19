# Deployment security and artifact controls

This document describes the implemented access gate and local model staging.
It does not authorize deployment. No identity provider, cloud account, or
public endpoint was configured in this phase.

## Authentication and authorization

The supported entry point is `app.py`. It calls
`require_authenticated_user()` immediately after Streamlit page configuration
and before registering/running the page router. A run stops before any page
data-loading code unless all of these conditions hold:

1. Streamlit has a complete `[auth]` OIDC configuration.
2. `APP_ALLOWED_EMAILS` contains one or more exact email addresses in the
   deployment process environment.
3. The current `st.user` is logged in, has `email_verified is True`, and its
   normalized email exactly matches an allowlisted address.

Missing/placeholder OIDC settings and an empty allowlist fail closed. A logged
in but unlisted identity receives an access-denied message and sign-out button.
The app does not show user email addresses in its sidebar.

Use an OIDC provider already managed by the organization. Configure the
provider's client/application to require assignment or otherwise restrict the
eligible accounts. Configure the absolute redirect URI as
`https://<deployment-host>/oauth2callback` (local development may use
`http://localhost:8501/oauth2callback`). The provider must return the standard
`email` and boolean `email_verified` claims. Streamlit's OIDC login relies on
Authlib; the deployment requirements pin the tested version.

The `[auth]` secrets belong in the hosting platform's secret manager or an
ignored local `.streamlit/secrets.toml`. The checked-in
`.streamlit/secrets.toml.example` contains placeholders only. Generate
`cookie_secret` from a cryptographically secure random source with at least
32 characters. Never reuse the client secret as the cookie secret. Keep
`APP_ALLOWED_EMAILS` in platform environment configuration; it is an
authorization setting, not a credential.

Streamlit OIDC provides authentication, not general role-based access control.
The application implements one exact-email allowlist and has no role or
tenant model. Use provider-side assignment and private ingress controls as
additional gates. Streamlit's identity cookie persists after sign-in; apply
the identity provider's session, revocation, and MFA policies as appropriate.

Official references: [Streamlit user authentication](https://docs.streamlit.io/develop/concepts/connections/authentication),
[`st.login`](https://docs.streamlit.io/develop/api-reference/user/st.login),
and [`st.user`](https://docs.streamlit.io/develop/api-reference/user/st.user).

## Artifact staging

`deployment_staging/` is ignored by Git and contains only exact copies of the
eight configured model/preprocessing artifacts. `MODEL_MANIFEST.sha256.txt`
records each relative path, file size, and SHA-256. The source and staged copy
hashes were compared at staging time. The directory contains no CSV, Parquet,
customer snapshot, customer insight, or private dataset files.

These model files remain private and must be stored/transferred through an
access-controlled artifact channel. The staging directory is a local
preparation copy, not an upload or public release bundle. When a deployment
target is separately approved, provision the model files at the application's
configured relative `models/` paths and verify the manifest before startup.

Customer-level snapshots, prediction features, recommendations, insights,
row-level reports, raw transactions, and protected holdout material are not
part of this model staging bundle. The application requires some approved
March/June data/report files for customer workflows. Those files must be
provisioned privately and independently reviewed for cutoff lineage; do not
copy them into a public source checkout or container layer.

The Phase 12B `HistoricalSnapshotService` remains fixed to the separate March
1 and June 1, 2011 snapshot artifacts. Page 01 uses those same snapshots and
the verified March/June cluster profile summary. No September holdout data or
September-derived artifact was accessed in Phase 15A.

## Repository and runtime controls

- `.gitignore` excludes dataset content, trained model files, the private
  `deployment_staging/` directory, `.streamlit/secrets.toml`, environment
  files, private key/certificate files, and row-level customer reports.
- A local Windows ACL metadata inspection found owner/admin/system entries, inherited `CodexSandboxUsers` access, and two unresolved SID entries. This inspection cannot determine OneDrive sharing, remote sync, tenant, or production-host access. Treat local ACL evidence as insufficient to approve private runtime data for hosting; verify approved account-level access controls and storage settings before provisioning.
- The workspace is not a Git repository. Ignore behavior and tracked status
  could not be verified with Git commands; no repository was initialized.
- `.streamlit/config.toml` keeps CORS/XSRF protection on, disables usage
  statistics, and does not bind to all interfaces by default.
- Only run `python -m streamlit run app.py`. The app entrypoint enforces the
  access gate. Do not use a page script as the server entrypoint.
- For a public host, require HTTPS, restrict ingress, use provider-side
  account assignment/MFA where available, and keep secrets and model storage
  out of source/image layers.
- The Streamlit health endpoint `/_stcore/health` reports server health; it
  does not authenticate users or verify data/model artifacts.

## Verification and remaining limits

Phase 15A tests verify allowlist normalization, verified-email matching,
placeholder rejection, and fail-closed startup before any CSV read. They do
not connect to a live identity provider. A new clean Python environment
installed the pinned deployment requirements, loaded the saved artifacts,
and passed the full unit suite. The local health endpoint returned `200 ok`.

No browser-based sign-in, provider callback, MFA, identity lifecycle,
production ingress, data-volume provisioning, security penetration, or
deployment test was performed. Do not treat these checks as proof of
production readiness. Before release, validate the real provider config and
allowlist with authorized test accounts, verify logout/session behavior,
confirm secure artifact/data mounts, and obtain a separate deployment review.
