from pathlib import Path

import plotly.graph_objects as go
import plotly.express as px
import streamlit as st

from src.ui.components import render_page_header, render_kpi_card
from src.ui.dashboard_data import load_dashboard_data

ROOT = Path(__file__).resolve().parents[1]
data = load_dashboard_data(ROOT)

render_page_header(
    "Executive overview",
    "Retail intelligence at a glance",
    "Cutoff-limited historical customer behaviour and verified segment summaries for March and June 2011.",
)

summary = data["summary"]
snapshots = data["snapshots"]
segment_profile = data["segment_profile"]

col1, col2, col3, col4 = st.columns(4)
with col1:
    render_kpi_card("Customer-cutoff records", f"{summary['total_customer_cutoff_records']:,}", "March and June snapshots", "#3568FF")
with col2:
    render_kpi_card("Unique customers", f"{summary['total_unique_customers']:,}", "Across approved snapshots", "#18A999")
with col3:
    render_kpi_card("June historical invoices", f"{summary['june_invoice_count_sum']:,}", "Sum of customer-level counts", "#F59E0B")
with col4:
    render_kpi_card("June historical gross spend", f"{summary['june_gross_spend_sum']:,.2f}", "No currency label assigned", "#A855F7")

st.markdown('<div style="height:.8rem"></div>', unsafe_allow_html=True)
left, right = st.columns([1.45, 1], gap="medium")

with left:
    st.markdown('<div class="section-card">', unsafe_allow_html=True)
    st.subheader("Customer cutoffs")
    cutoff_counts = snapshots.groupby("snapshot_cutoff").size().reset_index(name="customer_records")
    fig = px.bar(
        cutoff_counts,
        x="snapshot_cutoff",
        y="customer_records",
        text="customer_records",
        color_discrete_sequence=["#3568FF"],
    )
    fig.update_layout(template="plotly_white", height=330, margin=dict(l=15, r=15, t=30, b=10), paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)")
    fig.update_traces(textposition="outside", cliponaxis=False)
    fig.update_xaxes(title="Snapshot cutoff", showgrid=False)
    fig.update_yaxes(title="Customer records", showgrid=True, gridcolor="#EEF2F7")
    st.plotly_chart(fig, width="stretch")
    st.markdown('</div>', unsafe_allow_html=True)

with right:
    st.markdown('<div class="section-card">', unsafe_allow_html=True)
    st.subheader("Segment distribution")
    profile = segment_profile.sort_values("segment_id")
    fig = go.Figure(go.Pie(labels=[f"Segment {int(i)}" for i in profile["segment_id"]], values=profile["customer_count"], hole=.58, marker_colors=["#3568FF", "#18A999", "#F59E0B"], textinfo="label+percent"))
    fig.update_layout(template="plotly_white", height=330, margin=dict(l=10, r=10, t=30, b=10), paper_bgcolor="rgba(0,0,0,0)", showlegend=True)
    st.plotly_chart(fig, width="stretch")
    st.markdown('</div>', unsafe_allow_html=True)

st.markdown('<div style="height:.8rem"></div>', unsafe_allow_html=True)
left, right = st.columns(2, gap="medium")

with left:
    st.markdown('<div class="section-card">', unsafe_allow_html=True)
    st.subheader("Historical invoice count distribution")
    fig = px.histogram(snapshots, x="historical_invoice_count", color="snapshot_cutoff", nbins=30, color_discrete_sequence=["#18A999", "#3568FF"])
    fig.update_layout(template="plotly_white", height=310, margin=dict(l=15, r=15, t=25, b=10), paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)", bargap=.08)
    fig.update_xaxes(title="Invoices per customer snapshot", showgrid=False)
    fig.update_yaxes(title="Customer-cutoff records", showgrid=True, gridcolor="#EEF2F7")
    st.plotly_chart(fig, width="stretch")
    st.markdown('</div>', unsafe_allow_html=True)

with right:
    st.markdown('<div class="section-card">', unsafe_allow_html=True)
    st.subheader("Historical gross-spend distribution")
    fig = px.histogram(snapshots, x="historical_gross_spend", color="snapshot_cutoff", nbins=40, color_discrete_sequence=["#3568FF", "#18A999"])
    fig.update_layout(template="plotly_white", height=310, margin=dict(l=15, r=15, t=25, b=10), paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)", bargap=.08)
    fig.update_xaxes(title="Historical gross spending (no currency label)", showgrid=False)
    fig.update_yaxes(title="Customer-cutoff records", showgrid=True, gridcolor="#EEF2F7")
    st.plotly_chart(fig, width="stretch")
    st.caption("Historical snapshot values; no currency label is assigned.")
    st.markdown('</div>', unsafe_allow_html=True)
