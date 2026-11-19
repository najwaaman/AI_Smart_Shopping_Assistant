# Deployment preparation guide

This project is prepared for a later deployment review. It has **not** been
deployed, published, or tested in a production environment. Do not place
customer data, models, credentials, or private reports in a public repository
or image.

The root README now describes the implemented project. The older
`docs/running-locally.md` still contains historical testing notes; use this
guide and the phase reports for deployment preparation.

## Runtime and dependency set

Use CPython 3.14.3 and the pinned direct application dependencies in
[`requirements-deployment.txt`](../requirements-deployment.txt). Pins were
validated in a new `.venv-phase15a` environment; the existing project `.venv`
was not modified. The saved estimators were created with scikit-learn 1.9.1,
which is pinned to avoid the warning observed with global Python 3.14.3, which
has scikit-learn 1.9.0. Authlib is included for Streamlit OIDC login.

`requirements.txt` is the original unpinned analysis/development list. It
contains packages such as Jupyter and SHAP that are not directly imported by
the current Streamlit application. Do not use that unpinned list for a
reproducible deployment. The deployment file pins direct runtime packages;
it is not a complete transitive lock file. A clean install resolved and passed `pip check` in `.venv-phase15a`; revalidate in the actual deployment build.

Never install packages into the existing project `.venv` as part of deployment
preparation. A clean validation environment was created at `.venv-phase15a`.
For a later deployment, create a separate environment:

```powershell
py -3.14 -m venv .venv-deploy
.\.venv-deploy\Scripts\Activate.ps1
python -m pip install -r requirements-deployment.txt
python -m pip check
```

`.venv-phase15a` was created and validated in this phase; `.venv-deploy` is an example path for a later approved deployment.

## Configuration and secrets

The repository includes `.streamlit/config.toml` with headless mode, the
standard port, CORS and XSRF protection enabled, and usage statistics disabled.
`.env.example` documents non-secret server variables and `APP_ALLOWED_EMAILS`.
It is a template only: application code does not load `.env` files. Set
`APP_ALLOWED_EMAILS` in the host process environment. Configure OIDC credentials
in the hosting secret manager or a local ignored `.streamlit/secrets.toml`,
using [the placeholder example](../.streamlit/secrets.toml.example). Never
commit real client or cookie secrets.

The app denies access unless OIDC settings are complete and the identity has a
verified email claim present in the exact `APP_ALLOWED_EMAILS` allowlist. The
provider must also restrict access to intended accounts. Streamlit OIDC
authenticates identities; the application's exact-email allowlist performs its
authorization check. No OIDC provider or client was configured or tested here.

The container-only `STREAMLIT_SERVER_ADDRESS=0.0.0.0` option is deliberately
not enabled in the checked-in config. Set it only when the container is behind
the deployment platform's ingress and authentication controls.

## Private data and model handling

`.gitignore` excludes the raw and processed source directories, customer-level
analytics/insights/features/model-ready/recommendation datasets, model files,
local secrets, and row-level segmentation/explanation reports. Do not remove
these exclusions to make a deployment build succeed. Stage only the artifacts
needed by the app in private storage with access controls. Never upload the
September holdout, combined customer snapshots, September-derived records, or
any raw customer transaction data.

`deployment_staging/` is an ignored local bundle containing only the eight
allow-listed saved model/preprocessing artifacts and a SHA-256 manifest. It
contains no datasets or customer records. Treat these model copies as private
and transfer only through an approved access-controlled artifact channel. The
application still needs separate private runtime datasets and reports for
customer workflows; do not add them to the model bundle or public image.

Pages 04â€“06 use the fixed `HistoricalSnapshotService` mapping to the separate
March 2011 and June 2011 snapshots. Page 01 uses only those two snapshots and
the verified March/June cluster profile summary. The recommendation feature
is June-only. Other page-specific feature and insight inputs must be checked
against the approved March/June lineage before being staged. Start the app only
through `app.py`, which applies authentication before the Streamlit multipage
router runs. Do not run individual page scripts as deployment entrypoints.

## Startup and preflight checks

From the project root, in the separately approved deployment environment:

```powershell
python -m pip check
python -m unittest discover -s tests -p "test_phase12b_snapshot_isolation.py" -v
python -m unittest discover -s tests -p "test_phase13b_dashboard_isolation.py" -v
python -m unittest discover -s tests -p "test_*.py" -q
python -m streamlit run app.py --server.headless true --server.port 8501
```

Before startup, confirm the two approved Phase 12 snapshots, the verified
cluster profile report, and each required private model/feature artifact are
present at their configured paths. Check model imports and sample outputs
without using protected holdout records. Do not copy the broad transaction
table into the deployment image just to populate overview metrics.
Configure the OIDC provider redirect URI to the deployment host's absolute
`/oauth2callback` URL, supply all required `[auth]` settings, and populate the
exact verified-email allowlist before expecting the app pages to be available.

## Health checks

Streamlit's documented health endpoint is `/_stcore/health`. Configure the
hosting platform to probe `http://127.0.0.1:8501/_stcore/health` (or the
container's equivalent) and treat an unsuccessful response as an unhealthy
instance. This endpoint checks server health; it does not prove that private
artifacts are present or that each workflow succeeds. Follow it with the
approved snapshot-isolation and page/service smoke tests above.

The health path follows the [official Streamlit Docker deployment guidance](https://docs.streamlit.io/deploy/tutorials/docker).

## Rollback and recovery plan for a future host

No hosting platform has been selected, so these are generic preparation steps, not an executed rollback test:

1. Keep a versioned release bundle containing only approved source/config, the matching dependency lock, and privately provisioned March/June-only runtime artifacts. Record model SHA-256 values from the approved manifest.
2. Retain the previous known-good application and model bundle in access-controlled storage. Do not place customer datasets or secrets in source/image layers or public release assets.
3. On a failed health or workflow check, remove the new instance from ingress, restore the previous application and matching model artifact version, restore the last verified private data mount, and re-run `pip check`, model-load smoke checks, snapshot-isolation tests, startup, and `/_stcore/health` before returning traffic.
4. Rotate OIDC client/cookie secrets if exposure is suspected; use the identity provider to revoke sessions as appropriate. Preserve logs under the host privacy/retention policy and avoid logging customer inputs or tokens.
5. Document the host-specific backup, restore, secret rotation, log retention, and rollback commands before an actual deployment.

No backup, restore, rollback, or recovery drill was performed in this phase.
## Current readiness limits

- Dependency versions and the test suite were validated in a new
  `.venv-phase15a`; the existing `.venv` was not modified.
- The Phase 15A run passed 93 tests; the final audit run passed 95 tests in `.venv-phase15a`. Browser, accessibility, load, security-penetration, and production tests were not performed.
- OIDC login and exact-email authorization are implemented, but no real
  identity-provider configuration or end-to-end login was tested.
- Private model and data artifacts are ignored by Git and must be provided
  securely by a separately approved deployment process.
- No deployment platform or hosting target has been selected or validated.
