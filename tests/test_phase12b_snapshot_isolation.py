import ast
from pathlib import Path
import unittest
from unittest.mock import patch

from synthetic_fixtures import snapshot_frame

from src.services.historical_snapshot_service import HistoricalSnapshotService
from src.utils.exceptions import UnsupportedCutoffError


ROOT = Path(__file__).resolve().parents[1]
ALLOWED = {
    "2011-03-01": "march_2011_historical_customer_snapshots.csv",
    "2011-06-01": "june_2011_historical_customer_snapshots.csv",
}


class Phase12BSnapshotIsolationTest(unittest.TestCase):
    def test_service_reads_only_the_selected_approved_file(self):
        for cutoff, filename in ALLOWED.items():
            with self.subTest(cutoff=cutoff):
                with patch("src.services.historical_snapshot_service.Path.is_file", return_value=True), \
                     patch(
                    "src.services.historical_snapshot_service.pd.read_csv",
                    return_value=snapshot_frame(cutoff),
                ) as read_csv:
                    frame = HistoricalSnapshotService(project_root=ROOT).load_for_cutoff(cutoff)
                self.assertEqual(read_csv.call_count, 1)
                self.assertEqual(Path(read_csv.call_args.args[0]).name, filename)
                self.assertTrue(frame["snapshot_cutoff"].eq(cutoff).all())

    def test_unknown_cutoff_is_rejected_before_any_file_read(self):
        with patch("src.services.historical_snapshot_service.pd.read_csv") as read_csv:
            with self.assertRaises(UnsupportedCutoffError):
                HistoricalSnapshotService(project_root=ROOT).load_for_cutoff("2011-09-10")
        read_csv.assert_not_called()

    def test_affected_pages_and_tests_use_approved_loader(self):
        paths = [
            ROOT / "pages/04_Customer_Intelligence.py",
            ROOT / "pages/05_Predictions.py",
            ROOT / "pages/06_Customer_Segments.py",
            ROOT / "tests/test_phase10g_integration.py",
            ROOT / "tests/test_phase10g_r1_remediation.py",
        ]
        for path in paths:
            source = path.read_text(encoding="utf-8")
            with self.subTest(path=path.name):
                self.assertNotIn("customer_snapshots_90d.csv", source)
                self.assertIn("HistoricalSnapshotService", source)

    def test_loader_paths_are_fixed_to_two_march_june_artifacts(self):
        self.assertEqual(set(HistoricalSnapshotService.SNAPSHOT_FILES), set(ALLOWED))
        self.assertEqual(HistoricalSnapshotService.SNAPSHOT_FILES, ALLOWED)
        tree = ast.parse(
            (ROOT / "src/services/historical_snapshot_service.py").read_text(encoding="utf-8")
        )
        self.assertIsInstance(tree, ast.Module)


if __name__ == "__main__":
    unittest.main()
