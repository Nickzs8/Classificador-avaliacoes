# Review Classifier with MongoDB & FastAPI

<p align="center">
  <b>English</b> | <a href="README.pt-br.md">Português</a>
</p>

<p align="center">
  <img src="https://img.shields.io/badge/Python-3.11+-blue.svg" alt="Python 3.11+">
  <img src="https://img.shields.io/badge/FastAPI-0.162.0-009688.svg?logo=fastapi&logoColor=white" alt="FastAPI">
  <img src="https://img.shields.io/badge/MongoDB-8.2-green.svg" alt="MongoDB 8.2">
  <img src="https://img.shields.io/badge/Docker-compose-2496ED.svg?logo=docker&logoColor=white" alt="Docker">
  <img src="https://img.shields.io/badge/Tests-39%20passed-brightgreen.svg" alt="Pytest">
  <img src="https://img.shields.io/badge/Streamlit-1.35+-FF4B4B.svg?logo=streamlit&logoColor=white" alt="Streamlit">
  <img src="https://img.shields.io/badge/License-MIT-yellow.svg" alt="License: MIT">
</p>

Production-ready Machine Learning system that classifies Portuguese product reviews as **positive** or **negative**, featuring:
* **Batch Analytics Pipeline:** Cleans, labels, and loads over 20,000 documents into **MongoDB 8.2**, with automated Scikit-Learn model training and aggregation pipelines.
* **Real-Time REST API:** Powered by **FastAPI** with synchronous threadpool routes, Pydantic V2 DTO validation, and OpenAPI documentation.
* **Interactive Web Presentation:** Built with **Streamlit** for real-time customer review inference and business intelligence analytics.
* **Developer Ergonomics:** Managed via native **GNU Makefile** (`make dev`, `make api`, `make ui`, `make test`).

---

## Web Interfaces (Streamlit)

The system provides two distinct web presentation layers:
1. **Real-Time Inference Interface (`src/interface/app.py`):** Allows end users to type a product review and receive real-time sentiment prediction, confidence metrics, and database persistence.
2. **Analytical BI Dashboard (`src/interface/dashboard.py`):** Aggregates business KPIs, ranks products with highest negative feedback, tracks temporal sentiment distribution, and lists recent reviews.

---

## Tech Stack

| Layer | Tool | Purpose |
|---|---|---|
| **Language** | Python 3.11+ | Core services, data pipelines, and APIs |
| **REST API** | FastAPI & Uvicorn | High-performance ASGI REST API with auto-generated OpenAPI docs |
| **Data Contracts** | Pydantic V2 | Input sanitization, strict schema validation, and serialization |
| **Database** | MongoDB 8.2 (Docker) | Flexible document store and analytical aggregation pipelines |
| **Database Driver** | PyMongo | Native connection driver and bulk operations (Repository Pattern) |
| **Machine Learning** | Scikit-Learn & Joblib | TF-IDF vectorization, Logistic Regression, and model serialization |
| **Data Processing** | Pandas | Data sanitization, sampling, and reshaping (`pivot`) |
| **HTTP Client** | HTTPX | Resilient synchronous client connecting Streamlit to FastAPI |
| **Web Presentation** | Streamlit | Real-time sentiment tester and analytical business dashboard |
| **Testing** | Pytest | 39 automated tests with in-memory mocks (`TestClient`, zero DB dependency) |
| **Developer Tooling** | GNU Make & Docker | Single-command workflow orchestration (`Makefile`, `docker-compose.yml`) |

---

## System Architecture

Layered architecture enforcing the **Repository Pattern**, **Service Layer**, and **Dependency Injection**, ensuring zero coupling between HTTP controllers, ML models, and persistence:

```
┌────────────────────────────────────────────────────────┐
│             Presentation Layer (Streamlit)             │
│   src/interface/app.py    │   src/interface/dashboard.py │
└───────────────────────┬──────────────────────┬─────────┘
                        │ (HTTP / httpx)       │ (Internal)
┌───────────────────────▼────────────────┐     │
│         REST API Layer (FastAPI)       │     │
│   POST /avaliacoes  │  GET /avaliacoes │     │
└───────────────────────┬────────────────┘     │
                        ▼                      │
┌────────────────────────────────────────┐     │
│     Service Layer (Classificador)      │     │
│       Shared ML Inference Logic        │     │
└───────────────────────┬────────────────┘     │
                        ▼                      ▼
┌────────────────────────────────────────────────────────┐
│     Repository Layer (src/repository.py - PyMongo)     │
└───────────────────────────────┬────────────────────────┘
                                ▼
┌────────────────────────────────────────────────────────┐
│               MongoDB 8.2 (Docker Container)           │
└────────────────────────────────────────────────────────┘
```

> For deep architectural specifications, data flows, and design patterns, refer to **[docs/ARCHITECTURE.md](docs/ARCHITECTURE.md)** and **[docs/adr/](docs/adr/)**.

---

## Project Structure

```text
classificador-avaliacoes/
├── data/              # Raw datasets and processed sample artifacts (gitignored)
├── docs/              # Architectural Decision Records (ADRs), specs, and roadmap
├── models/            # Serialized machine learning models (.joblib, gitignored)
├── src/               # Application source code
│   ├── api/           # REST API layer (FastAPI routes, Pydantic schemas, and dependencies)
│   ├── interface/     # Web presentation layer (Streamlit customer UI and BI dashboard)
│   └── services/      # Business logic and shared ML inference service layer
└── tests/             # Automated unit and integration test suite (Pytest)
```

---

## Quickstart & Execution (Makefile)

The project includes a **GNU Makefile** providing simple, single-command workflows:

| Command | Action |
|---|---|
| **`make dev`** | **Run backend API and Streamlit UI concurrently in parallel** |
| **`make api`** | Start FastAPI backend server with auto-reload (`http://localhost:8000`) |
| **`make ui`** | Start Streamlit customer review UI (`http://localhost:8501`) |
| **`make dashboard`** | Start Streamlit analytical metrics dashboard |
| **`make test`** | Run complete automated test suite (39 tests in ~1.5s) |
| **`make up`** | Start MongoDB container in background |
| **`make down`** | Stop MongoDB container |
| **`make pipeline`** | Run data pipeline (prepare -> ingest -> train) |
| **`make help`** | Display all available commands |

> [!NOTE]
> **Windows Compatibility:** `make` is native to Linux and macOS. On native Windows environments (PowerShell / Command Prompt), the `make` utility is not available by default. Windows developers can:
> 1. Use **WSL (Windows Subsystem for Linux)** or **Git Bash**.
> 2. Install GNU Make via a package manager like **Chocolatey** (`choco install make`) or **Winget**.
> 3. Or run the underlying Python commands directly:
>    * API: `uvicorn api.main:app --reload --app-dir src`
>    * Interface: `streamlit run src/interface/app.py`
>    * Dashboard: `streamlit run src/interface/dashboard.py`
>    * Tests: `pytest -v`

---

## REST API Documentation (FastAPI)

When the API is running (`make api` or `make dev`), access the interactive OpenAPI documentation:
* **Interactive Swagger UI:** [http://localhost:8000/docs](http://localhost:8000/docs)
* **ReDoc Documentation:** [http://localhost:8000/redoc](http://localhost:8000/redoc)

### API Endpoints Overview

| Method | Endpoint | Description | Status Code |
|---|---|---|---|
| `POST` | `/avaliacoes` | Submit review, classify sentiment in real-time, and store in MongoDB | `201 Created` |
| `GET` | `/avaliacoes/{id}` | Retrieve review by hexadecimal MongoDB ObjectId | `200 OK` / `404 Not Found` |
| `GET` | `/avaliacoes?limite=10` | List recent reviews sorted by creation date descending | `200 OK` |
| `GET` | `/saude` | Healthcheck validating API, database connectivity, and ML model | `200 OK` / `503 Unavailable` |

### Practical `curl` Examples

#### 1. Submit a Customer Review (`POST /avaliacoes`)

```bash
curl -X POST "http://localhost:8000/avaliacoes" \
  -H "Content-Type: application/json" \
  -d '{
    "texto": "Entrega super rápida e o fone tem um som excelente! Recomendo muito.",
    "produto": "Fone Bluetooth Pro"
  }'
```

**Response (`201 Created`):**
```json
{
  "id": "6720d2a1e4b0a1d2c3e4f5b2",
  "texto": "Entrega super rápida e o fone tem um som excelente! Recomendo muito.",
  "produto": "Fone Bluetooth Pro",
  "classe": "positivo",
  "confianca": 0.965,
  "modelo": "modelo_v1",
  "data": "2026-10-27T20:30:00Z"
}
```

* Validation: Text must be between 3 and 2000 characters (returns `422 Unprocessable Entity` otherwise).
* Stored with `origem: "api"`, `nota: null`, and `rotulo_real: null` (ensuring API inputs never contaminate model retraining or evaluation accuracy metrics).

#### 2. Retrieve Review by ID (`GET /avaliacoes/{id}`)

```bash
curl -X GET "http://localhost:8000/avaliacoes/6720d2a1e4b0a1d2c3e4f5b2"
```

#### 3. List Recent Reviews (`GET /avaliacoes?limite=5`)

```bash
curl -X GET "http://localhost:8000/avaliacoes?limite=5"
```

#### 4. System Healthcheck (`GET /saude`)

```bash
curl -X GET "http://localhost:8000/saude"
```

**Response (`200 OK`):**
```json
{
  "status": "ok",
  "banco": "conectado",
  "modelo": "carregado"
}
```

---

## Automated Tests

The test suite enforces full test isolation: **no test requires a running MongoDB database or network access**. External dependencies are substituted with in-memory test doubles (`FakeReviewRepository` and `FakeClassificador`) via FastAPI's `app.dependency_overrides`.

```bash
make test
# or:
pytest -v
```

Output:
```text
============================== 39 passed in 1.45s ==============================
```

---

## Architectural Decision Records (ADRs)

All foundational architectural decisions, technology selections, and trade-offs are documented in Markdown following the MADR (*Markdown Any Decision Records*) framework.

For the complete decision catalog, status, and architectural context, refer to the **[Architecture Decision Records Index](docs/adr/README.md)**.

---

## License

Distributed under the MIT License. See [LICENSE](LICENSE) for more details.
The [B2W-Reviews01](https://github.com/b2wdigital/b2w-reviews01) dataset follows its original repository license.
