from pathlib import Path
import joblib
import pandas as pd
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import classification_report
from sklearn.model_selection import train_test_split
from sklearn.pipeline import Pipeline

from config import MODEL_PATH
from repository import ReviewRepository


def load_data() -> pd.DataFrame:
    """Loads labeled documents from MongoDB for training."""
    with ReviewRepository() as repo:
        documents = repo.find_labeled()

    if not documents:
        raise ValueError(
            "No labeled documents found in MongoDB. Please run src/ingest.py first."
        )

    df = pd.DataFrame(documents)
    print(f"Data loaded from MongoDB: {len(df)} labeled documents.")
    return df


def build_pipeline() -> Pipeline:
    """Constructs the Scikit-Learn TF-IDF vectorizer and Logistic Regression pipeline."""
    return Pipeline(
        [
            (
                "tfidf",
                TfidfVectorizer(
                    ngram_range=(1, 2),  # unigrams and bigrams
                    min_df=2,  # drops tokens appearing in fewer than 2 texts
                ),
            ),
            (
                "clf",
                LogisticRegression(
                    class_weight="balanced",  # adjusts loss weights inversely proportional to class frequencies
                    max_iter=1000,
                    random_state=42,
                ),
            ),
        ]
    )


def predict_set(pipeline: Pipeline, X_test: pd.Series):
    """Generates predictions for a feature set."""
    return pipeline.predict(X_test)


def train_model():
    """Executes model training, evaluation on stratified test split, and joblib serialization."""
    df = load_data()
    X = df["text"]
    y = df["label"]

    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.20, random_state=42, stratify=y
    )

    print(f"Dataset split: {len(X_train)} train samples and {len(X_test)} test samples.\n")

    pipeline = build_pipeline()

    print("Fitting NLP pipeline...")
    pipeline.fit(X_train, y_train)

    y_pred = predict_set(pipeline, X_test)

    print("\n" + "=" * 50)
    print("CLASSIFICATION REPORT (TEST SPLIT)")
    print("=" * 50)
    print(classification_report(y_test, y_pred))

    model_path = Path(MODEL_PATH)
    model_path.parent.mkdir(parents=True, exist_ok=True)
    joblib.dump(pipeline, model_path)
    print(f"Model artifact successfully saved to: {model_path}")


if __name__ == "__main__":
    train_model()
