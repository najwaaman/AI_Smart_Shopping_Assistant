"""Synthetic-only tests for the public aggregate data boundary."""

import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

import pandas as pd

from src.services.public_aggregate_service import (
    REPORT_SPECS,
    PublicAggregateDataError,
    PublicAggregateService,
)


def _synthetic_frame(relative_path, rows=2):
    spec = REPORT_SPECS[relative_path]
    allowed_values = dict(spec.allowed_values)
    records = []
    for index in range(rows):
        record = {}
        for column in spec.columns:
            if column in spec.text_columns:
                options = allowed_values.get(column)
                record[column] = options[index % len(options)] if options else f"synthetic_{column}_{index}"
            elif column in spec.nullable_numeric_columns:
                record[column] = float(index + 1)
            elif column in spec.numeric_columns:
                # Cell counts stay above the default suppression threshold
                # unless a test deliberately supplies small synthetic cells.
                record[column] = float(100 + index) if "count" in column or column in {"tn", "fp", "fn", "tp"} else float(index + 1)
            else:
                record[column] = f"synthetic_{column}_{index}"
        for key in spec.unique_by:
            if key in spec.numeric_columns:
                options = allowed_values.get(key)
                record[key] = options[index % len(options)] if options else float(index + 1)
        records.append(record)
    return pd.DataFrame(records, columns=spec.columns)


def _write(root, relative_path, frame):
    target = root.joinpath(*relative_path.split("/"))
    target.parent.mkdir(parents=True, exist_ok=True)
    frame.to_csv(target, index=False)
    return target


class PublicAggregateServiceTest(unittest.TestCase):
    def test_accepts_each_exact_allowlisted_path_and_returns_only_selected_columns(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            service = PublicAggregateService(project_root=root)
            for relative_path, spec in REPORT_SPECS.items():
                with self.subTest(relative_path=relative_path):
                    _write(root, relative_path, _synthetic_frame(relative_path))
                    result = service.load_report(relative_path)
                    self.assertEqual(tuple(result.columns), spec.columns)
                    self.assertNotIn("customer_id", result.columns)
                    self.assertNotIn("average_recency", result.columns)
                    self.assertNotIn("average_unique_products", result.columns)

    def test_rejects_unapproved_paths_and_non_string_paths(self):
        service = PublicAggregateService(project_root=Path("unused-root"))
        for path in (
            "reports/segmentation/phase_9/Customer_Segment_Assignments.csv",
            "../datasets/private.csv",
            "reports/segmentation/phase_9/Cluster_Profiles.csv/../Customer_Segment_Assignments.csv",
            Path("reports/segmentation/phase_9/Cluster_Profiles.csv"),
        ):
            with self.subTest(path=path), self.assertRaises(PublicAggregateDataError):
                service.load_report(path)

    def test_missing_approved_report_has_safe_error(self):
        with tempfile.TemporaryDirectory() as temporary:
            service = PublicAggregateService(project_root=Path(temporary))
            with self.assertRaisesRegex(PublicAggregateDataError, "Approved aggregate report is missing"):
                service.load_report("reports/segmentation/phase_9/Cluster_Profiles.csv")

    def test_invalid_schema_is_rejected_after_header_only_read(self):
        relative_path = "reports/segmentation/phase_9/Cluster_Profiles.csv"
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            bad = _synthetic_frame(relative_path).drop(columns=["percentage"])
            _write(root, relative_path, bad)
            real_read_csv = pd.read_csv
            with patch("src.services.public_aggregate_service.pd.read_csv", wraps=real_read_csv) as read_csv:
                with self.assertRaisesRegex(PublicAggregateDataError, "invalid schema"):
                    PublicAggregateService(project_root=root).load_report(relative_path)
            self.assertEqual(read_csv.call_count, 1)
            self.assertEqual(read_csv.call_args.kwargs, {"nrows": 0})

    def test_invalid_numeric_type_is_rejected(self):
        relative_path = "reports/segmentation/phase_9/Cluster_Profiles.csv"
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            frame = _synthetic_frame(relative_path).astype(object)
            frame.loc[0, "customer_count"] = "not-a-number"
            _write(root, relative_path, frame)
            with self.assertRaisesRegex(PublicAggregateDataError, "invalid data types"):
                PublicAggregateService(project_root=root).load_report(relative_path)

    def test_customer_identifier_column_is_rejected_before_data_rows_are_read(self):
        relative_path = "reports/segmentation/phase_9/Cluster_Profiles.csv"
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            frame = _synthetic_frame(relative_path)
            frame.insert(0, "customer_id", ["synthetic-id-a", "synthetic-id-b"])
            _write(root, relative_path, frame)
            real_read_csv = pd.read_csv
            with patch("src.services.public_aggregate_service.pd.read_csv", wraps=real_read_csv) as read_csv:
                with self.assertRaisesRegex(PublicAggregateDataError, "Customer-level identifiers"):
                    PublicAggregateService(project_root=root).load_report(relative_path)
            self.assertEqual(read_csv.call_count, 1)
            self.assertEqual(read_csv.call_args.kwargs, {"nrows": 0})

    def test_excess_rows_are_rejected(self):
        relative_path = "reports/segmentation/phase_9/Cluster_Profiles.csv"
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            _write(root, relative_path, _synthetic_frame(relative_path, rows=4))
            with self.assertRaisesRegex(PublicAggregateDataError, "invalid row count"):
                PublicAggregateService(project_root=root).load_report(relative_path)

    def test_nonaggregate_group_values_are_rejected(self):
        relative_path = "reports/segmentation/phase_9/Cluster_Profiles.csv"
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            frame = _synthetic_frame(relative_path)
            frame.loc[0, "segment_id"] = 909090909
            _write(root, relative_path, frame)
            with self.assertRaisesRegex(PublicAggregateDataError, "invalid group values"):
                PublicAggregateService(project_root=root).load_report(relative_path)

    def test_profile_suppression_hides_small_and_complementary_groups_and_all_counts(self):
        relative_path = "reports/segmentation/phase_9/Cluster_Profiles.csv"
        frame = pd.DataFrame(
            [
                {"segment_id": 0, "customer_count": 80, "unique_customers": 70, "average_historical_gross_spending": 10.0, "median_historical_gross_spending": 9.0, "average_invoice_frequency": 2.0, "percentage": 80.0},
                {"segment_id": 1, "customer_count": 5, "unique_customers": 4, "average_historical_gross_spending": 100.0, "median_historical_gross_spending": 90.0, "average_invoice_frequency": 8.0, "percentage": 5.0},
                {"segment_id": 2, "customer_count": 15, "unique_customers": 14, "average_historical_gross_spending": 50.0, "median_historical_gross_spending": 40.0, "average_invoice_frequency": 4.0, "percentage": 15.0},
            ],
            columns=REPORT_SPECS[relative_path].columns,
        )
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            _write(root, relative_path, frame)
            result = PublicAggregateService(project_root=root).load_report(relative_path).set_index("segment_id")

        # Segment 1 is primary-suppressed; segment 0 is complementary-suppressed.
        self.assertTrue(result.loc[0].isna().all())
        self.assertTrue(result.loc[1].isna().all())
        # No count or percentage subtotal can be calculated from visible rows.
        self.assertTrue(result[["customer_count", "unique_customers", "percentage"]].isna().all().all())
        self.assertNotIn("total", result.columns)

    def test_temporal_suppression_hides_period_counts_and_percentages(self):
        relative_path = "reports/segmentation/phase_9/Temporal_Stability_Report.csv"
        frame = pd.DataFrame(
            [
                {"segment_id": 0, "march_count": 80, "june_count": 82, "march_percentage": 80.0, "june_percentage": 82.0},
                {"segment_id": 1, "march_count": 3, "june_count": 4, "march_percentage": 3.0, "june_percentage": 4.0},
                {"segment_id": 2, "march_count": 17, "june_count": 14, "march_percentage": 17.0, "june_percentage": 14.0},
            ],
            columns=REPORT_SPECS[relative_path].columns,
        )
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            _write(root, relative_path, frame)
            result = PublicAggregateService(project_root=root).load_report(relative_path).set_index("segment_id")

        self.assertTrue(result.loc[0].isna().all())
        self.assertTrue(result.loc[1].isna().all())
        self.assertTrue(result[["march_count", "june_count", "march_percentage", "june_percentage"]].isna().all().all())

    def test_small_confusion_count_suppresses_entire_model_row(self):
        relative_path = "reports/classification/phase_6/Model_comparison.csv"
        frame = _synthetic_frame(relative_path)
        frame.loc[0, "fp"] = 3
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            _write(root, relative_path, frame)
            result = PublicAggregateService(project_root=root).load_report(relative_path)
        self.assertTrue(result.loc[0].isna().all())


if __name__ == "__main__":
    unittest.main()
