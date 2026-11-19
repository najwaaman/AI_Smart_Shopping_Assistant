from pathlib import Path

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

from src.services.segmentation_service import SegmentationService
from src.services.historical_snapshot_service import HistoricalSnapshotService
from src.ui.components import render_kpi_card, render_page_header, render_status_label
from src.utils.exceptions import BackendError, UnknownCustomerError, UnsupportedCutoffError, ValidationError

ROOT = Path(__file__).resolve().parents[1]
SEGMENTATION_REPORTS = ROOT / "reports/segmentation/phase_9"
APPROVED_CUTOFFS = ["2011-03-01", "2011-06-01"]

render_page_header(
    "Customer Intelligence",
    "Customer Segments",
    "Explore behavioral customer clusters fitted on March 2011 and applied to June 2011.",
)
render_status_label("Descriptive segmentation")

st.markdown('<div style="height:.8rem"></div>', unsafe_allow_html=True)


@st.cache_data(ttl=300)
def load_segmentation_artifacts():
    profiles = pd.read_csv(SEGMENTATION_REPORTS / "Cluster_Profiles.csv")
    stability = pd.read_csv(SEGMENTATION_REPORTS / "Temporal_Stability_Report.csv")
    comparison = pd.read_csv(SEGMENTATION_REPORTS / "Clustering_Model_Comparison.csv")
    assignments = pd.read_csv(SEGMENTATION_REPORTS / "Customer_Segment_Assignments.csv")
    return profiles, stability, comparison, assignments


profiles_df, stability_df, comparison_df, assignments_df = load_segmentation_artifacts()

total_records = len(assignments_df)
unique_customers = assignments_df["customer_id"].nunique()
num_clusters = len(profiles_df)

col1, col2, col3, col4 = st.columns(4)
with col1:
    render_kpi_card("Number of clusters", f"{num_clusters}", "Selected KMeans (K=3)", "#3568FF")
with col2:
    render_kpi_card("Customer-cutoff records", f"{total_records:,}", "March (1,682) + June (2,718)", "#18A999")
with col3:
    render_kpi_card("Distinct customers", f"{unique_customers:,}", "De-duplicated across cutoffs", "#F59E0B")
with col4:
    render_kpi_card("Largest segment", "Segment 0 (98.2%)", "4,322 customer-cutoff records", "#A855F7")

st.caption(
    "Note on population counts: Customer-cutoff records (4,400) reflect snapshots across March and June 2011. "
    "Distinct customers (2,718) represent unique customer identifiers who may appear at one or both cutoffs."
)

st.markdown('<div style="height:.9rem"></div>', unsafe_allow_html=True)

tab_profiles, tab_stability, tab_evaluation, tab_lookup = st.tabs(
    [
        "Cluster Profiles & Distribution",
        "Temporal Stability",
        "Algorithm Evaluation & PCA",
        "Customer Lookup",
    ]
)

# -----------------------------------------------------------------------------
# TAB 1: Cluster Profiles & Distribution
# -----------------------------------------------------------------------------
with tab_profiles:
    st.markdown('<div class="section-card">', unsafe_allow_html=True)
    st.subheader("Section A: Cluster Profiles")
    st.markdown(
        "Cluster profiles aggregate historical customer behavior by assigned segment. "
        "Segments are descriptive behavioral groupings based on four features: historical gross spending, "
        "invoice count, total quantity, and active month count."
    )

    # Data Quality Restriction: Omit average_recency and average_unique_products
    display_profiles = profiles_df[
        [
            "segment_id",
            "customer_count",
            "unique_customers",
            "percentage",
            "average_historical_gross_spending",
            "median_historical_gross_spending",
            "average_invoice_frequency",
        ]
    ].copy()

    display_profiles.columns = [
        "Segment ID",
        "Record Count",
        "Unique Customers",
        "Share (%)",
        "Avg Gross Spend",
        "Median Gross Spend",
        "Avg Invoices",
    ]

    st.dataframe(
        display_profiles.style.format(
            {
                "Record Count": "{:,}",
                "Unique Customers": "{:,}",
                "Share (%)": "{:.2f}%",
                "Avg Gross Spend": "{:,.2f}",
                "Median Gross Spend": "{:,.2f}",
                "Avg Invoices": "{:.2f}",
            }
        ),
        width="stretch",
        hide_index=True,
    )

    st.info(
        "**Data Quality Notice:** In accordance with the Phase 9B data audit, `average_recency` and "
        "`average_unique_products` are strictly omitted from this presentation. In the upstream pipeline, "
        "both columns duplicated `historical_invoice_count` due to aggregation column scope. "
        "Replacement values are not invented or approximated. "
        "No marketing personas (such as 'Champions' or 'VIPs') are assigned; clusters remain strictly Segments 0, 1, and 2."
    )
    st.markdown("</div>", unsafe_allow_html=True)

    st.markdown('<div style="height:.8rem"></div>', unsafe_allow_html=True)

    st.markdown('<div class="section-card">', unsafe_allow_html=True)
    st.subheader("Section B: Segment Distribution")
    st.markdown(
        "Segment 0 accounts for the vast majority of customer snapshots. "
        "Segments 1 and 2 represent small, high-spending cohorts."
    )

    chart_col1, chart_col2 = st.columns([1, 1.3], gap="medium")

    with chart_col1:
        st.markdown("**Share of Customer Snapshots**")
        pie_fig = go.Figure(
            go.Pie(
                labels=[f"Segment {row['segment_id']}" for _, row in profiles_df.iterrows()],
                values=profiles_df["customer_count"],
                hole=0.55,
                marker=dict(colors=["#3568FF", "#18A999", "#F59E0B"]),
                textinfo="label+percent",
                hoverinfo="label+value+percent",
            )
        )
        pie_fig.update_layout(
            template="plotly_white",
            height=320,
            margin=dict(l=10, r=10, t=10, b=10),
            paper_bgcolor="rgba(0,0,0,0)",
            showlegend=True,
        )
        st.plotly_chart(pie_fig, width="stretch")

    with chart_col2:
        st.markdown("**Detailed Segment Scale (Linear vs Log Comparison)**")
        scale_choice = st.radio(
            "Y-axis Scale",
            ["Logarithmic (Recommended for visibility of Segments 1 & 2)", "Linear"],
            horizontal=True,
            key="dist_scale_choice",
        )
        is_log = "Logarithmic" in scale_choice

        bar_fig = px.bar(
            profiles_df,
            x="segment_id",
            y="customer_count",
            text="customer_count",
            color="segment_id",
            color_discrete_sequence=["#3568FF", "#18A999", "#F59E0B"],
            labels={"segment_id": "Segment", "customer_count": "Customer-Cutoff Records"},
        )
        bar_fig.update_traces(
            texttemplate="%{text:,}",
            textposition="outside",
            cliponaxis=False,
        )
        bar_fig.update_layout(
            template="plotly_white",
            height=280,
            margin=dict(l=15, r=15, t=15, b=10),
            paper_bgcolor="rgba(0,0,0,0)",
            plot_bgcolor="rgba(0,0,0,0)",
            showlegend=False,
            yaxis_type="log" if is_log else "linear",
        )
        bar_fig.update_xaxes(
            tickmode="array",
            tickvals=[0, 1, 2],
            ticktext=["Segment 0 (Core: 4,322)", "Segment 1 (Ultra: 5)", "Segment 2 (High: 73)"],
            showgrid=False,
        )
        bar_fig.update_yaxes(
            title="Records (Log scale)" if is_log else "Records",
            showgrid=True,
            gridcolor="#EEF2F7",
        )
        st.plotly_chart(bar_fig, width="stretch")

    st.markdown("</div>", unsafe_allow_html=True)

# -----------------------------------------------------------------------------
# TAB 2: Temporal Stability
# -----------------------------------------------------------------------------
with tab_stability:
    st.markdown('<div class="section-card">', unsafe_allow_html=True)
    st.subheader("Section C: Temporal Stability (March vs. June 2011)")
    st.markdown(
        "KMeans clustering was fitted on the March 1, 2011 feature distribution and applied directly to the June 1, 2011 "
        "snapshot using the March-fitted imputer and scaler. This evaluation compares cluster distribution across the two approved snapshots."
    )

    stab_chart_col, stab_table_col = st.columns([1.3, 1], gap="medium")

    with stab_chart_col:
        st.markdown("**Segment Distribution by Cutoff Period**")
        melted_stab = pd.melt(
            stability_df,
            id_vars=["segment_id"],
            value_vars=["march_percentage", "june_percentage"],
            var_name="Period",
            value_name="Percentage",
        )
        melted_stab["Period"] = melted_stab["Period"].map(
            {"march_percentage": "March 2011 (Fit)", "june_percentage": "June 2011 (Applied)"}
        )
        melted_stab["Segment"] = melted_stab["segment_id"].apply(lambda s: f"Segment {s}")

        stab_fig = px.bar(
            melted_stab,
            x="Segment",
            y="Percentage",
            color="Period",
            barmode="group",
            text="Percentage",
            color_discrete_sequence=["#3568FF", "#18A999"],
        )
        stab_fig.update_traces(texttemplate="%{text:.2f}%", textposition="outside", cliponaxis=False)
        stab_fig.update_layout(
            template="plotly_white",
            height=320,
            margin=dict(l=15, r=15, t=15, b=10),
            paper_bgcolor="rgba(0,0,0,0)",
            plot_bgcolor="rgba(0,0,0,0)",
            legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
        )
        stab_fig.update_yaxes(title="Share of Snapshot (%)", showgrid=True, gridcolor="#EEF2F7")
        st.plotly_chart(stab_fig, width="stretch")

    with stab_table_col:
        st.markdown("**Stability Metrics Table**")
        display_stab = stability_df.copy()
        display_stab.columns = [
            "Segment",
            "March Count",
            "June Count",
            "March Share (%)",
            "June Share (%)",
        ]
        display_stab["Segment"] = display_stab["Segment"].apply(lambda s: f"Segment {s}")
        st.dataframe(
            display_stab.style.format(
                {
                    "March Count": "{:,}",
                    "June Count": "{:,}",
                    "March Share (%)": "{:.2f}%",
                    "June Share (%)": "{:.2f}%",
                }
            ),
            width="stretch",
            hide_index=True,
        )

    st.caption(
        "Important limitation: This temporal comparison assesses stability across the two approved snapshots (March and June 2011). "
        "It evaluates cluster migration across two fixed historical points and does not claim unbounded multi-year stability."
    )
    st.markdown("</div>", unsafe_allow_html=True)

# -----------------------------------------------------------------------------
# TAB 3: Algorithm Evaluation & PCA
# -----------------------------------------------------------------------------
with tab_evaluation:
    st.markdown('<div class="section-card">', unsafe_allow_html=True)
    st.subheader("Section D: Clustering Algorithm Evaluation")
    st.markdown(
        "During Phase 9B, KMeans and Agglomerative clustering were evaluated across cluster counts $K \\in [3, 6]$. "
        "The selected configuration is **KMeans with 3 clusters**, achieving the highest Silhouette score and strongest Calinski-Harabasz index."
    )

    eval_col1, eval_col2 = st.columns([1.5, 1], gap="medium")

    with eval_col1:
        st.markdown("**Model Comparison Matrix**")
        display_comp = comparison_df.copy()
        display_comp.columns = [
            "Algorithm",
            "Clusters (K)",
            "Silhouette Score",
            "Davies-Bouldin",
            "Calinski-Harabasz",
            "Noise",
            "Inertia",
        ]

        def highlight_selected(row):
            if row["Algorithm"] == "KMeans" and row["Clusters (K)"] == 3:
                return ["background-color: #EBF3FF; font-weight: bold; color: #172033"] * len(row)
            return [""] * len(row)

        st.dataframe(
            display_comp.style.apply(highlight_selected, axis=1).format(
                {
                    "Silhouette Score": "{:.4f}",
                    "Davies-Bouldin": "{:.4f}",
                    "Calinski-Harabasz": "{:,.2f}",
                    "Noise": "{:.1f}",
                    "Inertia": lambda x: f"{x:,.2f}" if pd.notnull(x) and x != "" else "N/A",
                }
            ),
            width="stretch",
            hide_index=True,
        )

    with eval_col2:
        st.markdown("**Metric Interpretation**")
        st.markdown(
            """
            - **Silhouette Score (0.9159):** Measures intra-cluster cohesion versus nearest-cluster separation ($-1$ to $+1$; higher is better).
            - **Davies-Bouldin Index (0.5153):** Evaluates similarity between clusters based on dispersion and distance ($0$ to $\\infty$; lower is better).
            - **Calinski-Harabasz (3,576.47):** Ratio of between-cluster variance to within-cluster variance (higher is better).
            - **Inertia (26,573.06):** Sum of squared distances to closest cluster centers (KMeans only).
            """
        )

    st.markdown("</div>", unsafe_allow_html=True)

    st.markdown('<div style="height:.8rem"></div>', unsafe_allow_html=True)

    st.markdown('<div class="section-card">', unsafe_allow_html=True)
    st.subheader("Section E: Principal Component Analysis (PCA) Projection")
    st.markdown(
        "This visualization projects the 4-dimensional clustering feature space onto its first two principal components. "
        "It illustrates the spatial separation of March and June customer records across the three clusters."
    )

    pca_img_path = SEGMENTATION_REPORTS / "charts/segmentation_pca.png"
    if pca_img_path.is_file():
        st.image(
            str(pca_img_path),
            caption=(
                "Figure 1: Two-dimensional PCA projection of customer feature space across March and June 2011 cohorts. "
                "Notice: PCA is a lower-dimensional projection for visualization only; actual clustering was performed in the standardized 4D feature space."
            ),
            width="stretch",
        )
    else:
        st.warning("PCA projection chart artifact not found on disk.")

    st.markdown("</div>", unsafe_allow_html=True)

# -----------------------------------------------------------------------------
# TAB 4: Customer Lookup
# -----------------------------------------------------------------------------
with tab_lookup:
    st.markdown('<div class="section-card">', unsafe_allow_html=True)
    st.subheader("Section F: Individual Customer Segment Lookup")
    st.markdown(
        "Look up a customer's verified historical cluster assignment using `SegmentationService.assign()`. "
        "This lookup retrieves an existing approved segment assignment from the Phase 9 dataset; "
        "it does not recalculate features or generate new cluster assignments dynamically."
    )

    lookup_col1, lookup_col2, lookup_action = st.columns([1.2, 1, 1], gap="medium")
    with lookup_col1:
        lookup_customer_id = st.number_input(
            "Customer ID",
            min_value=1,
            step=1,
            value=None,
            placeholder="Enter an approved customer ID",
            key="segment_lookup_customer",
        )
    with lookup_col2:
        lookup_cutoff = st.selectbox(
            "Approved Cutoff",
            APPROVED_CUTOFFS,
            index=1,
            key="segment_lookup_cutoff",
        )
    with lookup_action:
        st.markdown('<div style="height:1.95rem"></div>', unsafe_allow_html=True)
        lookup_submitted = st.button("Lookup customer segment", type="primary", use_container_width=True)

    st.markdown("</div>", unsafe_allow_html=True)

    if lookup_submitted:
        st.markdown('<div style="height:.8rem"></div>', unsafe_allow_html=True)
        try:
            with st.spinner("Retrieving verified customer segment assignment..."):
                result = SegmentationService().assign(int(lookup_customer_id or 0), lookup_cutoff)

            segment_id = result["segment_id"]
            model_name = result.get("model_name", "KMeans")
            profile_data = result.get("segment_profile", {})

            # Retrieve customer's snapshot historical spending if available
            customer_hist_spend = None
            try:
                customer_snapshot = HistoricalSnapshotService(project_root=ROOT).get_customer(
                    int(lookup_customer_id or 0), lookup_cutoff
                )
                if customer_snapshot is not None:
                    customer_hist_spend = float(customer_snapshot["historical_gross_spend"])
            except (FileNotFoundError, ValueError):
                customer_hist_spend = None

            segment_accent = "#3568FF" if segment_id == 0 else ("#18A999" if segment_id == 1 else "#F59E0B")

            st.markdown('<div class="section-card">', unsafe_allow_html=True)
            st.subheader(f"Customer {int(lookup_customer_id or 0)} Assignment Result")

            res_c1, res_c2, res_c3 = st.columns(3)
            with res_c1:
                st.markdown('<div class="kpi-card">', unsafe_allow_html=True)
                st.markdown('<div class="kpi-label">Assigned Cluster</div>', unsafe_allow_html=True)
                st.markdown(
                    f'<div class="kpi-value" style="color:{segment_accent}">Segment {segment_id}</div>',
                    unsafe_allow_html=True,
                )
                st.markdown(f'<div class="kpi-note">Model: {model_name} (K=3)</div>', unsafe_allow_html=True)
                st.markdown("</div>", unsafe_allow_html=True)

            with res_c2:
                st.markdown('<div class="kpi-card">', unsafe_allow_html=True)
                st.markdown('<div class="kpi-label">Snapshot Cutoff</div>', unsafe_allow_html=True)
                st.markdown(
                    f'<div class="kpi-value" style="font-size:1.45rem">{lookup_cutoff}</div>',
                    unsafe_allow_html=True,
                )
                st.markdown('<div class="kpi-note">Historical snapshot point</div>', unsafe_allow_html=True)
                st.markdown("</div>", unsafe_allow_html=True)

            with res_c3:
                st.markdown('<div class="kpi-card">', unsafe_allow_html=True)
                st.markdown('<div class="kpi-label">Cluster Record Share</div>', unsafe_allow_html=True)
                share = profile_data.get("percentage", 0.0)
                st.markdown(f'<div class="kpi-value">{share:.2f}%</div>', unsafe_allow_html=True)
                st.markdown(
                    f'<div class="kpi-note">{profile_data.get("customer_count", 0):,} total cohort records</div>',
                    unsafe_allow_html=True,
                )
                st.markdown("</div>", unsafe_allow_html=True)

            st.markdown('<div style="height:.8rem"></div>', unsafe_allow_html=True)

            # Benchmark comparison
            st.markdown("#### Comparison with Cluster Spending Benchmarks")
            bench_col1, bench_col2, bench_col3 = st.columns(3)

            cluster_avg_spend = float(profile_data.get("average_historical_gross_spending", 0.0))
            cluster_med_spend = float(profile_data.get("median_historical_gross_spending", 0.0))

            with bench_col1:
                if customer_hist_spend is not None:
                    st.metric("Customer Historical Spend", f"{customer_hist_spend:,.2f}")
                else:
                    st.metric("Customer Historical Spend", "Context not indexed")

            with bench_col2:
                delta_str = (
                    f"{customer_hist_spend - cluster_avg_spend:+,.2f} vs cluster avg"
                    if customer_hist_spend is not None
                    else None
                )
                st.metric("Cluster Average Spend", f"{cluster_avg_spend:,.2f}", delta=delta_str)

            with bench_col3:
                delta_med_str = (
                    f"{customer_hist_spend - cluster_med_spend:+,.2f} vs cluster median"
                    if customer_hist_spend is not None
                    else None
                )
                st.metric("Cluster Median Spend", f"{cluster_med_spend:,.2f}", delta=delta_med_str)

            st.markdown('<div style="height:.6rem"></div>', unsafe_allow_html=True)
            st.caption(
                f"Cluster {segment_id} summary profile: {profile_data.get('customer_count', 0):,} records "
                f"({profile_data.get('unique_customers', 0):,} unique customers across periods). "
                f"Average historical invoices: {profile_data.get('average_invoice_frequency', 0.0):.2f}. "
                "This lookup reflects precomputed segment assignments and does not dynamically cluster raw features."
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
        except ValueError as exc:
            st.error(f"Data Record Error: {exc}")
        except Exception:
            st.error("The segmentation lookup could not be completed. Please verify the customer ID and cutoff.")
