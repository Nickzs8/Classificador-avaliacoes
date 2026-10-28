# Operational Guide for AI Agents (`AGENTS.md`)

This document defines the technical directives, architectural rules, frequent commands, and coding conventions that **any AI agent** (Antigravity, Cursor, Claude Code, Aider, etc.) must strictly adhere to when interacting with, developing, or refactoring this repository.

---

## 1. Project Overview

* **Project Name:** `review-classifier`
* **Objective:** Ingestion, sentiment classification (*positive* / *negative*) of customer product reviews, analytical storage in MongoDB, and presentation via REST API and Streamlit Dashboard.
* **Core Tech Stack:** Python 3.11+, MongoDB 8.2 (Docker), PyMongo, Pandas, Scikit-Learn, Joblib, FastAPI, Streamlit, and Pytest.
* **GitHub Repository:** `Nickzs8/review-classifier`

---

## 2. Non-Negotiable Architectural Rules

1. **Strict Repository Pattern:**
   * **Only** `src/repository.py` may import and use `pymongo` or `MongoClient`.
   * Any new query, insertion, or analytical aggregation must be implemented as a method of `ReviewRepository`.
2. **Synchronous API Route Handlers (`def`):**
   * Because `pymongo` and `scikit-learn` perform blocking synchronous operations, **never declare FastAPI route handlers with `async def`** if they invoke the repository or classifier.
   * Always use standard `def` so FastAPI executes requests in the worker threadpool, preventing event loop starvation.
3. **Shared Service Layer (`src/services/classifier.py`):**
   * NLP inference must remain centralized in the `Classifier` service in `src/services/classifier.py`. Both batch processing (`predict.py`) and the real-time API (`api/main.py`) consume this service to prevent logic duplication.
   * The `.joblib` model artifact must be loaded once into memory on startup, never per HTTP request.
4. **Dependency Injection (`Depends`):**
   * FastAPI routes must receive instances of `ReviewRepository` and `Classifier` via `Depends`. This enables automated tests to inject in-memory mocks without requiring a running database.
5. **Module Shadowing Prevention:**
   * **Never** name local scripts or modules after installed third-party libraries (e.g., `streamlit.py`, `fastapi.py`, `pytest.py`). Use descriptive names such as `dashboard.py` or `app.py`.
6. **BSON Schema Integrity & Aggregations:**
   * Every review persisted via API must contain `origin: "api"`, `rating: null`, `label: null`, and `true_label: null`.
   * The `accuracy_rate` pipeline in the repository must explicitly filter `true_label: {"$ne": null}` so API submissions are never counted as classification errors in global evaluation accuracy.

---

## 3. Total Test Suite Isolation

* **Zero Database Dependency:** The test suite in `tests/` **MUST NEVER** depend on a running MongoDB container.
* **Preprocessing & Ingestion Tests:** Use in-memory synthetic data fixtures and Pytest's built-in `tmp_path` fixture for temporary file I/O.
* **API Tests:** Use FastAPI's `TestClient` with `app.dependency_overrides` to substitute `ReviewRepository` and `Classifier` with in-memory test doubles (`FakeReviewRepository` and `FakeClassifier`).
* **Configuration:** `pytest.ini` must maintain `pythonpath = . src` and `testpaths = tests`.

---

## 4. Frequent Development Commands

```bash
# Activate virtual environment
source .venv/bin/activate

# Run complete automated test suite
pytest -v
# or via make:
make test

# Start MongoDB container
docker compose up -d
docker compose ps
# or via make:
make up

# Run complete Machine Learning pipeline (Batch)
python run_pipeline.py
# or via make:
make pipeline

# Run individual pipeline stages:
python src/prepare_data.py
python src/ingest.py
python src/train.py
python src/predict.py
python src/analytics.py

# Launch Web Presentation UI (Streamlit)
streamlit run src/interface/app.py
# or via make:
make ui

# Launch BI Analytics Dashboard (Streamlit)
streamlit run src/interface/dashboard.py
# or via make:
make dashboard

# Start REST API server (FastAPI)
uvicorn api.main:app --reload --app-dir src
# or via make:
make api

# Run API and UI concurrently in parallel
make dev
```

---

## 5. Git Conventions, Commits & Sensitive Files

* **Strictly Ignored Files (Never Commit):**
  * Environments and secrets: `.venv/`, `.env`
  * Caches: `__pycache__/`, `.pytest_cache/`
  * Datasets: `data/raw/`, `data/reviews.csv`
  * Model artifacts: `models/`, `*.joblib`
* **Conventional Commits Standard:**
  * `feat:` New features or endpoints
  * `fix:` Bug fixes
  * `test:` Adding or modifying tests
  * `docs:` Documentation updates (`README.md`, `ARCHITECTURE.md`, `ROADMAP_V2.md`)
  * `refactor:` Code refactoring without behavioral alterations
  * `chore:` Maintenance, dependencies, or `.gitignore` updates

---

## 6. Knowledge Base Integration (Obsidian / Second Brain)

The developer maintains a technical documentation vault (Obsidian Vault) connected to the development environment for continuous learning consolidation.

**Directives for AI Agents:**
* The primary agent may delegate research and note drafting to the specialized subagent **`vault-researcher`**, operating concurrently in the background.
* Whenever a new architectural pattern, framework, or best practice is introduced or refactored, verify the vault and record it.
* Adhere strictly to the vault structure and templates in `Templates/`:
  * Standardized YAML frontmatter with `tags:`
  * Internal bidirectional connections using Obsidian wikilinks (`[[Note Name]]`)
  * Explicit code syntax highlighting
  * Preservation of folder hierarchy and integration with the Waypoint plugin (`%% Begin Waypoint %%`)
