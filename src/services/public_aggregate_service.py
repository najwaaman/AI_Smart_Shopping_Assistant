"""Strict loader for allowlisted, non-customer-level public aggregate reports.

This service intentionally has no directory scanning or caller-supplied file
path support. Callers can request only the exact relative report paths listed
in ``REPORT_SPECS``. Returned frames contain only explicitly selected columns.
"""

from dataclasses import dataclass
from pathlib import Path
from types import MappingProxyType

import pandas as pd


class PublicAggregateDataError(Exception):
    """Raised when an allowlisted public aggregate report is unsafe or invalid."""


@dataclass(frozen=True)
class ReportSpec:
    columns: tuple[str, ...]
    text_columns: tuple[str, ...] = ()
    numeric_columns: tuple[str, ...] = ()
    nullable_numeric_columns: tuple[str, ...] = ()
    unique_by: tuple[str, ...] = ()
    max_rows: int = 100
    allowed_values: tuple[tuple[str, tuple[object, ...]], ...] = ()
    suppression_groups: tuple[tuple[str, ...], ...] = ()
    suppression_mode: str = "rows"
    suppression_hide_columns: tuple[str, ...] = ()


_CLUSTER_PROFILE_COLUMNS = (
    "segment_id",
    "customer_count",
    "unique_customers",
    "average_historical_gross_spending",
    "median_historical_gross_spending",
    "average_invoice_frequency",
    "percentage",
)

REPORT_SPECS = MappingProxyType(
    {
        "reports/segmentation/phase_9/Cluster_Profiles.csv": ReportSpec(
            columns=_CLUSTER_PROFILE_COLUMNS,
            numeric_columns=(
                "segment_id",
                "customer_count",
                "unique_customers",
                "average_historical_gross_spending",
                "median_historical_gross_spending",
                "average_invoice_frequency",
                "percentage",
            ),
            unique_by=("segment_id",),
            max_rows=3,
            allowed_values=(("segment_id", (0, 1, 2)),),
            suppression_groups=(("customer_count", "unique_customers"),),
            suppression_hide_columns=("customer_count", "unique_customers", "percentage"),
        ),
        "reports/segmentation/phase_9/Temporal_Stability_Report.csv": ReportSpec(
            columns=("segment_id", "march_count", "june_count", "march_percentage", "june_percentage"),
            numeric_columns=("segment_id", "march_count", "june_count", "march_percentage", "june_percentage"),
            unique_by=("segment_id",),
            max_rows=3,
            allowed_values=(("segment_id", (0, 1, 2)),),
            suppression_groups=(("march_count",), ("june_count",)),
            suppression_hide_columns=("march_count", "june_count", "march_percentage", "june_percentage"),
        ),
        "reports/segmentation/phase_9/Clustering_Model_Comparison.csv": ReportSpec(
            columns=("algorithm", "clusters", "silhouette", "davies_bouldin", "calinski_harabasz", "noise", "inertia"),
            text_columns=("algorithm",),
            numeric_columns=("clusters", "silhouette", "davies_bouldin", "calinski_harabasz", "noise"),
            nullable_numeric_columns=("inertia",),
            unique_by=("algorithm", "clusters"),
            max_rows=8,
            allowed_values=(("algorithm", ("KMeans", "Agglomerative")), ("clusters", (3, 4, 5, 6))),
        ),
        "reports/explainability/phase_9/Classification_Feature_Importance.csv": ReportSpec(
            columns=("feature_name", "importance", "permutation_mean", "permutation_std"),
            text_columns=("feature_name",),
            numeric_columns=("importance", "permutation_mean", "permutation_std"),
            unique_by=("feature_name",),
            max_rows=15,
            allowed_values=(("feature_name", (
                "missing_indicator_average_days_between_invoices", "scaled_average_days_between_invoices",
                "scaled_customer_active_days", "scaled_gross_spending_180d", "scaled_gross_spending_90d",
                "scaled_historical_active_month_count", "scaled_historical_gross_spending",
                "scaled_historical_invoice_count", "scaled_historical_total_quantity",
                "scaled_historical_weekday_invoice_count", "scaled_invoice_count_180d",
                "scaled_invoice_count_90d", "scaled_quantity_180d", "scaled_quantity_90d",
                "scaled_unique_products_90d",
            )),),
        ),
        "reports/explainability/phase_9/Regression_Feature_Importance.csv": ReportSpec(
            columns=("feature_name", "coefficient_abs", "permutation_mean", "permutation_std"),
            text_columns=("feature_name",),
            numeric_columns=("coefficient_abs", "permutation_mean", "permutation_std"),
            unique_by=("feature_name",),
            max_rows=14,
            allowed_values=(("feature_name", (
                "scaled_customer_active_days", "scaled_gross_spending_180d", "scaled_gross_spending_90d",
                "scaled_historical_active_month_count", "scaled_historical_gross_spending",
                "scaled_historical_invoice_count", "scaled_historical_total_quantity",
                "scaled_historical_transaction_line_count", "scaled_historical_weekday_invoice_count",
                "scaled_invoice_count_180d", "scaled_invoice_count_90d", "scaled_quantity_180d",
                "scaled_quantity_90d", "scaled_spending_per_active_day",
            )),),
        ),
        "reports/classification/phase_6/Model_comparison.csv": ReportSpec(
            columns=("model_name", "accuracy", "precision", "recall", "f1", "roc_auc", "average_precision", "tn", "fp", "fn", "tp"),
            text_columns=("model_name",),
            numeric_columns=("accuracy", "precision", "recall", "f1", "roc_auc", "average_precision", "tn", "fp", "fn", "tp"),
            unique_by=("model_name",),
            max_rows=20,
            allowed_values=(("model_name", ("gradient_boosting", "random_forest", "logistic_regression", "decision_tree")),),
            suppression_groups=(("tn", "fp", "fn", "tp"),),
            suppression_mode="cells",
        ),
        "reports/regression/phase_7/Model_Comparison.csv": ReportSpec(
            columns=("model_name", "mae", "rmse", "r2", "median_absolute_error", "explained_variance", "mape", "zero_target_count", "positive_target_count", "zero_target_mae", "positive_target_mae", "exact_zero_predictions", "negative_prediction_count", "mean_prediction", "median_prediction", "training_seconds"),
            text_columns=("model_name",),
            numeric_columns=("mae", "rmse", "r2", "median_absolute_error", "explained_variance", "mape", "zero_target_count", "positive_target_count", "zero_target_mae", "positive_target_mae", "exact_zero_predictions", "negative_prediction_count", "mean_prediction", "median_prediction", "training_seconds"),
            unique_by=("model_name",),
            max_rows=20,
            allowed_values=(("model_name", ("ridge_regression", "linear_regression", "random_forest", "gradient_boosting", "decision_tree", "hist_gradient_boosting", "dummy_mean")),),
            suppression_groups=(("zero_target_count", "positive_target_count"),),
            suppression_mode="cells",
        ),
        "reports/recommendation/phase_8/Recommendation_Metrics_By_K.csv": ReportSpec(
            columns=("method", "k", "precision", "recall", "map", "ndcg", "hit_rate", "catalog_coverage", "diversity"),
            text_columns=("method",),
            numeric_columns=("k", "precision", "recall", "map", "ndcg", "hit_rate", "catalog_coverage", "diversity"),
            unique_by=("method", "k"),
            max_rows=40,
            allowed_values=(("method", ("popularity", "item_item", "customer_cf", "hybrid")), ("k", (5, 10, 20))),
        ),
    }
)

_IDENTIFIER_NAMES = {
    "customer_id",
    "customerid",
    "customer id",
    "customer identifier",
    "customer_name",
    "email",
    "email_address",
    "phone",
    "address",
    "invoice",
    "invoiceno",
    "stockcode",
    "description",
}


class PublicAggregateService:
    """Read and validate only named public aggregate reports."""

    def __init__(self, project_root=None, minimum_cell_size=10):
        if isinstance(minimum_cell_size, bool) or not isinstance(minimum_cell_size, int) or minimum_cell_size < 2:
            raise ValueError("minimum_cell_size must be an integer of at least 2")
        self.project_root = (Path(project_root) if project_root is not None else Path(__file__).resolve().parents[2]).resolve()
        self.minimum_cell_size = minimum_cell_size

    def load_report(self, relative_path):
        """Load one exact allowlisted relative path; arbitrary paths are rejected."""
        if not isinstance(relative_path, str) or relative_path not in REPORT_SPECS:
            raise PublicAggregateDataError("Report path is not on the public aggregate allowlist.")

        spec = REPORT_SPECS[relative_path]
        source = self.project_root.joinpath(*relative_path.split("/"))
        current = self.project_root
        for part in relative_path.split("/"):
            current = current / part
            if current.is_symlink():
                raise PublicAggregateDataError(f"Approved aggregate report path is invalid: {Path(relative_path).name}")
        if not source.is_file():
            raise PublicAggregateDataError(f"Approved aggregate report is missing: {Path(relative_path).name}")

        try:
            header = list(pd.read_csv(source, nrows=0).columns)
        except Exception as exc:
            raise PublicAggregateDataError(f"Approved aggregate report has an unreadable header: {Path(relative_path).name}") from exc

        self._validate_header(header, spec, relative_path)
        try:
            # Read at most one row beyond the schema cap. Oversized inputs are
            # rejected without loading an unbounded table into memory.
            frame = pd.read_csv(source, usecols=list(spec.columns), nrows=spec.max_rows + 1)
        except Exception as exc:
            raise PublicAggregateDataError(f"Approved aggregate report could not be read: {Path(relative_path).name}") from exc

        frame = self._validate_frame(frame, spec, relative_path)
        return self._suppress_small_cells(frame, spec)

    def _validate_header(self, header, spec, relative_path):
        normalized = {str(name).strip().casefold() for name in header}
        if normalized & _IDENTIFIER_NAMES:
            raise PublicAggregateDataError(f"Customer-level identifiers are not allowed: {Path(relative_path).name}")

        missing = set(spec.columns).difference(header)
        if missing:
            raise PublicAggregateDataError(f"Approved aggregate report has an invalid schema: {Path(relative_path).name}")

        # These two legacy cluster-profile columns are known defective. They may
        # exist in the source report, but are never selected or returned.
        legacy_omissions = set()
        if relative_path == "reports/segmentation/phase_9/Cluster_Profiles.csv":
            legacy_omissions = {"average_recency", "average_unique_products"}
        unexpected = set(header).difference(spec.columns).difference(legacy_omissions)
        if unexpected:
            raise PublicAggregateDataError(f"Approved aggregate report has an invalid schema: {Path(relative_path).name}")

    def _validate_frame(self, frame, spec, relative_path):
        if tuple(frame.columns) != spec.columns:
            raise PublicAggregateDataError(f"Approved aggregate report has an invalid schema: {Path(relative_path).name}")
        if frame.empty or len(frame) > spec.max_rows:
            raise PublicAggregateDataError(f"Approved aggregate report has an invalid row count: {Path(relative_path).name}")

        for name in spec.text_columns:
            if frame[name].isna().any() or not frame[name].map(lambda value: isinstance(value, str) and bool(value.strip())).all():
                raise PublicAggregateDataError(f"Approved aggregate report has invalid values: {Path(relative_path).name}")
        for name in spec.numeric_columns + spec.nullable_numeric_columns:
            try:
                frame[name] = pd.to_numeric(frame[name], errors="raise")
            except (TypeError, ValueError) as exc:
                raise PublicAggregateDataError(f"Approved aggregate report has invalid data types: {Path(relative_path).name}") from exc
        for name in spec.numeric_columns:
            if frame[name].isna().any():
                raise PublicAggregateDataError(f"Approved aggregate report has missing required values: {Path(relative_path).name}")
        for name, allowed in spec.allowed_values:
            if not frame[name].isin(allowed).all():
                raise PublicAggregateDataError(f"Approved aggregate report has invalid group values: {Path(relative_path).name}")
        if spec.unique_by and frame.duplicated(list(spec.unique_by)).any():
            raise PublicAggregateDataError(f"Approved aggregate report has duplicate groups: {Path(relative_path).name}")
        return frame

    def _suppress_small_cells(self, frame, spec):
        result = frame.copy()
        if not spec.suppression_groups:
            return result

        if spec.suppression_mode == "cells":
            for group in spec.suppression_groups:
                for index in result.index:
                    values = pd.to_numeric(result.loc[index, list(group)], errors="coerce")
                    small = [column for column in group if pd.notna(values[column]) and values[column] < self.minimum_cell_size]
                    if small:
                        # Other metrics in the same row can algebraically reveal
                        # small cells (for example precision or accuracy), so
                        # suppress the full row when a count cell is small.
                        result.loc[index, :] = float("nan")
            return result

        for group in spec.suppression_groups:
            available = [column for column in group if column in result]
            if not available:
                continue
            small_mask = pd.DataFrame(
                {column: result[column].notna() & (result[column] < self.minimum_cell_size) for column in available}
            ).any(axis=1)
            small_rows = set(result.index[small_mask])
            if not small_rows:
                continue

            # Primary suppression: every group with a small population measure.
            suppressed_rows = set(small_rows)
            # Complementary suppression: hide the largest remaining group too,
            # preventing a known total minus visible cells from exposing one
            # suppressed group's value.
            score = result.loc[~result.index.isin(suppressed_rows), available].max(axis=1, skipna=True)
            score = score.dropna()
            if not score.empty:
                suppressed_rows.add(score.idxmax())
            # Suppress all fields for affected groups, including percentages and
            # descriptive measures that could reveal the count indirectly.
            row_keys = result.loc[list(suppressed_rows), list(spec.unique_by)].copy() if spec.unique_by else None
            result.loc[list(suppressed_rows), :] = float("nan")
            if row_keys is not None:
                result.loc[list(suppressed_rows), list(spec.unique_by)] = row_keys
            # Hide full count/percentage columns so a consumer cannot compute a
            # misleading partial subtotal from only the visible groups.
            hide = [column for column in spec.suppression_hide_columns if column in result]
            if hide:
                result.loc[:, hide] = float("nan")
        return result
