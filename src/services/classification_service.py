from src.config.settings import Settings
from src.models.model_loader import ModelLoader
from src.preprocessing.input_validation import validate_text


class ProductCategoryService:
    def __init__(self, settings=None, loader=None):
        self.settings = settings or Settings()
        self.loader = loader or ModelLoader()

    def predict(self, text):
        text = validate_text(text)
        model = self.loader.load(self.settings.category_model)
        predicted = model.predict([text])[0]
        score = None
        if hasattr(model, "decision_function"):
            try:
                raw_score = model.decision_function([text])[0]
                score = float(max(raw_score)) if hasattr(raw_score, "__iter__") else float(raw_score)
            except Exception:
                score = None
        elif hasattr(model, "predict_proba"):
            try:
                score = model.predict_proba([text])[0].max()
            except Exception:
                score = None
        return {
            "predicted_category": str(predicted),
            "model_name": "linear_svm_tfidf",
            "prediction_status": "valid",
            "confidence_or_decision_score": score,
            "score_type": "decision_score" if hasattr(model, "decision_function") else ("probability" if hasattr(model, "predict_proba") else "unsupported"),
        }
