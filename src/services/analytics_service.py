import pandas as pd

from src.config.settings import Settings


class AnalyticsService:
    def __init__(self, settings=None):
        self.settings = settings or Settings()

    def dashboard_summary(self):
        insights = pd.read_csv(self.settings.customer_insights)
        recommendations = pd.read_csv(self.settings.customer_recommendations)
        return {
            "total_customer_cutoff_records": len(insights),
            "total_unique_customers": insights["customer_id"].nunique(),
            "cutoff_counts": insights["snapshot_cutoff"].value_counts().sort_index().to_dict(),
            "total_recommendation_records": len(recommendations),
            "recommendation_customers": recommendations["customer_id"].nunique(),
            "segment_counts": insights["segment_id"].value_counts().sort_index().to_dict(),
        }
