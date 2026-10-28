from typing import List
from fastapi import FastAPI, Depends, HTTPException, Query, Response, status

from api.dependencies import get_repository, get_classifier
from api.schemas import ReviewInput, ReviewOutput, HealthOutput
from repository import ReviewRepository
from services.classifier import Classifier

app = FastAPI(
    title="Review Sentiment Classifier API",
    description="Real-time sentiment classification for customer reviews.",
    version="2.0.0",
)


@app.post(
    "/reviews",
    response_model=ReviewOutput,
    status_code=status.HTTP_201_CREATED,
    tags=["Reviews"],
)
def create_review(
    payload: ReviewInput,
    repo: ReviewRepository = Depends(get_repository),
    classifier: Classifier = Depends(get_classifier),
):
    """Classifies a customer review and persists the record into MongoDB."""
    prediction = classifier.classify_text(payload.text)

    document = {
        "text": payload.text,
        "product": payload.product,
        "date": prediction["date"],
        "rating": None,
        "label": None,
        "true_label": None,
        "prediction": {
            "sentiment": prediction["sentiment"],
            "confidence": prediction["confidence"],
            "model": prediction["model"],
            "date": prediction["date"],
        },
        "origin": "api",
    }

    generated_id = repo.insert_review(document)

    return ReviewOutput(
        id=generated_id,
        text=payload.text,
        product=payload.product,
        sentiment=prediction["sentiment"],
        confidence=prediction["confidence"],
        model=prediction["model"],
        date=prediction["date"],
    )


@app.get(
    "/reviews/{id}",
    response_model=ReviewOutput,
    tags=["Reviews"],
)
def get_review(
    id: str,
    repo: ReviewRepository = Depends(get_repository),
):
    """Retrieves a specific review by its unique identifier."""
    doc = repo.find_by_id(id)
    if not doc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Review with ID '{id}' was not found.",
        )

    pred = doc.get("prediction") or {}
    return ReviewOutput(
        id=doc["_id"],
        text=doc["text"],
        product=doc.get("product"),
        sentiment=pred.get("sentiment") or doc.get("label") or "positive",
        confidence=pred.get("confidence", 1.0),
        model=pred.get("model", "legacy"),
        date=doc.get("date") or pred.get("date"),
    )


@app.get(
    "/reviews",
    response_model=List[ReviewOutput],
    tags=["Reviews"],
)
def list_reviews(
    limit: int = Query(default=10, ge=1, le=100, description="Maximum number of items to return"),
    repo: ReviewRepository = Depends(get_repository),
):
    """Lists recent reviews ordered by date descending."""
    docs = repo.list_recent(limit=limit)
    results = []
    for doc in docs:
        pred = doc.get("prediction") or {}
        results.append(
            ReviewOutput(
                id=doc["_id"],
                text=doc["text"],
                product=doc.get("product"),
                sentiment=pred.get("sentiment") or doc.get("label") or "positive",
                confidence=pred.get("confidence", 1.0),
                model=pred.get("model", "legacy"),
                date=doc.get("date") or pred.get("date"),
            )
        )
    return results


@app.get(
    "/health",
    response_model=HealthOutput,
    tags=["Health"],
)
def check_health(
    response: Response,
    repo: ReviewRepository = Depends(get_repository),
    classifier: Classifier = Depends(get_classifier),
):
    """Healthcheck: validates MongoDB connection and loaded model artifact."""
    db_ok = repo.ping()
    model_ok = classifier is not None and classifier.model is not None

    if not db_ok or not model_ok:
        response.status_code = status.HTTP_503_SERVICE_UNAVAILABLE
        return HealthOutput(status="error", database=db_ok, model=model_ok)

    return HealthOutput(status="ok", database=True, model=True)
