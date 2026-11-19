import numpy as np
import pandas as pd

from src.utils.exceptions import ValidationError, UnsupportedCutoffError


def validate_text(text, maximum_length=5000):
    if not isinstance(text, str):
        raise ValidationError("Product description must be text.")
    text = text.strip()
    if not text:
        raise ValidationError("Product description cannot be empty or whitespace.")
    if len(text) > maximum_length:
        raise ValidationError(f"Product description exceeds {maximum_length} characters.")
    return text


def validate_customer_id(customer_id):
    if isinstance(customer_id, bool):
        raise ValidationError("Customer ID must be a positive integer.")
    try:
        value = int(customer_id)
    except (TypeError, ValueError) as exc:
        raise ValidationError("Customer ID must be a positive integer.") from exc
    if value <= 0:
        raise ValidationError("Customer ID must be a positive integer.")
    return value


def validate_cutoff(cutoff, approved_cutoffs):
    value = str(cutoff).strip()
    if value not in approved_cutoffs:
        raise UnsupportedCutoffError(f"Unsupported snapshot cutoff: {value}")
    return value


def validate_feature_frame(frame: pd.DataFrame, expected_columns, target_columns=None):
    target_columns = target_columns or set()
    if not isinstance(frame, pd.DataFrame):
        raise ValidationError("Feature input must be a pandas DataFrame.")
    missing = [column for column in expected_columns if column not in frame.columns]
    if missing:
        raise ValidationError("Missing required predictors: " + ", ".join(missing))
    leaked = [column for column in target_columns if column in frame.columns]
    if leaked:
        raise ValidationError("Target columns are not allowed in predictor data.")
    selected = frame[expected_columns]
    numeric = selected.apply(pd.to_numeric, errors="coerce")
    if numeric.isna().any().any():
        raise ValidationError("Predictor data contains missing or non-numeric values.")
    if not np.isfinite(numeric.to_numpy()).all():
        raise ValidationError("Predictor data contains infinite values.")
    if frame.duplicated(["customer_id", "snapshot_cutoff"]).any() if {"customer_id", "snapshot_cutoff"}.issubset(frame.columns) else False:
        raise ValidationError("Duplicate customer-cutoff records are not allowed.")
    return numeric
