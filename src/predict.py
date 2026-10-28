from datetime import datetime, timezone
from pathlib import Path

from sklearn.metrics import accuracy_score, classification_report

from config import MODEL_PATH
from repository import ReviewRepository
from services.classifier import Classifier


def predict_batch(model, documents: list[dict]) -> list[dict]:
    """Generates predictions for a batch of documents using a Scikit-Learn model."""
    texts = [d["text"] for d in documents]
    probabilities = model.predict_proba(texts)
    positions = probabilities.argmax(axis=1)

    version = Path(MODEL_PATH).stem
    now = datetime.now(timezone.utc)

    predictions = []
    for doc, probs, pos in zip(documents, probabilities, positions):
        predictions.append(
            {
                "_id": doc["_id"],
                "prediction": {
                    "sentiment": str(model.classes_[pos]),
                    "confidence": float(probs[pos]),
                    "model": version,
                    "date": now,
                },
            }
        )
    return predictions


def load_unlabeled_documents() -> list[dict]:
    """Fetches unlabeled documents from MongoDB awaiting inference."""
    with ReviewRepository() as repo:
        return repo.find_unlabeled()


def save_predictions(predictions: list[dict]) -> int:
    """Persists prediction subdocuments to MongoDB."""
    with ReviewRepository() as repo:
        return repo.save_predictions(predictions)


def evaluate_predictions(documents: list[dict], predictions: list[dict], n_errors: int = 5):
    """Evaluates prediction accuracy against true ground truth labels."""
    true_labels = [d["true_label"] for d in documents]
    predicted_labels = [p["prediction"]["sentiment"] for p in predictions]

    print("\n" + "=" * 50)
    print("PREDICTION EVALUATION")
    print("=" * 50)
    print(f"Accuracy: {accuracy_score(true_labels, predicted_labels):.3f}\n")
    print(classification_report(true_labels, predicted_labels))

    errors = [
        (d, p)
        for d, p in zip(documents, predictions)
        if d["true_label"] != p["prediction"]["sentiment"]
    ]
    print(f"Errors: {len(errors)} of {len(documents)}")
    for doc, pred in errors[:n_errors]:
        sentiment = pred["prediction"]["sentiment"]
        confidence = pred["prediction"]["confidence"]
        text_snippet = doc["text"][:100]
        print(f"- true={doc['true_label']} | predicted={sentiment} ({confidence:.2f}) | {text_snippet}")


def classify_pending():
    """Service-level workflow to run batch classification for pending reviews."""
    classifier = Classifier()

    documents = load_unlabeled_documents()
    if not documents:
        print("No documents pending classification.")
        return

    print(f"Documents to classify: {len(documents)}")

    predictions = classifier.classify_documents(documents)
    saved_count = save_predictions(predictions)
    print(f"Predictions saved: {saved_count}")

    evaluate_predictions(documents, predictions)


if __name__ == "__main__":
    classify_pending()
