import time

import streamlit as st

from src.services.classification_service import ProductCategoryService
from src.ui.components import escape_html_text, render_page_header, render_status_label
from src.utils.exceptions import BackendError, ValidationError


CATEGORY_ACCENTS = {
    "Household": "#18A999",
    "Books": "#3568FF",
    "Clothing & Accessories": "#A855F7",
    "Electronics": "#F59E0B",
}

render_page_header(
    "Product intelligence",
    "Classify a product description",
    "Use the saved TF-IDF and Linear SVM pipeline to identify the most likely approved product category.",
)
render_status_label("Live model")

st.markdown('<div style="height:.7rem"></div>', unsafe_allow_html=True)
left, right = st.columns([1.55, 1], gap="large")

with left:
    st.markdown('<div class="section-card">', unsafe_allow_html=True)
    st.subheader("Product description")
    text = st.text_area(
        "Description",
        key="classification_text",
        height=180,
        max_chars=5000,
        placeholder="Example: Lightweight cotton shirt for men, soft fabric and regular fit",
        label_visibility="collapsed",
    )
    st.caption(f"{len(text)} / 5,000 characters")

    submitted = st.button("Classify product", type="primary", use_container_width=True)
    st.markdown('</div>', unsafe_allow_html=True)

with right:
    st.markdown('<div class="section-card">', unsafe_allow_html=True)
    st.subheader("Classification context")
    st.markdown("**Approved categories**")
    for category in CATEGORY_ACCENTS:
        st.markdown(f'<span style="display:inline-block;margin:.2rem .25rem .2rem 0;padding:.28rem .55rem;border:1px solid {escape_html_text(CATEGORY_ACCENTS[category])};border-radius:999px;color:{escape_html_text(CATEGORY_ACCENTS[category])};font-size:.78rem;font-weight:800">{escape_html_text(category)}</span>', unsafe_allow_html=True)
    st.markdown("<hr style='border:none;border-top:1px solid #DDE4EC;margin:.8rem 0'>", unsafe_allow_html=True)
    st.caption("The decision score is a model score, not a calibrated probability or percentage.")
    st.markdown('</div>', unsafe_allow_html=True)

if submitted:
    try:
        with st.spinner("Analyzing product description..."):
            time.sleep(.25)
            result = ProductCategoryService().predict(text)
        category = result["predicted_category"]
        accent = CATEGORY_ACCENTS.get(category, "#3568FF")
        st.markdown('<div style="height:.8rem"></div>', unsafe_allow_html=True)
        st.markdown('<div class="section-card">', unsafe_allow_html=True)
        st.subheader("Prediction result")
        st.markdown(f'<div style="border-left:5px solid {escape_html_text(accent)};padding:.4rem 0 .4rem 1rem"><div style="color:#67748A;font-size:.78rem;text-transform:uppercase;font-weight:800">Predicted category</div><div style="font-size:1.85rem;font-weight:850;color:#172033;margin-top:.2rem">{escape_html_text(category)}</div></div>', unsafe_allow_html=True)
        score = result["confidence_or_decision_score"]
        if score is not None:
            st.metric("Linear SVM decision score", f"{float(score):.4f}")
            st.caption("This is a decision score, not a probability or confidence percentage.")
        st.caption(f"Model: {result['model_name']} · status: {result['prediction_status']}")
        st.markdown('</div>', unsafe_allow_html=True)
        if st.button("Clear and classify another", key="clear_classification"):
            st.session_state.classification_text = ""
            st.rerun()
    except ValidationError as exc:
        st.error(str(exc))
    except BackendError as exc:
        st.error(str(exc))
    except Exception:
        st.error("The category model could not complete this prediction.")
