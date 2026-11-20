"""Synthetic page tests for the aggregate-only public pages."""

import ast
from pathlib import Path
import unittest
from unittest.mock import patch

import numpy as np
import pandas as pd
from streamlit.testing.v1 import AppTest

from src.services.public_aggregate_service import REPORT_SPECS, PublicAggregateDataError, PublicAggregateService
from src.ui.public_aggregate_pages import cluster_profile_view, temporal_stability_view


ROOT = Path(__file__).resolve().parents[1]
PAGE_REPORTS = {
    "01_Overview.py": (
        "reports/segmentation/phase_9/Cluster_Profiles.csv",
        "reports/segmentation/phase_9/Clustering_Model_Comparison.csv",
        "reports/classification/phase_6/Model_comparison.csv",
        "reports/regression/phase_7/Model_Comparison.csv",
        "reports/recommendation/phase_8/Recommendation_Metrics_By_K.csv",
    ),
    "06_Customer_Segments.py": (
        "reports/segmentation/phase_9/Cluster_Profiles.csv",
        "reports/segmentation/phase_9/Temporal_Stability_Report.csv",
        "reports/segmentation/phase_9/Clustering_Model_Comparison.csv",
    ),
    "07_Model_Insights.py": (
        "reports/explainability/phase_9/Classification_Feature_Importance.csv",
        "reports/explainability/phase_9/Regression_Feature_Importance.csv",
        "reports/classification/phase_6/Model_comparison.csv",
        "reports/regression/phase_7/Model_Comparison.csv",
    ),
}


def _synthetic_reports():
    profiles = pd.DataFrame(
        [
            {"segment_id": 0, "customer_count": np.nan, "unique_customers": np.nan, "average_historical_gross_spending": np.nan, "median_historical_gross_spending": np.nan, "average_invoice_frequency": np.nan, "percentage": np.nan},
            {"segment_id": 1, "customer_count": np.nan, "unique_customers": np.nan, "average_historical_gross_spending": np.nan, "median_historical_gross_spending": np.nan, "average_invoice_frequency": np.nan, "percentage": np.nan},
            {"segment_id": 2, "customer_count": np.nan, "unique_customers": np.nan, "average_historical_gross_spending": 245.5, "median_historical_gross_spending": 190.0, "average_invoice_frequency": 4.2, "percentage": np.nan},
        ],
        columns=REPORT_SPECS["reports/segmentation/phase_9/Cluster_Profiles.csv"].columns,
    )
    stability = pd.DataFrame(
        [
            {"segment_id": segment, "march_count": np.nan, "june_count": np.nan, "march_percentage": np.nan, "june_percentage": np.nan}
            for segment in (0, 1, 2)
        ],
        columns=REPORT_SPECS["reports/segmentation/phase_9/Temporal_Stability_Report.csv"].columns,
    )
    clustering_rows = []
    for algorithm, offset in (("KMeans", 0.0), ("Agglomerative", 0.05)):
        for k in (3, 4, 5, 6):
            clustering_rows.append(
                {"algorithm": algorithm, "clusters": k, "silhouette": 0.7 - offset - (k - 3) * 0.02, "davies_bouldin": 0.6 + offset, "calinski_harabasz": 1000.0 / k, "noise": 0.0, "inertia": np.nan if algorithm == "Agglomerative" else 1000.0 / k}
            )
    classification_names = ("gradient_boosting", "random_forest", "logistic_regression", "decision_tree")
    classification = pd.DataFrame(
        [
            {"model_name": name, "accuracy": 0.70 + i * 0.01, "precision": 0.68, "recall": 0.69, "f1": 0.68 + i * 0.01, "roc_auc": 0.75, "average_precision": 0.76, "tn": 100.0, "fp": 100.0, "fn": 100.0, "tp": 100.0}
            for i, name in enumerate(classification_names)
        ],
        columns=REPORT_SPECS["reports/classification/phase_6/Model_comparison.csv"].columns,
    )
    regression_names = ("ridge_regression", "linear_regression", "random_forest", "gradient_boosting", "decision_tree", "hist_gradient_boosting", "dummy_mean")
    regression = pd.DataFrame(
        [
            {"model_name": name, "mae": 250.0 + i, "rmse": 400.0 + i, "r2": 0.6, "median_absolute_error": 100.0, "explained_variance": 0.61, "mape": 1.0, "zero_target_count": 100.0, "positive_target_count": 100.0, "zero_target_mae": 100.0, "positive_target_mae": 200.0, "exact_zero_predictions": 0.0, "negative_prediction_count": 1.0, "mean_prediction": 180.0, "median_prediction": 120.0, "training_seconds": 0.1}
            for i, name in enumerate(regression_names)
        ],
        columns=REPORT_SPECS["reports/regression/phase_7/Model_Comparison.csv"].columns,
    )
    classification_features = tuple(dict(REPORT_SPECS["reports/explainability/phase_9/Classification_Feature_Importance.csv"].allowed_values)["feature_name"])
    class_importance = pd.DataFrame(
        [{"feature_name": name, "importance": index / 20, "permutation_mean": index / 100, "permutation_std": 0.001} for index, name in enumerate(classification_features)],
        columns=REPORT_SPECS["reports/explainability/phase_9/Classification_Feature_Importance.csv"].columns,
    )
    regression_features = tuple(dict(REPORT_SPECS["reports/explainability/phase_9/Regression_Feature_Importance.csv"].allowed_values)["feature_name"])
    regression_importance = pd.DataFrame(
        [{"feature_name": name, "coefficient_abs": index * 10.0, "permutation_mean": index * 2.0, "permutation_std": 0.1} for index, name in enumerate(regression_features)],
        columns=REPORT_SPECS["reports/explainability/phase_9/Regression_Feature_Importance.csv"].columns,
    )
    recommendation_rows = []
    for method_index, method in enumerate(("popularity", "item_item", "customer_cf", "hybrid")):
        for k in (5, 10, 20):
            recommendation_rows.append({"method": method, "k": k, "precision": 0.1, "recall": 0.2, "map": 0.05 + method_index / 100, "ndcg": 0.1, "hit_rate": 0.3, "catalog_coverage": 0.4, "diversity": 0.5})
    return {
        "reports/segmentation/phase_9/Cluster_Profiles.csv": profiles,
        "reports/segmentation/phase_9/Temporal_Stability_Report.csv": stability,
        "reports/segmentation/phase_9/Clustering_Model_Comparison.csv": pd.DataFrame(clustering_rows, columns=REPORT_SPECS["reports/segmentation/phase_9/Clustering_Model_Comparison.csv"].columns),
        "reports/classification/phase_6/Model_comparison.csv": classification,
        "reports/regression/phase_7/Model_Comparison.csv": regression,
        "reports/explainability/phase_9/Classification_Feature_Importance.csv": class_importance,
        "reports/explainability/phase_9/Regression_Feature_Importance.csv": regression_importance,
        "reports/recommendation/phase_8/Recommendation_Metrics_By_K.csv": pd.DataFrame(recommendation_rows, columns=REPORT_SPECS["reports/recommendation/phase_8/Recommendation_Metrics_By_K.csv"].columns),
    }


class Phase1BAggregatePagesTest(unittest.TestCase):
    def test_all_three_pages_render_while_public_release_is_closed(self):
        for page in PAGE_REPORTS:
            with self.subTest(page=page), \
                 patch("src.ui.public_aggregate_pages.PUBLIC_AGGREGATES_RELEASED", False), \
                 patch.object(PublicAggregateService, "load_report", side_effect=AssertionError("closed release gate must prevent report reads")) as load_report:
                app = AppTest.from_file(str(ROOT / "pages" / page), default_timeout=30).run()
                self.assertEqual(app.exception, [])
                self.assertEqual(app.error, [])
                self.assertTrue(app.info)
                load_report.assert_not_called()

    def test_enabled_pages_load_only_their_explicit_allowlisted_reports_and_render_synthetic_data(self):
        synthetic = _synthetic_reports()
        for page, expected_paths in PAGE_REPORTS.items():
            calls = []

            def fake_load(path):
                calls.append(path)
                return synthetic[path].copy()

            with self.subTest(page=page), \
                 patch("src.ui.public_aggregate_pages.PUBLIC_AGGREGATES_RELEASED", True), \
                 patch.object(PublicAggregateService, "load_report", side_effect=fake_load), \
                 patch("pandas.read_csv", side_effect=AssertionError("page must not bypass the public aggregate service")):
                app = AppTest.from_file(str(ROOT / "pages" / page), default_timeout=30).run()
            self.assertEqual(app.exception, [])
            self.assertEqual(app.error, [])
            self.assertEqual(calls, list(expected_paths))

    def test_invalid_or_missing_aggregate_report_is_handled_without_traceback(self):
        for page in PAGE_REPORTS:
            with self.subTest(page=page), \
                 patch("src.ui.public_aggregate_pages.PUBLIC_AGGREGATES_RELEASED", True), \
                 patch.object(PublicAggregateService, "load_report", side_effect=PublicAggregateDataError("synthetic missing/invalid report")):
                app = AppTest.from_file(str(ROOT / "pages" / page), default_timeout=30).run()
            self.assertEqual(app.exception, [])
            self.assertTrue(app.warning)

    def test_suppressed_profile_and_temporal_values_are_not_reconstructed(self):
        synthetic = _synthetic_reports()
        profile_view = cluster_profile_view(synthetic["reports/segmentation/phase_9/Cluster_Profiles.csv"])
        self.assertEqual(list(profile_view.columns), ["segment_id", "average_historical_gross_spending", "median_historical_gross_spending", "average_invoice_frequency"])
        self.assertEqual(profile_view["segment_id"].tolist(), [2])
        self.assertNotIn("customer_count", profile_view.columns)
        self.assertNotIn("unique_customers", profile_view.columns)
        self.assertNotIn("percentage", profile_view.columns)

        temporal_view, available = temporal_stability_view(synthetic["reports/segmentation/phase_9/Temporal_Stability_Report.csv"])
        self.assertEqual(available, [])
        self.assertEqual(list(temporal_view.columns), ["segment_id"])
        tree = ast.parse((ROOT / "pages/06_Customer_Segments.py").read_text(encoding="utf-8"))
        sum_calls = [node for node in ast.walk(tree) if isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute) and node.func.attr == "sum"]
        self.assertEqual(sum_calls, [])

    def test_pages_do_not_import_customer_services_or_individual_report_names(self):
        forbidden_modules = {
            "src.services.historical_snapshot_service",
            "src.services.segmentation_service",
            "src.services.explanation_service",
            "src.services.recommendation_service",
            "src.services.repeat_purchase_service",
            "src.services.spending_prediction_service",
        }
        for page in PAGE_REPORTS:
            source = (ROOT / "pages" / page).read_text(encoding="utf-8")
            tree = ast.parse(source)
            imported = {
                node.module
                for node in ast.walk(tree)
                if isinstance(node, ast.ImportFrom)
            }
            self.assertTrue(imported.isdisjoint(forbidden_modules), page)
            self.assertNotIn("customer_id", source)
            self.assertNotIn("Customer ID", source)
            self.assertNotIn("Individual_Explanations.csv", source)
            self.assertNotIn("Customer_Segment_Assignments.csv", source)


if __name__ == "__main__":
    unittest.main()
