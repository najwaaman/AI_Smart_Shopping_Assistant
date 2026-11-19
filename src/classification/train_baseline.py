"""Train a TF-IDF and Logistic Regression product-category baseline."""

from __future__ import annotations

import json
import sys
import warnings
from pathlib import Path

import joblib
import pandas as pd
import sklearn
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import (
    accuracy_score,
    classification_report,
    confusion_matrix,
    precision_recall_fscore_support,
)
from sklearn.pipeline import Pipeline


PROJECT_ROOT = Path(__file__).resolve().parents[2]
TRAIN_PATH = PROJECT_ROOT / "datasets" / "cleaned" / "train.csv"
VALIDATION_PATH = PROJECT_ROOT / "datasets" / "cleaned" / "validation.csv"

MODEL_PATH = (
    PROJECT_ROOT
    / "models"
    / "classification"
    / "tfidf_logistic_regression.joblib"
)
RESULTS_DIR = PROJECT_ROOT / "reports" / "classification"
CONFUSION_MATRIX_PATH = RESULTS_DIR / "validation_confusion_matrix.csv"
METRICS_PATH = RESULTS_DIR / "validation_metrics.json"
REPORT_PATH = RESULTS_DIR / "Baseline_Model_Report.txt"


def load_split(path: Path) -> pd.DataFrame:
    """Load only the two expected columns from one cleaned split."""
    if not path.is_file():
        raise FileNotFoundError(f"Required cleaned dataset was not found: {path}")

    frame = pd.read_csv(
        path,
        usecols=["description", "label"],
        dtype={"description": "string", "label": "string"},
    )
    if frame.empty:
        raise ValueError(f"Dataset has no rows: {path}")
    return frame


def write_baseline_report(
    *,
    train_rows_before_drop: int,
    dropped_missing_descriptions: int,
    train_rows_used: int,
    validation_rows: int,
    classes: list[str],
    metrics: dict[str, float],
    class_report_text: str,
    matrix: list[list[int]],
    warning_messages: list[str],
) -> None:
    """Write the human-readable record of the baseline experiment."""
    report_lines = [
        "AI-Powered Smart Shopping Assistant",
        "Phase 1: Product Category Text Classification",
        "Baseline Model Report",
        "",
        "1. Data used",
        "------------",
        "Training input: datasets\\cleaned\\train.csv",
        "Validation input: datasets\\cleaned\\validation.csv",
        "The test split was not loaded or used.",
        "Raw E-commerce splits and zero-byte CSVs were not used.",
        f"Training rows before missing-text handling: {train_rows_before_drop:,}",
        f"Training rows excluded for missing description: {dropped_missing_descriptions:,}",
        f"Training rows used to fit the pipeline: {train_rows_used:,}",
        f"Validation rows used for evaluation: {validation_rows:,}",
        f"Target classes: {', '.join(classes)}",
        "",
        "2. Preprocessing",
        "----------------",
        "The single training row with a missing description was excluded. A",
        "missing text value cannot provide meaningful text features; it was",
        "not imputed with invented text or an empty string. Training labels",
        "and all validation descriptions/labels were checked for missing",
        "values. No other custom cleaning or normalization was applied.",
        "The TF-IDF vectorizer performs its configured lowercase and token",
        "processing as part of the fitted pipeline.",
        "",
        "3. TF-IDF configuration",
        "------------------------",
        "Word-level unigrams (ngram_range=(1, 1)); lowercase=True;",
        "min_df=1; max_df=1.0; max_features=None; sublinear_tf=False;",
        "L2 normalization. The vectorizer was fitted only on training text.",
        "Validation text was transformed by that already-fitted vectorizer.",
        "",
        "4. Classifier configuration",
        "----------------------------",
        "LogisticRegression(C=1.0, solver='lbfgs', max_iter=1000,",
        "random_state=42). The classifier and vectorizer are saved together",
        "as one scikit-learn Pipeline.",
        "",
        "5. Training and evaluation",
        "--------------------------",
        "The pipeline was fitted on training descriptions and labels only.",
        "The validation split was used only to generate predictions and",
        "calculate the metrics below; it was not used to fit the vectorizer",
        "or classifier. Macro precision, recall, and F1 give each class equal",
        "weight. The confusion matrix uses the class order shown below.",
        "",
        f"Accuracy:          {metrics['accuracy']:.6f}",
        f"Precision (macro): {metrics['precision_macro']:.6f}",
        f"Recall (macro):    {metrics['recall_macro']:.6f}",
        f"F1-score (macro):  {metrics['f1_macro']:.6f}",
        "",
        "Classification report (validation):",
        class_report_text,
        "Confusion matrix (rows=true class, columns=predicted class):",
        "Class order: " + " | ".join(classes),
        *[
            f"{classes[index]}: " + " | ".join(str(value) for value in row)
            for index, row in enumerate(matrix)
        ],
        "",
        "6. Limitations",
        "---------------",
        "This is a single TF-IDF/Logistic Regression baseline, not a tuned",
        "model comparison. Validation scores are an intermediate estimate;",
        "the untouched test split should be considered only after model and",
        "configuration decisions are complete. Product descriptions can be",
        "long or noisy, and category imbalance and the excluded missing-text",
        "row may affect results. No customer, product-interaction, review, or",
        "sentiment information is present in these classification inputs.",
        "",
        "Training warnings:",
        *(
            [f"- {message}" for message in warning_messages]
            if warning_messages
            else ["None captured."]
        ),
        "",
        f"Python version: {sys.version.split()[0]}",
        f"pandas version: {pd.__version__}",
        f"scikit-learn version: {sklearn.__version__}",
        "",
        "Artifacts:",
        "models\\classification\\tfidf_logistic_regression.joblib",
        "reports\\classification\\validation_confusion_matrix.csv",
        "reports\\classification\\validation_metrics.json",
        "reports\\classification\\Baseline_Model_Report.txt",
        "",
    ]
    REPORT_PATH.write_text("\n".join(report_lines), encoding="utf-8")


def main() -> None:
    """Fit the baseline on train.csv and evaluate it on validation.csv."""
    # Fail before training rather than replacing artifacts from another run.
    output_paths = [
        MODEL_PATH,
        CONFUSION_MATRIX_PATH,
        METRICS_PATH,
        REPORT_PATH,
    ]
    existing_outputs = [path for path in output_paths if path.exists()]
    if existing_outputs:
        paths = "\n".join(str(path) for path in existing_outputs)
        raise FileExistsError(
            "Refusing to overwrite existing baseline artifacts:\n" + paths
        )

    train = load_split(TRAIN_PATH)
    validation = load_split(VALIDATION_PATH)
    train_rows_before_drop = len(train)

    # Drop the known missing training description instead of inventing text.
    dropped_missing_descriptions = int(train["description"].isna().sum())
    train = train.dropna(subset=["description"]).copy()

    if train["label"].isna().any():
        raise ValueError("Training labels contain missing values.")
    if validation[["description", "label"]].isna().any().any():
        raise ValueError("Validation descriptions or labels contain missing values.")

    # Empty strings are different from missing values, so reject them explicitly.
    if train["description"].str.strip().eq("").any():
        raise ValueError("Training data contains empty descriptions.")
    if validation["description"].str.strip().eq("").any():
        raise ValueError("Validation data contains empty descriptions.")

    x_train = train["description"].tolist()
    y_train = train["label"].tolist()
    x_validation = validation["description"].tolist()
    y_validation = validation["label"].tolist()

    classes = sorted(set(y_train))
    unseen_validation_labels = sorted(set(y_validation) - set(classes))
    if unseen_validation_labels:
        raise ValueError(
            "Validation contains labels not present in training: "
            + ", ".join(unseen_validation_labels)
        )

    # Keeping TF-IDF inside the pipeline ensures fit() sees training text only.
    pipeline = Pipeline(
        steps=[
            (
                "tfidf",
                TfidfVectorizer(
                    lowercase=True,
                    ngram_range=(1, 1),
                    min_df=1,
                    max_df=1.0,
                    max_features=None,
                    sublinear_tf=False,
                    norm="l2",
                ),
            ),
            (
                "classifier",
                LogisticRegression(
                    C=1.0,
                    solver="lbfgs",
                    max_iter=1000,
                    random_state=42,
                ),
            ),
        ]
    )

    # Capture warnings so they are both visible and recorded in the report.
    with warnings.catch_warnings(record=True) as captured_warnings:
        warnings.simplefilter("always")
        pipeline.fit(x_train, y_train)
        predictions = pipeline.predict(x_validation)

    warning_messages = [
        f"{warning.category.__name__}: {warning.message}"
        for warning in captured_warnings
    ]
    for message in warning_messages:
        print(f"WARNING: {message}", file=sys.stderr)

    accuracy = float(accuracy_score(y_validation, predictions))
    precision, recall, f1, _ = precision_recall_fscore_support(
        y_validation,
        predictions,
        labels=classes,
        average="macro",
        zero_division=0,
    )
    metrics = {
        "accuracy": accuracy,
        "precision_macro": float(precision),
        "recall_macro": float(recall),
        "f1_macro": float(f1),
    }
    class_report = classification_report(
        y_validation,
        predictions,
        labels=classes,
        target_names=classes,
        output_dict=True,
        zero_division=0,
    )
    class_report_text = classification_report(
        y_validation,
        predictions,
        labels=classes,
        target_names=classes,
        zero_division=0,
    )
    matrix_array = confusion_matrix(
        y_validation,
        predictions,
        labels=classes,
    )
    matrix = matrix_array.tolist()

    # Create output folders only after inputs and evaluation have succeeded.
    MODEL_PATH.parent.mkdir(parents=True, exist_ok=True)
    RESULTS_DIR.mkdir(parents=True, exist_ok=True)

    joblib.dump(pipeline, MODEL_PATH)
    pd.DataFrame(matrix, index=classes, columns=classes).to_csv(
        CONFUSION_MATRIX_PATH,
        index_label="true_label",
    )

    results = {
        "training_data": {
            "path": str(TRAIN_PATH.relative_to(PROJECT_ROOT)),
            "rows_before_missing_description_drop": train_rows_before_drop,
            "missing_description_rows_dropped": dropped_missing_descriptions,
            "rows_used": len(train),
        },
        "validation_data": {
            "path": str(VALIDATION_PATH.relative_to(PROJECT_ROOT)),
            "rows_evaluated": len(validation),
        },
        "test_data_used": False,
        "classes": classes,
        "model_configuration": {
            "pipeline": ["TfidfVectorizer", "LogisticRegression"],
            "tfidf": {
                "lowercase": True,
                "ngram_range": [1, 1],
                "min_df": 1,
                "max_df": 1.0,
                "max_features": None,
                "sublinear_tf": False,
                "norm": "l2",
                "fit_data": "training split only",
            },
            "logistic_regression": {
                "C": 1.0,
                "solver": "lbfgs",
                "max_iter": 1000,
                "random_state": 42,
            },
        },
        "validation_metrics": metrics,
        "classification_report": class_report,
        "confusion_matrix": {
            "class_order": classes,
            "values": matrix,
        },
        "warnings": warning_messages,
    }
    METRICS_PATH.write_text(
        json.dumps(results, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )

    write_baseline_report(
        train_rows_before_drop=train_rows_before_drop,
        dropped_missing_descriptions=dropped_missing_descriptions,
        train_rows_used=len(train),
        validation_rows=len(validation),
        classes=classes,
        metrics=metrics,
        class_report_text=class_report_text,
        matrix=matrix,
        warning_messages=warning_messages,
    )

    print(f"Training rows used: {len(train):,}")
    print(f"Validation rows evaluated: {len(validation):,}")
    for name, value in metrics.items():
        print(f"{name}: {value:.6f}")
    print(f"Model: {MODEL_PATH}")
    print(f"Validation results: {METRICS_PATH}")


if __name__ == "__main__":
    main()
