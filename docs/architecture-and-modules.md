# Architecture and modules

## Application flow

`app.py` configures Streamlit, applies the fail-closed authentication gate, then registers and runs seven pages. Pages call services in `src/services/`; services validate inputs and use `ModelLoader` for saved-model inference. Shared rendering, navigation, authentication, and Overview data assembly live under `src/ui/`.

```text
app.py -> OIDC / verified-email allowlist gate -> seven-page navigation
  01 Overview              -> March/June snapshot service + cluster profile summary
  02 Product Classification -> ProductCategoryService -> saved TF-IDF / Linear SVM
  03 Recommendations        -> RecommendationService -> precomputed June item-item rows
  04 Customer Intelligence  -> historical snapshots + customer insights + segment lookup
  05 Predictions            -> repeat-purchase and spending services + cutoff features
  06 Customer Segments      -> segment profiles, assignments, and stability summaries
  07 Model Insights         -> model comparison, importance, residual, explanation reports
```

This describes local code paths, not a deployment architecture. The app has no external commerce API or database integration.

## Implemented modules and runtime behavior

| Module | Implemented behavior |
| --- | --- |
| Product classification | `ProductCategoryService` loads the configured Linear SVM + TF-IDF pipeline and classifies supplied text into the saved classes. |
| Recommendations | `RecommendationService` validates June 1, 2011 and returns precomputed item-item cosine-similarity rows. Unknown customers are rejected. Saved recommendation artifacts are not used for on-demand ranking in this path. |
| Repeat purchase | `RepeatPurchaseService` chooses the March or June model-ready feature file, validates predictors, and calls the saved Gradient Boosting classifier. |
| Future spending | `SpendingPredictionService` chooses the matching approved cutoff feature file and calls saved Ridge Regression. Raw output may be negative and has no established currency label. |
| Historical customer view | `HistoricalSnapshotService` maps the March and June cutoffs to separate Phase 12 snapshot files. Pages may also use other precomputed reports/insights as described by their services. Their data lineage is not inferred from the snapshot mapping. |
| Segmentation | `SegmentationService` looks up precomputed customer/cutoff assignments. KMeans was fitted on March with three clusters; the service does not perform arbitrary feature-vector assignment. |
| Explainability | `ExplanationService` serves saved global-importance tables and a fixed cohort of individual perturbation examples. It does not compute SHAP or explanations for arbitrary new customers. |
| Overview | `src/ui/dashboard_data.py` loads the two approved historical snapshots and the Phase 9 March/June cluster profile summary. It does not load the broad transaction-lines table. |
| Authentication | `require_authenticated_user()` is called before page registration. It checks OIDC settings and an exact allowlist of verified emails. No role/tenant system exists. |

The Phase 9 source reports describe the segmentation and explainability artifacts as March/June based, with September untouched. Deployment should still provision only those specific approved artifacts and verify their lineage before mounting them.

## Shared implementation details

- `Settings` contains configured relative paths for saved models and task-specific data.
- `ModelLoader` deserializes and caches models within its instance; it is not documented as process-wide caching.
- Input validators restrict customer cutoff workflows to March 1 and June 1, 2011. Recommendations accept June only.
- HTML-escaped display helpers are used for untrusted textual content where applicable; this is not a complete application security audit.
- Pages use local files and the running process's filesystem permissions. `.gitignore` does not enforce runtime access control.

## Known integration limits

- There is no database, commerce API, user role model, tenant isolation, or automated asset download.
- Some pages read precomputed customer-level reports at page initialization. Their lineage and file permissions must be checked before a deployment mount is approved.
- Page-level Streamlit tests are not browser or live navigation tests. Authenticated multipage navigation requires a real configured provider and remains unverified.