"""Integration and contract tests for the FastAPI REST API endpoints."""

from datetime import datetime, timezone
import pytest
from fastapi.testclient import TestClient

from api.main import app
from api.dependencies import get_repository, get_classifier


class FakeReviewRepository:
    """In-memory fake implementation of ReviewRepository for isolated testing."""

    def __init__(self):
        self.documents = []
        self._ping_ok = True

    def ping(self) -> bool:
        return self._ping_ok

    def insert_review(self, doc: dict) -> str:
        doc_copy = dict(doc)
        generated_id = f"6720c1f2e4b0a1d2c3e4f5a{len(self.documents) + 1}"
        doc_copy["_id"] = generated_id
        self.documents.append(doc_copy)
        return generated_id

    def find_by_id(self, review_id: str) -> dict | None:
        for doc in self.documents:
            if doc["_id"] == review_id:
                return dict(doc)
        return None

    def list_recent(self, limit: int = 10) -> list[dict]:
        return [dict(d) for d in reversed(self.documents)][:limit]


class FakeClassifier:
    """In-memory fake implementation of Classifier without disk model loading."""

    def __init__(self, model_ok: bool = True):
        self.model = object() if model_ok else None
        self.version = "modelo_teste"

    def classify_text(self, text: str) -> dict:
        sentiment = "positive" if "bom" in text.lower() or "excelente" in text.lower() or "great" in text.lower() else "negative"
        return {
            "sentiment": sentiment,
            "confidence": 0.95,
            "model": self.version,
            "date": datetime.now(timezone.utc),
        }


@pytest.fixture
def fake_repo():
    return FakeReviewRepository()


@pytest.fixture
def fake_classifier():
    return FakeClassifier()


@pytest.fixture
def client(fake_repo, fake_classifier):
    """TestClient with database and classifier dependencies replaced by in-memory fakes."""
    app.dependency_overrides[get_repository] = lambda: fake_repo
    app.dependency_overrides[get_classifier] = lambda: fake_classifier

    with TestClient(app) as test_client:
        yield test_client

    app.dependency_overrides.clear()


# Creation and Persistence Endpoint Tests


def test_post_valid_review_returns_201_and_persists_schema(client, fake_repo):
    """Asserts that a valid payload returns 201 and persists proper schema attributes."""
    payload = {
        "text": "Produto excelente, chegou muito rápido!",
        "product": "Fone Bluetooth X",
    }
    response = client.post("/reviews", json=payload)

    assert response.status_code == 201
    data = response.json()

    assert data["id"].startswith("6720c1f2e4b0a1d2c3e4f5a")
    assert data["text"] == "Produto excelente, chegou muito rápido!"
    assert data["product"] == "Fone Bluetooth X"
    assert data["sentiment"] == "positive"
    assert data["confidence"] == 0.95
    assert data["model"] == "modelo_teste"
    assert "date" in data

    # Validate persisted document in repository
    assert len(fake_repo.documents) == 1
    persisted_doc = fake_repo.documents[0]
    assert persisted_doc["origin"] == "api"
    assert persisted_doc["rating"] is None
    assert persisted_doc["label"] is None
    assert persisted_doc["true_label"] is None
    assert persisted_doc["prediction"]["sentiment"] == "positive"


def test_post_review_with_text_shorter_than_3_returns_422(client):
    """Asserts that review texts with fewer than 3 characters fail with 422 Unprocessable Entity."""
    response = client.post("/reviews", json={"text": "Oi"})
    assert response.status_code == 422
    assert any(err["type"] == "string_too_short" for err in response.json()["detail"])


def test_post_review_with_empty_or_whitespace_text_returns_422(client):
    """Verifies that whitespace-only and empty strings are rejected by custom field validator."""
    response_spaces = client.post("/reviews", json={"text": "     "})
    assert response_spaces.status_code == 422

    response_empty = client.post("/reviews", json={"text": ""})
    assert response_empty.status_code == 422


def test_post_review_with_text_longer_than_2000_returns_422(client):
    """Verifies that review texts exceeding 2000 characters fail with 422."""
    giant_text = "a" * 2001
    response = client.post("/reviews", json={"text": giant_text})
    assert response.status_code == 422
    assert any(err["type"] == "string_too_long" for err in response.json()["detail"])


# Lookup Endpoint Tests


def test_get_existing_review_by_id_returns_200(client):
    """Asserts that an existing review can be retrieved by its hexadecimal ID."""
    post_res = client.post("/reviews", json={"text": "Muito bom produto!"})
    created_id = post_res.json()["id"]

    get_res = client.get(f"/reviews/{created_id}")
    assert get_res.status_code == 200
    assert get_res.json()["id"] == created_id
    assert get_res.json()["text"] == "Muito bom produto!"


def test_get_nonexistent_review_by_id_returns_404(client):
    """Asserts that querying a nonexistent ID returns 404 Not Found."""
    response = client.get("/reviews/id_inexistente_123")
    assert response.status_code == 404
    assert "was not found" in response.json()["detail"]


# List and Pagination Tests


def test_get_reviews_with_limit_and_pagination(client):
    """Asserts that listing reviews respects the limit parameter and orders chronologically."""
    for i in range(5):
        client.post("/reviews", json={"text": f"Avaliação teste número {i+1}"})

    response = client.get("/reviews?limit=3")
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 3
    # The first item must be the most recently created (number 5)
    assert data[0]["text"] == "Avaliação teste número 5"


def test_get_reviews_with_invalid_limit_returns_422(client):
    """Asserts that limits less than 1 or greater than 100 fail with 422."""
    res_zero = client.get("/reviews?limit=0")
    assert res_zero.status_code == 422

    res_large = client.get("/reviews?limit=101")
    assert res_large.status_code == 422


# System Healthcheck Tests


def test_get_health_success_returns_200(client):
    """Asserts that /health returns 200 OK when database and model are operational."""
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok", "database": True, "model": True}


def test_get_health_database_failure_returns_503(client, fake_repo):
    """Asserts that /health returns 503 Service Unavailable when database ping fails."""
    fake_repo._ping_ok = False
    response = client.get("/health")

    assert response.status_code == 503
    assert response.json() == {"status": "error", "database": False, "model": True}


def test_get_health_model_failure_returns_503(client, fake_classifier):
    """Asserts that /health returns 503 Service Unavailable when model is uninitialized."""
    fake_classifier.model = None
    response = client.get("/health")

    assert response.status_code == 503
    assert response.json() == {"status": "error", "database": True, "model": False}
