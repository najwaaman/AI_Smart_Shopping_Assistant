import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

from src.services.public_aggregate_service import PublicAggregateDataError
from src.ui.components import render_kpi_card, render_page_header, render_status_label
from src.ui.public_aggregate_pages import PUBLIC_AGGREGATES_RELEASED, load_public_aggregate


REPORTS = {
    "classification_importance": "reports/explainability/phase_9/Classification_Feature_Importance.csv",
    "regression_importance": "reports/explainability/phase_9/Regression_Feature_Importance.csv",
    "classification_comparison": "reports/classification/phase_6/Model_comparison.csv",
    "regression_comparison": "reports/regression/phase_7/Model_Comparison.csv",
}

render_page_header(
    "Model governance",
    "Model insights",
    "Global feature importance and aggregate evaluation results. Individual explanations and customer-level records are not used.",
)
render_status_label("Aggregate release approved" if PUBLIC_AGGREGATES_RELEASED else "Aggregate review pending")

try:
    data = {name: load_public_aggregate(path) for name, path in REPORTS.items()}
except PublicAggregateDataError:
    if PUBLIC_AGGREGATES_RELEASED:
        st.warning("Approved aggregate reports are unavailable or invalid. Model values cannot be displayed.")
    else:
        st.info(
            "Aggregate report values are withheld pending provenance and privacy review. "
            "After approval, this page will use only allowlisted global importance and model-comparison reports."
        )
    st.stop()

classification_importance = data["classification_importance"]
regression_importance = data["regression_importance"]
classification_comparison = data["classification_comparison"].dropna(subset=["model_name", "f1"])
regression_comparison = data["regression_comparison"].dropna(subset=["model_name", "mae"])

classification_tab, regression_tab = st.tabs(["Repeat-purchase classification", "Future-spending regression"])

with classification_tab:
    st.markdown('<div class="section-card">', unsafe_allow_html=True)
    st.subheader("Aggregate classification comparison")
    st.caption("Model-level scores from the Phase 6 aggregate comparison report. Confusion-count fields are not displayed.")
    if classification_comparison.empty:
        st.info("Classification comparison rows are unavailable after privacy suppression.")
    else:
        best = classification_comparison.loc[classification_comparison["f1"].idxmax()]
        col1, col2, col3 = st.columns(3)
        with col1:
            render_kpi_card("Highest F1 in report", str(best["model_name"]).replace("_", " ").title(), f"F1 {best['f1']:.4f}", "#3568FF")
        with col2:
            render_kpi_card("ROC-AUC", f"{best['roc_auc']:.4f}", "For the same reported model", "#18A999")
        with col3:
            render_kpi_card("Precision / recall", f"{best['precision']:.3f} / {best['recall']:.3f}", "For the same reported model", "#F59E0B")

        comparison_view = classification_comparison[["model_name", "accuracy", "precision", "recall", "f1", "roc_auc", "average_precision"]].rename(
            columns={
                "model_name": "Model",
                "accuracy": "Accuracy",
                "precision": "Precision",
                "recall": "Recall",
                "f1": "F1",
                "roc_auc": "ROC-AUC",
                "average_precision": "Average precision",
            }
        )
        left, right = st.columns([1.2, 1], gap="medium")
        with left:
            fig = px.bar(classification_comparison.sort_values("f1"), x="f1", y="model_name", orientation="h", color_discrete_sequence=["#3568FF"])
            fig.update_layout(template="plotly_white", height=340, margin=dict(l=12, r=18, t=12, b=12), paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)")
            fig.update_xaxes(title="F1 score", showgrid=True, gridcolor="#EEF2F7")
            fig.update_yaxes(title="", showgrid=False)
            st.plotly_chart(fig, width="stretch")
        with right:
            st.dataframe(comparison_view.style.format({column: "{:.4f}" for column in comparison_view.columns if column != "Model"}), width="stretch", hide_index=True)
    st.markdown("</div>", unsafe_allow_html=True)

    st.markdown('<div style="height:.8rem"></div>', unsafe_allow_html=True)
    st.markdown('<div class="section-card">', unsafe_allow_html=True)
    st.subheader("Global classification feature importance")
    st.markdown(
        "Native feature importance summarizes training split contribution; permutation importance summarizes the change in validation ROC-AUC when a feature is shuffled. "
        "These are global model measures, not customer explanations or causal effects."
    )
    if classification_importance.empty:
        st.info("Global classification importance is unavailable.")
    else:
        metric = st.radio(
            "Global measure",
            ["Native importance", "Validation permutation importance"],
            horizontal=True,
            key="public_classification_importance_metric",
        )
        value_column = "importance" if metric == "Native importance" else "permutation_mean"
        chart = classification_importance.sort_values(value_column).copy()
        fig = go.Figure(
            go.Bar(
                x=chart[value_column],
                y=chart["feature_name"],
                orientation="h",
                marker_color="#18A999" if value_column == "permutation_mean" else "#3568FF",
                error_x=(
                    {"type": "data", "array": chart["permutation_std"], "visible": True, "color": "#0E6B60"}
                    if value_column == "permutation_mean"
                    else None
                ),
            )
        )
        fig.update_layout(template="plotly_white", height=500, margin=dict(l=16, r=18, t=12, b=12), paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)")
        fig.update_xaxes(title=metric, showgrid=True, gridcolor="#EEF2F7")
        fig.update_yaxes(title="", showgrid=False)
        st.plotly_chart(fig, width="stretch")
    st.markdown("</div>", unsafe_allow_html=True)

with regression_tab:
    st.markdown('<div class="section-card">', unsafe_allow_html=True)
    st.subheader("Aggregate spending-model comparison")
    st.caption("Model-level error and fit metrics from the Phase 7 aggregate comparison report. No customer-level prediction records are loaded.")
    if regression_comparison.empty:
        st.info("Spending comparison rows are unavailable after privacy suppression.")
    else:
        best = regression_comparison.loc[regression_comparison["mae"].idxmin()]
        col1, col2, col3 = st.columns(3)
        with col1:
            render_kpi_card("Lowest MAE in report", str(best["model_name"]).replace("_", " ").title(), f"MAE {best['mae']:,.2f}", "#3568FF")
        with col2:
            render_kpi_card("RMSE", f"{best['rmse']:,.2f}", "For the same reported model", "#18A999")
        with col3:
            render_kpi_card("R-squared", f"{best['r2']:.4f}", "For the same reported model", "#F59E0B")

        regression_view = regression_comparison[["model_name", "mae", "rmse", "r2", "median_absolute_error", "explained_variance"]].rename(
            columns={
                "model_name": "Model",
                "mae": "MAE",
                "rmse": "RMSE",
                "r2": "R-squared",
                "median_absolute_error": "Median absolute error",
                "explained_variance": "Explained variance",
            }
        )
        left, right = st.columns([1.2, 1], gap="medium")
        with left:
            fig = px.bar(regression_comparison.sort_values("mae", ascending=False), x="mae", y="model_name", orientation="h", color_discrete_sequence=["#18A999"])
            fig.update_layout(template="plotly_white", height=360, margin=dict(l=12, r=18, t=12, b=12), paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)")
            fig.update_xaxes(title="Mean Absolute Error (ledger units)", showgrid=True, gridcolor="#EEF2F7")
            fig.update_yaxes(title="", showgrid=False)
            st.plotly_chart(fig, width="stretch")
        with right:
            st.dataframe(regression_view.style.format({column: "{:,.4f}" for column in regression_view.columns if column != "Model"}), width="stretch", hide_index=True)
    st.markdown("</div>", unsafe_allow_html=True)

    st.markdown('<div style="height:.8rem"></div>', unsafe_allow_html=True)
    st.markdown('<div class="section-card">', unsafe_allow_html=True)
    st.subheader("Global regression feature importance")
    st.markdown(
        "Absolute Ridge coefficients describe standardized-space weight magnitude. Validation permutation importance describes the change in MAE after shuffling a feature. "
        "Neither measure identifies a customer-level driver or establishes causation."
    )
    if regression_importance.empty:
        st.info("Global regression importance is unavailable.")
    else:
        metric = st.radio(
            "Global measure",
            ["Absolute Ridge coefficient", "Validation permutation importance"],
            horizontal=True,
            key="public_regression_importance_metric",
        )
        value_column = "coefficient_abs" if metric == "Absolute Ridge coefficient" else "permutation_mean"
        chart = regression_importance.sort_values(value_column).copy()
        fig = go.Figure(
            go.Bar(
                x=chart[value_column],
                y=chart["feature_name"],
                orientation="h",
                marker_color="#3568FF" if value_column == "coefficient_abs" else "#18A999",
                error_x=(
                    {"type": "data", "array": chart["permutation_std"], "visible": True, "color": "#0E6B60"}
                    if value_column == "permutation_mean"
                    else None
                ),
            )
        )
        fig.update_layout(template="plotly_white", height=500, margin=dict(l=16, r=18, t=12, b=12), paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)")
        fig.update_xaxes(title=metric, showgrid=True, gridcolor="#EEF2F7")
        fig.update_yaxes(title="", showgrid=False)
        st.plotly_chart(fig, width="stretch")
    st.markdown("</div>", unsafe_allow_html=True)
