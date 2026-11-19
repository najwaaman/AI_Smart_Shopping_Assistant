from pathlib import Path

import pandas as pd
import streamlit as st

from src.services.historical_snapshot_service import HistoricalSnapshotService


@st.cache_data(ttl=300)
def load_dashboard_data(project_root):
    root = Path(project_root)
    snapshots = HistoricalSnapshotService(project_root=root).load_all_approved()
    segment_profile = pd.read_csv(root / "reports/segmentation/phase_9/Cluster_Profiles.csv")
    june = snapshots[snapshots["snapshot_cutoff"] == "2011-06-01"]
    summary = {
        "total_customer_cutoff_records": len(snapshots),
        "total_unique_customers": int(snapshots["customer_id"].nunique()),
        "cutoff_counts": snapshots["snapshot_cutoff"].value_counts().sort_index().to_dict(),
        "june_customer_count": len(june),
        "june_invoice_count_sum": int(june["historical_invoice_count"].sum()),
        "june_gross_spend_sum": float(june["historical_gross_spend"].sum()),
        "june_average_customer_gross_spend": float(june["historical_gross_spend"].mean()),
    }

    return {
        "summary": summary,
        "snapshots": snapshots,
        "segment_profile": segment_profile,
    }
