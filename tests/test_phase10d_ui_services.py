import unittest
from unittest.mock import patch

from src.config.settings import Settings
from src.services.classification_service import ProductCategoryService
from src.services.recommendation_service import RecommendationService
from src.utils.exceptions import UnknownCustomerError, UnsupportedCutoffError, ValidationError
from synthetic_fixtures import SYNTHETIC_CUSTOMER_ID, UNKNOWN_CUSTOMER_ID, SyntheticLoader, recommendations_frame


class Phase10DUITest(unittest.TestCase):
    def setUp(self):
        self.settings = Settings()
        self.loader = SyntheticLoader()

    def test_known_category_result(self):
        result = ProductCategoryService(settings=self.settings, loader=self.loader).predict("wireless bluetooth headphones")
        self.assertEqual(result["predicted_category"], "Electronics")

    def test_all_known_category_smoke_inputs(self):
        inputs = ["steel cookware household", "history novel books", "cotton shirt clothing", "smartphone electronics"]
        for text in inputs:
            result = ProductCategoryService(settings=self.settings, loader=self.loader).predict(text)
            self.assertIn(result["predicted_category"], self.loader.load(self.settings.category_model).classes_)

    def test_invalid_text(self):
        with self.assertRaises(ValidationError):
            ProductCategoryService(settings=self.settings, loader=self.loader).predict("   ")

    def test_known_recommendation_customer(self):
        with patch("src.services.recommendation_service.Path.is_file", return_value=True), \
             patch("src.services.recommendation_service.pd.read_csv", return_value=recommendations_frame()):
            result = RecommendationService(settings=self.settings).recommendations(
                SYNTHETIC_CUSTOMER_ID, k=5, cutoff="2011-06-01"
            )
        self.assertEqual(len(result["recommendations"]), 5)
        codes = [item["StockCode"] for item in result["recommendations"]]
        self.assertEqual(len(codes), len(set(codes)))

    def test_unknown_recommendation_customer(self):
        empty = recommendations_frame().iloc[0:0]
        with patch("src.services.recommendation_service.Path.is_file", return_value=True), \
             patch("src.services.recommendation_service.pd.read_csv", return_value=empty):
            with self.assertRaises(UnknownCustomerError):
                RecommendationService(settings=self.settings).recommendations(
                    UNKNOWN_CUSTOMER_ID, k=10, cutoff="2011-06-01"
                )

    def test_march_recommendation_cutoff_rejected(self):
        with self.assertRaises(UnsupportedCutoffError):
            RecommendationService(settings=self.settings).recommendations(
                SYNTHETIC_CUSTOMER_ID, k=10, cutoff="2011-03-01"
            )

    def test_invalid_recommendation_count(self):
        with self.assertRaises(ValidationError):
            RecommendationService(settings=self.settings).recommendations(
                SYNTHETIC_CUSTOMER_ID, k=7, cutoff="2011-06-01"
            )


if __name__ == "__main__":
    unittest.main()
