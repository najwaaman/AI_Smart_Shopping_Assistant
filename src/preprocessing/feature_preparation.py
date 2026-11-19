import pandas as pd

from src.preprocessing.input_validation import validate_feature_frame


def prepare_feature_frame(frame: pd.DataFrame, expected_columns: list[str], target_columns=None):
    return validate_feature_frame(frame, expected_columns, target_columns)
