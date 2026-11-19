import unittest
from unittest.mock import patch

import pandas as pd

from src.config.settings import Settings
from src.services.repeat_purchase_service import RepeatPurchaseService
from src.services.spending_prediction_service import SpendingPredictionService
from src.utils.exceptions import UnknownCustomerError, UnsupportedCutoffError
from synthetic_fixtures import SYNTHETIC_CUSTOMER_ID, UNKNOWN_CUSTOMER_ID, SyntheticLoader, feature_frame


class Phase10EPredictionTest(unittest.TestCase):
    def setUp(self):
        self.settings = Settings()
        self.loader = SyntheticLoader()

    def test_repeat_known_march(self):
        frame = feature_frame(self.settings.classification_predictors, "2011-03-01")
        result = RepeatPurchaseService(settings=self.settings, loader=self.loader).predict(
            SYNTHETIC_CUSTOMER_ID, "2011-03-01", feature_frame=frame
        )
        self.assertEqual(result["predicted_repeat_purchase_status"], 1)
        self.assertAlmostEqual(result["positive_class_probability"], 0.7)

    def test_repeat_known_june(self):
        frame = feature_frame(self.settings.classification_predictors, "2011-06-01")
        result = RepeatPurchaseService(settings=self.settings, loader=self.loader).predict(
            SYNTHETIC_CUSTOMER_ID, "2011-06-01", feature_frame=frame
        )
        self.assertEqual(result["predicted_repeat_purchase_status"], 1)

    def test_spending_known_march(self):
        frame = feature_frame(self.settings.regression_predictors, "2011-03-01")
        result = SpendingPredictionService(settings=self.settings, loader=self.loader).predict(
            SYNTHETIC_CUSTOMER_ID, "2011-03-01", feature_frame=frame
        )
        self.assertEqual(result["predicted_future_gross_spending"], 42.0)

    def test_spending_known_june(self):
        frame = feature_frame(self.settings.regression_predictors, "2011-06-01")
        result = SpendingPredictionService(settings=self.settings, loader=self.loader).predict(
            SYNTHETIC_CUSTOMER_ID, "2011-06-01", feature_frame=frame
        )
        self.assertEqual(result["predicted_future_gross_spending"], 42.0)

    def test_unknown_repeat_customer(self):
        empty = feature_frame(self.settings.classification_predictors).iloc[0:0]
        with patch("src.services.repeat_purchase_service.pd.read_csv", return_value=empty):
            with self.assertRaises(UnknownCustomerError):
                RepeatPurchaseService(settings=self.settings, loader=self.loader).predict(UNKNOWN_CUSTOMER_ID, "2011-06-01")

    def test_unknown_spending_customer(self):
        empty = feature_frame(self.settings.regression_predictors).iloc[0:0]
        with patch("src.services.spending_prediction_service.pd.read_csv", return_value=empty):
            with self.assertRaises(UnknownCustomerError):
                SpendingPredictionService(settings=self.settings, loader=self.loader).predict(UNKNOWN_CUSTOMER_ID, "2011-06-01")

    def test_unsupported_repeat_cutoff(self):
        with self.assertRaises(UnsupportedCutoffError):
            RepeatPurchaseService(settings=self.settings, loader=self.loader).predict(SYNTHETIC_CUSTOMER_ID, "2011-09-10")

    def test_unsupported_spending_cutoff(self):
        with self.assertRaises(UnsupportedCutoffError):
            SpendingPredictionService(settings=self.settings, loader=self.loader).predict(SYNTHETIC_CUSTOMER_ID, "2011-09-10")


if __name__ == "__main__":
    unittest.main()
