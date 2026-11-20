# Running the public app locally

## Requirements

Use a Python version supported by your environment. CPython 3.14.3 was used for the previously prepared pinned dependency environment; this guide does not claim compatibility with every Streamlit host. Root `requirements.txt` includes the Streamlit `auth` extra but is unpinned and includes development/analysis libraries.

```powershell
py -3.14 -m venv .venv-public
.\.venv-public\Scripts\Activate.ps1
python -m pip install -r requirements.txt
python -m pip check
```

No package installation was performed during Phase 1E.1.

## Authentication and startup

Configure the OIDC placeholder values from `.streamlit/secrets.toml.example` in an ignored local secrets file or an approved secret manager. Set `APP_ALLOWED_EMAILS` in the process environment to exact verified email addresses. The app denies access when configuration is missing or incomplete. Do not place real values in `.env.example`.

Start from the project root through the authenticated entry point:

```powershell
python -m streamlit run app.py --server.headless true --server.port 8501
```

## Public page behavior

The fictional Recommendations and Predictions demonstrations require no private data or model. Customer Intelligence, Overview, Customer Segments, and Model Insights withhold aggregate report values while privacy approval is pending. Product Classification displays an unavailable state unless its private classifier artifact has been legitimately provisioned. No customer records, reports, or model files are included in this public release manifest.

The Streamlit health endpoint checks server liveness only; it does not validate OIDC, model availability, or report approval. See the [deployment guide](deployment-guide.md) for host limitations and the [public release manifest](public-release-manifest.md) for file exclusions.
