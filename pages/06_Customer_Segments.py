import plotly.express as px
import pandas as pd
import streamlit as st

from src.services.public_aggregate_service import PublicAggregateDataError
from src.ui.components import render_kpi_card, render_page_header, render_status_label
from src.ui.public_aggregate_pages import (
    PUBLIC_AGGREGATES_RELEASED,
    cluster_profile_view,
    load_public_aggregate,
    temporal_stability_view,
)


REPORTS = {
    "profiles": "reports/segmentation/phase_9/Cluster_Profiles.csv",
    "stability": "reports/segmentation/phase_9/Temporal_Stability_Report.csv",
    "comparison": "reports/segmentation/phase_9/Clustering_Model_Comparison.csv",
}

render_page_header(
    "Commerce intelligence",
    "Customer segments",
    "Aggregate clustering profiles and evaluation. Individual assignments and customer lookups are not available in this public view.",
)
render_status_label("Aggregate release approved" if PUBLIC_AGGREGATES_RELEASED else "Aggregate review pending")

try:
    data = {name: load_public_aggregate(path) for name, path in REPORTS.items()}
except PublicAggregateDataError:
    if PUBLIC_AGGREGATES_RELEASED:
        st.warning("Approved aggregate reports are unavailable or invalid. Segment values cannot be displayed.")
    else:
        st.info(
            "Aggregate report values are withheld pending provenance and privacy review. "
            "This page will use only approved, suppression-filtered reports after release approval."
        )
    st.stop()

profiles = data["profiles"]
stability = data["stability"]
comparison = data["comparison"]

col1, col2, col3 = st.columns(3)
with col1:
    render_kpi_card("Segment labels", f"{profiles['segment_id'].nunique()}", "Categories in the approved profile schema", "#3568FF")
with col2:
    render_kpi_card("Clustering algorithms", f"{comparison['algorithm'].nunique()}", "Aggregate comparison report", "#18A999")
with col3:
    render_kpi_card("Configurations compared", f"{len(comparison)}", "Across the approved cluster-count range", "#F59E0B")

tab_profiles, tab_stability, tab_comparison = st.tabs(
    ["Aggregate profiles", "Temporal stability", "Algorithm comparison"]
)

with tab_profiles:
    st.markdown('<div class="section-card">', unsafe_allow_html=True)
    st.subheader("Privacy-filtered segment profiles")
    st.caption(
        "Only unsuppressed aggregate measures are shown. Segment sizes, unique-customer counts, and shares are omitted; "
        "no totals or percentages are reconstructed."
    )
    visible_profiles = cluster_profile_view(profiles)
    if visible_profiles.empty:
        st.info("Profile measures are unavailable after privacy suppression.")
    else:
        display_profiles = visible_profiles.rename(
            columns={
                "segment_id": "Segment",
                "average_historical_gross_spending": "Average gross spend",
                "median_historical_gross_spending": "Median gross spend",
                "average_invoice_frequency": "Average invoice frequency",
            }
        )
        st.dataframe(
            display_profiles.style.format(
                {
                    "Average gross spend": "{:,.2f}",
                    "Median gross spend": "{:,.2f}",
                    "Average invoice frequency": "{:.2f}",
                },
                na_rep="Suppressed",
            ),
            width="stretch",
            hide_index=True,
        )
        chart_data = visible_profiles.dropna(subset=["average_historical_gross_spending"])
        if not chart_data.empty:
            chart_data = chart_data.copy()
            chart_data["Segment"] = chart_data["segment_id"].map(lambda value: f"Segment {int(value)}")
            fig = px.bar(
                chart_data.sort_values("average_historical_gross_spending"),
                x="average_historical_gross_spending",
                y="Segment",
                orientation="h",
                color_discrete_sequence=["#3568FF"],
                labels={"average_historical_gross_spending": "Average gross spend (no currency label)", "Segment": "Segment"},
            )
            fig.update_layout(template="plotly_white", height=300, margin=dict(l=12, r=18, t=12, b=12), paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)")
            fig.update_xaxes(title="Average gross spend (no currency label)", showgrid=True, gridcolor="#EEF2F7")
            fig.update_yaxes(title="", showgrid=False)
            st.plotly_chart(fig, width="stretch")
        st.caption("Historical gross-spend values have no established currency label.")
    st.markdown("</div>", unsafe_allow_html=True)

with tab_stability:
    st.markdown('<div class="section-card">', unsafe_allow_html=True)
    st.subheader("March and June temporal comparison")
    st.markdown(
        "This report compares aggregate cluster counts and shares for the two approved time points. "
        "The public aggregate service applies primary and complementary suppression."
    )
    safe_stability, available_metrics = temporal_stability_view(stability)
    if not available_metrics:
        st.info("Temporal counts and shares are suppressed. No values or totals have been reconstructed.")
    else:
        st.dataframe(safe_stability, width="stretch", hide_index=True)
        st.caption("Only non-suppressed report cells are shown; displayed values are not summed or backfilled.")
    st.markdown("</div>", unsafe_allow_html=True)

with tab_comparison:
    st.markdown('<div class="section-card">', unsafe_allow_html=True)
    st.subheader("Clustering algorithm evaluation")
    st.caption("Aggregate evaluation scores from the approved model-comparison report; these describe configurations, not individuals.")
    safe_comparison = comparison[["algorithm", "clusters", "silhouette", "davies_bouldin", "calinski_harabasz", "inertia"]].copy()
    left, right = st.columns([1.2, 1], gap="medium")
    with left:
        fig = px.line(
            safe_comparison,
            x="clusters",
            y="silhouette",
            color="algorithm",
            markers=True,
            color_discrete_sequence=["#3568FF", "#18A999"],
        )
        fig.update_layout(template="plotly_white", height=340, margin=dict(l=12, r=18, t=12, b=12), paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)")
        fig.update_xaxes(title="Number of clusters (K)", dtick=1, showgrid=False)
        fig.update_yaxes(title="Silhouette score", showgrid=True, gridcolor="#EEF2F7")
        st.plotly_chart(fig, width="stretch")
    with right:
        st.dataframe(
            safe_comparison.rename(
                columns={
                    "algorithm": "Algorithm",
                    "clusters": "Clusters (K)",
                    "silhouette": "Silhouette",
                    "davies_bouldin": "Davies-Bouldin",
                    "calinski_harabasz": "Calinski-Harabasz",
                    "inertia": "Inertia",
                }
            ).style.format(
                {
                    "Silhouette": "{:.4f}",
                    "Davies-Bouldin": "{:.4f}",
                    "Calinski-Harabasz": "{:,.2f}",
                    "Inertia": lambda value: f"{value:,.2f}" if pd.notna(value) else "Unavailable",
                }
            ),
            width="stretch",
            hide_index=True,
        )
    st.markdown("</div>", unsafe_allow_html=True)
