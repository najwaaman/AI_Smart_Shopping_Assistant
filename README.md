# AI Smart Shopping Assistant

A Streamlit portfolio application for retail product classification and approved historical customer analytics. It demonstrates saved-model inference, June-only product recommendations, March/June customer predictions, descriptive segmentation, and precomputed model explanations. It is an evaluation prototype, not a production shopping service.

## Features

- **Product classification:** Linear SVM with TF-IDF, served through a saved scikit-learn pipeline. The recorded separate product-description test accuracy is **95.80%**.
- **Product recommendations:** June 2011 only. The UI returns precomputed item-item cosine-similarity recommendation rows; it does not generate an on-demand recommendation from the serialized recommender artifacts. No unknown-customer fallback is implemented.
- **Repeat-purchase prediction:** saved Gradient Boosting classifier using approved March or June feature records.
- **Future-spending prediction:** saved Ridge Regression model. Outputs are unconstrained and have no established currency label.
- **Customer segmentation:** March-fitted KMeans with three descriptive clusters; the application looks up approved March/June assignments.
- **Model insights:** native feature importance, Ridge coefficient magnitude, June permutation importance, and saved zero-feature perturbation examples. SHAP is not used.
- **Seven Streamlit pages:** Overview, Product Classification, Recommendations, Customer Intelligence, Predictions, Customer Segments, and Model Insights.
- **Sign-in gate:** Streamlit OIDC with an exact verified-email allowlist. A real identity provider is not configured in this workspace.

## Data and evaluation

The product-description corpus and retail transaction data are separate data families. Customer snapshots, model-ready classification/regression features, recommendation records, customer insights, and model reports remain separate artifacts; the project does not describe them as one merged dataset.

Customer temporal evaluation uses March 1, 2011 for training/fitting and June 1, 2011 for validation. The September 2011 holdout is protected and is not used or reported here. The text-classification test split is a distinct task and is not a customer holdout.

Detailed metric sources, preprocessing, field definitions, and limitations are documented in [data and evaluation](docs/data-and-evaluation.md). Gross spending is shown without a currency denomination. See [architecture and modules](docs/architecture-and-modules.md) for details on precomputed versus live model behavior.

## Screenshots

No screenshots are included because this final audit did not perform browser-based visual testing. Add screenshots only after reviewing them for customer identifiers, private data, credentials, and misleading values.

## Requirements and local setup

Use standard CPython 3.14.3 and a **new** virtual environment. `requirements-deployment.txt` pins direct runtime dependencies, but is not a fully resolved transitive lock file. Local model and approved March/June data/report artifacts are private and are not included in a public checkout.

Windows PowerShell, from the project root:

```powershell
py -3.14 -m venv .venv-local
.\.venv-local\Scripts\Activate.ps1
python -m pip install -r requirements-deployment.txt
python -m pip check
```

Do not install into an existing project environment. The supported Streamlit entry point is `app.py`:

```powershell
python -m streamlit run app.py --server.headless true --server.port 8501
```

### Configure OIDC access

Create an OIDC client with a provider you control, then supply the `[auth]` values from `.streamlit/secrets.toml.example` through a secret manager or a local ignored `.streamlit/secrets.toml`. Set `APP_ALLOWED_EMAILS` in the process environment to comma-separated exact verified email addresses. The application denies access if secrets are incomplete, the allowlist is empty, or the identity is not logged in with a verified allowlisted email. The identity provider, callback, and account lifecycle have not been tested here.

Never commit credentials, customer data, model files, or private reports. Review [deployment security](docs/deployment-security.md) and [deployment guide](docs/deployment-guide.md) before exposing the service.

## Tests and checks

From the project root:

```powershell
python -m unittest discover -s tests -p "test_*.py" -v
```

The suite now uses synthetic fixtures and temporary model-loader artifacts; it does not load customer datasets or configured model files. Separate private artifact/model compatibility checks are needed when preparing a local deployment. Streamlit's `/_stcore/health` endpoint checks server liveness only; it does not validate authentication, model/data availability, or page workflows.

## Project layout

```text
app.py                         Authenticated Streamlit entry point
pages/                         Seven dashboard pages
src/config/                    Model, approved data, and predictor paths
src/models/                    Saved artifact loader
src/preprocessing/             Input and feature validation
src/services/                  Classification, recs, predictions, segments, insights
src/ui/                        Authentication, dashboard data, shared UI
models/                        Private saved models; excluded from publication
datasets/                      Private source and derived data; excluded from publication
deployment_staging/            Ignored local model-only staging bundle
docs/                          Architecture, data, local setup, deployment guides
tests/                         Unit, integration, isolation, and auth tests
reports/                       Evaluation and internal phase reports
```

## Known limitations and status

- The recommendation runtime serves precomputed June rows, not on-demand personalized model inference.
- Repeat-purchase validation performance is moderate; spending can be negative and has no currency label.
- Segment identifiers are descriptive, not customer-value ranks.
- Individual explanations are precomputed zero-feature perturbation proxies and are not causal explanations.
- Authentication was tested with local mocks only. No provider login, browser, accessibility, performance, deployment-host, or production test is claimed.
- Private runtime data provisioning and cloud-level access controls remain to be finalized and verified.
- No deployment has occurred. This project is **not production-ready**.

Internal final audit, readiness, and release-checklist reports are retained in the local workspace and are not part of a public source release.
