from pathlib import Path


class Settings:
    def __init__(self, project_root: Path | None = None):
        self.project_root = project_root or Path(__file__).resolve().parents[2]

        self.category_model = self.project_root / "models/classification/comparison/linear_svm_tfidf.joblib"
        self.repeat_model = self.project_root / "models/classification/phase_6/selected_model.joblib"
        self.spending_model = self.project_root / "models/regression/phase_7/selected_model.joblib"
        self.selected_recommender = self.project_root / "models/recommendation/phase_8/selected_recommender.joblib"
        self.item_similarity = self.project_root / "models/recommendation/phase_8/item_item_similarity.joblib"
        self.segmentation_model = self.project_root / "models/segmentation/phase_9/segmentation_model.joblib"
        self.segmentation_imputer = self.project_root / "models/segmentation/phase_9/segmentation_imputer.joblib"
        self.segmentation_scaler = self.project_root / "models/segmentation/phase_9/segmentation_scaler.joblib"

        self.classification_march = self.project_root / "datasets/model_ready/classification/march_training.csv"
        self.classification_june = self.project_root / "datasets/model_ready/classification/june_validation.csv"
        self.regression_march = self.project_root / "datasets/model_ready/regression/march_training.csv"
        self.regression_june = self.project_root / "datasets/model_ready/regression/june_validation.csv"
        self.customer_insights = self.project_root / "datasets/customer_insights/phase_9/customer_insights.csv"
        self.customer_recommendations = self.project_root / "datasets/recommendations/phase_8/customer_recommendations.csv"
        self.segment_profiles = self.project_root / "reports/segmentation/phase_9/Cluster_Profiles.csv"

        self.classification_predictors = [
            "scaled_invoice_count_90d", "scaled_historical_invoice_count",
            "scaled_invoice_count_180d", "scaled_customer_active_days",
            "scaled_historical_active_month_count", "scaled_quantity_90d",
            "scaled_average_days_between_invoices", "scaled_gross_spending_180d",
            "scaled_unique_products_90d", "scaled_historical_gross_spending",
            "scaled_gross_spending_90d", "scaled_historical_total_quantity",
            "scaled_historical_weekday_invoice_count", "scaled_quantity_180d",
            "missing_indicator_average_days_between_invoices",
        ]
        self.regression_predictors = [
            "scaled_gross_spending_180d", "scaled_historical_gross_spending",
            "scaled_gross_spending_90d", "scaled_quantity_90d",
            "scaled_quantity_180d", "scaled_historical_total_quantity",
            "scaled_invoice_count_180d", "scaled_historical_invoice_count",
            "scaled_historical_weekday_invoice_count", "scaled_invoice_count_90d",
            "scaled_spending_per_active_day", "scaled_customer_active_days",
            "scaled_historical_active_month_count", "scaled_historical_transaction_line_count",
        ]
        self.approved_cutoffs = {"2011-03-01", "2011-06-01"}
