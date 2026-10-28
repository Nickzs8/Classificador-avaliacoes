# ADR 0007: Development Workflow Automation with `Makefile`

* **Status:** Accepted
* **Date:** 2026-10-27
* **Context:** Version 2 (Developer Experience & Tooling)

---

## 1. Context and Problem Statement

With the evolution of Version 2, local development workflows expanded to involve multiple independent services and tools:
* Provisioning the MongoDB container via Docker Compose (`docker compose up -d`).
* Starting the FastAPI backend server with hot-reload (`uvicorn api.main:app --reload --app-dir src`).
* Starting the Streamlit real-time user interface (`streamlit run src/interface/app.py`).
* Starting the Streamlit analytical BI dashboard (`streamlit run src/interface/dashboard.py`).
* Running the automated test suite with Pytest (`pytest -v`).
* Running the end-to-end batch data pipeline (`python run_pipeline.py`).

The need to memorize long commands with directory flags (`--app-dir src`) and the requirement to open multiple terminal tabs to run the backend and frontend simultaneously created operational friction and slowed down daily developer experience (DX).

---

## 2. Decision

Adopt **`Makefile` (GNU Make)** as the canonical automation and shortcut interface at the root of the repository:

1. **Automatic Virtual Environment Resolution (`.venv`):**
   * Binary targets (`python`, `pytest`, `uvicorn`, `streamlit`) prioritize executable paths inside `.venv/bin/`, with fallback to system `PATH`.
   * Developers do not need to manually run `source .venv/bin/activate` before executing make targets.

2. **Targets Declared as `.PHONY`:**
   * All commands (`help`, `up`, `down`, `test`, `api`, `ui`, `dashboard`, `dev`, `pipeline`, `status`) are registered as `.PHONY`, preventing conflicts with any physical files or folders sharing the same name.

3. **Concurrent Execution via `make dev`:**
   * Uses target dependency `dev: up` to automatically guarantee that MongoDB is running before launching applications.
   * Runs both the FastAPI backend and Streamlit frontend concurrently in parallel within a single terminal using Make's native parallel job execution (`@$(MAKE) -j 2 api ui`), cleanly propagating termination signals (`Ctrl + C`) to both child processes.

4. **Self-Documenting Default Target:**
   * Sets `.DEFAULT_GOAL := help` to display an interactive command menu when running `make` with no arguments.

---

## 3. Considered Alternatives

* **Node.js scripts via `package.json` (`npm run dev`):**
  * *Pros:* Familiar syntax for full-stack developers.
  * *Cons:* Introduces the Node.js runtime and `package.json` into a purely Python/Data/ML repository, creating unnecessary external dependencies.
* **Bash Shell Scripts (`scripts/dev.sh`):**
  * *Pros:* No new tools needed.
  * *Cons:* Fragile parallel process orchestration and unreliable cleanup of child processes upon receiving `Ctrl + C`.
* **Python Task Runners (`taskipy`, `invoke`):**
  * *Pros:* Defined in Python or TOML (`pyproject.toml`).
  * *Cons:* Requires additional dependencies in `requirements.txt` with less mature concurrent job management compared to GNU Make.

---

## 4. Consequences and Trade-offs

* **Positive:**
  * **Single-Command Developer Workflow:** Start the entire stack with a single command (`make dev`).
  * **Industry Standard on Linux / macOS:** Ubiquitous across Unix systems, Docker images, and CI/CD environments.
  * **Virtual Environment Independence:** Direct execution of pinned virtualenv binaries.
* **Negative / Mitigated Risks:**
  * Native Windows environments (PowerShell / CMD) do not include `make` by default, requiring WSL, Git Bash, or package managers like Chocolatey/Winget (clearly documented in README).
