import pandas as pd

from src.config.settings import Settings
from src.models.model_loader import ModelLoader
from src.preprocessing.input_validation import validate_customer_id, validate_cutoff, validate_feature_frame
from src.utils.exceptions import UnknownCustomerError


class SpendingPredictionService:
    def __init__(self, settings=None, loader=None):
        self.settings = settings or Settings()
        self.loader = loader or ModelLoader()

    def predict(self, customer_id, cutoff="2011-06-01", feature_frame=None):
        customer_id = validate_customer_id(customer_id)
        cutoff = validate_cutoff(cutoff, self.settings.approved_cutoffs)
        if feature_frame is None:
            source = self.settings.regression_june if cutoff == "2011-06-01" else self.settings.regression_march
            frame = pd.read_csv(source)
            frame = frame[(frame["customer_id"] == customer_id) & (frame["snapshot_cutoff"].astype(str) == cutoff)]
            if frame.empty:
                raise UnknownCustomerError(f"No approved customer-cutoff record for customer {customer_id} at cutoff {cutoff}")
            if len(frame) != 1:
                raise ValueError("Duplicate customer-cutoff record")
            feature_frame = frame.drop(columns=["future_gross_spend_90d"])
        numeric = validate_feature_frame(feature_frame, self.settings.regression_predictors, {"future_gross_spend_90d"})
        model = self.loader.load(self.settings.spending_model)
        predicted = float(model.predict(numeric)[0])
        return {"customer_id": customer_id, "snapshot_cutoff": cutoff,
                "predicted_future_gross_spending": predicted,
                "model_name": "Ridge", "prediction_status": "valid",
                "negative_prediction_warning": predicted < 0,
                "currency_label": None}
