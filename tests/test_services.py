import unittest
from unittest.mock import patch

import pandas as pd

from src.config.settings import Settings
from src.services.analytics_service import AnalyticsService
from src.services.classification_service import ProductCategoryService
from src.services.recommendation_service import RecommendationService
from src.services.repeat_purchase_service import RepeatPurchaseService
from src.services.segmentation_service import SegmentationService
from src.services.spending_prediction_service import SpendingPredictionService
from src.utils.exceptions import UnknownCustomerError, UnsupportedCutoffError, ValidationError
from synthetic_fixtures import (
    SYNTHETIC_CUSTOMER_ID, UNKNOWN_CUSTOMER_ID, SyntheticLoader, feature_frame,
    insights_frame, recommendations_frame, segment_profile_frame,
)


class BackendServiceTest(unittest.TestCase):
    def setUp(self):
        self.settings = Settings()
        self.loader = SyntheticLoader()

    def test_valid_category_prediction(self):
        result = ProductCategoryService(settings=self.settings, loader=self.loader).predict("red cotton dress")
        self.assertEqual(result["prediction_status"], "valid")
        self.assertEqual(result["predicted_category"], "Clothing & Accessories")

    def test_invalid_category_text(self):
        with self.assertRaises(ValidationError):
            ProductCategoryService(settings=self.settings, loader=self.loader).predict("   ")

    def test_repeat_prediction(self):
        frame = feature_frame(self.settings.classification_predictors)
        result = RepeatPurchaseService(settings=self.settings, loader=self.loader).predict(
            SYNTHETIC_CUSTOMER_ID, feature_frame=frame
        )
        self.assertEqual(result["predicted_repeat_purchase_status"], 1)
        self.assertAlmostEqual(result["positive_class_probability"], 0.7)

    def test_spending_prediction(self):
        frame = feature_frame(self.settings.regression_predictors)
        result = SpendingPredictionService(settings=self.settings, loader=self.loader).predict(
            SYNTHETIC_CUSTOMER_ID, feature_frame=frame
        )
        self.assertEqual(result["predicted_future_gross_spending"], 42.0)
        self.assertIsNone(result["currency_label"])

    def test_recommendation(self):
        with patch("src.services.recommendation_service.Path.is_file", return_value=True), \
             patch("src.services.recommendation_service.pd.read_csv", return_value=recommendations_frame()):
            result = RecommendationService(settings=self.settings).recommendations(
                SYNTHETIC_CUSTOMER_ID, k=5, cutoff="2011-06-01"
            )
        self.assertEqual(len(result["recommendations"]), 5)

    def test_unknown_recommendation_customer(self):
        empty = recommendations_frame().iloc[0:0]
        with patch("src.services.recommendation_service.Path.is_file", return_value=True), \
             patch("src.services.recommendation_service.pd.read_csv", return_value=empty):
            with self.assertRaises(UnknownCustomerError):
                RecommendationService(settings=self.settings).recommendations(
                    UNKNOWN_CUSTOMER_ID, k=5, cutoff="2011-06-01"
                )

    def test_segmentation_lookup(self):
        def synthetic_read(path, *args, **kwargs):
            return segment_profile_frame() if str(path).endswith("Cluster_Profiles.csv") else insights_frame()
        with patch("src.services.segmentation_service.pd.read_csv", side_effect=synthetic_read):
            result = SegmentationService(settings=self.settings).assign(SYNTHETIC_CUSTOMER_ID, "2011-06-01")
        self.assertEqual(result["segment_id"], 0)

    def test_unsupported_cutoff(self):
        with self.assertRaises(UnsupportedCutoffError):
            RepeatPurchaseService(settings=self.settings, loader=self.loader).predict(
                SYNTHETIC_CUSTOMER_ID, "2011-09-10", feature_frame=feature_frame(self.settings.classification_predictors)
            )

    def test_analytics_summary_uses_synthetic_frames(self):
        def synthetic_read(path, *args, **kwargs):
            return recommendations_frame() if "recommendations" in str(path) else insights_frame()
        with patch("src.services.analytics_service.pd.read_csv", side_effect=synthetic_read):
            result = AnalyticsService(settings=self.settings).dashboard_summary()
        self.assertEqual(result["total_unique_customers"], 1)
        self.assertEqual(result["total_customer_cutoff_records"], 2)


if __name__ == "__main__":
    unittest.main()
