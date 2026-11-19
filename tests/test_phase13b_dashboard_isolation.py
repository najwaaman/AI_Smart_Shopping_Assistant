import ast
from pathlib import Path
import unittest
from unittest.mock import patch

import pandas as pd
from streamlit.testing.v1 import AppTest

from src.ui.dashboard_data import load_dashboard_data
from synthetic_fixtures import segment_profile_frame, snapshot_frame


ROOT = Path(__file__).resolve().parents[1]
ALLOWED_READS = {
    (ROOT / "datasets/customer_analytics/phase_12/march_2011_historical_customer_snapshots.csv").resolve(),
    (ROOT / "datasets/customer_analytics/phase_12/june_2011_historical_customer_snapshots.csv").resolve(),
    (ROOT / "reports/segmentation/phase_9/Cluster_Profiles.csv").resolve(),
}


class Phase13BDashboardIsolationTest(unittest.TestCase):
    def test_overview_renders_using_only_approved_inputs(self):
        load_dashboard_data.clear()
        reads = []

        def guarded_read_csv(path, *args, **kwargs):
            resolved = Path(path).resolve()
            if resolved not in ALLOWED_READS:
                raise AssertionError(f"Overview attempted an unapproved data read: {resolved.name}")
            reads.append(resolved)
            if resolved.name.startswith("march_"):
                return snapshot_frame("2011-03-01")
            if resolved.name.startswith("june_"):
                return snapshot_frame("2011-06-01")
            return segment_profile_frame()

        with patch("src.services.historical_snapshot_service.Path.is_file", return_value=True), \
             patch("pandas.read_csv", side_effect=guarded_read_csv):
            app = AppTest.from_file(str(ROOT / "pages/01_Overview.py"), default_timeout=30).run()

        self.assertEqual(app.exception, [])
        self.assertEqual(app.error, [])
        self.assertEqual(set(reads), ALLOWED_READS)
        self.assertEqual(len(reads), 3)

        load_dashboard_data.clear()
        with patch("src.services.historical_snapshot_service.Path.is_file", return_value=True), \
             patch("pandas.read_csv", side_effect=guarded_read_csv):
            data = load_dashboard_data(ROOT)
        self.assertEqual(data["summary"]["total_customer_cutoff_records"], 4)
        self.assertEqual(data["summary"]["cutoff_counts"], {"2011-03-01": 2, "2011-06-01": 2})
        self.assertEqual(data["summary"]["june_invoice_count_sum"], 4)
        self.assertEqual(data["segment_profile"]["customer_count"].sum(), 4)
        load_dashboard_data.clear()

    def test_overview_data_loader_has_no_broad_or_prediction_input_paths(self):
        source = (ROOT / "src/ui/dashboard_data.py").read_text(encoding="utf-8")
        tree = ast.parse(source)
        self.assertIsInstance(tree, ast.Module)
        for forbidden in (
            "accepted_paid_transaction_lines.csv",
            "customer_snapshots_90d.csv",
            "customer_insights.csv",
            "customer_recommendations.csv",
        ):
            with self.subTest(forbidden=forbidden):
                self.assertNotIn(forbidden, source)


if __name__ == "__main__":
    unittest.main()
