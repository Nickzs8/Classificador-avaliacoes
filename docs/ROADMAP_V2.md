# V2 Roadmap: Real-Time User Review Classification

## 1. Overview

In V1, the model performed batch sentiment inference exclusively on static data stored in the database. In V2, reviews can be submitted by external users in real time via a REST API:

```
User → Interface → API (FastAPI) → Classification Service → Model (.joblib)
                          │
                          └→ ReviewRepository → MongoDB (stores classified review)
```

The underlying V1 components (data repository, ML pipeline, MongoDB database, analytics aggregations) remain fully leveraged. V2 introduces two upper layers: the **REST API** and the **User Interface**.

---

## 2. Architectural Decisions Summary

| Decision | Rationale |
|---|---|
| **FastAPI + Uvicorn** | High-performance Python ASGI framework with automatic type validation and interactive OpenAPI docs at `/docs`. |
| **Model loaded once at application startup** | Deserializing the binary `.joblib` model on every HTTP request would introduce prohibitive latency. |
| **Synchronous route handlers (`def`, not `async def`)** | `pymongo` and `scikit-learn` are synchronous and blocking. Using standard `def` offloads execution to an AnyIO worker threadpool, preserving event loop responsiveness. |
| **Decoupled Service Layer (`services/classificador.py`)** | Centralizes ML inference into a reusable service consumed by both batch jobs (`predict.py`) and API controllers without logic duplication. |
| **Dependency Injection (`Depends`)** | Decouples lifecycle management for repositories and services, enabling seamless unit and integration testing via in-memory mocks. |
| **Pydantic Schemas for DTOs** | Establishes strict data contracts, field validation, and documentation for both request payloads and responses. |
| **Decoupled HTTP Interface** | The frontend communicates strictly via standard REST HTTP endpoints, with no direct access to the database or ML model. |

**Key Design Patterns:** *Repository Pattern*, *Service Layer*, *Data Transfer Object (DTO)*, and *Dependency Injection*.

---

## 3. REST API Contracts

| Method & Route | Description | Expected Status |
|---|---|---|
| `POST /avaliacoes` | Receives review text, runs ML inference, persists to MongoDB, and returns result | `201 Created` |
| `GET /avaliacoes/{id}` | Fetches a single review by its hexadecimal MongoDB ObjectId | `200 OK` or `404 Not Found` |
| `GET /avaliacoes?limite=10` | Lists recent reviews ordered by creation date descending | `200 OK` (list) |
| `GET /saude` | System healthcheck validating API, database connectivity, and ML model | `200 OK` or `503 Service Unavailable` |

### Payload Examples

**Request (`POST /avaliacoes`):**
```json
{
  "texto": "Chegou rápido, mas a embalagem veio amassada",
  "produto": "Fone Bluetooth X"
}
```

**Response (`201 Created`):**
```json
{
  "id": "6720c1f2e4b0a1d2c3e4f5a6",
  "texto": "Chegou rápido, mas a embalagem veio amassada",
  "produto": "Fone Bluetooth X",
  "classe": "negativo",
  "confianca": 0.71,
  "modelo": "modelo_v1",
  "data": "2026-10-26T14:05:00Z"
}
```

* The `produto` field is optional.
* Review texts shorter than 3 characters or longer than 2000 characters return `422 Unprocessable Entity`.

### MongoDB Document Schema for API Submissions

```json
{
  "texto": "Chegou rápido, mas a embalagem veio amassada",
  "produto": "Fone Bluetooth X",
  "data": "2026-10-26T14:05:00Z",
  "nota": null,
  "rotulo": null,
  "rotulo_real": null,
  "predicao": {
    "classe": "negativo",
    "confianca": 0.71,
    "modelo": "modelo_v1",
    "data": "2026-10-26T14:05:00Z"
  },
  "origem": "api"
}
```

> **Data Integrity:** Because `rotulo` and `rotulo_real` are set to `null`, API submissions are **never included in model retraining**. Furthermore, the `taxa_acerto` aggregation pipeline explicitly filters `rotulo_real: {"$ne": null}` so that API data does not distort model evaluation accuracy.

---

## 4. Directory Structure (V2 Additions)

```text
src/
├─ (V1 core pipeline files)
├─ services/
│  └─ classificador.py     # Service: loads model and runs text inference
├─ api/
│  ├─ main.py              # FastAPI app, lifecycle, and route handlers
│  ├─ schemas.py           # Pydantic schemas (input/output validation)
│  └─ dependencies.py      # Dependency injection providers (Depends)
├─ interface/
│  ├─ app.py               # Real-time review classification UI (Streamlit)
│  └─ dashboard.py         # Analytical business dashboard (Streamlit)
tests/
├─ (V1 pipeline tests)
├─ test_classificador.py   # Unit tests for the inference service layer
├─ test_api.py             # Integration tests for API endpoints (with TestClient)
└─ test_interface.py       # Unit tests for Streamlit HTTP client utilities
```

---

## 5. Implementation Phases

### Phase 1: RESTful API
* **Step 1: Planning and Contract Definition**
  * Finalize endpoints, schemas, and validation rules.
  * Create `v2` development branch.
* **Step 2: Project Preparation**
  * Install dependencies (`fastapi`, `uvicorn[standard]`, `httpx`).
  * Extend `ReviewRepository`: `inserir_avaliacao()`, `buscar_por_id()`, `listar_recentes()`, `ping()`, and index on `data`.
  * Adjust `taxa_acerto` pipeline to filter `rotulo_real: {"$ne": null}`.
* **Step 3: Classification Service Layer (`services/classificador.py`)**
  * Create decoupled `Classificador` class.
  * Refactor `predict.py` to use the shared classification service.
* **Step 4: API Endpoints**
  * Implement `schemas.py`, `main.py`, and `dependencies.py`.
  * Handle HTTP errors (`422`, `404`, `503`).
* **Step 5: Automated API Testing**
  * Test suite using `TestClient` with in-memory fake repository.
  * Validate 100% database isolation without requiring MongoDB.

### Phase 2: User Interface
* **Step 6: Submission and Real-Time Results UI**
  * Interactive form with text input and optional product field.
  * Visual feedback: sentiment badge and confidence progress bar.
* **Step 7: User Experience (UX) and Live Activity Feed**
  * Recent review listing via `GET /avaliacoes?limite=10`.
  * Low confidence alerts (< 60%) and API error handling.
* **Step 8: Documentation and V2 Release**
  * Update READMEs with `curl` examples and interactive documentation links.
  * Create GNU `Makefile` for developer workflow orchestration.
  * Tag release `v2.0`.

### Phase 3: Codebase Internationalization 
* **Step 9: Backend and Database Translation to English**
  * Translate all docs.
  * Translate `ReviewRepository` methods (`insert_review`, `find_by_id`, `list_recent`, `accuracy_rate`).
  * Translate Pydantic schemas (`ReviewInput`, `ReviewOutput`, `HealthOutput`) and API routes (`/reviews`, `/health`).
  * Rename `Classificador` to `ClassifierService` (`classify_text`, `classify_documents`).
* **Step 10: Test Suite and Pipeline Refactoring**
  * Translate test functions and assertions in `tests/` while preserving 100% test coverage.
  * Update data scripts (`prepare_data.py`, `ingest.py`, `train.py`) and `run_pipeline.py`.
  * Preserve B2W Portuguese dataset as an authentic NLP use case.

---