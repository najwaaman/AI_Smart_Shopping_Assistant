from pathlib import Path

import streamlit as st

from src.services.repeat_purchase_service import RepeatPurchaseService
from src.services.spending_prediction_service import SpendingPredictionService
from src.services.historical_snapshot_service import HistoricalSnapshotService
from src.ui.components import render_page_header, render_status_label
from src.utils.exceptions import BackendError, UnknownCustomerError, UnsupportedCutoffError, ValidationError


ROOT = Path(__file__).resolve().parents[1]
APPROVED_CUTOFFS = ["2011-03-01", "2011-06-01"]

render_page_header(
    "Customer intelligence",
    "Repeat purchase and future spending",
    "Use approved March/June customer records to distinguish historical behaviour from 90-day model predictions.",
)
render_status_label("Live prediction services")

st.markdown('<div style="height:.7rem"></div>', unsafe_allow_html=True)
repeat_tab, spending_tab = st.tabs(["Repeat purchase", "Future spending"])


def get_customer_context(customer_id, cutoff):
    return HistoricalSnapshotService(project_root=ROOT).get_customer(customer_id, cutoff)


def render_historical_context(context):
    if context is None:
        st.warning("No approved historical snapshot is available for this customer-cutoff combination.")
        return
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Historical invoices", f"{int(context['historical_invoice_count']):,}")
    c2.metric("Historical spending", f"{float(context['historical_gross_spend']):,.2f}")
    c3.metric("Distinct products", f"{int(context['historical_unique_stockcode_count']):,}")
    c4.metric("Recency (days)", f"{float(context['recency_days']):,.1f}")


with repeat_tab:
    st.markdown('<div class="section-card">', unsafe_allow_html=True)
    st.subheader("Repeat-purchase prediction")
    st.caption("Predict whether the customer makes at least one qualifying paid purchase during the next 90 days.")
    c1, c2, action = st.columns([1.2, 1, 1], gap="medium")
    with c1:
        repeat_customer = st.number_input("Customer ID", min_value=1, step=1, value=None, placeholder="Enter an approved customer ID", key="repeat_customer")
    with c2:
        repeat_cutoff = st.selectbox("Approved cutoff", APPROVED_CUTOFFS, key="repeat_cutoff")
    with action:
        st.markdown('<div style="height:1.95rem"></div>', unsafe_allow_html=True)
        repeat_submit = st.button("Run repeat-purchase model", type="primary", use_container_width=True)
    st.markdown('</div>', unsafe_allow_html=True)

    if repeat_submit:
        try:
            with st.spinner("Running saved classification model..."):
                result = RepeatPurchaseService().predict(int(repeat_customer or 0), repeat_cutoff)
            context = get_customer_context(repeat_customer, repeat_cutoff)

            st.markdown('<div style="height:.8rem"></div>', unsafe_allow_html=True)
            st.markdown('<div class="section-card">', unsafe_allow_html=True)
            st.subheader("Historical context")
            render_historical_context(context)
            st.markdown('</div>', unsafe_allow_html=True)

            st.markdown('<div style="height:.8rem"></div>', unsafe_allow_html=True)
            left, right = st.columns([1.15, 1], gap="large")
            probability = result["positive_class_probability"]
            predicted = result["predicted_repeat_purchase_status"]
            label = "Likely repeat purchase" if predicted == 1 else "Likely no repeat purchase"
            accent = "#18A999" if predicted == 1 else "#3568FF"
            with left:
                st.markdown('<div class="kpi-card">', unsafe_allow_html=True)
                st.markdown('<div class="kpi-label">90-day prediction</div>', unsafe_allow_html=True)
                st.markdown(f'<div class="kpi-value" style="color:{accent}">{label}</div>', unsafe_allow_html=True)
                st.progress(probability)
                st.markdown(f'<div class="kpi-note">Positive-class probability: {probability:.1%}</div>', unsafe_allow_html=True)
                st.markdown('</div>', unsafe_allow_html=True)
            with right:
                st.markdown('<div class="kpi-card">', unsafe_allow_html=True)
                st.markdown('<div class="kpi-label">Model</div>', unsafe_allow_html=True)
                st.markdown('<div style="font-size:1.15rem;font-weight:800;margin:.35rem 0">Gradient Boosting</div>', unsafe_allow_html=True)
                st.markdown(f'<div class="kpi-note">Cutoff {repeat_cutoff} · 90-day horizon</div>', unsafe_allow_html=True)
                st.caption("A model estimate, not a guarantee or factual future outcome.")
                st.markdown('</div>', unsafe_allow_html=True)
        except UnknownCustomerError as exc:
            st.error(str(exc))
        except UnsupportedCutoffError as exc:
            st.error(str(exc))
        except ValidationError as exc:
            st.error(str(exc))
        except BackendError as exc:
            st.error(str(exc))
        except Exception:
            st.error("The repeat-purchase prediction could not be completed.")


with spending_tab:
    st.markdown('<div class="section-card">', unsafe_allow_html=True)
    st.subheader("Future spending prediction")
    st.caption("Raw Ridge model output for the next 90 days. No currency label is inferred.")
    c1, c2, action = st.columns([1.2, 1, 1], gap="medium")
    with c1:
        spending_customer = st.number_input("Customer ID", min_value=1, step=1, value=None, placeholder="Enter an approved customer ID", key="spending_customer")
    with c2:
        spending_cutoff = st.selectbox("Approved cutoff", APPROVED_CUTOFFS, key="spending_cutoff")
    with action:
        st.markdown('<div style="height:1.95rem"></div>', unsafe_allow_html=True)
        spending_submit = st.button("Predict future spending", type="primary", use_container_width=True)
    st.markdown('</div>', unsafe_allow_html=True)

    if spending_submit:
        try:
            with st.spinner("Running saved Ridge model..."):
                result = SpendingPredictionService().predict(int(spending_customer or 0), spending_cutoff)
            context = get_customer_context(spending_customer, spending_cutoff)

            st.markdown('<div style="height:.8rem"></div>', unsafe_allow_html=True)
            st.markdown('<div class="section-card">', unsafe_allow_html=True)
            st.subheader("Historical context")
            render_historical_context(context)
            if context is not None:
                st.caption(f"Historical average invoice value: {float(context['historical_average_invoice_value']):,.2f}")
            st.markdown('</div>', unsafe_allow_html=True)

            st.markdown('<div style="height:.8rem"></div>', unsafe_allow_html=True)
            left, right = st.columns([1.15, 1], gap="large")
            predicted = result["predicted_future_gross_spending"]
            with left:
                st.markdown('<div class="kpi-card">', unsafe_allow_html=True)
                st.markdown('<div class="kpi-label">Predicted 90-day gross spending</div>', unsafe_allow_html=True)
                st.markdown(f'<div class="kpi-value" style="color:#3568FF">{predicted:,.2f}</div>', unsafe_allow_html=True)
                st.markdown('<div class="kpi-note">Raw model prediction; no currency label is assigned</div>', unsafe_allow_html=True)
                st.markdown('</div>', unsafe_allow_html=True)
            with right:
                st.markdown('<div class="kpi-card">', unsafe_allow_html=True)
                st.markdown('<div class="kpi-label">Model</div>', unsafe_allow_html=True)
                st.markdown('<div style="font-size:1.15rem;font-weight:800;margin:.35rem 0">Ridge Regression</div>', unsafe_allow_html=True)
                st.markdown(f'<div class="kpi-note">Cutoff {spending_cutoff} · 90-day horizon</div>', unsafe_allow_html=True)
                if result["negative_prediction_warning"]:
                    st.warning("The saved model produced a negative raw prediction. It is shown unchanged and has not been clipped to zero.")
                st.caption("Historical spending and predicted future spending are separate values.")
                st.markdown('</div>', unsafe_allow_html=True)
        except UnknownCustomerError as exc:
            st.error(str(exc))
        except UnsupportedCutoffError as exc:
            st.error(str(exc))
        except ValidationError as exc:
            st.error(str(exc))
        except BackendError as exc:
            st.error(str(exc))
        except Exception:
            st.error("The spending prediction could not be completed.")
