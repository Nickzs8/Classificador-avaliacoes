"""Unit tests for the Classifier inference service layer."""

from datetime import datetime
import joblib
import pytest
from services.classifier import Classifier
from src.train import build_pipeline

TEXTS = [
    "excelente produto, recomendo muito",
    "produto excelente, entrega rápida",
    "muito bom, recomendo o produto",
    "ótimo produto, recomendo",
    "péssimo produto, não funciona",
    "produto horrível, não funciona",
    "muito ruim, péssimo produto",
    "qualidade horrível, não recomendo",
]
LABELS = ["positive"] * 4 + ["negative"] * 4


@pytest.fixture
def temp_model(tmp_path):
    """Trains a quick synthetic model and saves it to a temporary directory."""
    pipeline = build_pipeline()
    pipeline.fit(TEXTS, LABELS)

    model_path = tmp_path / "modelo_teste.joblib"
    joblib.dump(pipeline, model_path)
    return model_path


def test_raises_error_when_model_does_not_exist(tmp_path):
    """Asserts FileNotFoundError is raised when the joblib artifact is missing."""
    nonexistent_path = tmp_path / "nonexistent_model.joblib"
    with pytest.raises(FileNotFoundError, match="Model artifact not found"):
        Classifier(model_path=str(nonexistent_path))


def test_classify_individual_text(temp_model):
    """Validates real-time single text classification output structure."""
    service = Classifier(model_path=str(temp_model))
    result = service.classify_text("produto excelente, recomendo muito")

    assert result["sentiment"] == "positive"
    assert 0.5 <= result["confidence"] <= 1.0
    assert result["model"] == "modelo_teste"
    assert isinstance(result["date"], datetime)


def test_classify_documents_in_batch(temp_model):
    """Validates batch document classification formatting and IDs."""
    service = Classifier(model_path=str(temp_model))
    docs = [
        {"_id": "id_1", "text": "produto excelente, recomendo"},
        {"_id": "id_2", "text": "produto péssimo, não funciona"},
    ]
    predictions = service.classify_documents(docs)

    assert len(predictions) == 2
    assert predictions[0]["_id"] == "id_1"
    assert predictions[0]["prediction"]["sentiment"] == "positive"
    assert predictions[1]["_id"] == "id_2"
    assert predictions[1]["prediction"]["sentiment"] == "negative"
