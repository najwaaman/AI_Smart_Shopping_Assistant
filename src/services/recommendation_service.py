from pathlib import Path

import pandas as pd

from src.config.settings import Settings
from src.models.model_loader import ModelLoader
from src.preprocessing.input_validation import validate_customer_id, validate_cutoff
from src.utils.exceptions import UnknownCustomerError, ValidationError, UnsupportedCutoffError


class RecommendationService:
    def __init__(self, settings=None, loader=None):
        self.settings = settings or Settings()
        self.loader = loader or ModelLoader()

    def recommendations(self, customer_id, k=10, cutoff="2011-06-01"):
        customer_id = validate_customer_id(customer_id)
        validate_cutoff(cutoff, {"2011-03-01", "2011-06-01"})
        if cutoff != "2011-06-01":
            raise UnsupportedCutoffError("Recommendations are available only at the approved 2011-06-01 cutoff")
        if not isinstance(k, int) or isinstance(k, bool) or k not in {5, 10, 20}:
            raise ValidationError("K must be 5, 10 or 20.")
        if not self.settings.customer_recommendations.is_file():
            raise FileNotFoundError(str(self.settings.customer_recommendations))
        frame = pd.read_csv(self.settings.customer_recommendations)
        frame = frame[(frame["customer_id"] == customer_id) & (frame["snapshot_cutoff"].astype(str) == cutoff)] if "snapshot_cutoff" in frame.columns else frame[frame["customer_id"] == customer_id]
        if frame.empty:
            raise UnknownCustomerError(f"No approved recommendation record for customer {customer_id} at cutoff {cutoff}")
        frame = frame.sort_values("rank").head(k)
        frame = frame.drop_duplicates(["customer_id", "StockCode"])
        return {"customer_id": customer_id, "snapshot_cutoff": cutoff,
                "recommendation_method": "item_item",
                "recommendations": frame[["rank", "StockCode", "Description", "recommendation_source", "score"]].to_dict("records")}
