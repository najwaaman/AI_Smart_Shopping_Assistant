"""Shared, release-gated access for public aggregate Streamlit pages."""

from src.services.public_aggregate_service import PublicAggregateDataError, PublicAggregateService


# Keep the public release closed until report provenance and privacy review are
# complete. Tests may enable this gate while returning synthetic DataFrames.
PUBLIC_AGGREGATES_RELEASED = False


def load_public_aggregate(relative_path):
    """Load one report through the strict Phase 1A allowlist after approval."""
    if not PUBLIC_AGGREGATES_RELEASED:
        raise PublicAggregateDataError("Public aggregate report values are pending provenance and privacy review.")
    return PublicAggregateService().load_report(relative_path)


def cluster_profile_view(frame):
    """Return only visible, approved descriptive profile measures."""
    columns = (
        "segment_id",
        "average_historical_gross_spending",
        "median_historical_gross_spending",
        "average_invoice_frequency",
    )
    measures = list(columns[1:])
    return frame.loc[:, list(columns)].dropna(subset=measures, how="all").copy()


def temporal_stability_view(frame):
    """Select only service-returned temporal cells; never compute totals/fills."""
    metrics = ("march_count", "june_count", "march_percentage", "june_percentage")
    visible = [column for column in metrics if frame[column].notna().any()]
    columns = ["segment_id", *visible]
    result = frame.loc[:, columns].copy()
    if visible:
        result = result.dropna(subset=visible, how="all")
    return result, visible
