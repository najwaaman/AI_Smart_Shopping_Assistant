"""Synthetic, non-customer fixtures shared by public-safe tests."""

import pandas as pd


SYNTHETIC_CUSTOMER_ID = 987000001
UNKNOWN_CUSTOMER_ID = 987000099
SYNTHETIC_CUTOFFS = ("2011-03-01", "2011-06-01")


def feature_frame(predictors, cutoff="2011-06-01", customer_id=SYNTHETIC_CUSTOMER_ID):
    return pd.DataFrame(
        [{"customer_id": customer_id, "snapshot_cutoff": cutoff, **{name: 0.0 for name in predictors}}]
    )


def snapshot_frame(cutoff="2011-06-01"):
    rows = []
    primary = (2, 18.0, 6) if cutoff == "2011-03-01" else (3, 42.5, 12)
    for customer_id, invoice_count, gross, quantity in (
        (SYNTHETIC_CUSTOMER_ID, *primary),
        (SYNTHETIC_CUSTOMER_ID + 1, 1, 10.0, 2),
    ):
        rows.append(
            {
                "customer_id": customer_id,
                "snapshot_cutoff": cutoff,
                "historical_gross_spend": gross,
                "historical_invoice_count": invoice_count,
                "historical_total_quantity": quantity,
                "historical_unique_stockcode_count": 2,
                "recency_days": 4.0,
                "historical_average_invoice_value": gross / invoice_count,
                "historical_active_month_count": 2,
                "historical_weekday_invoice_count": invoice_count,
            }
        )
    return pd.DataFrame(rows)


def insights_frame():
    return pd.DataFrame(
        [
            {
                "customer_id": SYNTHETIC_CUSTOMER_ID,
                "snapshot_cutoff": cutoff,
                "segment_id": 0,
                "repeat_purchase_probability": 0.7,
                "predicted_future_gross_spending": 42.0,
            }
            for cutoff in SYNTHETIC_CUTOFFS
        ]
    )


def recommendations_frame(customer_id=SYNTHETIC_CUSTOMER_ID):
    return pd.DataFrame(
        [
            {
                "customer_id": customer_id,
                "snapshot_cutoff": "2011-06-01",
                "rank": rank,
                "StockCode": f"SYN-{rank:03d}",
                "Description": f"Synthetic product {rank}",
                "recommendation_source": "item_item",
                "score": 1.0 / rank,
            }
            for rank in range(1, 21)
        ]
    )


def segment_profile_frame():
    return pd.DataFrame(
        [
            {"segment_id": i, "customer_count": count, "average_historical_gross_spending": spend}
            for i, count, spend in ((0, 2, 26.25), (1, 1, 50.0), (2, 1, 80.0))
        ]
    )


def explanation_frame(regression=False):
    rows = []
    for offset in range(50):
        customer_id = SYNTHETIC_CUSTOMER_ID + offset
        if regression:
            rows.append(
                {
                    "customer_id": customer_id,
                    "predicted_future_gross_spending": 42.0,
                    "top_increasing_feature": "synthetic_feature_a",
                    "top_decreasing_feature": "synthetic_feature_b",
                }
            )
        else:
            rows.append(
                {
                    "customer_id": customer_id,
                    "predicted_probability": 0.7,
                    "predicted_class": 1,
                    "top_positive_feature": "synthetic_feature_a",
                    "top_negative_feature": "synthetic_feature_b",
                }
            )
    return pd.DataFrame(rows)


def importance_frame(regression=False):
    return pd.DataFrame(
        [
            {
                "feature_name": f"synthetic_feature_{index}",
                **(
                    {"coefficient_abs": float(index), "permutation_mean": 0.1, "permutation_std": 0.01}
                    if regression
                    else {"importance": float(index), "permutation_mean": 0.1, "permutation_std": 0.01}
                ),
            }
            for index in range(14 if regression else 15)
        ]
    )


class SyntheticCategoryModel:
    classes_ = ["Books", "Clothing & Accessories", "Electronics", "Household"]

    def predict(self, texts):
        categories = []
        for text in texts:
            normalized = text.casefold()
            if any(word in normalized for word in ("cotton", "shirt", "dress", "clothing")):
                categories.append("Clothing & Accessories")
            elif any(word in normalized for word in ("cookware", "cooking", "pot", "pan", "household")):
                categories.append("Household")
            elif any(word in normalized for word in ("history", "novel", "book", "textbook")):
                categories.append("Books")
            else:
                categories.append("Electronics")
        return categories

    def decision_function(self, texts):
        return [[0.1, 0.2, 0.9, 0.0] for _ in texts]


class SyntheticRepeatModel:
    def predict(self, frame):
        return [1 for _ in range(len(frame))]

    def predict_proba(self, frame):
        return [[0.3, 0.7] for _ in range(len(frame))]


class SyntheticSpendingModel:
    def __init__(self, value=42.0):
        self.value = value

    def predict(self, frame):
        return [self.value for _ in range(len(frame))]


class SyntheticLoader:
    def __init__(self, spending_value=42.0):
        self.spending_value = spending_value

    def load(self, path):
        path = str(path).replace("\\", "/")
        if path.endswith("linear_svm_tfidf.joblib"):
            return SyntheticCategoryModel()
        if "/classification/phase_6/" in path:
            return SyntheticRepeatModel()
        if "/regression/phase_7/" in path:
            return SyntheticSpendingModel(self.spending_value)
        raise FileNotFoundError("Synthetic fixture has no model for the requested path")
