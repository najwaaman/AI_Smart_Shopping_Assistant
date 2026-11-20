import plotly.express as px
import streamlit as st

from src.services.public_aggregate_service import PublicAggregateDataError
from src.ui.components import render_page_header, render_status_label
from src.ui.public_aggregate_pages import (
    PUBLIC_AGGREGATES_RELEASED,
    cluster_profile_view,
    load_public_aggregate,
    temporal_stability_view,
)


PROFILE_REPORT = "reports/segmentation/phase_9/Cluster_Profiles.csv"
STABILITY_REPORT = "reports/segmentation/phase_9/Temporal_Stability_Report.csv"
PROFILE_MEASURES = {
    "Average gross spend": "average_historical_gross_spending",
    "Median gross spend": "median_historical_gross_spending",
    "Average invoice frequency": "average_invoice_frequency",
}

render_page_header(
    "Commerce intelligence",
    "Shopping cohort explorer",
    "Explore reviewed aggregate cohort measures. This public page never accepts a customer identifier or displays individual records.",
)
render_status_label("Aggregate release approved" if PUBLIC_AGGREGATES_RELEASED else "Aggregate review pending")

st.markdown('<div class="section-card">', unsafe_allow_html=True)
st.subheader("Choose an aggregate measure")
selected_label = st.selectbox("Cohort measure", list(PROFILE_MEASURES))
st.caption(
    "The selected measure describes an approved cluster profile after the public aggregate service has applied suppression. "
    "Group counts and shares are intentionally not available here."
)
st.markdown("</div>", unsafe_allow_html=True)

st.markdown('<div style="height:.8rem"></div>', unsafe_allow_html=True)
left, right = st.columns([1.3, 1], gap="medium")
with left:
    st.markdown('<div class="section-card">', unsafe_allow_html=True)
    st.subheader("Cohort profile")
    st.markdown(
        "Once approved aggregate reports are released, this chart will show only nonsuppressed profile values. "
        "It will not use customer lookup, customer insight rows, or segment assignments."
    )
    try:
        profiles_raw = load_public_aggregate(PROFILE_REPORT)
        profiles = cluster_profile_view(profiles_raw)
    except PublicAggregateDataError:
        if PUBLIC_AGGREGATES_RELEASED:
            st.warning("The approved cohort profile report is unavailable or invalid.")
        else:
            st.info("Cohort statistics are pending aggregate provenance and privacy approval. No report values are being shown.")
    else:
        column = PROFILE_MEASURES[selected_label]
        visible = profiles.dropna(subset=[column])
        if visible.empty:
            st.info("This measure is unavailable after privacy suppression. No value has been estimated or reconstructed.")
        else:
            chart = visible[["segment_id", column]].copy()
            chart["Cohort"] = chart["segment_id"].map(lambda value: f"Segment {int(value)}")
            fig = px.bar(
                chart,
                x="Cohort",
                y=column,
                color_discrete_sequence=["#3568FF"],
                labels={column: selected_label + (" (no currency label)" if "spend" in column else ""), "Cohort": "Aggregate cohort"},
            )
            fig.update_layout(template="plotly_white", height=340, margin=dict(l=12, r=18, t=15, b=12), paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)")
            fig.update_xaxes(title="Aggregate cohort", showgrid=False)
            fig.update_yaxes(title=selected_label + (" (no currency label)" if "spend" in column else ""), showgrid=True, gridcolor="#EEF2F7")
            st.plotly_chart(fig, width="stretch")
            if "spend" in column:
                st.caption("Spending values have no established currency label.")
    st.markdown("</div>", unsafe_allow_html=True)

with right:
    st.markdown('<div class="section-card">', unsafe_allow_html=True)
    st.subheader("Privacy and interpretation")
    st.markdown(
        "- Cohort measures are aggregate summaries, not a profile of an individual shopper.\n"
        "- Small-cell and complementary suppression are applied by the approved aggregate service.\n"
        "- Suppressed values are left blank; this page does not calculate totals, shares, or substitute values.\n"
        "- No customer identifier or customer-level dataset is requested or loaded."
    )
    st.markdown("</div>", unsafe_allow_html=True)

st.markdown('<div style="height:.8rem"></div>', unsafe_allow_html=True)
st.markdown('<div class="section-card">', unsafe_allow_html=True)
st.subheader("March and June aggregate comparison")
try:
    stability_raw = load_public_aggregate(STABILITY_REPORT)
    stability, available_metrics = temporal_stability_view(stability_raw)
except PublicAggregateDataError:
    if PUBLIC_AGGREGATES_RELEASED:
        st.warning("The approved temporal comparison report is unavailable or invalid.")
    else:
        st.info("Temporal cohort measures are pending aggregate provenance and privacy approval.")
else:
    if not available_metrics:
        st.info("Temporal counts and shares remain suppressed. No comparison values or totals have been reconstructed.")
    else:
        st.dataframe(stability, width="stretch", hide_index=True)
        st.caption("Only non-suppressed cells returned by the aggregate service are shown.")
st.markdown("</div>", unsafe_allow_html=True)
