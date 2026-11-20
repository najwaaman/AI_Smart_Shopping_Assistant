# Public deployment guide

This guide describes preparation for the public portfolio application. It is not evidence of a hosted or production deployment. No platform was selected or tested.

## Entry point and public runtime

Start Streamlit through `app.py`; do not use individual page scripts as the host entry point. The app applies its OIDC and exact-email allowlist before rendering navigation. All seven pages can render without customer datasets, model artifacts, or aggregate reports when the aggregate release gate remains closed. Product Classification shows an unavailable state until an approved private pipeline artifact is provisioned. Recommendations and Predictions use fictional, clearly labeled demonstrations.

The public aggregate loader only reads explicitly allowlisted reports, but the application release gate is currently disabled. Do not bundle or provision those reports until each report has separate provenance and privacy approval. The manifest intentionally excludes all datasets, reports, and models.

## Dependencies and Python

The root `requirements.txt` contains `streamlit[auth]` and the app's core libraries but is unpinned and includes development/analysis packages. `requirements-deployment.txt` pins direct dependencies and was previously prepared for CPython 3.14.3; it is not a complete transitive lock. The file currently uses plain `streamlit==1.67.0` and lists Authlib but does not explicitly include the Streamlit `auth` extra or `httpx`. Streamlit 1.67.0 metadata lists Authlib and httpx under that extra. Resolve and validate this mismatch before using the deployment requirements for OIDC. No packages were installed in this phase.

Local development bootstrap, using the root requirements file:

```powershell
py -3.14 -m venv .venv-public
.\.venv-public\Scripts\Activate.ps1
python -m pip install -r requirements.txt
python -m pip check
```

Confirm the target host supports the selected Python version and dependency set. No host runtime pin or platform-specific build file is included in this manifest.

## Startup and health

```powershell
python -m streamlit run app.py --server.headless true --server.port 8501
```

Streamlit's `/_stcore/health` endpoint checks server liveness only. It does not establish that OIDC works, that a private model is provisioned, or that any report has approval. No browser, accessibility, performance, identity-provider, or production checks are claimed.

## Authentication configuration

Supply the placeholder `[auth]` configuration from `.streamlit/secrets.toml.example` through the host secret manager. Set `APP_ALLOWED_EMAILS` in the process environment to exact verified addresses. Configuring an external OAuth audience or broad provider-side user type setting does not remove or bypass the application-level email allowlist: every user must still be explicitly listed in `APP_ALLOWED_EMAILS` with a verified email claim. Do not claim that public access is enabled until authentication and authorization have been properly configured and tested. Do not put real credentials in source control or treat `.env.example` as an automatic loader. Missing or invalid authentication configuration intentionally denies access. No live identity provider, callback, or authorized account flow was tested.

## Private artifact policy

Keep customer data, private reports, saved models, notebooks with unreviewed outputs, local environments, and real secrets outside the public release. Do not add them to a container or repository. The classifier does not download or copy its model; without a legitimate private provisioned artifact it returns the safe unavailable state. Aggregate values remain withheld until report approval. Do not weaken `.gitignore` to make a build appear complete.

## Release blockers

Before deployment, reconcile the OIDC dependency extra/httpx, validate the target host's Python support, configure the approved identity provider and allowlist, and obtain approval for any report or model provisioning. The working tree must also receive exact staged-file review; this phase does not stage or publish files.
