import pandas as pd

from src.config.settings import Settings
from src.models.model_loader import ModelLoader
from src.preprocessing.input_validation import validate_customer_id, validate_cutoff, validate_feature_frame
from src.utils.exceptions import UnknownCustomerError


class SegmentationService:
    def __init__(self, settings=None, loader=None):
        self.settings = settings or Settings()
        self.loader = loader or ModelLoader()

    def assign(self, customer_id, cutoff="2011-06-01", feature_frame=None):
        customer_id = validate_customer_id(customer_id)
        cutoff = validate_cutoff(cutoff, self.settings.approved_cutoffs)
        if feature_frame is None:
            insights = pd.read_csv(self.settings.customer_insights)
            row = insights[(insights["customer_id"] == customer_id) & (insights["snapshot_cutoff"].astype(str) == cutoff)]
            if row.empty:
                raise UnknownCustomerError(f"No approved segment record for customer {customer_id} at cutoff {cutoff}")
            if len(row) != 1:
                raise ValueError("Duplicate customer-cutoff segment record")
            segment_id = int(row.iloc[0]["segment_id"])
            profile = pd.read_csv(self.settings.segment_profiles)
            profile_row = profile[profile["segment_id"] == segment_id]
            profile_data = profile_row.iloc[0].to_dict() if not profile_row.empty else {"segment_id": segment_id}
            return {"customer_id": customer_id, "snapshot_cutoff": cutoff, "segment_id": segment_id,
                    "segment_profile": profile_data, "model_name": "KMeans"}
        raise NotImplementedError("Raw segmentation feature assignment requires a separate approved feature-computation service.")
