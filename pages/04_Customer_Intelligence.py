from pathlib import Path

import pandas as pd
import streamlit as st

from src.services.segmentation_service import SegmentationService
from src.services.historical_snapshot_service import HistoricalSnapshotService
from src.ui.components import render_kpi_card, render_page_header, render_status_label
from src.utils.exceptions import BackendError, UnknownCustomerError, UnsupportedCutoffError, ValidationError

ROOT = Path(__file__).resolve().parents[1]
INSIGHTS_PATH = ROOT / "datasets/customer_insights/phase_9/customer_insights.csv"
APPROVED_CUTOFFS = ["2011-03-01", "2011-06-01"]

render_page_header(
    "Commerce Intelligence",
    "Customer Intelligence Profile",
    "Comprehensive customer profile uniting verified historical ledger behavior with forward-looking model intelligence.",
)
render_status_label("Customer 360")

st.markdown('<div style="height:.8rem"></div>', unsafe_allow_html=True)


@st.cache_data(ttl=300)
def load_customer_intelligence_data():
    snapshots = HistoricalSnapshotService(project_root=ROOT).load_all_approved()
    insights = pd.read_csv(INSIGHTS_PATH)
    insights["snapshot_cutoff"] = insights["snapshot_cutoff"].astype(str)
    return snapshots, insights


snapshots_df, insights_df = load_customer_intelligence_data()

# Customer Search Card
st.markdown('<div class="section-card">', unsafe_allow_html=True)
st.subheader("Customer Profile Lookup")
st.markdown(
    "Search any approved customer record across the historical cutoff dates. "
    "This unified profile strictly separates **actual historical behavior** from **forward-looking model estimates**."
)

c_col1, c_col2, c_act = st.columns([1.2, 1, 1], gap="medium")
with c_col1:
    customer_id = st.number_input(
        "Customer ID",
        min_value=1,
        step=1,
        value=None,
        placeholder="Enter an approved customer ID",
        key="ci_customer_id",
    )
with c_col2:
    cutoff = st.selectbox(
        "Historical Cutoff",
        APPROVED_CUTOFFS,
        index=1,
        key="ci_cutoff",
    )
with c_act:
    st.markdown('<div style="height:1.95rem"></div>', unsafe_allow_html=True)
    submitted = st.button("Generate Customer 360 Profile", type="primary", use_container_width=True)

st.markdown("</div>", unsafe_allow_html=True)

if submitted:
    st.markdown('<div style="height:.8rem"></div>', unsafe_allow_html=True)

    try:
        # Validate customer existence in snapshots
        if customer_id is None:
            raise ValidationError("Enter an approved customer ID.")
        cust_id = int(customer_id)
        if cutoff not in APPROVED_CUTOFFS:
            raise UnsupportedCutoffError(f"Cutoff {cutoff} is not supported. Choose from {APPROVED_CUTOFFS}.")

        snap_row = snapshots_df[
            (snapshots_df["customer_id"] == cust_id) & (snapshots_df["snapshot_cutoff"] == cutoff)
        ]

        if snap_row.empty:
            raise UnknownCustomerError(
                f"No verified customer snapshot found for Customer ID {cust_id} at cutoff {cutoff}."
            )

        snap = snap_row.iloc[0]

        # Retrieve segmentation via SegmentationService
        seg_result = SegmentationService().assign(cust_id, cutoff)
        segment_id = seg_result["segment_id"]

        # Retrieve model insights predictions
        insight_row = insights_df[
            (insights_df["customer_id"] == cust_id) & (insights_df["snapshot_cutoff"] == cutoff)
        ]
        has_predictions = not insight_row.empty

        # Profile Overview Banner
        st.markdown(
            f"""
            <div class="kpi-card" style="border-left: 5px solid #3568FF; margin-bottom: 1rem">
              <div style="display:flex; justify-content:space-between; align-items:center">
                <div>
                  <div class="kpi-label">Customer Record</div>
                  <div style="font-size: 1.6rem; font-weight: 850; color: #172033">Customer {cust_id}</div>
                </div>
                <div style="text-align:right">
                  <div class="kpi-label">Snapshot Date</div>
                  <div style="font-size: 1.15rem; font-weight: 800; color: #3568FF">{cutoff}</div>
                </div>
              </div>
            </div>
            """,
            unsafe_allow_html=True,
        )

        # SECTION A: Actual Historical Behavior
        st.markdown('<div class="section-card">', unsafe_allow_html=True)
        st.subheader("Section A: Actual Historical Activity (Verified Ledger Data)")
        st.caption(f"Observed customer metrics prior to {cutoff}. These represent ground-truth historical records.")

        hist_c1, hist_c2, hist_c3, hist_c4 = st.columns(4)
        with hist_c1:
            render_kpi_card(
                "Historical Invoices",
                f"{int(snap['historical_invoice_count']):,}",
                "Paid order count",
                "#3568FF",
            )
        with hist_c2:
            render_kpi_card(
                "Historical Gross Spend",
                f"{float(snap['historical_gross_spend']):,.2f}",
                "No currency label assigned",
                "#18A999",
            )
        with hist_c3:
            render_kpi_card(
                "Distinct Products",
                f"{int(snap['historical_unique_stockcode_count']):,}",
                "Unique StockCodes",
                "#F59E0B",
            )
        with hist_c4:
            render_kpi_card(
                "Recency (Days)",
                f"{float(snap['recency_days']):,.1f}",
                "Days since last invoice",
                "#A855F7",
            )

        st.markdown('<div style="height:.6rem"></div>', unsafe_allow_html=True)

        detail_c1, detail_c2, detail_c3, detail_c4 = st.columns(4)
        detail_c1.metric(
            "Avg Invoice Value",
            f"{float(snap.get('historical_average_invoice_value', 0.0)):,.2f}",
        )
        detail_c2.metric(
            "Active Months",
            f"{int(snap.get('historical_active_month_count', 0)):,}",
        )
        detail_c3.metric(
            "Total Quantity",
            f"{float(snap.get('historical_total_quantity', 0.0)):,.0f}",
        )
        detail_c4.metric(
            "Weekday Invoices",
            f"{int(snap.get('historical_weekday_invoice_count', 0)):,}",
        )

        st.markdown("</div>", unsafe_allow_html=True)

        st.markdown('<div style="height:.8rem"></div>', unsafe_allow_html=True)

        # SECTION B: Forward-Looking Model Predictions
        st.markdown('<div class="section-card">', unsafe_allow_html=True)
        st.subheader("Section B: Model Predictions & Segmentation (Forward-Looking AI Outlook)")
        st.caption("Statistical model estimates over the subsequent 90-day horizon. These are model projections, not factual outcomes.")

        if has_predictions:
            pred = insight_row.iloc[0]
            rep_prob = float(pred["repeat_purchase_probability"])
            rep_status = int(pred["predicted_repeat_purchase_class"])
            pred_spend = float(pred["predicted_future_gross_spending"])

            pred_c1, pred_c2, pred_c3 = st.columns(3)

            with pred_c1:
                status_text = "Likely repeat purchase" if rep_status == 1 else "Likely no repeat purchase"
                accent = "#18A999" if rep_status == 1 else "#3568FF"
                st.markdown('<div class="kpi-card">', unsafe_allow_html=True)
                st.markdown('<div class="kpi-label">Repeat Purchase (90-Day)</div>', unsafe_allow_html=True)
                st.markdown(f'<div class="kpi-value" style="color:{accent}">{status_text}</div>', unsafe_allow_html=True)
                st.progress(rep_prob)
                st.markdown(f'<div class="kpi-note">Probability: <strong>{rep_prob:.1%}</strong> · Gradient Boosting</div>', unsafe_allow_html=True)
                st.markdown("</div>", unsafe_allow_html=True)

            with pred_c2:
                spend_accent = "#DF5B68" if pred_spend < 0 else "#3568FF"
                st.markdown('<div class="kpi-card">', unsafe_allow_html=True)
                st.markdown('<div class="kpi-label">Future Spending (90-Day)</div>', unsafe_allow_html=True)
                st.markdown(f'<div class="kpi-value" style="color:{spend_accent}">{pred_spend:,.2f}</div>', unsafe_allow_html=True)
                if pred_spend < 0:
                    st.markdown('<div class="kpi-note" style="color:#DF5B68">Unclipped negative raw projection</div>', unsafe_allow_html=True)
                else:
                    st.markdown('<div class="kpi-note">Ridge Regression · No currency label</div>', unsafe_allow_html=True)
                st.markdown("</div>", unsafe_allow_html=True)

            with pred_c3:
                seg_accent = "#3568FF" if segment_id == 0 else ("#18A999" if segment_id == 1 else "#F59E0B")
                st.markdown('<div class="kpi-card">', unsafe_allow_html=True)
                st.markdown('<div class="kpi-label">Behavioral Segment</div>', unsafe_allow_html=True)
                st.markdown(f'<div class="kpi-value" style="color:{seg_accent}">Segment {segment_id}</div>', unsafe_allow_html=True)
                st.markdown(f'<div class="kpi-note">KMeans Model (K=3) · March-fitted</div>', unsafe_allow_html=True)
                st.markdown("</div>", unsafe_allow_html=True)
        else:
            st.info("No forward-looking predictions are pre-indexed for this customer snapshot.")

        st.markdown("</div>", unsafe_allow_html=True)

        st.markdown('<div style="height:.8rem"></div>', unsafe_allow_html=True)

        # SECTION C: Governance & Data Lineage Notice
        st.markdown('<div class="section-card">', unsafe_allow_html=True)
        st.subheader("Data Lineage & Governance Principles")
        st.markdown(
            """
            - **Strict Cutoff Discipline:** Historical activity strictly reflects transactions processed before the selected cutoff date. No future information is leaked.
            - **Actual vs. Prediction Separation:** Historical gross spending and predicted future spending are distinct fields and are never combined or presented as factual equivalents.
            - **Raw Spending Units:** Values reflect recorded ledger units from Online Retail II. In compliance with governance rules, no currency symbol or currency name is assigned.
            - **Unclipped Projections:** Linear model projections are displayed raw without artificial clipping.
            """
        )
        st.markdown("</div>", unsafe_allow_html=True)

    except UnknownCustomerError as exc:
        st.error(f"Unknown Customer: {exc}")
    except UnsupportedCutoffError as exc:
        st.error(f"Unsupported Cutoff: {exc}")
    except ValidationError as exc:
        st.error(f"Validation Error: {exc}")
    except BackendError as exc:
        st.error(f"Backend Service Error: {exc}")
    except Exception:
        st.error("The customer intelligence profile could not be generated. Please verify the customer ID and cutoff.")
