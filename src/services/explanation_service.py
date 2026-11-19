import pandas as pd

from src.config.settings import Settings
from src.utils.exceptions import UnknownCustomerError, ValidationError


class ExplanationService:
    def __init__(self, settings=None):
        self.settings = settings or Settings()

    def get_global_importance(self, model_type):
        model_type = str(model_type).lower()
        if model_type in {"classification", "repeat_purchase", "repeat-purchase"}:
            path = self.settings.project_root / "reports/explainability/phase_9/Classification_Feature_Importance.csv"
        elif model_type in {"regression", "spending", "future_spending"}:
            path = self.settings.project_root / "reports/explainability/phase_9/Regression_Feature_Importance.csv"
        else:
            raise ValidationError("model_type must be classification or regression")
        if not path.is_file():
            raise FileNotFoundError(str(path))
        return pd.read_csv(path).to_dict("records")

    def get_individual(self, model_type, customer_id, cutoff="2011-06-01"):
        model_type = str(model_type).lower()
        if model_type in {"classification", "repeat_purchase", "repeat-purchase"}:
            path = self.settings.project_root / "reports/explainability/phase_9/Classification_Individual_Explanations.csv"
        elif model_type in {"regression", "spending", "future_spending"}:
            path = self.settings.project_root / "reports/explainability/phase_9/Regression_Individual_Explanations.csv"
        else:
            raise ValidationError("model_type must be classification or regression")
        if not path.is_file():
            raise FileNotFoundError(str(path))
        frame = pd.read_csv(path)
        row = frame[frame["customer_id"] == int(customer_id)].head(1)
        if row.empty:
            raise UnknownCustomerError(f"No approved explanation sample for customer {customer_id}")
        return row.iloc[0].to_dict()
