import pandas as pd

from src.config.settings import Settings
from src.models.model_loader import ModelLoader
from src.preprocessing.input_validation import validate_customer_id, validate_cutoff, validate_feature_frame
from src.utils.exceptions import UnknownCustomerError


class RepeatPurchaseService:
    def __init__(self, settings=None, loader=None):
        self.settings = settings or Settings()
        self.loader = loader or ModelLoader()

    def predict(self, customer_id, cutoff="2011-06-01", feature_frame=None):
        customer_id = validate_customer_id(customer_id)
        cutoff = validate_cutoff(cutoff, self.settings.approved_cutoffs)
        if feature_frame is None:
            source = self.settings.classification_june if cutoff == "2011-06-01" else self.settings.classification_march
            frame = pd.read_csv(source)
            frame = frame[(frame["customer_id"] == customer_id) & (frame["snapshot_cutoff"].astype(str) == cutoff)]
            if frame.empty:
                raise UnknownCustomerError(f"No approved customer-cutoff record for customer {customer_id} at cutoff {cutoff}")
            if len(frame) != 1:
                raise ValueError("Duplicate customer-cutoff record")
            feature_frame = frame.drop(columns=["repeat_purchase_90d"])
        elif not isinstance(feature_frame, pd.DataFrame):
            raise ValueError("feature_frame must be a pandas DataFrame")
        numeric = validate_feature_frame(feature_frame, self.settings.classification_predictors, {"repeat_purchase_90d"})
        model = self.loader.load(self.settings.repeat_model)
        probability = float(model.predict_proba(numeric)[0][1])
        predicted = int(model.predict(numeric)[0])
        return {"customer_id": customer_id, "snapshot_cutoff": cutoff, "predicted_repeat_purchase_status": predicted,
                "positive_class_probability": probability, "model_name": "GradientBoostingClassifier",
                "prediction_status": "valid"}
