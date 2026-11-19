import pandas as pd
import streamlit as st
from src.ui.components import escape_html_text

from src.services.recommendation_service import RecommendationService
from src.ui.components import render_page_header, render_status_label
from src.utils.exceptions import BackendError, ValidationError, UnknownCustomerError, UnsupportedCutoffError


render_page_header(
    "Personalized commerce",
    "Product recommendations",
    "Explore ranked item-item recommendations for customers represented in the approved June dataset.",
)
render_status_label("Live recommendations")

st.markdown('<div style="height:.7rem"></div>', unsafe_allow_html=True)
st.markdown('<div class="section-card">', unsafe_allow_html=True)
st.subheader("Recommendation input")
col1, col2, col3, action = st.columns([1.2, 1, 1, 1], gap="medium")
with col1:
    customer_id = st.number_input("Customer ID", min_value=1, step=1, value=None, placeholder="Enter an approved customer ID")
with col2:
    cutoff = st.selectbox("Approved cutoff", ["2011-06-01"])
with col3:
    k = st.selectbox("Recommendations", [5, 10, 20], index=1)
with action:
    st.markdown('<div style="height:1.95rem"></div>', unsafe_allow_html=True)
    submitted = st.button("Generate recommendations", type="primary", use_container_width=True)
st.markdown('</div>', unsafe_allow_html=True)

if submitted:
    try:
        with st.spinner("Preparing recommendation ranking..."):
            result = RecommendationService().recommendations(int(customer_id or 0), k=k, cutoff=cutoff)
        st.markdown('<div style="height:.8rem"></div>', unsafe_allow_html=True)

        history = pd.read_csv("datasets/features/recommendation/customer_recommendation_features.csv")
        june_history = history[(history["snapshot_cutoff"] == cutoff) & (history["Customer ID"] == int(customer_id or 0))]
        history_count = int(june_history["customer_interaction_count"].iloc[0]) if not june_history.empty else 0

        if history_count > 0 and history_count <= 5:
            st.info("Known customer with limited purchase history. The displayed ranking comes from the approved recommendation records.")
        elif history_count == 0:
            st.warning("Customer record exists, but approved purchase history is insufficient for personalized ranking.")

        st.markdown('<div class="section-card">', unsafe_allow_html=True)
        st.subheader(f"Top {k} recommendations")
        st.caption(f"Customer {int(customer_id or 0)} · cutoff {cutoff} · {result['recommendation_method']}")
        st.markdown('</div>', unsafe_allow_html=True)

        recommendations = result["recommendations"]
        if not recommendations:
            st.warning("No recommendations were returned. No alternate customer or result set was substituted.")
        else:
            cols = st.columns(2)
            for index, item in enumerate(recommendations):
                with cols[index % 2]:
                    description = escape_html_text(item.get("Description") or "No description available")
                    stockcode = escape_html_text(item.get("StockCode"))
                    recommendation_source = escape_html_text(item.get("recommendation_source", ""))
                    st.markdown(
                        f'<div class="kpi-card" style="min-height:178px;margin-bottom:.8rem"><div style="display:flex;justify-content:space-between;align-items:center"><div class="kpi-label">Rank {int(item["rank"])}</div><div style="font-size:.72rem;color:#3568FF;font-weight:800">{recommendation_source}</div></div><div style="font-size:1.04rem;font-weight:850;margin:.8rem 0 .35rem;color:#172033">{description}</div><div style="color:#67748A;font-size:.82rem">StockCode <strong>{stockcode}</strong></div><div style="margin-top:.9rem;font-size:.78rem;color:#67748A">Item-item ranking score: {float(item["score"]):.4f}</div></div>',
                        unsafe_allow_html=True,
                    )
    except UnknownCustomerError:
        st.error("Unknown customer: no approved Phase 8 recommendation record exists for this customer and cutoff.")
    except UnsupportedCutoffError:
        st.error("Unsupported cutoff: recommendations are available only for the approved June 1, 2011 dataset.")
    except ValidationError as exc:
        st.error(str(exc))
    except BackendError as exc:
        st.error(str(exc))
    except Exception:
        st.error("Recommendations could not be generated. No alternate result was substituted.")
