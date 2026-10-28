# ADR 0006: Training Pipeline Orchestration via `run_pipeline.py`

* **Status:** Accepted
* **Date:** 2026-10-27
* **Context:** Version 1 (Tooling & Operation)

---

## 1. Context and Problem Statement

The end-to-end Machine Learning data preparation and model training workflow requires three sequential, interdependent steps:
1. `src/prepare_data.py` (Raw CSV cleaning, deduplication, and initial labeling).
2. `src/ingest.py` (BSON document ingestion into MongoDB).
3. `src/train.py` (TF-IDF vectorizer and Logistic Regression training, exporting `.joblib`).

Manually typing these commands in the terminal created friction, required memorizing the exact execution sequence, and produced messy error cascades if the database container was not running.

---

## 2. Decision

1. **Implement a Central Python Orchestrator (`run_pipeline.py`):**
   * Uses `sys.executable` to ensure all child scripts execute within the active virtual environment (`.venv`) across Linux, macOS, and Windows.
   * Executes steps sequentially via `subprocess.run`, terminating immediately if any step returns a non-zero exit code (`returncode != 0`).
2. **Infrastructure Health Verification:**
   * Validates that the MongoDB Docker container is running via `docker compose ps` before triggering network/database operations, displaying clear remediation instructions if offline.
3. **Standardized Log Formatting:**
   * Clean terminal output using standard text markers (`[INFO]`, `[OK]`, `[AVISO]`, `[ERRO]`, `[ETAPA]`) without unrendered Unicode or emoji artifacts.

---

## 3. Considered Alternatives

* **Bash Shell Script (`scripts/run_pipeline.sh`):**
  * *Pros:* Simple and concise.
  * *Cons:* Not cross-platform (fails on Windows without WSL or Git Bash) and requires manual virtualenv activation.
* **Makefile / Taskfile alone:**
  * *Pros:* Standard in backend ecosystems.
  * *Cons:* Requires the `make` binary installed (not native on Windows) and tab-sensitive syntax.
* **Complex Data Orchestrators (Airflow / Prefect / Dagster):**
  * *Pros:* Visual DAGs and task caching.
  * *Cons:* Excessive accidental complexity and heavy overhead (*over-engineering*) for chaining 3 scripts that finish in ~5 seconds.

---

## 4. Consequences and Trade-offs

* **Positive:**
  * **One-Command Golden Path:** Any developer can train the model from scratch via `python run_pipeline.py`.
  * Cross-platform and zero external dependencies.
  * Fail-fast: prevents upstream data errors from corrupting downstream model artifacts.
* **Negative / Mitigated Risks:**
  * Does not support artifact caching based on input file hashes (acceptable given the total execution time is only ~5 seconds).
