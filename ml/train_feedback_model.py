"""Train the SmartServe feedback text classifier on reviewed labels."""
from pathlib import Path

import pandas as pd
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.pipeline import make_pipeline

DATA_FILE = Path(__file__).resolve().parents[1] / "data" / "feedback_labels.csv"


def load_training_data():
    if not DATA_FILE.exists():
        raise FileNotFoundError("Add labelled rows to data/feedback_labels.csv first")

    data = pd.read_csv(DATA_FILE)
    if not {"comment", "label"}.issubset(data.columns):
        raise ValueError("Training CSV needs comment and label columns")

    data = data[["comment", "label"]].dropna()
    data["comment"] = data["comment"].astype(str).str.strip()
    data["label"] = data["label"].astype(str).str.strip()
    data = data[(data["comment"] != "") & (data["label"] != "")]
    data = data.drop_duplicates(subset=["comment", "label"])

    if data["label"].nunique() < 2:
        raise ValueError("Training CSV needs at least two different labels")
    if data["label"].value_counts().min() < 3:
        raise ValueError("Each label needs at least 3 examples for the 3-fold evaluation")
    return data


def build_model():
    """Build a compact model that also recognizes character-level word patterns."""
    return make_pipeline(
        TfidfVectorizer(
            analyzer="char_wb",
            ngram_range=(2, 5),
            sublinear_tf=True,
            strip_accents="unicode",
        ),
        LogisticRegression(C=3, class_weight="balanced", max_iter=2000, random_state=42),
    )


def train_model():
    data = load_training_data()
    model = build_model()
    model.fit(data["comment"], data["label"])
    return model


if __name__ == "__main__":
    model = train_model()
    print(f"Feedback model trained on {len(model[-1].classes_)} labels and reviewed demo data.")
