# System Architecture

This document provides a detailed specification of the software architecture, design patterns, MongoDB data modeling, and technical guidelines for the **Review Sentiment Classifier**.

---

## 1. Architectural Principles and Design Patterns

The project follows a **Layered Architecture** emphasizing loose coupling, high cohesion, and isolated automated testing:

```
┌────────────────────────────────────────────────────────┐
│               Presentation Layer / UI                  │
│       (CLI Scripts, BI Dashboard, and Web App)         │
├────────────────────────────────────────────────────────┤
│             API / Transport Layer                      │
│        (FastAPI: routes, validation, and DTOs)         │
├────────────────────────────────────────────────────────┤
│             Service / Domain Layer                     │
│  (Ingestion, ML Classifier, Training, and Prediction)  │
├────────────────────────────────────────────────────────┤
│             Data Access Layer                          │
│   (ReviewRepository: sole point of PyMongo usage)      │
├────────────────────────────────────────────────────────┤
│             Database / Storage Layer                   │
│             (MongoDB 8.2 on Docker)                    │
└────────────────────────────────────────────────────────┘
```

### Adopted Patterns:
* **Repository Pattern (`ReviewRepository`):** Encapsulates all query complexity, BSON aggregation pipelines, and MongoDB operations in a single class. No other module imports or interacts directly with `pymongo` or `MongoClient`.
* **Service Layer (`src/services/classifier.py`):** Centralizes model loading and NLP inference logic, sharing the exact same prediction pipeline across batch workflows and real-time API endpoints.
* **DTO / Schemas (Pydantic V2):** Enforces strict data contracts, type safety, and input sanitization on API boundaries.
* **Dependency Injection (`Depends`):** Injects repositories and services into FastAPI route handlers, enabling deterministic unit testing via in-memory mocks without requiring a running database.
* **Threadpool Offloading:** Route handlers that interact with blocking libraries (`pymongo`, `scikit-learn`, `joblib`) are defined with synchronous `def`. FastAPI automatically executes them in a dedicated worker threadpool, preventing event loop starvation.

---

## 2. Workflow Diagrams

### Batch Processing Workflow
```
Raw Dataset (CSV)
        │
        ▼
[prepare_data.py] ── Cleaning and Labeling ──► Sanitized CSV
                                                    │
                                                    ▼
                                            [ingest.py] ── BSON Ingestion ──► MongoDB
                                                                                │
       ┌───────────────────────────────────────────────────────────────────────┘
       ├─ Labeled Documents (90%) ──► [train.py] ──► Artifact models/modelo_v1.joblib
       │                                                         │
       └─ Unlabeled Documents (10%) ──► [predict.py] ◄───────────┘
                                                │
                                                ▼
                                   MongoDB (Retroactive UpdateOne)
                                                │
                                                ▼
                                    [analytics.py / dashboard.py]
```

### Real-Time API Inference Workflow
```
End User / Web Client
        │
        │ HTTP POST /reviews {"text": "...", "product": "..."}
        ▼
   FastAPI (Synchronous routes + Pydantic Schemas)
        │
        ├──► Classifier Service (loads modelo_v1.joblib once in memory)
        │         │
        │         ▼
        │    Prediction: sentiment ("positive"/"negative") + confidence (float)
        │
        └──► ReviewRepository (MongoDB)
                  │
                  ▼
          Persists BSON document:
          - rating: null, label: null, true_label: null
          - prediction: { sentiment, confidence, model, date }
          - origin: "api"
```

---

## 3. MongoDB Data Modeling

The database uses flexible BSON documents, ensuring seamless interoperability between historical batch records and real-time user submissions:

### Consolidated Document Schema:
```json
{
  "_id": {"$oid": "653b1e7c8f9b2a1234567890"},
  "text": "Chegou rápido, mas a embalagem veio amassada",
  "product": "Fone Bluetooth X",
  "date": "2018-03-12T14:05:00.000Z",
  "rating": 2,
  "label": null,
  "true_label": "negative",
  "prediction": {
    "sentiment": "negative",
    "confidence": 0.71,
    "model": "modelo_v1",
    "date": "2026-10-24T14:05:00.000Z"
  },
  "origin": "api"
}
```

### Field Rationale:
* **`text` (String):** Sanitized customer review text (trimmed, minimum 10 characters for training; minimum 3 characters for API).
* **`product` (String / Null):** Evaluated product name (optional for API clients).
* **`date` (ISODate):** Native BSON UTC timestamp enabling temporal aggregation and grouping via `$dateToString`.
* **`rating` (Int / Null):** Customer rating from 1 to 5 (null for reviews submitted via API).
* **`label` (String / Null):** Supervised training label (`"positive"` or `"negative"`). Stored as `null` in ~10% of batch data and in all API submissions to simulate unlabeled production data.
* **`true_label` (String / Null):** Original ground truth rating from the dataset for auditability. **Never exposed during training**.
* **`prediction` (Object / Null):** Subdocument populated by the classifier containing predicted `sentiment`, calibrated `confidence` probability, model identifier, and execution timestamp.
* **`origin` (String / Null):** Tracks data provenance (`"api"` or default `"batch"`).

---

## 4. Database Indexing & Optimization

To ensure predictable $O(\log N)$ lookups and fast analytical aggregations, the repository automatically provisions indexes on startup:

```python
db.reviews.create_index([("rotulo", ASCENDING)])
db.reviews.create_index([("produto", ASCENDING)])
db.reviews.create_index([("data", DESCENDING)])
```

* **Index on `data` (DESCENDING):** Directly satisfies the sorting criteria of `listar_recentes(limite=10)` used by the API and live feeds, performing an optimal `IXSCAN` without in-memory sorting.

---

## 5. Aggregation Pipeline Strategy

The repository delegates analytical calculations directly to the MongoDB Aggregation Framework, avoiding expensive in-memory processing in Python:

### Sentiment Coalescence Stage (`SENTIMENTO`):
```javascript
SENTIMENTO = {
  "$addFields": {
    "sentimento": {
      "$ifNull": ["$rotulo", "$predicao.classe"]
    }
  }
}
```
* **Analytical Coalescence:** If a review already contains a supervised `rotulo`, it is prioritized. If null, the pipeline falls back to the ML prediction (`predicao.classe`), unifying the dataset dynamically at query time.

### Evaluation Metric Protection:
The `taxa_acerto()` method explicitly filters documents where `rotulo_real != null`:
```javascript
{
  "$match": {
    "predicao": { "$ne": null },
    "rotulo_real": { "$ne": null }
  }
}
```
This guarantees that API submissions (which lack ground truth labels) are never counted as classification errors in global model accuracy calculations.

---

## 6. Automated Testing Strategy

The test suite enforces complete test isolation:
* **Preprocessing Tests (`test_labeling.py`):** Verify sanitization rules, class balance sampling, and immutability without disk or database access.
* **Ingestion Tests (`test_ingest.py`):** Validate BSON types and random 10% unlabeling using in-memory synthetic datasets and Pytest's `tmp_path`.
* **Model Tests (`test_model.py`):** Train a synthetic pipeline with 16 samples using a module-scoped fixture, asserting probability calibrations and `joblib` roundtrips.
* **API Tests (`test_api.py`):** Use FastAPI's `TestClient` and `app.dependency_overrides` with `FakeReviewRepository` and `FakeClassifier` to validate HTTP status codes (201, 404, 422, 503) with 0 network calls.
* **Interface Tests (`test_interface.py`):** Mock `httpx` network responses to test Streamlit connectivity, health checks, and timeout handling.
