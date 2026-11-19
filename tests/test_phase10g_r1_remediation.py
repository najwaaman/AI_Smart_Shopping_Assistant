import ast
import unittest
from pathlib import Path
from unittest.mock import patch

import pandas as pd

from src.config.settings import Settings
from src.services.classification_service import ProductCategoryService
from src.services.recommendation_service import RecommendationService
from src.services.repeat_purchase_service import RepeatPurchaseService
from src.services.segmentation_service import SegmentationService
from src.services.spending_prediction_service import SpendingPredictionService
from src.services.historical_snapshot_service import HistoricalSnapshotService
from src.ui.components import escape_html_text
from src.utils.exceptions import UnknownCustomerError, ValidationError
from synthetic_fixtures import (
    SYNTHETIC_CUSTOMER_ID, UNKNOWN_CUSTOMER_ID, SyntheticCategoryModel, SyntheticLoader,
    feature_frame, insights_frame, recommendations_frame, segment_profile_frame, snapshot_frame,
)


ROOT = Path(__file__).resolve().parents[1]
APPROVED_CATEGORIES = {"Books", "Clothing & Accessories", "Electronics", "Household"}


class Phase10GRemediationTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.settings = Settings()
        cls.loader = SyntheticLoader()
        cls.service = ProductCategoryService(settings=cls.settings, loader=cls.loader)
        cls.model = SyntheticCategoryModel()

    def test_service_uses_provenance_selected_linear_svm(self):
        self.assertEqual(
            self.settings.category_model,
            ROOT / "models/classification/comparison/linear_svm_tfidf.joblib",
        )
        self.assertEqual(set(self.model.classes_), APPROVED_CATEGORIES)
        page = ast.parse((ROOT / "pages/02_Product_Classification.py").read_text(encoding="utf-8"))
        category_keys = set()
        for node in ast.walk(page):
            if isinstance(node, ast.Assign) and any(
                isinstance(target, ast.Name) and target.id == "CATEGORY_ACCENTS"
                for target in node.targets
            ) and isinstance(node.value, ast.Dict):
                category_keys = {key.value for key in node.value.keys if isinstance(key, ast.Constant)}
                break
        self.assertEqual(category_keys, set(self.model.classes_))

    def test_exact_example_service_matches_selected_pipeline(self):
        text = "VINTAGE UNION JACK CUSHION COVER"
        self.assertEqual(
            self.service.predict(text)["predicted_category"],
            str(self.model.predict([text])[0]),
        )
        self.assertEqual(self.service.predict(text)["model_name"], "linear_svm_tfidf")

    def test_representative_category_inputs_match_raw_model(self):
        texts = [
            "world history hardcover novel book",
            "cotton summer dress shirt clothing",
            "wireless bluetooth headphones electronics",
            "stainless steel kitchen cooking pot household",
        ]
        for text in texts:
            with self.subTest(text=text):
                raw = str(self.model.predict([text])[0])
                result = self.service.predict(text)
                self.assertEqual(result["predicted_category"], raw)
                self.assertIn(result["predicted_category"], APPROVED_CATEGORIES)

    def test_empty_and_whitespace_text_are_rejected(self):
        for text in ("", " \n\t "):
            with self.subTest(text=repr(text)):
                with self.assertRaises(ValidationError):
                    self.service.predict(text)

    def test_output_escaping_for_dataset_text(self):
        self.assertEqual(escape_html_text('<img src=x onerror="alert(1)">'),
                         "&lt;img src=x onerror=&quot;alert(1)&quot;&gt;")

    def test_unknown_recommendation_is_reported_without_substitution(self):
        with patch("src.services.recommendation_service.Path.is_file", return_value=True), \
             patch("src.services.recommendation_service.pd.read_csv", return_value=recommendations_frame().iloc[0:0]):
            with self.assertRaises(UnknownCustomerError):
                RecommendationService(settings=self.settings).recommendations(UNKNOWN_CUSTOMER_ID, k=5, cutoff="2011-06-01")

    def test_synthetic_customer_cutoffs_match_services(self):
        def snapshot_read(path, *args, **kwargs):
            return snapshot_frame("2011-03-01" if "march_" in str(path) else "2011-06-01")

        with patch("src.services.historical_snapshot_service.Path.is_file", return_value=True), \
             patch("src.services.historical_snapshot_service.pd.read_csv", side_effect=snapshot_read):
            snapshot_service = HistoricalSnapshotService(project_root=ROOT)
            snapshots = {cutoff: snapshot_service.get_customer(SYNTHETIC_CUSTOMER_ID, cutoff) for cutoff in ("2011-03-01", "2011-06-01")}

        for cutoff, expected in {"2011-03-01": (2, 18.0, 6), "2011-06-01": (3, 42.5, 12)}.items():
            with self.subTest(cutoff=cutoff):
                snapshot = snapshots[cutoff]
                self.assertEqual(int(snapshot.historical_invoice_count), expected[0])
                self.assertEqual(float(snapshot.historical_gross_spend), expected[1])
                self.assertEqual(int(snapshot.historical_total_quantity), expected[2])
                repeat = RepeatPurchaseService(settings=self.settings, loader=self.loader).predict(
                    SYNTHETIC_CUSTOMER_ID, cutoff, feature_frame=feature_frame(self.settings.classification_predictors, cutoff)
                )
                spending = SpendingPredictionService(settings=self.settings, loader=self.loader).predict(
                    SYNTHETIC_CUSTOMER_ID, cutoff, feature_frame=feature_frame(self.settings.regression_predictors, cutoff)
                )
                with patch("src.services.segmentation_service.pd.read_csv", side_effect=lambda path, *a, **k: segment_profile_frame() if str(path).endswith("Cluster_Profiles.csv") else insights_frame()):
                    segment = SegmentationService(settings=self.settings).assign(SYNTHETIC_CUSTOMER_ID, cutoff)
                self.assertEqual(repeat["positive_class_probability"], 0.7)
                self.assertEqual(spending["predicted_future_gross_spending"], 42.0)
                self.assertEqual(segment["segment_id"], 0)
                self.assertIsNone(spending["currency_label"])


if __name__ == "__main__":
    unittest.main()
