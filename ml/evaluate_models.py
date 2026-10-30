"""Measure feedback classifier performance across repeated held-out folds."""
from sklearn.metrics import make_scorer, precision_score, recall_score, f1_score
from sklearn.model_selection import RepeatedStratifiedKFold, cross_validate

try:  # Support both `python ml/evaluate_models.py` and `import ml.evaluate_models`.
    from .train_feedback_model import build_model, load_training_data
except ImportError:
    from train_feedback_model import build_model, load_training_data


def evaluate(repeats=5):
    data = load_training_data()
    folds = RepeatedStratifiedKFold(n_splits=3, n_repeats=repeats, random_state=42)
    scoring = {
        "accuracy": "accuracy",
        "precision": make_scorer(precision_score, average="macro", zero_division=0),
        "recall": make_scorer(recall_score, average="macro", zero_division=0),
        "f1": make_scorer(f1_score, average="macro", zero_division=0),
    }
    result = cross_validate(
        build_model(),
        data["comment"],
        data["label"],
        cv=folds,
        scoring=scoring,
        error_score="raise",
    )
    return {
        metric: (result[f"test_{metric}"].mean(), result[f"test_{metric}"].std())
        for metric in scoring
    }, len(data), data["label"].nunique(), repeats


if __name__ == "__main__":
    metrics, rows, labels, repeats = evaluate()
    print(f"Feedback classification · {rows} labeled examples · {labels} labels")
    print(f"Repeated stratified 3-fold cross-validation ({repeats} repeats; 15 held-out folds)")
    for metric, (mean, deviation) in metrics.items():
        print(f"{metric.title()}: {mean:.3f} ± {deviation:.3f}")
    print("Small demo data: results are preliminary, not a production accuracy claim.")
