"""Synthetic-only regression tests for fail-closed public page behavior."""

from pathlib import Path
import unittest
from unittest.mock import patch

from streamlit.testing.v1 import AppTest

from src.services.public_aggregate_service import PublicAggregateService
from src.utils.exceptions import ModelLoadError
from src.ui.public_aggregate_pages import PUBLIC_AGGREGATES_RELEASED


ROOT = Path(__file__).resolve().parents[1]
CLASSIFICATION_PAGE = ROOT / "pages" / "02_Product_Classification.py"
UNAVAILABLE_MESSAGE = (
    "Product Classification is temporarily unavailable while its model is being prepared for public access."
)


class _UnavailableArtifact:
    def is_file(self):
        return False


class _AvailableArtifact:
    def is_file(self):
        return True


class _FakeSettings:
    def __init__(self, artifact):
        self.category_model = artifact


def _visible_messages(app):
    return [
        str(element.value)
        for group in (app.info, app.warning, app.error, app.success, app.exception)
        for element in group
    ]


class Phase1D2PublicFallbackTest(unittest.TestCase):
    def test_missing_classifier_artifact_shows_safe_unavailable_state(self):
        with patch("src.config.settings.Settings", return_value=_FakeSettings(_UnavailableArtifact())), \
             patch("src.services.classification_service.ProductCategoryService.predict", side_effect=AssertionError("classifier must not be invoked when its artifact is absent")) as predict, \
             patch("src.models.model_loader.ModelLoader.load", side_effect=AssertionError("missing artifact must not be loaded")) as load:
            app = AppTest.from_file(str(CLASSIFICATION_PAGE), default_timeout=30).run()

        self.assertEqual(app.exception, [])
        self.assertTrue(any(UNAVAILABLE_MESSAGE == item.value for item in app.info))
        self.assertFalse(any(item.value == "Prediction result" for item in app.subheader))
        self.assertEqual(app.metric, [])
        self.assertFalse(any("C:\\" in text or ".joblib" in text or "ModelLoadError" in text or "Traceback" in text for text in _visible_messages(app)))
        predict.assert_not_called()
        load.assert_not_called()

    def test_classifier_load_failure_is_sanitized_and_returns_no_prediction(self):
        private_path = r"C:\private\model-store\classification\internal-model.joblib"
        with patch("src.config.settings.Settings", return_value=_FakeSettings(_AvailableArtifact())), \
             patch("src.services.classification_service.ProductCategoryService.predict", side_effect=ModelLoadError(f"Required model artifact does not exist: {private_path}")), \
             patch("src.models.model_loader.ModelLoader.load", side_effect=ModelLoadError(f"Required model artifact does not exist: {private_path}")):
            app = AppTest.from_file(str(CLASSIFICATION_PAGE), default_timeout=30).run()
            app.text_area[0].set_value("Synthetic cotton shirt description")
            app.button[0].click()
            app.run()

        messages = _visible_messages(app)
        self.assertEqual(app.exception, [])
        self.assertIn(UNAVAILABLE_MESSAGE, messages)
        self.assertFalse(any(private_path in text or ".joblib" in text or "ModelLoadError" in text or "Traceback" in text for text in messages))
        self.assertFalse(any(item.value == "Prediction result" for item in app.subheader))
        self.assertEqual(app.metric, [])

    def test_aggregate_gate_is_closed_and_values_remain_hidden_pending_review(self):
        self.assertFalse(PUBLIC_AGGREGATES_RELEASED)
        aggregate_pages = (
            "01_Overview.py",
            "03_Product_Recommendations.py",
            "04_Customer_Intelligence.py",
            "06_Customer_Segments.py",
            "07_Model_Insights.py",
        )
        with patch("src.ui.public_aggregate_pages.PUBLIC_AGGREGATES_RELEASED", False), \
             patch.object(PublicAggregateService, "load_report", side_effect=AssertionError("pending aggregate reports must not be loaded")) as load_report, \
             patch("pandas.read_csv", side_effect=AssertionError("public page must not read CSV files")):
            for page in aggregate_pages:
                with self.subTest(page=page):
                    app = AppTest.from_file(str(ROOT / "pages" / page), default_timeout=30).run()
                    self.assertEqual(app.exception, [])
                    self.assertEqual(app.error, [])
                    visible = " ".join(_visible_messages(app))
                    self.assertRegex(visible.casefold(), r"pending|withheld|not displayed")
            load_report.assert_not_called()

    def test_all_seven_pages_render_without_project_csv_or_model_reads(self):
        pages = sorted((ROOT / "pages").glob("*.py"))
        self.assertEqual(len(pages), 7)
        with patch("src.config.settings.Settings", return_value=_FakeSettings(_UnavailableArtifact())), \
             patch("src.ui.public_aggregate_pages.PUBLIC_AGGREGATES_RELEASED", False), \
             patch.object(PublicAggregateService, "load_report", side_effect=AssertionError("aggregate gate must block report access")), \
             patch("pandas.read_csv", side_effect=AssertionError("public pages must not read project CSV files")), \
             patch("src.models.model_loader.ModelLoader.load", side_effect=AssertionError("public pages must not load private model files")):
            for page in pages:
                with self.subTest(page=page.name):
                    app = AppTest.from_file(str(page), default_timeout=30).run()
                    self.assertEqual(app.exception, [])
                    self.assertEqual(app.error, [])


if __name__ == "__main__":
    unittest.main()
