import pandas as pd
import unittest

from src.config.settings import Settings
from src.preprocessing.input_validation import validate_text, validate_customer_id, validate_cutoff, validate_feature_frame
from src.utils.exceptions import ValidationError, UnsupportedCutoffError


class InputValidationTest(unittest.TestCase):
    def test_empty_text_rejected(self):
        with self.assertRaises(ValidationError):
            validate_text("   ")

    def test_invalid_customer_id_rejected(self):
        with self.assertRaises(ValidationError):
            validate_customer_id("unknown")

    def test_supported_cutoff(self):
        self.assertEqual(validate_cutoff("2011-06-01", Settings().approved_cutoffs), "2011-06-01")

    def test_unsupported_cutoff_rejected(self):
        with self.assertRaises(UnsupportedCutoffError):
            validate_cutoff("2011-09-10", Settings().approved_cutoffs)

    def test_target_column_rejected_as_predictor(self):
        frame = pd.DataFrame([[1.0, 0]], columns=["feature_a", "repeat_purchase_90d"])
        with self.assertRaises(ValidationError):
            validate_feature_frame(frame, ["feature_a"], {"repeat_purchase_90d"})


if __name__ == "__main__":
    unittest.main()
