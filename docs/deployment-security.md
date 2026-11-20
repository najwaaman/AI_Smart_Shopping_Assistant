# Public deployment security

This document covers the public portfolio release boundary. It does not authorize publication or deployment.

## Access control

`app.py` calls `require_authenticated_user()` before registering page navigation. Streamlit Google OIDC must be configured in the host secret manager (`[auth]` table). Every visitor can access all seven public demo pages after signing in with their own valid, verified Google account. The application requires an authenticated identity with a verified email claim from the identity provider. The previous restrictive `APP_ALLOWED_EMAILS` allowlist requirement has been removed, enabling public access for all verified Google accounts while ensuring unauthenticated visitors cannot access application pages. Unauthenticated visitors see a clear "Sign in with Google" prompt and execution stops until authentication completes. Secure session logout is available in the sidebar, returning visitors to the sign-in screen. Missing OIDC configuration fails closed. No real identity provider, callback, or hosted login was tested in this offline environment.

Use `.streamlit/secrets.toml.example` only as a placeholder template. Never commit real credentials, tokens, cookie secrets, or a populated local environment file. Provider-side account restrictions and HTTPS are required for any later hosted deployment.

## Data and artifact minimization

The public page set does not load customer-level datasets. The aggregate report service is explicit and allowlisted, and the release gate remains disabled while report provenance/privacy approval is pending. No report values should be displayed before approval. Fictional recommendation and prediction demonstrations are separate from project model results.

Model artifacts, datasets, private reports, deployment staging, and unreviewed notebook outputs are excluded from the release manifest. Product Classification is fail-closed when its private pipeline is unavailable: it shows a neutral unavailable message, does not expose an internal path, and returns no fabricated prediction. Do not embed the classifier or other private models in a public repository or image. No approved automated artifact download is configured.

`.gitignore` excludes dataset and report trees, model serialization formats, deployment staging, local secret files, and local environments. It does not ignore notebook files generally; the manifest excludes all unreviewed notebooks explicitly. Ignore rules are not access control and do not replace exact release review.

## Verification limits

The test suite uses synthetic fixtures and does not establish the privacy of any real aggregate report. No credentials were inspected as part of this documentation update. No secret scanning, browser test, penetration test, cloud build, identity-provider test, or production security review was performed. Obtain separate approval before provisioning private artifacts or opening the aggregate release gate.
