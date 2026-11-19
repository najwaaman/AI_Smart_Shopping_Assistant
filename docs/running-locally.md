# Running locally

## Requirements

- Standard CPython 3.14.3.
- Direct application dependencies pinned in `requirements-deployment.txt` (not a full transitive lock).
- Private saved models plus approved March/June data and report files at configured paths. These are not included in a public source checkout.

## Windows PowerShell

Use a fresh virtual environment; do not replace an existing environment:

```powershell
py -3.14 -m venv .venv-local
.\.venv-local\Scripts\Activate.ps1
python -m pip install -r requirements-deployment.txt
python -m pip check
```

Configure OIDC values from `.streamlit/secrets.toml.example` in a local ignored `.streamlit/secrets.toml` or a secret manager. Set `APP_ALLOWED_EMAILS` to comma-separated exact verified addresses in the process environment. Missing or placeholder values fail closed. Never place secrets in `.env.example` or commit real values.

Start only through the authenticated entry point:

```powershell
python -m streamlit run app.py --server.headless true --server.port 8501
```

The server health endpoint is `/_stcore/health`; a healthy response does not prove authentication, artifacts, or page workflows.

## Tests

```powershell
python -m unittest discover -s tests -p "test_*.py" -v
```

The suite uses synthetic in-memory fixtures and temporary model-loader artifacts. It does not require or read customer-level files. Private artifact compatibility checks are a separate task and must use only approved March/June assets.

## Pages

The app registers Overview, Product Classification, Recommendations, Customer Intelligence, Predictions, Customer Segments, and Model Insights. Customer prediction/history workflows support March 1 and June 1, 2011; recommendations are June-only. Page harnesses are not a substitute for browser navigation, responsive-layout, accessibility, or identity-provider testing.

See the [deployment guide](deployment-guide.md) before any hosting work.
