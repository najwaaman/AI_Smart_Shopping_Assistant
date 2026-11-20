"""Synthetic-only privacy and behavior tests for public demonstration pages."""

import ast
from pathlib import Path
import unittest
from unittest.mock import patch

import numpy as np
import pandas as pd
from streamlit.testing.v1 import AppTest

from src.services.public_aggregate_service import REPORT_SPECS, PublicAggregateDataError, PublicAggregateService
from src.ui.public_demo_logic import ILLUSTRATIVE_CATALOGUE, illustrative_recommendations, illustrative_threshold_met


ROOT = Path(__file__).resolve().parents[1]
PAGES = (
    "03_Product_Recommendations.py",
    "04_Customer_Intelligence.py",
    "05_Predictions.py",
)


def _synthetic_profile_reports():
    profiles = pd.DataFrame(
        [
            {"segment_id": 0, "customer_count": np.nan, "unique_customers": np.nan, "average_historical_gross_spending": np.nan, "median_historical_gross_spending": np.nan, "average_invoice_frequency": np.nan, "percentage": np.nan},
            {"segment_id": 1, "customer_count": np.nan, "unique_customers": np.nan, "average_historical_gross_spending": np.nan, "median_historical_gross_spending": np.nan, "average_invoice_frequency": np.nan, "percentage": np.nan},
            {"segment_id": 2, "customer_count": np.nan, "unique_customers": np.nan, "average_historical_gross_spending": 345.0, "median_historical_gross_spending": 240.0, "average_invoice_frequency": 3.5, "percentage": np.nan},
        ],
        columns=REPORT_SPECS["reports/segmentation/phase_9/Cluster_Profiles.csv"].columns,
    )
    stability = pd.DataFrame(
        [{"segment_id": segment, "march_count": np.nan, "june_count": np.nan, "march_percentage": np.nan, "june_percentage": np.nan} for segment in (0, 1, 2)],
        columns=REPORT_SPECS["reports/segmentation/phase_9/Temporal_Stability_Report.csv"].columns,
    )
    return profiles, stability


class Phase1CPublicDemosTest(unittest.TestCase):
    def test_pages_have_no_customer_lookup_or_customer_data_services(self):
        forbidden_modules = {
            "src.services.recommendation_service",
            "src.services.segmentation_service",
            "src.services.historical_snapshot_service",
            "src.services.repeat_purchase_service",
            "src.services.spending_prediction_service",
            "src.services.explanation_service",
        }
        for page in PAGES:
            with self.subTest(page=page):
                source = (ROOT / "pages" / page).read_text(encoding="utf-8")
                tree = ast.parse(source)
                imports = {node.module for node in ast.walk(tree) if isinstance(node, ast.ImportFrom)}
                self.assertTrue(imports.isdisjoint(forbidden_modules))
                self.assertNotIn("customer_id", source)
                self.assertNotIn("Customer ID", source)
                self.assertNotIn("customer_recommendations.csv", source)
                self.assertNotIn("customer_insights.csv", source)
                self.assertNotIn("march_training.csv", source)
                self.assertNotIn("june_validation.csv", source)

    def test_recommendation_demo_uses_fictional_cosine_logic(self):
        self.assertEqual(len(ILLUSTRATIVE_CATALOGUE), 6)
        result = illustrative_recommendations(["Comet Trail Mug", "Paperleaf Notebook"], limit=3)
        self.assertEqual(len(result), 3)
        self.assertTrue(all(0.0 <= row["illustrative_similarity"] <= 1.0 for row in result))
        self.assertTrue(all(row["product"] not in {"Comet Trail Mug", "Paperleaf Notebook"} for row in result))
        self.assertEqual(illustrative_recommendations(list(ILLUSTRATIVE_CATALOGUE), limit=3), [])
        with self.assertRaises(ValueError):
            illustrative_recommendations(["Not a fictional catalogue item"])

    def test_recommendation_page_is_interactive_and_marks_scores_illustrative(self):
        with patch("src.ui.public_aggregate_pages.PUBLIC_AGGREGATES_RELEASED", False), \
             patch.object(PublicAggregateService, "load_report", side_effect=PublicAggregateDataError("release pending")):
            app = AppTest.from_file(str(ROOT / "pages/03_Product_Recommendations.py"), default_timeout=30).run()
        self.assertEqual(app.exception, [])
        self.assertEqual(app.error, [])
        self.assertTrue(app.multiselect)
        self.assertTrue(app.get("plotly_chart"))
        self.assertTrue(any("Toy cosine similarities only" in element.value for element in app.caption))
        self.assertTrue(any("pending the Phase 1B" in element.value for element in app.info))

    def test_cohort_explorer_respects_closed_gate(self):
        with patch("src.ui.public_aggregate_pages.PUBLIC_AGGREGATES_RELEASED", False), \
             patch.object(PublicAggregateService, "load_report", side_effect=AssertionError("closed gate must not reach the service")) as load_report:
            app = AppTest.from_file(str(ROOT / "pages/04_Customer_Intelligence.py"), default_timeout=30).run()
        self.assertEqual(app.exception, [])
        self.assertEqual(app.error, [])
        self.assertTrue(app.selectbox)
        self.assertTrue(any("pending aggregate provenance and privacy approval" in element.value for element in app.info))
        load_report.assert_not_called()

    def test_cohort_explorer_uses_gate_and_keeps_suppressed_cells_unavailable(self):
        profiles, stability = _synthetic_profile_reports()
        calls = []

        def fake_load(path):
            calls.append(path)
            return profiles.copy() if path.endswith("Cluster_Profiles.csv") else stability.copy()

        with patch("src.ui.public_aggregate_pages.PUBLIC_AGGREGATES_RELEASED", True), \
             patch.object(PublicAggregateService, "load_report", side_effect=fake_load), \
             patch("pandas.read_csv", side_effect=AssertionError("page must not bypass aggregate service")):
            app = AppTest.from_file(str(ROOT / "pages/04_Customer_Intelligence.py"), default_timeout=30).run()
        self.assertEqual(app.exception, [])
        self.assertEqual(app.error, [])
        self.assertEqual(calls, [
            "reports/segmentation/phase_9/Cluster_Profiles.csv",
            "reports/segmentation/phase_9/Temporal_Stability_Report.csv",
        ])
        self.assertTrue(any("No comparison values or totals have been reconstructed" in element.value for element in app.info))
        self.assertNotIn("customer_count", (ROOT / "pages/04_Customer_Intelligence.py").read_text(encoding="utf-8"))

    def test_synthetic_threshold_demo_is_explicit_rule_not_model_prediction(self):
        self.assertTrue(illustrative_threshold_met(4, 3))
        self.assertFalse(illustrative_threshold_met(2, 3))
        with self.assertRaises(ValueError):
            illustrative_threshold_met(True, 3)

        with patch("src.models.model_loader.ModelLoader.load", side_effect=AssertionError("public demo must not load a model")), \
             patch("pandas.read_csv", side_effect=AssertionError("public demo must not load datasets")):
            app = AppTest.from_file(str(ROOT / "pages/05_Predictions.py"), default_timeout=30).run()
        self.assertEqual(app.exception, [])
        self.assertEqual(app.error, [])
        self.assertGreaterEqual(len(app.slider), 5)
        self.assertTrue(any("No prediction is generated" in element.value for element in app.info))
        self.assertTrue(any("not been approved for public inference" in element.value for element in app.warning))

    def test_aggregate_report_failure_is_graceful_on_demo_pages(self):
        for page in ("03_Product_Recommendations.py", "04_Customer_Intelligence.py"):
            with self.subTest(page=page), \
                 patch("src.ui.public_aggregate_pages.PUBLIC_AGGREGATES_RELEASED", True), \
                 patch.object(PublicAggregateService, "load_report", side_effect=PublicAggregateDataError("synthetic missing or invalid report")):
                app = AppTest.from_file(str(ROOT / "pages" / page), default_timeout=30).run()
            self.assertEqual(app.exception, [])
            if page == "03_Product_Recommendations.py":
                self.assertTrue(app.info)
            else:
                self.assertTrue(app.warning)

    def test_all_seven_pages_and_navigation_remain_registered(self):
        expected = [f"pages/{number:02d}_" for number in range(1, 8)]
        app_source = (ROOT / "app.py").read_text(encoding="utf-8")
        self.assertEqual(app_source.count("st.Page("), 7)
        for prefix in expected:
            with self.subTest(prefix=prefix):
                self.assertIn(prefix, app_source)
        for page in (ROOT / "pages").glob("*.py"):
            with self.subTest(page=page.name):
                self.assertIsInstance(ast.parse(page.read_text(encoding="utf-8")), ast.Module)

    def test_all_seven_page_scripts_render_without_private_runtime_reads(self):
        for page in sorted((ROOT / "pages").glob("*.py")):
            with self.subTest(page=page.name), \
                 patch("src.config.settings.Settings") as settings, \
                 patch("src.ui.public_aggregate_pages.PUBLIC_AGGREGATES_RELEASED", False), \
                 patch("pandas.read_csv", side_effect=AssertionError("page smoke test must not read CSVs")), \
                 patch("src.models.model_loader.ModelLoader.load", side_effect=AssertionError("page smoke test must not load model files")):
                settings.return_value.category_model.is_file.return_value = False
                app = AppTest.from_file(str(page), default_timeout=30).run()
            self.assertEqual(app.exception, [])
            self.assertEqual(app.error, [])


if __name__ == "__main__":
    unittest.main()
