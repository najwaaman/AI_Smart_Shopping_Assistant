# Public application architecture

## Application flow

`app.py` configures Streamlit, applies the fail-closed OIDC/email-allowlist gate, and registers all seven page scripts. Shared layout and theme code lives under `src/ui/`. Public aggregate pages call the Phase 1A allowlisted loader through the Phase 1B release-gate helper. Fictional demonstrations use deterministic helpers from `src/ui/public_demo_logic.py`.

| Page | Runtime behavior |
| --- | --- |
| 01 Overview | Shows an aggregate-review pending state; it does not render report values while the release gate is closed. |
| 02 Product Classification | Checks whether the configured saved TF-IDF + Linear SVM pipeline is available. If missing or unloadable, it shows a safe unavailable message and produces no classification. |
| 03 Recommendations | Ranks fictional catalogue items using illustrative cosine similarity. The aggregate evaluation panel remains pending. |
| 04 Customer Intelligence | Shows the privacy-reviewed aggregate cohort interface only after approval; no customer lookup or individual rows. |
| 05 Predictions | Shows hypothetical visitor inputs and transparent illustrative arithmetic; no trained customer model is called. |
| 06 Customer Segments | Aggregate-only profile, stability, and comparison views behind the release gate. |
| 07 Model Insights | Global model metrics and importance views behind the release gate; no individual explanations. |

## Public data boundary

`PublicAggregateService` has an explicit eight-report allowlist, required schema checks, selected-column projections, and configured suppression. `PUBLIC_AGGREGATES_RELEASED` remains `False`, so the helper rejects report requests before reading report files. Do not bypass the helper or reconstruct suppressed values.

The public pages do not call customer-specific history, recommendation, segmentation, explanation, repeat-purchase, or spending services. Existing backend modules remain in the package for compatibility; the current public navigation does not invoke those customer workflows. Their presence in the source tree is not permission to provision customer data.

No datasets, saved models, private reports, or static data assets are required for the public page shells and fictional demonstrations. Product Classification needs its private pipeline artifact to make real predictions; until an approved provisioning process exists, its unavailable state is expected. Aggregate pages remain useful as documented shells but withhold project-derived values pending review.

## Authentication and limitations

The app entry point requires OIDC configuration and an exact verified-email allowlist before page navigation. Missing configuration fails closed. A real identity provider and hosted callback have not been tested. The application has no database or commerce API, and no deployment, browser, accessibility, load, or production verification is claimed.

`src/services/__init__.py` eagerly imports the existing service modules. Those modules are included in the source manifest because package initialization loads them; their customer workflows are not called by public pages. Training scripts, private datasets, model artifacts, and reports are not runtime manifest entries.
