from pathlib import Path

import pandas as pd

from src.config.settings import Settings
from src.preprocessing.input_validation import validate_cutoff, validate_customer_id


class HistoricalSnapshotService:
    """Loads only the dedicated March or June historical snapshot artifact."""

    SNAPSHOT_FILES = {
        "2011-03-01": "march_2011_historical_customer_snapshots.csv",
        "2011-06-01": "june_2011_historical_customer_snapshots.csv",
    }
    REQUIRED_COLUMNS = {
        "customer_id",
        "snapshot_cutoff",
        "historical_gross_spend",
        "historical_invoice_count",
        "historical_total_quantity",
        "historical_unique_stockcode_count",
        "recency_days",
        "historical_average_invoice_value",
        "historical_active_month_count",
        "historical_weekday_invoice_count",
    }

    def __init__(self, project_root=None, settings=None):
        self.settings = settings or Settings(project_root=project_root)
        self.project_root = Path(self.settings.project_root)

    def load_for_cutoff(self, cutoff):
        cutoff = validate_cutoff(cutoff, self.SNAPSHOT_FILES)
        source = (
            self.project_root
            / "datasets"
            / "customer_analytics"
            / "phase_12"
            / self.SNAPSHOT_FILES[cutoff]
        )
        if not source.is_file():
            raise FileNotFoundError(f"Approved historical snapshot is missing: {source.name}")

        frame = pd.read_csv(source, dtype={"snapshot_cutoff": str})
        missing = self.REQUIRED_COLUMNS.difference(frame.columns)
        if missing:
            raise ValueError(f"Historical snapshot is missing required columns: {sorted(missing)}")
        if frame["snapshot_cutoff"].astype(str).ne(cutoff).any():
            raise ValueError(f"Historical snapshot contains a cutoff other than {cutoff}")
        if frame.duplicated(["customer_id", "snapshot_cutoff"]).any():
            raise ValueError("Historical snapshot has duplicate customer-cutoff records")
        return frame

    def load_all_approved(self):
        return pd.concat(
            [self.load_for_cutoff(cutoff) for cutoff in self.SNAPSHOT_FILES],
            ignore_index=True,
        )

    def get_customer(self, customer_id, cutoff):
        customer_id = validate_customer_id(customer_id)
        frame = self.load_for_cutoff(cutoff)
        match = frame[frame["customer_id"] == customer_id]
        if match.empty:
            return None
        if len(match) != 1:
            raise ValueError("Duplicate customer record in approved historical snapshot")
        return match.iloc[0]
