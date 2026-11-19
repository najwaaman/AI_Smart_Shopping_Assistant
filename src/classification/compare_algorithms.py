"""Compare TF-IDF classification algorithms using cleaned train/validation data."""

from __future__ import annotations

import sys
import time
import warnings
from pathlib import Path
from typing import Any

import joblib
import pandas as pd
import sklearn
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import accuracy_score, precision_recall_fscore_support
from sklearn.naive_bayes import MultinomialNB
from sklearn.pipeline import Pipeline
from sklearn.svm import LinearSVC


PROJECT_ROOT = Path(__file__).resolve().parents[2]
TRAIN_PATH = PROJECT_ROOT / "datasets" / "cleaned" / "train.csv"
VALIDATION_PATH = PROJECT_ROOT / "datasets" / "cleaned" / "validation.csv"

MODEL_DIR = PROJECT_ROOT / "models" / "classification" / "comparison"
RESULTS_DIR = PROJECT_ROOT / "reports" / "classification"
COMPARISON_PATH = RESULTS_DIR / "algorithm_comparison.csv"
REPORT_PATH = RESULTS_DIR / "Algorithm_Comparison_Report.txt"

ALGORITHMS: list[dict[str, Any]] = [
    {
        "name": "Multinomial Naive Bayes",
        "file_name": "multinomial_nb_tfidf.joblib",
        "classifier": MultinomialNB(alpha=1.0, fit_prior=True),
        "configuration": "MultinomialNB(alpha=1.0, fit_prior=True)",
    },
    {
        "name": "Linear SVM",
        "file_name": "linear_svm_tfidf.joblib",
        "classifier": LinearSVC(
            C=1.0,
            dual="auto",
            max_iter=5000,
            random_state=42,
        ),
        "configuration": (
            "LinearSVC(C=1.0, dual='auto', max_iter=5000, random_state=42)"
        ),
    },
    {
        "name": "Logistic Regression",
        "file_name": "logistic_regression_tfidf.joblib",
        "classifier": LogisticRegression(
            C=1.0,
            solver="lbfgs",
            max_iter=1000,
            random_state=42,
        ),
        "configuration": (
            "LogisticRegression(C=1.0, solver='lbfgs', max_iter=1000, "
            "random_state=42)"
        ),
    },
]


def load_split(path: Path) -> pd.DataFrame:
    """Read the description and label columns from a cleaned split."""
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


def make_pipeline(classifier: Any) -> Pipeline:
    """Create the same TF-IDF feature pipeline for each classifier."""
    return Pipeline(
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
            ("classifier", classifier),
        ]
    )


def write_report(
    *,
    records: list[dict[str, Any]],
    train_rows_before_drop: int,
    dropped_missing_descriptions: int,
    train_rows_used: int,
    validation_rows: int,
    classes: list[str],
    warning_messages: list[str],
) -> None:
    """Write the comparison findings and model-selection recommendation."""
    # Macro F1 is the primary ranking metric because it weights each class equally.
    best = max(
        records,
        key=lambda row: (
            row["f1_macro"],
            row["accuracy"],
            row["precision_macro"],
        ),
    )

    table_header = (
        f"{'Algorithm':<26} {'Accuracy':>10} {'Macro P':>10} "
        f"{'Macro R':>10} {'Macro F1':>10} {'Train sec':>11}"
    )
    table_rows = [
        (
            f"{row['algorithm']:<26} {row['accuracy']:>10.6f} "
            f"{row['precision_macro']:>10.6f} "
            f"{row['recall_macro']:>10.6f} "
            f"{row['f1_macro']:>10.6f} "
            f"{row['training_time_seconds']:>11.3f}"
        )
        for row in records
    ]

    report_lines = [
        "AI-Powered Smart Shopping Assistant",
        "Phase 2: Classification Algorithm Comparison",
        "Algorithm Comparison Report",
        "",
        "1. Data and split usage",
        "-----------------------",
        "Training input: datasets\\cleaned\\train.csv",
        "Validation input: datasets\\cleaned\\validation.csv",
        "Only these cleaned splits were loaded. The separate test split was",
        "not loaded, evaluated, or used for model selection.",
        "Raw E-commerce splits and zero-byte CSVs were not used.",
        f"Training rows before missing-text handling: {train_rows_before_drop:,}",
        f"Training rows excluded for missing description: {dropped_missing_descriptions:,}",
        f"Training rows used: {train_rows_used:,}",
        f"Validation rows evaluated: {validation_rows:,}",
        f"Target classes: {', '.join(classes)}",
        "",
        "2. Fair comparison setup",
        "------------------------",
        "Each algorithm received the same training rows, the same validation",
        "rows, and a fresh but identically configured TF-IDF vectorizer.",
        "Each vectorizer was fitted only on training descriptions. Validation",
        "text was transformed with the corresponding fitted vectorizer.",
        "The one training row with a missing description was excluded,",
        "matching the Phase 1 baseline decision. No other custom text",
        "preprocessing was applied.",
        "",
        "TF-IDF settings: lowercase=True; word unigrams; min_df=1;",
        "max_df=1.0; max_features=None; sublinear_tf=False; L2 normalization.",
        "Classifier settings:",
        "  Multinomial Naive Bayes: alpha=1.0, fit_prior=True.",
        "  Linear SVM: C=1.0, dual='auto', max_iter=5000, random_state=42.",
        "  Logistic Regression: C=1.0, solver='lbfgs', max_iter=1000,",
        "    random_state=42 (same settings as the Phase 1 baseline).",
        "",
        "Training time is the elapsed time for pipeline.fit(), including",
        "fitting TF-IDF and the classifier. It excludes data loading,",
        "validation prediction/scoring, and model serialization.",
        "",
        "3. Validation comparison",
        "-------------------------",
        table_header,
        "-" * len(table_header),
        *table_rows,
        "",
        "Macro precision, recall, and F1 use equal weight for each class.",
        "The table is also saved as reports\\classification\\algorithm_comparison.csv.",
        "",
        "4. Recommendation",
        "------------------",
        f"Recommended next-stage model: {best['algorithm']}. It has the highest",
        f"validation macro F1 ({best['f1_macro']:.6f}); accuracy is",
        f"{best['accuracy']:.6f}. Macro F1 is the primary ranking criterion",
        "because the class supports are not identical. Treat this as a",
        "validation-based choice only; do not make a final generalization",
        "claim from these validation results.",
        "",
        "The Logistic Regression result is a fresh re-evaluation using the",
        "same Phase 1 settings. Its comparison copy is saved under",
        "models\\classification\\comparison\\; the Phase 1 baseline model and",
        "reports were not overwritten.",
        "",
        "5. Limitations and warnings",
        "----------------------------",
        "This comparison uses one fixed parameter configuration per model;",
        "there was no hyperparameter search. Training times depend on the",
        "machine and software environment. Validation was used for algorithm",
        "comparison, so any later model changes should be evaluated only",
        "after decisions are finalized. The test data remains untouched.",
        "Warnings captured during fitting:",
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
        "Saved comparison models:",
        *[
            f"models\\classification\\comparison\\{row['model_file']}"
            for row in records
        ],
        "",
    ]
    REPORT_PATH.write_text("\n".join(report_lines), encoding="utf-8")


def main() -> None:
    """Fit, evaluate, and save all three TF-IDF classification pipelines."""
    model_paths = [MODEL_DIR / item["file_name"] for item in ALGORITHMS]
    output_paths = [*model_paths, COMPARISON_PATH, REPORT_PATH]
    existing_outputs = [path for path in output_paths if path.exists()]
    if existing_outputs:
        paths = "\n".join(str(path) for path in existing_outputs)
        raise FileExistsError(
            "Refusing to overwrite existing comparison artifacts:\n" + paths
        )

    train = load_split(TRAIN_PATH)
    validation = load_split(VALIDATION_PATH)
    train_rows_before_drop = len(train)

    # Match the documented baseline: exclude the row with missing input text.
    dropped_missing_descriptions = int(train["description"].isna().sum())
    train = train.dropna(subset=["description"]).copy()

    if train["label"].isna().any():
        raise ValueError("Training labels contain missing values.")
    if validation[["description", "label"]].isna().any().any():
        raise ValueError("Validation descriptions or labels contain missing values.")
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

    results: list[dict[str, Any]] = []
    warning_messages: list[str] = []
    fitted_models: list[tuple[str, Pipeline]] = []

    for item in ALGORITHMS:
        pipeline = make_pipeline(item["classifier"])
        print(f"Training {item['name']}...")

        # Timing includes the vectorizer fit, since it is part of the pipeline.
        with warnings.catch_warnings(record=True) as captured_warnings:
            warnings.simplefilter("always")
            start_time = time.perf_counter()
            pipeline.fit(x_train, y_train)
            training_time = time.perf_counter() - start_time
            predictions = pipeline.predict(x_validation)

        for warning in captured_warnings:
            message = (
                f"{item['name']} - {warning.category.__name__}: {warning.message}"
            )
            warning_messages.append(message)
            print(f"WARNING: {message}", file=sys.stderr)

        precision, recall, f1, _ = precision_recall_fscore_support(
            y_validation,
            predictions,
            labels=classes,
            average="macro",
            zero_division=0,
        )
        results.append(
            {
                "algorithm": item["name"],
                "accuracy": float(accuracy_score(y_validation, predictions)),
                "precision_macro": float(precision),
                "recall_macro": float(recall),
                "f1_macro": float(f1),
                "training_time_seconds": float(training_time),
                "model_file": item["file_name"],
                "configuration": item["configuration"],
            }
        )
        fitted_models.append((item["file_name"], pipeline))

    # All outputs use new, dedicated paths; existing baseline files stay intact.
    MODEL_DIR.mkdir(parents=True, exist_ok=True)
    RESULTS_DIR.mkdir(parents=True, exist_ok=True)
    for file_name, pipeline in fitted_models:
        joblib.dump(pipeline, MODEL_DIR / file_name)

    pd.DataFrame(results).to_csv(COMPARISON_PATH, index=False)
    write_report(
        records=results,
        train_rows_before_drop=train_rows_before_drop,
        dropped_missing_descriptions=dropped_missing_descriptions,
        train_rows_used=len(train),
        validation_rows=len(validation),
        classes=classes,
        warning_messages=warning_messages,
    )

    print("\nValidation comparison:")
    print(pd.DataFrame(results).to_string(index=False))
    print(f"\nComparison CSV: {COMPARISON_PATH}")
    print(f"Comparison report: {REPORT_PATH}")


if __name__ == "__main__":
    main()
