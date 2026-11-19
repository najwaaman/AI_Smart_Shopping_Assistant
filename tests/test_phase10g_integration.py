import ast
from pathlib import Path
import unittest
from unittest.mock import patch

import pandas as pd

from src.config.settings import Settings
from src.services.analytics_service import AnalyticsService
from src.services.classification_service import ProductCategoryService
from src.services.explanation_service import ExplanationService
from src.services.historical_snapshot_service import HistoricalSnapshotService
from src.services.recommendation_service import RecommendationService
from src.services.repeat_purchase_service import RepeatPurchaseService
from src.services.segmentation_service import SegmentationService
from src.services.spending_prediction_service import SpendingPredictionService
from src.utils.exceptions import UnknownCustomerError, UnsupportedCutoffError, ValidationError
from synthetic_fixtures import (
    SYNTHETIC_CUSTOMER_ID, UNKNOWN_CUSTOMER_ID, SyntheticLoader, explanation_frame,
    feature_frame, importance_frame, insights_frame, recommendations_frame,
    segment_profile_frame, snapshot_frame,
)


ROOT = Path(__file__).resolve().parents[1]


class Phase10GIntegrationTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.settings = Settings()
        cls.loader = SyntheticLoader()
        cls.cat_service = ProductCategoryService(settings=cls.settings, loader=cls.loader)
        cls.rec_service = RecommendationService(settings=cls.settings)
        cls.rep_service = RepeatPurchaseService(settings=cls.settings, loader=cls.loader)
        cls.spd_service = SpendingPredictionService(settings=cls.settings, loader=cls.loader)
        cls.seg_service = SegmentationService(settings=cls.settings)
        cls.exp_service = ExplanationService(settings=cls.settings)
        cls.ana_service = AnalyticsService(settings=cls.settings)

    def _snapshot_read(self, path, *args, **kwargs):
        return snapshot_frame("2011-03-01" if "march_" in str(path) else "2011-06-01")

    def _recommendation_read(self, path, *args, **kwargs):
        return recommendations_frame()

    def _explanation_read(self, path, *args, **kwargs):
        name = str(path)
        if "Classification_Feature_Importance" in name:
            return importance_frame()
        if "Regression_Feature_Importance" in name:
            return importance_frame(regression=True)
        if "Classification_Individual_Explanations" in name:
            return explanation_frame()
        if "Regression_Individual_Explanations" in name:
            return explanation_frame(regression=True)
        raise AssertionError("Unexpected synthetic explanation path")

    def test_workflow_a_valid_classification(self):
        result = self.cat_service.predict("Lightweight cotton shirt for men, regular fit")
        self.assertEqual(result["prediction_status"], "valid")
        self.assertEqual(result["predicted_category"], "Clothing & Accessories")
        self.assertIsInstance(result["confidence_or_decision_score"], float)

    def test_workflow_a_empty_description(self):
        with self.assertRaises(ValidationError):
            self.cat_service.predict("")

    def test_workflow_a_whitespace_description(self):
        with self.assertRaises(ValidationError):
            self.cat_service.predict("    \n\t   ")

    def test_workflow_a_all_four_categories_smoke(self):
        cases = [
            ("cotton summer dress shirt for women", "Clothing & Accessories"),
            ("stainless steel kitchen cooking pot pan", "Household"),
            ("world history hardcover textbook biography", "Books"),
            ("wireless bluetooth headphones usb speaker", "Electronics"),
        ]
        for text, expected in cases:
            with self.subTest(category=expected):
                self.assertEqual(self.cat_service.predict(text)["predicted_category"], expected)

    def test_workflow_b_known_customer_june(self):
        with patch("src.services.recommendation_service.Path.is_file", return_value=True), \
             patch("src.services.recommendation_service.pd.read_csv", side_effect=self._recommendation_read):
            result = self.rec_service.recommendations(SYNTHETIC_CUSTOMER_ID, k=10, cutoff="2011-06-01")
        self.assertEqual(result["customer_id"], SYNTHETIC_CUSTOMER_ID)
        self.assertEqual(result["snapshot_cutoff"], "2011-06-01")
        self.assertEqual(len(result["recommendations"]), 10)
        codes = [item["StockCode"] for item in result["recommendations"]]
        self.assertEqual(len(codes), len(set(codes)))
        self.assertEqual([item["rank"] for item in result["recommendations"]], list(range(1, 11)))

    def test_workflow_b_unknown_customer(self):
        empty = recommendations_frame().iloc[0:0]
        with patch("src.services.recommendation_service.Path.is_file", return_value=True), \
             patch("src.services.recommendation_service.pd.read_csv", return_value=empty):
            with self.assertRaises(UnknownCustomerError):
                self.rec_service.recommendations(UNKNOWN_CUSTOMER_ID, k=5, cutoff="2011-06-01")

    def test_workflow_b_unsupported_march_cutoff(self):
        with self.assertRaises(UnsupportedCutoffError):
            self.rec_service.recommendations(SYNTHETIC_CUSTOMER_ID, k=5, cutoff="2011-03-01")

    def test_workflow_b_invalid_k(self):
        with self.assertRaises(ValidationError):
            self.rec_service.recommendations(SYNTHETIC_CUSTOMER_ID, k=7, cutoff="2011-06-01")

    def test_workflow_c_historical_cutoffs_use_synthetic_fixtures(self):
        with patch("src.services.historical_snapshot_service.Path.is_file", return_value=True), \
             patch("src.services.historical_snapshot_service.pd.read_csv", side_effect=self._snapshot_read):
            service = HistoricalSnapshotService(project_root=ROOT)
            march = service.get_customer(SYNTHETIC_CUSTOMER_ID, "2011-03-01")
            june = service.get_customer(SYNTHETIC_CUSTOMER_ID, "2011-06-01")
        self.assertEqual(int(march["historical_invoice_count"]), 2)
        self.assertEqual(float(march["historical_gross_spend"]), 18.0)
        self.assertEqual(int(june["historical_invoice_count"]), 3)
        self.assertEqual(float(june["historical_gross_spend"]), 42.5)

    def test_workflow_c_unknown_customer(self):
        with patch("src.services.historical_snapshot_service.Path.is_file", return_value=True), \
             patch("src.services.historical_snapshot_service.pd.read_csv", side_effect=self._snapshot_read):
            result = HistoricalSnapshotService(project_root=ROOT).get_customer(UNKNOWN_CUSTOMER_ID, "2011-06-01")
        self.assertIsNone(result)

    def test_workflow_d_repeat_prediction_march_and_june(self):
        for cutoff in ("2011-03-01", "2011-06-01"):
            frame = feature_frame(self.settings.classification_predictors, cutoff)
            result = self.rep_service.predict(SYNTHETIC_CUSTOMER_ID, cutoff, feature_frame=frame)
            self.assertEqual(result["predicted_repeat_purchase_status"], 1)
            self.assertAlmostEqual(result["positive_class_probability"], 0.7)

    def test_workflow_d_repeat_prediction_unknown_customer(self):
        empty = feature_frame(self.settings.classification_predictors).iloc[0:0]
        with patch("src.services.repeat_purchase_service.pd.read_csv", return_value=empty):
            with self.assertRaises(UnknownCustomerError):
                self.rep_service.predict(UNKNOWN_CUSTOMER_ID, "2011-06-01")

    def test_workflow_d_repeat_prediction_unsupported_cutoff(self):
        with self.assertRaises(UnsupportedCutoffError):
            self.rep_service.predict(SYNTHETIC_CUSTOMER_ID, "2011-09-10")

    def test_workflow_e_spending_prediction_march_and_june(self):
        for cutoff in ("2011-03-01", "2011-06-01"):
            frame = feature_frame(self.settings.regression_predictors, cutoff)
            result = self.spd_service.predict(SYNTHETIC_CUSTOMER_ID, cutoff, feature_frame=frame)
            self.assertEqual(result["predicted_future_gross_spending"], 42.0)
            self.assertIsNone(result["currency_label"])

    def test_workflow_e_spending_prediction_unknown_customer(self):
        empty = feature_frame(self.settings.regression_predictors).iloc[0:0]
        with patch("src.services.spending_prediction_service.pd.read_csv", return_value=empty):
            with self.assertRaises(UnknownCustomerError):
                self.spd_service.predict(UNKNOWN_CUSTOMER_ID, "2011-06-01")

    def test_workflow_e_negative_spending_disclosure(self):
        loader = SyntheticLoader(spending_value=-3.0)
        service = SpendingPredictionService(settings=self.settings, loader=loader)
        result = service.predict(
            SYNTHETIC_CUSTOMER_ID,
            "2011-06-01",
            feature_frame=feature_frame(self.settings.regression_predictors),
        )
        self.assertTrue(result["negative_prediction_warning"])
        self.assertEqual(result["predicted_future_gross_spending"], -3.0)

    def test_workflow_f_segmentation_known_cutoffs(self):
        for cutoff in ("2011-03-01", "2011-06-01"):
            with patch("src.services.segmentation_service.pd.read_csv", side_effect=lambda path, *a, **k: segment_profile_frame() if str(path).endswith("Cluster_Profiles.csv") else insights_frame()):
                result = self.seg_service.assign(SYNTHETIC_CUSTOMER_ID, cutoff)
            self.assertEqual(result["segment_id"], 0)
            self.assertEqual(result["model_name"], "KMeans")

    def test_workflow_f_segmentation_unknown_customer(self):
        with patch("src.services.segmentation_service.pd.read_csv", return_value=insights_frame().iloc[0:0]):
            with self.assertRaises(UnknownCustomerError):
                self.seg_service.assign(UNKNOWN_CUSTOMER_ID, "2011-06-01")

    def test_workflow_f_segmentation_unsupported_cutoff(self):
        with self.assertRaises(UnsupportedCutoffError):
            self.seg_service.assign(SYNTHETIC_CUSTOMER_ID, "2011-09-10")

    def test_workflow_g_global_feature_importance(self):
        with patch("pathlib.Path.is_file", return_value=True), \
             patch("src.services.explanation_service.pd.read_csv", side_effect=self._explanation_read):
            self.assertEqual(len(self.exp_service.get_global_importance("classification")), 15)
            self.assertEqual(len(self.exp_service.get_global_importance("regression")), 14)

    def test_workflow_g_individual_explanation_sample(self):
        with patch("pathlib.Path.is_file", return_value=True), \
             patch("src.services.explanation_service.pd.read_csv", side_effect=self._explanation_read):
            category = self.exp_service.get_individual("classification", SYNTHETIC_CUSTOMER_ID)
            spending = self.exp_service.get_individual("regression", SYNTHETIC_CUSTOMER_ID)
        self.assertEqual(category["customer_id"], SYNTHETIC_CUSTOMER_ID)
        self.assertIn("top_positive_feature", category)
        self.assertIn("top_negative_feature", category)
        self.assertIn("top_increasing_feature", spending)
        self.assertIn("top_decreasing_feature", spending)

    def test_workflow_g_individual_unknown_customer(self):
        with patch("pathlib.Path.is_file", return_value=True), \
             patch("src.services.explanation_service.pd.read_csv", side_effect=self._explanation_read):
            with self.assertRaises(UnknownCustomerError):
                self.exp_service.get_individual("classification", UNKNOWN_CUSTOMER_ID)

    def test_all_seven_pages_parse_cleanly(self):
        pages = sorted((ROOT / "pages").glob("*.py"))
        self.assertEqual(len(pages), 7)
        for page in pages:
            with self.subTest(page=page.name):
                self.assertIsInstance(ast.parse(page.read_text(encoding="utf-8")), ast.Module)

    def test_dashboard_analytics_match_synthetic_fixtures(self):
        def read(path, *args, **kwargs):
            return recommendations_frame() if "recommendations" in str(path) else insights_frame()
        with patch("src.services.analytics_service.pd.read_csv", side_effect=read):
            result = self.ana_service.dashboard_summary()
        self.assertEqual(result["total_unique_customers"], 1)
        self.assertEqual(result["total_customer_cutoff_records"], 2)
        self.assertEqual(result["total_recommendation_records"], 20)
        self.assertEqual(result["cutoff_counts"], {"2011-03-01": 1, "2011-06-01": 1})

    def test_no_unapproved_cutoff_in_page_controls(self):
        for page in (ROOT / "pages").glob("*.py"):
            text = page.read_text(encoding="utf-8")
            self.assertNotIn("2011-09-10", text)
            self.assertNotIn("september_holdout", text.lower())


if __name__ == "__main__":
    unittest.main()
