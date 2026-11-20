import pandas as pd
import plotly.express as px
import streamlit as st

from src.ui.components import render_page_header, render_status_label
from src.ui.public_demo_logic import illustrative_threshold_met


render_page_header(
    "AI model studio",
    "Synthetic shopping prediction demo",
    "Explore fictional inputs and transparent example logic. No customer data or trained prediction model is used in this public demo.",
)
render_status_label("Illustrative demo")

st.warning(
    "The project's saved Gradient Boosting and Ridge artifacts are private and have not been approved for public inference. "
    "This page therefore shows transparent toy scenarios only; it does not produce model predictions or performance metrics."
)

repeat_tab, volume_tab = st.tabs(["Repeat-behavior rule example", "Synthetic shopping inputs"])

with repeat_tab:
    st.markdown('<div class="section-card">', unsafe_allow_html=True)
    st.subheader("Try a visitor-defined threshold")
    st.caption(
        "All inputs are hypothetical. This simple comparison is a rule illustration, not a fitted model, calibrated probability, "
        "or forecast of a real shopper's behavior."
    )
    col1, col2 = st.columns(2, gap="medium")
    with col1:
        hypothetical_baskets = st.slider("Fictional baskets in an example period", min_value=0, max_value=12, value=3)
    with col2:
        threshold = st.slider("Visitor-selected threshold", min_value=1, max_value=12, value=3)

    threshold_met = illustrative_threshold_met(hypothetical_baskets, threshold)
    if threshold_met:
        st.success(f"Example rule condition met: {hypothetical_baskets} fictional baskets is at or above your threshold of {threshold}.")
    else:
        st.info(f"Example rule condition not met: {hypothetical_baskets} fictional baskets is below your threshold of {threshold}.")
    st.caption("The threshold is chosen by you; it is not learned from the project's historical data.")
    st.markdown("</div>", unsafe_allow_html=True)

with volume_tab:
    st.markdown('<div class="section-card">', unsafe_allow_html=True)
    st.subheader("Inspect a synthetic input vector")
    st.caption("This visualizes only the values you enter. It does not estimate future spending or assign a currency.")
    col1, col2, col3 = st.columns(3, gap="medium")
    with col1:
        planned_baskets = st.slider("Hypothetical baskets", min_value=0, max_value=12, value=4, key="synthetic_baskets")
    with col2:
        items_per_basket = st.slider("Fictional items per basket", min_value=0, max_value=20, value=5)
    with col3:
        active_weeks = st.slider("Hypothetical active weeks", min_value=0, max_value=12, value=4)

    vector = pd.DataFrame(
        {
            "Synthetic input": ["Baskets", "Items per basket", "Active weeks", "Illustrative item volume"],
            "Visitor-entered value": [planned_baskets, items_per_basket, active_weeks, planned_baskets * items_per_basket],
        }
    )
    fig = px.bar(
        vector,
        x="Synthetic input",
        y="Visitor-entered value",
        color_discrete_sequence=["#18A999"],
        labels={"Synthetic input": "Synthetic input", "Visitor-entered value": "Example value (not a prediction)"},
    )
    fig.update_layout(template="plotly_white", height=340, margin=dict(l=12, r=18, t=15, b=12), paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)")
    fig.update_xaxes(title="", showgrid=False)
    fig.update_yaxes(title="Example value (not a prediction)", showgrid=True, gridcolor="#EEF2F7")
    st.plotly_chart(fig, width="stretch")
    st.info(
        f"Illustrative arithmetic only: {planned_baskets} hypothetical baskets × {items_per_basket} fictional items = "
        f"{planned_baskets * items_per_basket} item units. No prediction is generated."
    )
    st.markdown("</div>", unsafe_allow_html=True)
