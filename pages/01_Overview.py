import plotly.express as px
import pandas as pd
import streamlit as st

from src.services.public_aggregate_service import PublicAggregateDataError
from src.ui.components import render_kpi_card, render_page_header, render_status_label
from src.ui.public_aggregate_pages import PUBLIC_AGGREGATES_RELEASED, cluster_profile_view, load_public_aggregate


REPORTS = {
    "profiles": "reports/segmentation/phase_9/Cluster_Profiles.csv",
    "clustering": "reports/segmentation/phase_9/Clustering_Model_Comparison.csv",
    "classification": "reports/classification/phase_6/Model_comparison.csv",
    "regression": "reports/regression/phase_7/Model_Comparison.csv",
    "recommendations": "reports/recommendation/phase_8/Recommendation_Metrics_By_K.csv",
}

render_page_header(
    "Public portfolio",
    "Shopping analytics overview",
    "Aggregate model evaluation and privacy-filtered segment summaries. No customer-level records are loaded.",
)
render_status_label("Aggregate release approved" if PUBLIC_AGGREGATES_RELEASED else "Aggregate review pending")

try:
    data = {name: load_public_aggregate(path) for name, path in REPORTS.items()}
except PublicAggregateDataError:
    if PUBLIC_AGGREGATES_RELEASED:
        st.warning("Approved aggregate reports are unavailable or invalid. This page cannot display report values.")
    else:
        st.info(
            "Aggregate report values are not displayed until their provenance and privacy review is complete. "
            "The page is configured to use only the approved aggregate report service after release approval."
        )
    st.stop()

profiles = data["profiles"]
clustering = data["clustering"]
classification = data["classification"]
regression = data["regression"]
recommendations = data["recommendations"]

col1, col2, col3, col4 = st.columns(4)
with col1:
    render_kpi_card("Classifier candidates", f"{classification['model_name'].notna().sum()}", "Phase 6 comparison rows", "#3568FF")
with col2:
    render_kpi_card("Spending candidates", f"{regression['model_name'].notna().sum()}", "Phase 7 comparison rows", "#18A999")
with col3:
    render_kpi_card("Recommendation methods", f"{recommendations['method'].nunique()}", "Aggregate metrics by K", "#F59E0B")
with col4:
    render_kpi_card("Clustering candidates", f"{len(clustering)}", "Aggregate algorithm comparison", "#A855F7")

st.markdown('<div style="height:.8rem"></div>', unsafe_allow_html=True)
left, right = st.columns(2, gap="medium")

with left:
    st.markdown('<div class="section-card">', unsafe_allow_html=True)
    st.subheader("Classification model comparison")
    st.caption("F1 values from the approved Phase 6 aggregate model comparison report.")
    class_chart = classification.dropna(subset=["model_name", "f1"])
    if class_chart.empty:
        st.info("Classification comparison values are unavailable after suppression.")
    else:
        fig = px.bar(class_chart.sort_values("f1"), x="f1", y="model_name", orientation="h", color_discrete_sequence=["#3568FF"])
        fig.update_layout(template="plotly_white", height=320, margin=dict(l=12, r=18, t=15, b=12), paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)")
        fig.update_xaxes(title="F1 score", showgrid=True, gridcolor="#EEF2F7")
        fig.update_yaxes(title="", showgrid=False)
        st.plotly_chart(fig, width="stretch")
    st.markdown("</div>", unsafe_allow_html=True)

with right:
    st.markdown('<div class="section-card">', unsafe_allow_html=True)
    st.subheader("Spending model comparison")
    st.caption("Mean Absolute Error values from the approved Phase 7 aggregate comparison report.")
    regression_chart = regression.dropna(subset=["model_name", "mae"])
    if regression_chart.empty:
        st.info("Spending comparison values are unavailable after suppression.")
    else:
        fig = px.bar(regression_chart.sort_values("mae", ascending=False), x="mae", y="model_name", orientation="h", color_discrete_sequence=["#18A999"])
        fig.update_layout(template="plotly_white", height=320, margin=dict(l=12, r=18, t=15, b=12), paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)")
        fig.update_xaxes(title="Mean Absolute Error (ledger units)", showgrid=True, gridcolor="#EEF2F7")
        fig.update_yaxes(title="", showgrid=False)
        st.plotly_chart(fig, width="stretch")
    st.markdown("</div>", unsafe_allow_html=True)

st.markdown('<div style="height:.8rem"></div>', unsafe_allow_html=True)
left, right = st.columns(2, gap="medium")

with left:
    st.markdown('<div class="section-card">', unsafe_allow_html=True)
    st.subheader("Recommendation evaluation")
    st.caption("Aggregate ranking metrics by method and recommendation depth. No customer-specific recommendations are loaded.")
    recommendation_chart = recommendations.dropna(subset=["method", "k", "map"])
    if recommendation_chart.empty:
        st.info("Recommendation evaluation values are unavailable after suppression.")
    else:
        fig = px.line(recommendation_chart, x="k", y="map", color="method", markers=True, color_discrete_sequence=["#3568FF", "#18A999", "#F59E0B", "#A855F7"])
        fig.update_layout(template="plotly_white", height=320, margin=dict(l=12, r=18, t=15, b=12), paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)")
        fig.update_xaxes(title="Recommendation depth (K)", showgrid=False)
        fig.update_yaxes(title="Mean Average Precision", showgrid=True, gridcolor="#EEF2F7")
        st.plotly_chart(fig, width="stretch")
    st.markdown("</div>", unsafe_allow_html=True)

with right:
    st.markdown('<div class="section-card">', unsafe_allow_html=True)
    st.subheader("Privacy-filtered segment profile")
    st.caption("Only unsuppressed aggregate profile measures are shown. Counts and shares are never reconstructed.")
    profile_view = cluster_profile_view(profiles)
    if profile_view.empty:
        st.info("Segment profile measures are unavailable after privacy suppression.")
    else:
        display = profile_view.rename(
            columns={
                "segment_id": "Segment",
                "average_historical_gross_spending": "Average gross spend",
                "median_historical_gross_spending": "Median gross spend",
                "average_invoice_frequency": "Average invoice frequency",
            }
        )
        st.dataframe(display.style.format({"Average gross spend": "{:,.2f}", "Median gross spend": "{:,.2f}", "Average invoice frequency": "{:.2f}"}), width="stretch", hide_index=True)
        st.caption("Spend values have no established currency label.")
    st.markdown("</div>", unsafe_allow_html=True)

st.markdown('<div style="height:.8rem"></div>', unsafe_allow_html=True)
st.markdown('<div class="section-card">', unsafe_allow_html=True)
st.subheader("Clustering evaluation")
st.caption("Aggregate algorithm-comparison metrics; values are evaluation scores, not customer-level outcomes.")
cluster_view = clustering[["algorithm", "clusters", "silhouette", "davies_bouldin", "calinski_harabasz", "inertia"]].copy()
st.dataframe(
    cluster_view.rename(columns={"algorithm": "Algorithm", "clusters": "Clusters (K)", "silhouette": "Silhouette", "davies_bouldin": "Davies-Bouldin", "calinski_harabasz": "Calinski-Harabasz", "inertia": "Inertia"}).style.format(
        {"Silhouette": "{:.4f}", "Davies-Bouldin": "{:.4f}", "Calinski-Harabasz": "{:,.2f}", "Inertia": lambda value: f"{value:,.2f}" if pd.notna(value) else "Unavailable"}
    ),
    width="stretch",
    hide_index=True,
)
st.markdown("</div>", unsafe_allow_html=True)
