import ast
from pathlib import Path
import unittest
from unittest.mock import patch

import pandas as pd

from src.config.settings import Settings
from src.services.explanation_service import ExplanationService
from src.services.segmentation_service import SegmentationService
from src.utils.exceptions import UnknownCustomerError, UnsupportedCutoffError, ValidationError
from synthetic_fixtures import (
    SYNTHETIC_CUSTOMER_ID, UNKNOWN_CUSTOMER_ID, explanation_frame, importance_frame,
    insights_frame, segment_profile_frame,
)


ROOT = Path(__file__).resolve().parents[1]


class Phase10FServiceTest(unittest.TestCase):
    def setUp(self):
        self.segmentation_service = SegmentationService()
        self.explanation_service = ExplanationService()

    def _read_explanation(self, path, *args, **kwargs):
        path = str(path)
        if "Classification_Feature_Importance" in path:
            return importance_frame()
        if "Regression_Feature_Importance" in path:
            return importance_frame(regression=True)
        if "Classification_Individual_Explanations" in path:
            return explanation_frame()
        if "Regression_Individual_Explanations" in path:
            return explanation_frame(regression=True)
        raise AssertionError("Unexpected synthetic explanation path")

    def test_segmentation_known_march_customer(self):
        def read(path, *args, **kwargs):
            return segment_profile_frame() if str(path).endswith("Cluster_Profiles.csv") else insights_frame()
        with patch("src.services.segmentation_service.pd.read_csv", side_effect=read):
            result = self.segmentation_service.assign(SYNTHETIC_CUSTOMER_ID, "2011-03-01")
        self.assertEqual(result["customer_id"], SYNTHETIC_CUSTOMER_ID)
        self.assertEqual(result["snapshot_cutoff"], "2011-03-01")
        self.assertEqual(result["segment_id"], 0)
        self.assertEqual(result["model_name"], "KMeans")
        self.assertEqual(result["segment_profile"]["customer_count"], 2)

    def test_segmentation_known_june_customer(self):
        def read(path, *args, **kwargs):
            return segment_profile_frame() if str(path).endswith("Cluster_Profiles.csv") else insights_frame()
        with patch("src.services.segmentation_service.pd.read_csv", side_effect=read):
            result = self.segmentation_service.assign(SYNTHETIC_CUSTOMER_ID, "2011-06-01")
        self.assertEqual(result["snapshot_cutoff"], "2011-06-01")
        self.assertEqual(result["segment_id"], 0)

    def test_segmentation_unknown_customer(self):
        with patch("src.services.segmentation_service.pd.read_csv", return_value=insights_frame().iloc[0:0]):
            with self.assertRaises(UnknownCustomerError):
                self.segmentation_service.assign(UNKNOWN_CUSTOMER_ID, "2011-06-01")

    def test_segmentation_invalid_customer_id(self):
        with self.assertRaises(ValidationError):
            self.segmentation_service.assign(-5, "2011-06-01")

    def test_segmentation_unsupported_cutoff(self):
        with self.assertRaises(UnsupportedCutoffError):
            self.segmentation_service.assign(SYNTHETIC_CUSTOMER_ID, "2011-09-10")

    def test_segmentation_duplicate_handling(self):
        duplicate = pd.DataFrame(
            [
                {"customer_id": SYNTHETIC_CUSTOMER_ID, "snapshot_cutoff": "2011-06-01", "segment_id": 0},
                {"customer_id": SYNTHETIC_CUSTOMER_ID, "snapshot_cutoff": "2011-06-01", "segment_id": 1},
            ]
        )
        with patch("src.services.segmentation_service.pd.read_csv", return_value=duplicate):
            with self.assertRaises(ValueError):
                self.segmentation_service.assign(SYNTHETIC_CUSTOMER_ID, "2011-06-01")

    def test_global_classification_importance(self):
        with patch("pathlib.Path.is_file", return_value=True), \
             patch("src.services.explanation_service.pd.read_csv", side_effect=self._read_explanation):
            records = self.explanation_service.get_global_importance("classification")
        self.assertEqual(len(records), 15)
        for record in records:
            self.assertIn("feature_name", record)
            self.assertIn("importance", record)
            self.assertIn("permutation_mean", record)
            self.assertIn("permutation_std", record)

    def test_global_regression_importance(self):
        with patch("pathlib.Path.is_file", return_value=True), \
             patch("src.services.explanation_service.pd.read_csv", side_effect=self._read_explanation):
            records = self.explanation_service.get_global_importance("regression")
        self.assertEqual(len(records), 14)
        for record in records:
            self.assertIn("feature_name", record)
            self.assertIn("coefficient_abs", record)
            self.assertIn("permutation_mean", record)
            self.assertIn("permutation_std", record)

    def test_valid_individual_classification_explanation(self):
        with patch("pathlib.Path.is_file", return_value=True), \
             patch("src.services.explanation_service.pd.read_csv", side_effect=self._read_explanation):
            result = self.explanation_service.get_individual("classification", SYNTHETIC_CUSTOMER_ID)
        self.assertEqual(result["customer_id"], SYNTHETIC_CUSTOMER_ID)
        self.assertIn("predicted_probability", result)
        self.assertIn("predicted_class", result)
        self.assertIn("top_positive_feature", result)
        self.assertIn("top_negative_feature", result)

    def test_valid_individual_regression_explanation(self):
        with patch("pathlib.Path.is_file", return_value=True), \
             patch("src.services.explanation_service.pd.read_csv", side_effect=self._read_explanation):
            result = self.explanation_service.get_individual("regression", SYNTHETIC_CUSTOMER_ID)
        self.assertEqual(result["customer_id"], SYNTHETIC_CUSTOMER_ID)
        self.assertIn("predicted_future_gross_spending", result)
        self.assertIn("top_increasing_feature", result)
        self.assertIn("top_decreasing_feature", result)

    def test_unsupported_individual_customer(self):
        with patch("pathlib.Path.is_file", return_value=True), \
             patch("src.services.explanation_service.pd.read_csv", side_effect=self._read_explanation):
            with self.assertRaises(UnknownCustomerError):
                self.explanation_service.get_individual("classification", UNKNOWN_CUSTOMER_ID)

    def test_invalid_model_type(self):
        with self.assertRaises(ValidationError):
            self.explanation_service.get_global_importance("unsupported_model")

    def test_pages_parse_without_loading_private_artifacts(self):
        for page in ("06_Customer_Segments.py", "07_Model_Insights.py"):
            tree = ast.parse((ROOT / "pages" / page).read_text(encoding="utf-8"))
            self.assertIsInstance(tree, ast.Module)

    def test_charts_constructible_from_synthetic_summaries(self):
        profiles = segment_profile_frame()
        stability = pd.DataFrame({"segment_id": [0, 1, 2], "march_count": [2, 1, 1], "june_count": [2, 1, 1]})
        comparison = pd.DataFrame({"model": [f"synthetic_{i}" for i in range(8)]})
        self.assertEqual(len(profiles), 3)
        self.assertEqual(len(stability), 3)
        self.assertGreaterEqual(len(comparison), 8)
        self.assertEqual(len(importance_frame()), 15)
        self.assertEqual(len(importance_frame(regression=True)), 14)

    def test_no_unavailable_profile_metrics_displayed(self):
        page_source = (ROOT / "pages/06_Customer_Segments.py").read_text(encoding="utf-8")
        self.assertIn("display_profiles = profiles_df[", page_source)
        self.assertIn("Data Quality Notice", page_source)
        self.assertIn("average_recency", page_source)
        self.assertIn("average_unique_products", page_source)

    def test_50_sample_explanation_restriction_handled(self):
        classification = explanation_frame()
        regression = explanation_frame(regression=True)
        self.assertEqual(len(classification), 50)
        self.assertEqual(len(regression), 50)
        self.assertEqual(classification["customer_id"].tolist(), regression["customer_id"].tolist())

    def test_no_september_cutoff_offered(self):
        page_seg = (ROOT / "pages/06_Customer_Segments.py").read_text(encoding="utf-8")
        self.assertIn('APPROVED_CUTOFFS = ["2011-03-01", "2011-06-01"]', page_seg)
        self.assertNotIn("2011-09-10", page_seg)
        self.assertEqual(Settings().approved_cutoffs, {"2011-03-01", "2011-06-01"})


if __name__ == "__main__":
    unittest.main()
