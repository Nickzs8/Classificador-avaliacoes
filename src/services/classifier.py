from datetime import datetime, timezone
from pathlib import Path
import joblib

from config import MODEL_PATH


class Classifier:
    """Service layer responsible for loading the model and executing sentiment inference."""

    def __init__(self, model_path: str = MODEL_PATH):
        self.model_path = Path(model_path)

        if not self.model_path.exists():
            raise FileNotFoundError(
                f"Model artifact not found at '{self.model_path}'. "
                "Run 'python run_pipeline.py' to train and generate the model."
            )

        self.model = joblib.load(self.model_path)
        self.version = self.model_path.stem

    def classify_text(self, text: str) -> dict:
        """Classifies sentiment for a single review string."""
        probs = self.model.predict_proba([text])[0]
        pos = probs.argmax()

        return {
            "sentiment": str(self.model.classes_[pos]),
            "confidence": round(float(probs[pos]), 4),
            "model": self.version,
            "date": datetime.now(timezone.utc),
        }

    def classify_documents(self, documents: list[dict]) -> list[dict]:
        """Classifies a batch of review documents."""
        if not documents:
            return []

        texts = [d["text"] for d in documents]
        probabilities = self.model.predict_proba(texts)
        positions = probabilities.argmax(axis=1)
        now = datetime.now(timezone.utc)

        predictions = []
        for doc, probs, pos in zip(documents, probabilities, positions):
            predictions.append(
                {
                    "_id": doc["_id"],
                    "prediction": {
                        "sentiment": str(self.model.classes_[pos]),
                        "confidence": round(float(probs[pos]), 4),
                        "model": self.version,
                        "date": now,
                    },
                }
            )
        return predictions
