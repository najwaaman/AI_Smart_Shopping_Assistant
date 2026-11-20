# Public Release File Manifest

This document specifies the exact file manifest, synthetic tests, and explicit exclusions prepared for the public repository release of the AI Smart Shopping Assistant.

This manifest is prepared for release readiness review only; it does not authorize, execute, or publish any files, commits, or deployments.

---

## 1. Public Application Files

The following 44 files comprise the complete public application runtime, UI layer, configuration templates, documentation, and compatibility services.

| File Path | Component | Purpose |
| :--- | :--- | :--- |
| `app.py` | Entry Point | Configures Streamlit page layout, applies the fail-closed authentication gate (`require_authenticated_user`), applies UI theme, and registers all seven public pages into navigation. |
| `pages/01_Overview.py` | UI Page | Shopping analytics overview dashboard. Displays model candidates, comparative evaluation charts, and privacy-filtered segment profiles via the release-gated public aggregate service. |
| `pages/02_Product_Classification.py` | UI Page | Product category classification workspace. Invokes `ProductCategoryService` if the saved pipeline artifact is legitimately available; otherwise renders a fail-closed, neutral unavailable state without exposing internal paths. |
| `pages/03_Product_Recommendations.py` | UI Page | Personalized commerce demonstration page. Features an interactive fictional catalogue with illustrative item-to-item cosine similarity rankings and a release-gated aggregate evaluation panel. |
| `pages/04_Customer_Intelligence.py` | UI Page | Shopping cohort explorer. Renders privacy-filtered aggregate cluster metrics and temporal stability tables with small-cell suppression; strictly excludes customer identifiers and lookups. |
| `pages/05_Predictions.py` | UI Page | Synthetic shopping prediction demonstration. Provides interactive hypothetical sliders and transparent illustrative arithmetic; does not call trained prediction models. |
| `pages/06_Customer_Segments.py` | UI Page | Customer segments page. Displays aggregate cluster profiles, temporal stability metrics, and clustering algorithm evaluation behind the aggregate release gate. |
| `pages/07_Model_Insights.py` | UI Page | Model governance page. Presents global feature importance rankings (native and permutation) and aggregate model comparison tables behind the aggregate release gate. |
| `src/__init__.py` | Package Root | Root package initialization marker. |
| `src/config/__init__.py` | Configuration | Package initialization for application settings. |
| `src/config/settings.py` | Configuration | Application path resolution and model/cutoff configuration class. |
| `src/models/__init__.py` | Model Loader | Package initialization for model management utilities. |
| `src/models/model_loader.py` | Model Loader | Thread-safe caching deserializer for model artifacts (`joblib.load`). |
| `src/preprocessing/__init__.py` | Preprocessing | Package initialization for preprocessing and validation. |
| `src/preprocessing/input_validation.py` | Preprocessing | Defensive input validation for product text, customer IDs, cutoffs, and predictor frames. |
| `src/services/__init__.py` | Services | Package initialization exporting service interfaces for package compatibility. |
| `src/services/classification_service.py` | Services | `ProductCategoryService` executing text validation and category prediction. |
| `src/services/public_aggregate_service.py` | Services | Allowlisted aggregate report loader enforcing explicit report paths, schema validation, column selection, and small-cell suppression. |
| `src/services/recommendation_service.py` | Services | Legacy recommendation service retained for package compatibility; not invoked by public pages. |
| `src/services/repeat_purchase_service.py` | Services | Legacy repeat-purchase prediction service retained for package compatibility; not invoked by public pages. |
| `src/services/spending_prediction_service.py` | Services | Legacy spending prediction service retained for package compatibility; not invoked by public pages. |
| `src/services/segmentation_service.py` | Services | Legacy customer segmentation service retained for package compatibility; not invoked by public pages. |
| `src/services/explanation_service.py` | Services | Legacy model explanation service retained for package compatibility; not invoked by public pages. |
| `src/services/historical_snapshot_service.py` | Services | Legacy customer snapshot service retained for package compatibility; not invoked by public pages. |
| `src/services/analytics_service.py` | Services | Legacy analytics summary service retained for package compatibility; not invoked by public pages. |
| `src/ui/__init__.py` | UI Layer | UI package initialization exporting theme, styles, and core components. |
| `src/ui/authentication.py` | UI Layer | Fail-closed Streamlit OIDC setting validation and exact verified-email allowlist authorization (`APP_ALLOWED_EMAILS`). |
| `src/ui/components.py` | UI Layer | Reusable UI components including headers, KPI cards, section headings, status labels, and HTML escaping. |
| `src/ui/navigation.py` | UI Layer | Sidebar branding and footer navigation rendering functions. |
| `src/ui/public_aggregate_pages.py` | UI Layer | Shared release-gated access layer (`PUBLIC_AGGREGATES_RELEASED = False`) and view projection helpers for aggregate pages. |
| `src/ui/public_demo_logic.py` | UI Layer | Deterministic toy catalogue, illustrative item-to-item cosine similarity ranking, and synthetic threshold logic. |
| `src/ui/styles.py` | UI Layer | Application theme stylesheet, custom CSS variables, card classes, and layout definitions. |
| `src/ui/theme.py` | UI Layer | Design token definitions and color palette mappings. |
| `src/utils/__init__.py` | Utilities | Package initialization exporting custom exception classes. |
| `src/utils/exceptions.py` | Utilities | Application exception hierarchy (`BackendError`, `ModelLoadError`, `ValidationError`, `UnknownCustomerError`, `UnsupportedCutoffError`). |
| `.streamlit/config.toml` | Runtime Config | Streamlit runtime configuration: headless mode, port 8501, CORS enabled, XSRF protection enabled. |
| `.streamlit/secrets.toml.example` | Runtime Config | Redacted OIDC configuration template illustrating required authentication keys. |
| `requirements-deployment.txt` | Dependencies | Pinned direct runtime dependencies for deployment. |
| `README.md` | Documentation | Primary public documentation covering project purpose, pages, privacy boundaries, and setup instructions. |
| `docs/architecture-and-modules.md` | Documentation | Architecture reference detailing application flow, module responsibilities, and public data boundaries. |
| `docs/deployment-guide.md` | Documentation | Deployment guide covering entry points, runtime dependencies, health endpoints, and release blockers. |
| `docs/deployment-security.md` | Documentation | Security documentation detailing OIDC access controls, email allowlists, and artifact minimization. |
| `docs/running-locally.md` | Documentation | Local development instructions for running the authenticated public application. |
| `docs/public-release-manifest.md` | Documentation | This file: complete release file manifest, synthetic test manifest, exclusions, and dependency review. |

---

## 2. Synthetic Test Files

The following 7 test files validate the public application, authentication gate, aggregate data boundaries, fallback behaviors, and synthetic demonstrations without loading private customer records or trained model files.

| Test File Path | Scope | Verification Focus |
| :--- | :--- | :--- |
| `tests/synthetic_fixtures.py` | Shared Test Fixtures | Non-customer synthetic DataFrames and mock model loaders for unit testing. |
| `tests/test_authentication.py` | Authentication Gate | Email allowlist parsing, OIDC setting validation, placeholder rejection, and identity authorization logic. |
| `tests/test_public_aggregate_service.py` | Phase 1A Data Boundary | Report path allowlist, schema enforcement, identifier column rejection, row caps, and primary/complementary small-cell suppression. |
| `tests/test_phase1b_aggregate_pages.py` | Phase 1B Aggregate Pages | Unit and AST verification that aggregate pages respect suppression, omit private customer services, and avoid metric reconstruction. |
| `tests/test_phase1c_public_demos.py` | Phase 1C Demonstrations | Unit and AST verification that demonstration pages use fictional cosine rankings, synthetic threshold arithmetic, and no customer services. |
| `tests/test_phase1d2_public_fallback.py` | Phase 1D.2 Safe Fallback | Unit tests verifying that missing or unloadable classifier artifacts fail closed safely without error or path disclosure. |
| `tests/test_input_validation.py` | Defensive Validation | Validation checks on product text input, customer IDs, and approved cutoffs. |

---

## 3. Explicit Exclusions

The following file categories, directories, and data assets are strictly excluded from the public release manifest. They must never be staged, committed, bundled, or published.

| Category / Path | Exclusion Reason | Protection Mechanism |
| :--- | :--- | :--- |
| `datasets/` | Contains raw, interim, processed, feature, and model-ready customer transaction tables. | Excluded by `.gitignore` and release manifest. |
| `models/` | Contains serialized model binaries (`.joblib`), scalers, imputers, and pipelines. | Excluded by `.gitignore` and release manifest. |
| `reports/` | Contains internal phase reports, evaluation metrics, charts, and intermediate artifacts. | Excluded by `.gitignore` and release manifest. |
| `deployment_staging/` | Temporary deployment packages, staging trees, and local build artifacts. | Excluded by `.gitignore` and release manifest. |
| `notebooks/` | Exploratory, feature-engineering, model training, and analysis Jupyter notebooks. | Excluded by release manifest. |
| `docs/portfolio/` | Internal portfolio slide presentations (`.pptx`), resume drafts, and unreviewed materials. | Excluded by release manifest. |
| `.env*` and local configs | Local environment variables, active virtual environments (`.venv*`), and shell scripts. | Excluded by `.gitignore` and release manifest. |
| Real secrets & credentials | OIDC client secrets, cookie secrets, API keys, OAuth tokens, and passwords. | Excluded by `.gitignore` and security policy. |
| Protected holdout data | All September 2011 holdout transactions, labels, predictions, and derived evaluations. | Excluded by strict data protection boundary. |

---

## 4. Runtime Dependency Review

The public runtime dependencies listed in `requirements-deployment.txt` were evaluated against the direct imports of `app.py`, all seven public pages, and required source modules.

| Declared Dependency | Version | Runtime Consumer | Evaluation |
| :--- | :--- | :--- | :--- |
| `streamlit` | `1.67.0` | `app.py`, all 7 pages, `src/ui/` | Direct runtime dependency. |
| `Authlib` | `1.9.9` | Streamlit OIDC authentication | Required by Streamlit built-in OIDC (`st.login`/`st.logout`). |
| `pandas` | `3.1.1` | Overview, Intelligence, Predictions, Segments, Insights, `public_aggregate_service.py` | Direct runtime dependency. |
| `plotly` | `7.1.0` | Overview, Recommendations, Intelligence, Predictions, Segments, Insights | Direct runtime dependency. |
| `numpy` | `2.5.5` | `src/preprocessing/input_validation.py`, `src/services/` | Direct runtime dependency. |
| `joblib` | `1.6.0` | `src/models/model_loader.py` | Direct runtime dependency for model deserialization. |
| `scikit-learn` | `1.9.1` | `src/services/classification_service.py` | Runtime dependency if private classifier artifact is provisioned. |
| `scipy` | `1.18.1` | `scikit-learn` sparse matrix operations | Required transitively by scikit-learn TF-IDF pipeline. |

### Dependency Observations and Blockers:
1. **Streamlit OIDC Extra Alignment**: Streamlit 1.67.0 declares OIDC dependencies under the `streamlit[auth]` extra (which includes `authlib` and `httpx`). While `Authlib==1.9.9` is listed in `requirements-deployment.txt`, `httpx` is not explicitly declared. This reconciliation must be confirmed for the deployment target.
2. **Standard Library Utilization**: All other application imports (`pathlib`, `collections.abc`, `os`, `re`, `urllib.parse`, `html`, `dataclasses`, `types`, `time`, `threading`, `math`) are satisfied by the Python standard library with no external package requirements.
3. **No Unnecessary Runtime Packages**: No unneeded database drivers, cloud SDKs, visualization wrappers, or notebook packages are included in `requirements-deployment.txt`.

---

## 5. Security and Data Access Verification

- **Fail-Closed Authentication**: `app.py` blocks execution unless valid OIDC secrets and a non-empty `APP_ALLOWED_EMAILS` are configured.
- **Email Allowlist Precedence**: Configuring an external OAuth audience or broad provider-level user type setting does not remove or bypass the application-level email allowlist (`APP_ALLOWED_EMAILS`).
- **Release Gate Disabled**: `PUBLIC_AGGREGATES_RELEASED` is set to `False` in `src/ui/public_aggregate_pages.py`. All public aggregate pages show informative pending banners without attempting report reads.
- **Fail-Closed Classifier**: `ProductCategoryService` displays a safe unavailable notice when the model artifact is absent or fails to load, preventing error tracebacks or internal path disclosures.
- **Illustrative Demos**: Recommendations and Predictions use deterministic fictional logic and explicit arithmetic rules, not trained machine learning models or customer records.
- **Zero Protected Data Access**: Zero September 2011 holdout files, customer identifiers, or private model artifacts are included, referenced, or accessed.
