"""Unit tests for the Scikit-Learn TF-IDF and Logistic Regression ML pipeline."""

from datetime import datetime
import joblib
import pytest

import src.predict as predict
from src.train import build_pipeline

SAMPLE_TEXTS = [
    # Positive samples
    "excelente produto, recomendo",
    "ótimo produto, recomendo muito",
    "excelente qualidade, adorei",
    "chegou rápido, produto excelente",
    "adorei, produto ótimo",
    "ótima qualidade, recomendo",
    "produto excelente, chegou antes do prazo",
    "muito bom, excelente, recomendo",
    # Negative samples
    "péssimo produto, não funciona",
    "produto péssimo, não compensa",
    "não funciona, qualidade péssima",
    "chegou quebrado, produto péssimo",
    "horrível, não funciona nada",
    "qualidade horrível, não compensa",
    "produto horrível, chegou quebrado",
    "muito ruim, péssimo, não compensa",
]
SAMPLE_LABELS = ["positive"] * 8 + ["negative"] * 8


@pytest.fixture(scope="module")
def trained_pipeline():
    """Trains a lightweight synthetic Scikit-Learn pipeline once for module tests."""
    pipeline = build_pipeline()
    pipeline.fit(SAMPLE_TEXTS, SAMPLE_LABELS)
    return pipeline


def test_predicts_obvious_positive_and_negative_phrases(trained_pipeline):
    """Verifies clear sentiment inference for obvious positive and negative phrases."""
    predictions = trained_pipeline.predict(["excelente, recomendo", "péssimo, não funciona"])
    assert list(predictions) == ["positive", "negative"]


def test_prediction_probabilities_sum_to_one(trained_pipeline):
    """Verifies that predicted class probabilities are calibrated and sum to 1.0."""
    probs = trained_pipeline.predict_proba(["excelente, recomendo"])

    assert probs.shape == (1, 2)
    assert probs.sum() == pytest.approx(1.0)
    assert set(trained_pipeline.classes_) == {"negative", "positive"}


def test_serialized_and_reloaded_model_produces_identical_predictions(trained_pipeline, tmp_path):
    """Ensures model serialization via joblib preserves identical predictions upon reload."""
    model_path = tmp_path / "modelo_teste.joblib"
    joblib.dump(trained_pipeline, model_path)
    loaded_pipeline = joblib.load(model_path)

    phrases = ["excelente, recomendo", "péssimo, não funciona"]
    assert list(loaded_pipeline.predict(phrases)) == list(trained_pipeline.predict(phrases))


def test_batch_prediction_formats_database_document_correctly(trained_pipeline, monkeypatch):
    """Asserts that predict.prever formats the retroactive prediction subdocument for MongoDB."""
    monkeypatch.setattr(predict, "MODEL_PATH", "models/modelo_teste.joblib")
    documents = [{"_id": 1, "text": "excelente, recomendo", "true_label": "positive"}]

    predictions = predict.predict_batch(trained_pipeline, documents)

    assert len(predictions) == 1
    prediction = predictions[0]["prediction"]
    assert predictions[0]["_id"] == 1
    assert prediction["sentiment"] == "positive"
    assert 0.5 <= prediction["confidence"] <= 1.0
    assert prediction["model"] == "modelo_teste"
    assert isinstance(prediction["date"], datetime)

