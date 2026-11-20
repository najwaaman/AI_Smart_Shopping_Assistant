# AI Smart Shopping Assistant

A seven-page Streamlit portfolio application demonstrating product-text classification and privacy-aware retail analytics. This is a portfolio prototype, not a production shopping service. The public application is designed to render without customer datasets or private model files; some pages therefore show demonstrations or pending states instead of project data.

## Application pages

| Page | Public behavior |
| --- | --- |
| Overview | Withholds report-derived metrics while aggregate provenance and privacy review is pending. |
| Product Classification | Uses the saved TF-IDF + Linear SVM pipeline only when a legitimately provisioned artifact is available. Otherwise it shows a clear unavailable message and returns no prediction. The recorded separate product-text test accuracy is **95.80%**; this does not mean the model is included. |
| Recommendations | Interactive fictional catalogue and illustrative item-to-item cosine ranking. It does not use customer histories or represent trained-model output. Aggregate evaluation values remain withheld. |
| Customer Intelligence | No customer lookup or customer records. Aggregate cohort values remain withheld pending review. |
| Predictions | Interactive hypothetical inputs and transparent rule arithmetic. It does not produce predictions from the saved repeat-purchase or spending models. |
| Customer Segments | Aggregate profile, stability, and comparison values remain withheld pending review; no individual assignments are shown. |
| Model Insights | Global importance and comparison values remain withheld pending review; no individual explanation records are shown. |

The Phase 1A aggregate service accepts only its explicit report allowlist. The release gate is intentionally disabled. Keep it disabled until every report has completed provenance and privacy approval. Suppression must not be bypassed.

## Privacy and data boundaries

- Customer-level datasets, reports, and model artifacts are private and excluded from this public release manifest.
- Public demonstrations use fictional or visitor-entered values only; illustrative calculations and heuristic threshold checks are not trained ML predictions or causal inferences.
- Product descriptions and retail transaction analytics are separate data families; they are not described as one merged dataset.
- Do not add customer identifiers, individual records, credentials, private reports, or protected holdout data or derived outputs to source control or deployment assets.
- Independent final holdout evaluation is not performed or claimed; the final temporal holdout remains protected and unaccessed.
- Public pages do not expose customer-specific workflows. Backend service modules retained for package compatibility are not invoked by these pages.

## Local setup

Use a Python version supported by the selected host. The pinned deployment requirements were previously prepared for CPython 3.14.3, but compatibility must be confirmed for the chosen platform. The root `requirements.txt` is unpinned and includes analysis dependencies; it is a development bootstrap, not a reproducible lock file.

Windows PowerShell:

```powershell
py -3.14 -m venv .venv-public
.\.venv-public\Scripts\Activate.ps1
python -m pip install -r requirements.txt
python -m pip check
python -m streamlit run app.py --server.headless true --server.port 8501
```

Run the application through `app.py`, which applies the authentication gate before navigation. Pages can render without customer datasets, aggregate reports, or model artifacts. Product Classification stays unavailable unless an approved private provisioning path is established.

## Streamlit deployment requirements

Configure the selected host to use `app.py`, a supported Python version, and compatible runtime dependencies. The current `requirements.txt` includes `streamlit[auth]`; `requirements-deployment.txt` is pinned but does not declare the Streamlit `auth` extra or `httpx` explicitly. Reconcile and validate that dependency set before using it for an authenticated deployment. It is not a complete transitive lock file.

The application requires Streamlit OIDC configuration in the host's secret manager and a comma-separated `APP_ALLOWED_EMAILS` process environment value. The checked-in secret file is a placeholder template only. Missing or invalid authentication configuration fails closed. Configuring an external OAuth audience or broad provider-side user type setting alone does not remove or bypass the application-level email allowlist (`APP_ALLOWED_EMAILS`). Do not claim that public access is enabled until authentication and authorization have been properly configured and tested with authorized identities. No live identity provider or hosted deployment has been tested.

Streamlit's `/_stcore/health` endpoint indicates server liveness only; it does not verify authentication, model availability, aggregate approval, or page workflows. Browser, accessibility, performance, and production checks are not claimed.

## Project files and release exclusions

See [the public release manifest](docs/public-release-manifest.md) for the exact source, documentation, and synthetic tests selected for a future release. The manifest excludes datasets, models, reports, deployment staging, notebooks, unreviewed portfolio material, secrets, and local environments. `.gitignore` protects private artifact locations, but all release files still require exact staging review.

See [architecture and modules](docs/architecture-and-modules.md), the [deployment guide](docs/deployment-guide.md), and [deployment security](docs/deployment-security.md) for current behavior and limits.
