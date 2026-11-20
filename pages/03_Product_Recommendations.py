import plotly.express as px
import pandas as pd
import streamlit as st

from src.services.public_aggregate_service import PublicAggregateDataError
from src.ui.components import render_page_header, render_status_label
from src.ui.public_aggregate_pages import load_public_aggregate
from src.ui.public_demo_logic import ILLUSTRATIVE_CATALOGUE, illustrative_recommendations


render_page_header(
    "Personalized commerce",
    "Illustrative product recommendation demo",
    "Explore how item-to-item similarity can rank fictional products. This toy catalogue is not transaction data or a trained model output.",
)
render_status_label("Illustrative demo")

st.markdown('<div class="section-card">', unsafe_allow_html=True)
st.subheader("Build a fictional shopping basket")
st.caption("All products and feature descriptors below are invented for demonstration. No customer identifiers, shopping histories, or private recommendation files are used.")

left, right = st.columns([1.05, 1.25], gap="large")
with left:
    basket = st.multiselect(
        "Choose fictional items",
        options=list(ILLUSTRATIVE_CATALOGUE),
        default=["Comet Trail Mug", "Paperleaf Notebook"],
        help="Choose one or more products from the fictional catalogue.",
    )
    recommendation_count = st.slider("Products to show", min_value=1, max_value=5, value=3)
    st.markdown("**Illustrative feature dimensions**")
    st.caption("On-the-go · drinkware · reusable · desk · stationery · storage")

with right:
    st.markdown('<div class="info-card">', unsafe_allow_html=True)
    st.markdown("**How this demo ranks products**")
    st.markdown(
        "Each fictional product has a small hand-authored feature vector. The page computes cosine similarity between each candidate and the selected basket, then averages those similarities. "
        "These values explain the example logic only; they are not learned from purchases and do not represent the project recommender."
    )
    st.markdown("</div>", unsafe_allow_html=True)
st.markdown("</div>", unsafe_allow_html=True)

if not basket:
    st.info("Choose at least one fictional product to see the illustrative ranking.")
else:
    results = illustrative_recommendations(basket, recommendation_count)
    st.markdown('<div style="height:.8rem"></div>', unsafe_allow_html=True)
    st.markdown('<div class="section-card">', unsafe_allow_html=True)
    st.subheader("Illustrative item-to-item ranking")
    st.caption("Toy cosine similarities only — not model scores, recommendations for a real person, or evidence of product demand.")
    if not results:
        st.info("No fictional products remain outside the selected basket.")
    else:
        chart_data = pd.DataFrame(results)
        fig = px.bar(
            chart_data.sort_values("illustrative_similarity"),
            x="illustrative_similarity",
            y="product",
            orientation="h",
            color_discrete_sequence=["#3568FF"],
            labels={"illustrative_similarity": "Illustrative cosine similarity", "product": "Fictional product"},
        )
        fig.update_layout(template="plotly_white", height=300, margin=dict(l=12, r=18, t=12, b=12), paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)")
        fig.update_xaxes(range=[0, 1], title="Illustrative cosine similarity", showgrid=True, gridcolor="#EEF2F7")
        fig.update_yaxes(title="", showgrid=False)
        st.plotly_chart(fig, width="stretch")

        cards = st.columns(min(3, len(results)))
        for index, item in enumerate(results):
            with cards[index % len(cards)]:
                st.markdown('<div class="kpi-card">', unsafe_allow_html=True)
                st.markdown(f"<div class='kpi-label'>Illustrative rank {index + 1}</div>", unsafe_allow_html=True)
                st.markdown(f"<div class='kpi-value' style='font-size:1.15rem'>{item['product']}</div>", unsafe_allow_html=True)
                st.markdown(f"<div class='kpi-note'>Toy similarity: {item['illustrative_similarity']:.3f}</div>", unsafe_allow_html=True)
                st.markdown("</div>", unsafe_allow_html=True)
    st.markdown("</div>", unsafe_allow_html=True)

with st.expander("Aggregate recommendation evaluation"):
    try:
        metrics = load_public_aggregate("reports/recommendation/phase_8/Recommendation_Metrics_By_K.csv")
    except PublicAggregateDataError:
        st.info("Aggregate evaluation values are pending the Phase 1B provenance and privacy release gate.")
    else:
        view = metrics[["method", "k", "precision", "recall", "map", "ndcg", "hit_rate", "catalog_coverage", "diversity"]].copy()
        st.caption("Approved aggregate method metrics only. These population-level evaluation results are separate from the fictional ranking above.")
        st.dataframe(view, width="stretch", hide_index=True)
