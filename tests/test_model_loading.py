import tempfile
import unittest
from pathlib import Path

import joblib

from src.models.model_loader import ModelLoader
from src.utils.exceptions import ModelLoadError


class ModelLoadingTest(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.path = Path(self.temp.name) / "synthetic_model.joblib"
        joblib.dump({"fixture_kind": "synthetic"}, self.path)
        self.loader = ModelLoader()

    def tearDown(self):
        self.temp.cleanup()

    def test_repeat_model_fixture_loads(self):
        self.assertEqual(self.loader.load(self.path), {"fixture_kind": "synthetic"})

    def test_spending_model_fixture_loads(self):
        self.assertIsNotNone(self.loader.load(self.path))

    def test_category_model_fixture_loads(self):
        self.assertIn("fixture_kind", self.loader.load(self.path))

    def test_segmentation_fixture_loads_and_cache_can_be_cleared(self):
        first = self.loader.load(self.path)
        self.assertIs(first, self.loader.load(self.path))
        self.loader.clear()
        self.assertEqual(self.loader.load(self.path), first)

    def test_missing_artifact_is_reported(self):
        with self.assertRaises(ModelLoadError):
            self.loader.load(Path(self.temp.name) / "missing.joblib")


if __name__ == "__main__":
    unittest.main()
