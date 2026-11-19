# Data, preprocessing, and evaluation

## Separate data families

The application uses multiple task-specific artifacts. The product-description classifier corpus is separate from retail transaction data. Customer snapshots, model-ready predictors, recommendation rows, customer insights, and evaluation/report files are not represented as a single merged dataset.

| Data family | Example / approved path | Use |
| --- | --- | --- |
| Product text corpus | `datasets/cleaned/` | Four-category classification train/validation/test task. |
| Accepted transactions | Phase 2 accepted-paid-line output (private) | Approved upstream source for historical analysis; not required by Overview at runtime. |
| Historical customer facts | `datasets/customer_analytics/phase_12/march_2011_historical_customer_snapshots.csv` and `june_2011_historical_customer_snapshots.csv` | Separate March and June snapshots used by the historical snapshot service and Overview. |
| Supervised customer features | `datasets/model_ready/classification/` and `datasets/model_ready/regression/` | Separate cutoff-specific training/validation features for the approved March and June workflows. |
| Recommendations | `datasets/recommendations/phase_8/` and a June recommendation feature input | Precomputed June-only recommendation results and supporting input. |
| Customer insights and reports | Phase 9 private artifact directories | Approved March/June assignments, summaries, comparisons, and explanation examples. Keep private. |

Do not publish or mount broad historical tables or customer-level records by default. The referenced data files are private local assets and are absent from a public source release.

## Transaction acceptance and historical snapshots

The Phase 2 acceptance specification excludes disallowed dates, cancellation/return or adjustment records, nonpositive quantities/prices, missing required identifiers, and unresolved duplicate-group members. Returns/cancellations are not netted into spending totals. The source has no established currency denomination.

Phase 12A derives separate historical summaries from the approved accepted-paid-line input at or before each cutoff's midnight. Customer eligibility and feature calculations are cutoff-specific. The two outputs are distinct artifacts; they are not a March/June/September combined file. Internal Phase 12A field definitions and validation evidence remain in a private report and are intentionally not linked from this public document.

## Preprocessing and feature engineering

The project documents separate feature sets for repeat purchase, spending, recommendations, and segmentation. March-fitted imputation/scaling is used where specified; future targets and customer identifiers are excluded from model predictors. Services validate required numeric columns and reject target columns. The Phase 5 feature-selection and preprocessing reports are the source for detailed feature lists and fit boundaries.

## Temporal evaluation protocol

- **March 1, 2011:** customer-model training/fitting and segmentation preprocessing.
- **June 1, 2011:** validation and approved application cutoff.
- **September 2011:** protected customer holdout. No September records or metrics are included in this documentation or the current phase's tests.

The product text classifier has its own held-out text test split; it is not a customer holdout.

## Reported evaluation metrics

Values below are transcribed from the verified project evaluation documentation and prior phase reports; they were not recomputed in this documentation pass.

| Task | Metric | Value | Split |
| --- | --- | ---: | --- |
| Product category, Linear SVM + TF-IDF | Accuracy | 0.958044 (95.80%) | Separate final text test, 4,171 rows |
|  | Macro precision | 0.960613 | Separate final text test |
|  | Macro recall | 0.955156 | Separate final text test |
|  | Macro F1 | 0.957788 | Separate final text test |
| Repeat purchase, Gradient Boosting | Accuracy | 0.683959 | June validation |
|  | F1 | 0.690896 | June validation |
|  | ROC-AUC | 0.749553 | June validation |
|  | Average precision | 0.773749 | June validation |
| Future spending, Ridge | MAE | 533.927631 | June validation, no currency label |
|  | RMSE | 1541.713665 | June validation, no currency label |
|  | R-squared | 0.682499 | June validation, no currency label |
| Item-item recommendations | NDCG@10 | 0.133916 | June-only evaluation |
|  | Hit rate@10 | 0.359455 | June-only evaluation |
|  | Catalog coverage | 0.613753 | June-only evaluation |
| KMeans segmentation | Cluster count | 3 | March fit; June transformed / described |

Segmentation cluster IDs are descriptive categories, not an ordered quality or customer-value score.

## Interpretation limits

- Repeat-purchase June validation is moderate; reported known-versus-unseen splits have different performance. Unseen means not represented in the training cohort, not necessarily a new retail customer.
- Ridge spending is unconstrained, can be negative, and is not denominated in a verified currency. Zero-heavy targets make MAPE unsuitable in the source analysis.
- Recommendations are precomputed and June-only; the runtime does not promise an on-demand fallback.
- Permutation importance and zero-feature perturbation summaries are descriptive associations, not causal effects. SHAP and sentiment analysis are not implemented.
- No independent customer holdout score is claimed.

## Primary verification sources

The metric values and descriptions above are transcribed from the project workspace's Phase 2, Phase 6, Phase 7, Phase 8, Phase 9A/9B, Phase 11A, and Phase 12A reports. Those reports remain internal: they may include customer-level examples or operational details and are not included in the suggested public release file set.
