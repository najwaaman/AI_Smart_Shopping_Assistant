from pathlib import Path

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

from src.services.explanation_service import ExplanationService
from src.ui.components import escape_html_text, render_kpi_card, render_page_header, render_status_label
from src.utils.exceptions import BackendError, UnknownCustomerError, ValidationError

ROOT = Path(__file__).resolve().parents[1]
EXPLAINABILITY_REPORTS = ROOT / "reports/explainability/phase_9"
CLASSIFICATION_REPORTS = ROOT / "reports/classification/phase_6"
REGRESSION_REPORTS = ROOT / "reports/regression/phase_7"

render_page_header(
    "Model Governance",
    "Model Insights & Explainability",
    "Understand model evaluation, global feature importance, and representative customer-level sensitivity analysis.",
)
render_status_label("Live explainability")

st.markdown('<div style="height:.8rem"></div>', unsafe_allow_html=True)

# Important methodology notice
st.warning(
    "**Important Methodology Notice:** SHAP was unavailable during Phase 9A due to package compatibility constraints. "
    "This application uses native model feature importance, validation-set permutation importance, and precomputed "
    "feature perturbation sensitivity proxies instead. Individual perturbation values are local sensitivity checks in "
    "standardized feature space and must not be interpreted as SHAP values, causal effects, or guaranteed real-world outcomes."
)

st.markdown('<div style="height:.8rem"></div>', unsafe_allow_html=True)


@st.cache_data(ttl=300)
def load_explainability_artifacts():
    c_importance = pd.read_csv(EXPLAINABILITY_REPORTS / "Classification_Feature_Importance.csv")
    r_importance = pd.read_csv(EXPLAINABILITY_REPORTS / "Regression_Feature_Importance.csv")
    c_comp = pd.read_csv(CLASSIFICATION_REPORTS / "Model_comparison.csv")
    r_comp = pd.read_csv(REGRESSION_REPORTS / "Model_Comparison.csv")
    c_indiv = pd.read_csv(EXPLAINABILITY_REPORTS / "Classification_Individual_Explanations.csv")
    r_indiv = pd.read_csv(EXPLAINABILITY_REPORTS / "Regression_Individual_Explanations.csv")
    r_residuals = pd.read_csv(REGRESSION_REPORTS / "Residual_Analysis.csv")
    return c_importance, r_importance, c_comp, r_comp, c_indiv, r_indiv, r_residuals


c_importance_df, r_importance_df, c_comp_df, r_comp_df, c_indiv_df, r_indiv_df, r_residuals_df = (
    load_explainability_artifacts()
)

tab_classification, tab_regression, tab_individual = st.tabs(
    [
        "Repeat Purchase (Classification)",
        "Future Spending (Regression)",
        "Representative Customer Explanations",
    ]
)

# -----------------------------------------------------------------------------
# TAB 1: Repeat Purchase (Classification Insights)
# -----------------------------------------------------------------------------
with tab_classification:
    st.markdown('<div class="section-card">', unsafe_allow_html=True)
    st.subheader("Section 1: Classification Model Governance (Phase 6)")
    st.markdown(
        "The Repeat Purchase classifier predicts whether a customer will make at least one qualifying paid purchase "
        "within 90 days following a snapshot cutoff. The selected model is **Gradient Boosting**, chosen for its "
        "superior June validation F1 score and balanced precision-recall trade-off."
    )

    # Classification KPIs from actual model comparison
    gb_row = c_comp_df[c_comp_df["model_name"] == "gradient_boosting"].iloc[0]
    c_kpi1, c_kpi2, c_kpi3, c_kpi4 = st.columns(4)
    with c_kpi1:
        render_kpi_card("Selected Model", "Gradient Boosting", "Phase 6 production model", "#3568FF")
    with c_kpi2:
        render_kpi_card("June Validation F1", f"{gb_row['f1']:.4f}", "Top score across models", "#18A999")
    with c_kpi3:
        render_kpi_card("Validation ROC-AUC", f"{gb_row['roc_auc']:.4f}", "June validation split", "#F59E0B")
    with c_kpi4:
        render_kpi_card(
            "Precision / Recall",
            f"{gb_row['precision']:.1%} / {gb_row['recall']:.1%}",
            f"Accuracy: {gb_row['accuracy']:.1%}",
            "#A855F7",
        )

    st.markdown("</div>", unsafe_allow_html=True)

    st.markdown('<div style="height:.8rem"></div>', unsafe_allow_html=True)

    # Classification Feature Importance
    st.markdown('<div class="section-card">', unsafe_allow_html=True)
    st.subheader("Classification Feature Importance (All 15 Features)")
    st.markdown(
        "Compare native tree importance (Gini gain during training) against permutation importance on the June validation set. "
        "**Note:** A high native training importance does not automatically translate to a high validation contribution."
    )

    c_metric_choice = st.radio(
        "Importance Metric to Display",
        [
            "Native Gini Feature Importance (Training Impurity Reduction)",
            "June Permutation Importance (Validation ROC-AUC Drop)",
            "Side-by-Side Comparison",
        ],
        horizontal=True,
        key="c_importance_metric_choice",
    )

    if c_metric_choice == "Native Gini Feature Importance (Training Impurity Reduction)":
        sorted_c = c_importance_df.sort_values("importance", ascending=True)
        fig_c = px.bar(
            sorted_c,
            x="importance",
            y="feature_name",
            orientation="h",
            text="importance",
            color_discrete_sequence=["#3568FF"],
            labels={"importance": "Native Importance (Gini)", "feature_name": "Feature"},
        )
        fig_c.update_traces(texttemplate="%{text:.4f}", textposition="outside", cliponaxis=False)
        fig_c.update_layout(
            template="plotly_white",
            height=460,
            margin=dict(l=20, r=20, t=10, b=10),
            paper_bgcolor="rgba(0,0,0,0)",
            plot_bgcolor="rgba(0,0,0,0)",
        )
        fig_c.update_xaxes(title="Native Feature Importance (Gini Impurity Reduction)", showgrid=True, gridcolor="#EEF2F7")
        fig_c.update_yaxes(title="", showgrid=False)
        st.plotly_chart(fig_c, width="stretch")

    elif c_metric_choice == "June Permutation Importance (Validation ROC-AUC Drop)":
        sorted_c = c_importance_df.sort_values("permutation_mean", ascending=True)
        fig_c = go.Figure(
            go.Bar(
                x=sorted_c["permutation_mean"],
                y=sorted_c["feature_name"],
                orientation="h",
                marker_color="#18A999",
                error_x=dict(type="data", array=sorted_c["permutation_std"], visible=True, color="#0E6B60"),
                text=[f"{v:.4f}" for v in sorted_c["permutation_mean"]],
                textposition="outside",
                cliponaxis=False,
            )
        )
        fig_c.update_layout(
            template="plotly_white",
            height=460,
            margin=dict(l=20, r=20, t=10, b=10),
            paper_bgcolor="rgba(0,0,0,0)",
            plot_bgcolor="rgba(0,0,0,0)",
        )
        fig_c.update_xaxes(title="Permutation Importance on June Validation (ROC-AUC Drop)", showgrid=True, gridcolor="#EEF2F7")
        fig_c.update_yaxes(title="", showgrid=False)
        st.plotly_chart(fig_c, width="stretch")

    else:
        # Side-by-Side Comparison
        sorted_c = c_importance_df.sort_values("importance", ascending=True)
        fig_c = go.Figure()
        fig_c.add_trace(
            go.Bar(
                y=sorted_c["feature_name"],
                x=sorted_c["importance"],
                name="Native Gini Importance",
                orientation="h",
                marker_color="#3568FF",
            )
        )
        fig_c.add_trace(
            go.Bar(
                y=sorted_c["feature_name"],
                x=sorted_c["permutation_mean"],
                name="June Permutation Importance (ROC-AUC)",
                orientation="h",
                marker_color="#18A999",
            )
        )
        fig_c.update_layout(
            barmode="group",
            template="plotly_white",
            height=500,
            margin=dict(l=20, r=20, t=10, b=10),
            paper_bgcolor="rgba(0,0,0,0)",
            plot_bgcolor="rgba(0,0,0,0)",
            legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
        )
        fig_c.update_xaxes(title="Importance Score", showgrid=True, gridcolor="#EEF2F7")
        fig_c.update_yaxes(title="", showgrid=False)
        st.plotly_chart(fig_c, width="stretch")

    st.caption(
        "Explanation: Native Gini importance measures the total reduction of the splitting criterion across trees during training on March data. "
        "Permutation importance measures the drop in June validation ROC-AUC when a single feature is randomly shuffled. "
        "Notice that while `missing_indicator_average_days_between_invoices` ranks high in native splits (0.1918), "
        "its permutation importance on June validation is modest (0.0035), highlighting the value of validation-based evaluation."
    )
    st.markdown("</div>", unsafe_allow_html=True)

    st.markdown('<div style="height:.8rem"></div>', unsafe_allow_html=True)

    # Classification Model Comparison Table
    st.markdown('<div class="section-card">', unsafe_allow_html=True)
    st.subheader("Phase 6 Classification Model Comparison Matrix")
    st.markdown(
        "Evaluation of supervised classification candidate models on the June 2011 validation split (2,718 records). "
        "Gradient Boosting was selected as production model based on superior F1 score and balanced performance."
    )

    display_c_comp = c_comp_df.copy()
    display_c_comp.columns = [
        "Model Name",
        "Accuracy",
        "Precision",
        "Recall",
        "F1 Score",
        "ROC-AUC",
        "PR-AUC",
        "True Neg (TN)",
        "False Pos (FP)",
        "False Neg (FN)",
        "True Pos (TP)",
    ]

    def highlight_gb(row):
        if row["Model Name"] == "gradient_boosting":
            return ["background-color: #EBF3FF; font-weight: bold; color: #172033"] * len(row)
        return [""] * len(row)

    st.dataframe(
        display_c_comp.style.apply(highlight_gb, axis=1).format(
            {
                "Accuracy": "{:.4f}",
                "Precision": "{:.4f}",
                "Recall": "{:.4f}",
                "F1 Score": "{:.4f}",
                "ROC-AUC": "{:.4f}",
                "PR-AUC": "{:.4f}",
                "True Neg (TN)": "{:,}",
                "False Pos (FP)": "{:,}",
                "False Neg (FN)": "{:,}",
                "True Pos (TP)": "{:,}",
            }
        ),
        width="stretch",
        hide_index=True,
    )
    st.markdown("</div>", unsafe_allow_html=True)

# -----------------------------------------------------------------------------
# TAB 2: Future Spending (Regression Insights)
# -----------------------------------------------------------------------------
with tab_regression:
    st.markdown('<div class="section-card">', unsafe_allow_html=True)
    st.subheader("Section 2: Spending Regression Model Governance (Phase 7)")
    st.markdown(
        "The Future Spending model predicts total gross spending in the subsequent 90-day window. "
        "The selected model is **Ridge Regression** (regularization parameter $\\alpha = 10.0$), "
        "achieving the lowest Mean Absolute Error (MAE) and highest $R^2$ on the June validation dataset."
    )

    ridge_row = r_comp_df[r_comp_df["model_name"] == "ridge_regression"].iloc[0]
    r_kpi1, r_kpi2, r_kpi3, r_kpi4 = st.columns(4)
    with r_kpi1:
        render_kpi_card("Selected Model", "Ridge Regression", "alpha = 10.0, linear solver", "#3568FF")
    with r_kpi2:
        render_kpi_card("June Validation MAE", f"{ridge_row['mae']:,.2f}", "Lowest MAE across all models", "#18A999")
    with r_kpi3:
        render_kpi_card("Validation RMSE", f"{ridge_row['rmse']:,.2f}", "June validation split", "#F59E0B")
    with r_kpi4:
        render_kpi_card("R-squared (R²)", f"{ridge_row['r2']:.4f}", "MedAE: 227.29", "#A855F7")

    st.markdown("</div>", unsafe_allow_html=True)

    st.markdown('<div style="height:.8rem"></div>', unsafe_allow_html=True)

    # Documented Negative Prediction Disclosure
    st.markdown('<div class="section-card">', unsafe_allow_html=True)
    st.subheader("Documented Evaluation Finding: Unclipped Negative Predictions")
    neg_count = int(ridge_row.get("negative_prediction_count", 12))
    st.markdown(
        f"""
        During the Phase 7 June validation assessment, **{neg_count} out of 2,718 predictions (0.44%)** resulted in raw negative values.
        - **Model Architecture Context:** Ridge regression is an unconstrained linear regressor. While future gross spending cannot be negative in physical reality, the model's unconstrained hyperplane allows negative linear projections when input features take extreme standardized values.
        - **Preservation Policy:** In accordance with Phase 7 and 10E governance, negative predictions are strictly preserved as raw model outputs and are not artificially clipped or floored to zero.
        - **UI Handling:** The application displays raw values transparently alongside an explicit negative prediction warning badge.
        """
    )
    st.markdown("</div>", unsafe_allow_html=True)

    st.markdown('<div style="height:.8rem"></div>', unsafe_allow_html=True)

    # Regression Feature Importance
    st.markdown('<div class="section-card">', unsafe_allow_html=True)
    st.subheader("Regression Feature Importance (All 14 Features)")
    st.markdown(
        "Review Ridge feature weights and validation permutation importance. "
        "**Note:** Absolute coefficients represent sensitivity in the standardized predictor space, not direct raw currency impact."
    )

    r_metric_choice = st.radio(
        "Regression Metric to Display",
        [
            "Absolute Ridge Regression Coefficients (|β| in standardized space)",
            "June Permutation Importance (Validation MAE Impact)",
            "Side-by-Side Comparison",
        ],
        horizontal=True,
        key="r_importance_metric_choice",
    )

    if r_metric_choice == "Absolute Ridge Regression Coefficients (|β| in standardized space)":
        sorted_r = r_importance_df.sort_values("coefficient_abs", ascending=True)
        fig_r = px.bar(
            sorted_r,
            x="coefficient_abs",
            y="feature_name",
            orientation="h",
            text="coefficient_abs",
            color_discrete_sequence=["#3568FF"],
            labels={"coefficient_abs": "Absolute Coefficient |β|", "feature_name": "Feature"},
        )
        fig_r.update_traces(texttemplate="%{text:.2f}", textposition="outside", cliponaxis=False)
        fig_r.update_layout(
            template="plotly_white",
            height=440,
            margin=dict(l=20, r=20, t=10, b=10),
            paper_bgcolor="rgba(0,0,0,0)",
            plot_bgcolor="rgba(0,0,0,0)",
        )
        fig_r.update_xaxes(title="Absolute Regression Coefficient (|β|)", showgrid=True, gridcolor="#EEF2F7")
        fig_r.update_yaxes(title="", showgrid=False)
        st.plotly_chart(fig_r, width="stretch")

    elif r_metric_choice == "June Permutation Importance (Validation MAE Impact)":
        sorted_r = r_importance_df.sort_values("permutation_mean", ascending=True)
        fig_r = go.Figure(
            go.Bar(
                x=sorted_r["permutation_mean"],
                y=sorted_r["feature_name"],
                orientation="h",
                marker_color="#18A999",
                error_x=dict(type="data", array=sorted_r["permutation_std"], visible=True, color="#0E6B60"),
                text=[f"{v:.2f}" for v in sorted_r["permutation_mean"]],
                textposition="outside",
                cliponaxis=False,
            )
        )
        fig_r.update_layout(
            template="plotly_white",
            height=440,
            margin=dict(l=20, r=20, t=10, b=10),
            paper_bgcolor="rgba(0,0,0,0)",
            plot_bgcolor="rgba(0,0,0,0)",
        )
        fig_r.update_xaxes(title="Permutation Importance on June Validation (MAE Increase)", showgrid=True, gridcolor="#EEF2F7")
        fig_r.update_yaxes(title="", showgrid=False)
        st.plotly_chart(fig_r, width="stretch")

    else:
        # Side-by-Side Comparison
        sorted_r = r_importance_df.sort_values("coefficient_abs", ascending=True)
        fig_r = go.Figure()
        fig_r.add_trace(
            go.Bar(
                y=sorted_r["feature_name"],
                x=sorted_r["coefficient_abs"],
                name="Absolute Coefficient (|β|)",
                orientation="h",
                marker_color="#3568FF",
            )
        )
        fig_r.add_trace(
            go.Bar(
                y=sorted_r["feature_name"],
                x=sorted_r["permutation_mean"],
                name="June Permutation Importance (MAE)",
                orientation="h",
                marker_color="#18A999",
            )
        )
        fig_r.update_layout(
            barmode="group",
            template="plotly_white",
            height=480,
            margin=dict(l=20, r=20, t=10, b=10),
            paper_bgcolor="rgba(0,0,0,0)",
            plot_bgcolor="rgba(0,0,0,0)",
            legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
        )
        fig_r.update_xaxes(title="Metric Magnitude", showgrid=True, gridcolor="#EEF2F7")
        fig_r.update_yaxes(title="", showgrid=False)
        st.plotly_chart(fig_r, width="stretch")

    st.caption(
        "Explanation: The top predictor is `scaled_spending_per_active_day` (|β| = 1,696.60), followed by historical spending metrics "
        "over 90 and 180 days. Standardized coefficients indicate the expected change in predicted future gross spending per unit change in transformed feature."
    )
    st.markdown("</div>", unsafe_allow_html=True)

    st.markdown('<div style="height:.8rem"></div>', unsafe_allow_html=True)

    # Regression Model Comparison Table
    st.markdown('<div class="section-card">', unsafe_allow_html=True)
    st.subheader("Phase 7 Regression Model Comparison Matrix")
    st.markdown(
        "Candidate regression models evaluated on the June 2011 validation split (2,718 records). "
        "Ridge Regression achieved the lowest MAE and lowest Median Absolute Error, outperforming complex tree ensembles."
    )

    display_r_comp = r_comp_df[
        [
            "model_name",
            "mae",
            "rmse",
            "r2",
            "median_absolute_error",
            "explained_variance",
            "negative_prediction_count",
            "training_seconds",
        ]
    ].copy()
    display_r_comp.columns = [
        "Model Name",
        "MAE",
        "RMSE",
        "R-squared",
        "Median Absolute Error",
        "Explained Variance",
        "Negative Predictions",
        "Training (sec)",
    ]

    def highlight_ridge(row):
        if row["Model Name"] == "ridge_regression":
            return ["background-color: #EBF3FF; font-weight: bold; color: #172033"] * len(row)
        return [""] * len(row)

    st.dataframe(
        display_r_comp.style.apply(highlight_ridge, axis=1).format(
            {
                "MAE": "{:,.2f}",
                "RMSE": "{:,.2f}",
                "R-squared": "{:.4f}",
                "Median Absolute Error": "{:,.2f}",
                "Explained Variance": "{:.4f}",
                "Negative Predictions": "{:,}",
                "Training (sec)": "{:.4f}",
            }
        ),
        width="stretch",
        hide_index=True,
    )
    st.markdown("</div>", unsafe_allow_html=True)

# -----------------------------------------------------------------------------
# TAB 3: Representative Individual Explanations
# -----------------------------------------------------------------------------
with tab_individual:
    st.markdown('<div class="section-card">', unsafe_allow_html=True)
    st.subheader("Section 3: Representative Customer Explanations (Phase 9A Sample Cohort)")
    st.markdown(
        "Inspect local feature sensitivity analysis for the **50 representative customer samples** evaluated during Phase 9A. "
        "Local explanations use a zero-feature perturbation proxy in standardized predictor space: each feature is zeroed out "
        "to observe the resulting directional change in model output. "
        "**Important:** The individual explanation dataset does not contain a cutoff column; it represents the June validation sample cohort."
    )

    sample_ids = sorted(c_indiv_df["customer_id"].unique().tolist())

    exp_col1, exp_col2, exp_action = st.columns([1.2, 1.2, 1], gap="medium")
    with exp_col1:
        selected_model_type = st.selectbox(
            "Target Model",
            ["Repeat Purchase (Classification)", "Future Spending (Regression)"],
            key="indiv_model_type",
        )
    with exp_col2:
        entry_mode = st.radio(
            "Customer Selection Mode",
            ["Select from 50 Sample IDs", "Custom Customer ID"],
            horizontal=True,
            key="indiv_entry_mode",
        )
        if entry_mode == "Select from 50 Sample IDs":
            sample_labels = [f"Representative sample {index + 1:02d}" for index in range(len(sample_ids))]
            selected_sample = st.selectbox(
                "Representative June sample",
                sample_labels,
                index=0 if sample_labels else None,
                key="indiv_sample_id_select",
            )
            selected_customer_id = sample_ids[sample_labels.index(selected_sample)] if selected_sample is not None else None
        else:
            selected_customer_id = st.number_input(
                "Enter Customer ID",
                min_value=1,
                step=1,
                value=None,
                placeholder="Enter an approved customer ID",
                key="indiv_custom_id_input",
            )
    with exp_action:
        st.markdown('<div style="height:1.95rem"></div>', unsafe_allow_html=True)
        explain_submitted = st.button("Generate local explanation", type="primary", use_container_width=True)

    st.markdown("</div>", unsafe_allow_html=True)

    if explain_submitted:
        st.markdown('<div style="height:.8rem"></div>', unsafe_allow_html=True)
        model_key = "classification" if "Classification" in selected_model_type else "regression"

        try:
            with st.spinner("Retrieving representative sensitivity explanation..."):
                result = ExplanationService().get_individual(model_key, int(selected_customer_id or 0))

            st.markdown('<div class="section-card">', unsafe_allow_html=True)
            st.subheader("Local Explanation: Representative sample")
            st.caption(
                f"Model: {'GradientBoostingClassifier' if model_key == 'classification' else 'Ridge Regression'} · "
                "Sample Source: June 2011 Validation Cohort (50 Precomputed Samples)"
            )

            if model_key == "classification":
                # Classification individual display
                prob = float(result["predicted_probability"])
                pred_cls = int(result["predicted_class"])
                status_label = "Likely repeat purchase" if pred_cls == 1 else "Likely no repeat purchase"
                accent_color = "#18A999" if pred_cls == 1 else "#3568FF"

                kpi_col1, kpi_col2 = st.columns(2)
                with kpi_col1:
                    st.markdown('<div class="kpi-card">', unsafe_allow_html=True)
                    st.markdown('<div class="kpi-label">Predicted Class</div>', unsafe_allow_html=True)
                    st.markdown(f'<div class="kpi-value" style="color:{accent_color}">{status_label}</div>', unsafe_allow_html=True)
                    st.markdown(f'<div class="kpi-note">Class value: {pred_cls}</div>', unsafe_allow_html=True)
                    st.markdown("</div>", unsafe_allow_html=True)
                with kpi_col2:
                    st.markdown('<div class="kpi-card">', unsafe_allow_html=True)
                    st.markdown('<div class="kpi-label">Positive-Class Probability</div>', unsafe_allow_html=True)
                    st.markdown(f'<div class="kpi-value">{prob:.1%}</div>', unsafe_allow_html=True)
                    st.progress(prob)
                    st.markdown("</div>", unsafe_allow_html=True)

                st.markdown('<div style="height:.8rem"></div>', unsafe_allow_html=True)
                st.markdown("#### Primary Sensitivity Drivers (Zero-Feature Perturbation Proxies)")
                feat_col1, feat_col2 = st.columns(2)
                with feat_col1:
                    st.markdown(
                        f"""
                        <div class="kpi-card" style="border-left: 4px solid #18A999">
                          <div class="kpi-label" style="color:#18A999">Top Positive Sensitivity Driver</div>
                          <div style="font-weight: 800; font-size: 1.05rem; margin: .4rem 0">{escape_html_text(result['top_positive_feature'])}</div>
                          <div class="kpi-note">Perturbation Effect Proxy: <strong>{float(result['top_positive_effect_proxy']):+.4f}</strong></div>
                        </div>
                        """,
                        unsafe_allow_html=True,
                    )
                with feat_col2:
                    st.markdown(
                        f"""
                        <div class="kpi-card" style="border-left: 4px solid #DF5B68">
                          <div class="kpi-label" style="color:#DF5B68">Top Negative Sensitivity Driver</div>
                          <div style="font-weight: 800; font-size: 1.05rem; margin: .4rem 0">{escape_html_text(result['top_negative_feature'])}</div>
                          <div class="kpi-note">Perturbation Effect Proxy: <strong>{float(result['top_negative_effect_proxy']):+.4f}</strong></div>
                        </div>
                        """,
                        unsafe_allow_html=True,
                    )

            else:
                # Regression individual display
                pred_spend = float(result["predicted_future_gross_spending"])
                spend_accent = "#DF5B68" if pred_spend < 0 else "#3568FF"

                kpi_col1, kpi_col2 = st.columns(2)
                with kpi_col1:
                    st.markdown('<div class="kpi-card">', unsafe_allow_html=True)
                    st.markdown('<div class="kpi-label">Predicted 90-Day Gross Spending</div>', unsafe_allow_html=True)
                    st.markdown(f'<div class="kpi-value" style="color:{spend_accent}">{pred_spend:,.2f}</div>', unsafe_allow_html=True)
                    if pred_spend < 0:
                        st.markdown('<div class="kpi-note" style="color:#DF5B68">Unclipped negative raw projection</div>', unsafe_allow_html=True)
                    else:
                        st.markdown('<div class="kpi-note">Raw unclipped Ridge projection (no currency label)</div>', unsafe_allow_html=True)
                    st.markdown("</div>", unsafe_allow_html=True)
                with kpi_col2:
                    st.markdown('<div class="kpi-card">', unsafe_allow_html=True)
                    st.markdown('<div class="kpi-label">Explanation Methodology</div>', unsafe_allow_html=True)
                    st.markdown('<div style="font-size:1.15rem;font-weight:800;margin:.35rem 0">Zero-Feature Perturbation</div>', unsafe_allow_html=True)
                    st.markdown('<div class="kpi-note">Standardized feature space sensitivity check</div>', unsafe_allow_html=True)
                    st.markdown("</div>", unsafe_allow_html=True)

                st.markdown('<div style="height:.8rem"></div>', unsafe_allow_html=True)
                st.markdown("#### Primary Sensitivity Drivers (Zero-Feature Perturbation Proxies)")
                feat_col1, feat_col2 = st.columns(2)
                with feat_col1:
                    st.markdown(
                        f"""
                        <div class="kpi-card" style="border-left: 4px solid #18A999">
                          <div class="kpi-label" style="color:#18A999">Top Increasing Sensitivity Driver</div>
                          <div style="font-weight: 800; font-size: 1.05rem; margin: .4rem 0">{escape_html_text(result['top_increasing_feature'])}</div>
                          <div class="kpi-note">Perturbation Effect Proxy: <strong>{float(result['top_increasing_effect_proxy']):+,.2f}</strong></div>
                        </div>
                        """,
                        unsafe_allow_html=True,
                    )
                with feat_col2:
                    st.markdown(
                        f"""
                        <div class="kpi-card" style="border-left: 4px solid #DF5B68">
                          <div class="kpi-label" style="color:#DF5B68">Top Decreasing Sensitivity Driver</div>
                          <div style="font-weight: 800; font-size: 1.05rem; margin: .4rem 0">{escape_html_text(result['top_decreasing_feature'])}</div>
                          <div class="kpi-note">Perturbation Effect Proxy: <strong>{float(result['top_decreasing_effect_proxy']):+,.2f}</strong></div>
                        </div>
                        """,
                        unsafe_allow_html=True,
                    )

            st.markdown('<div style="height:.7rem"></div>', unsafe_allow_html=True)
            st.info(
                "**Interpretation Guidelines:** The perturbation effect proxy quantifies the directional shift in model prediction "
                "when that specific standardized feature is set to zero (representing sample baseline removal). "
                "These values reflect local model curvature around this customer's feature vector and do not imply causal real-world intervention."
            )
            st.markdown("</div>", unsafe_allow_html=True)

        except UnknownCustomerError:
            st.warning(
                "**Sample Restriction Notice:** This customer is not among the 50 approved June validation explanation samples. "
                "Select a representative sample from the list or check the customer ID."
            )
        except ValidationError as exc:
            st.error(f"Validation Error: {exc}")
        except BackendError as exc:
            st.error(f"Backend Service Error: {exc}")
        except Exception:
            st.error("The explanation could not be retrieved. Please check the customer ID.")
