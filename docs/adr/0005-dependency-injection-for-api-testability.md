# ADR 0005: Dependency Injection (`Depends`) for Test Isolation

* **Status:** Accepted
* **Date:** 2026-10-26
* **Context:** Version 2 (Testing & Maintainability)

---

## 1. Context and Problem Statement

A fundamental architectural constraint of this repository is that **automated tests must never depend on an active MongoDB instance or external network connectivity**.

If route handlers directly instantiated `ReviewRepository()` or `Classificador()` inside endpoint functions, unit and integration tests with `TestClient` would attempt to establish live network connections to `localhost:27017`, causing tests to fail in environments without running Docker containers (such as lightweight CI/CD runners).

---

## 2. Decision

Utilize FastAPI's native **Dependency Injection (`Depends`)** mechanism across all API route handlers:

1. **Provider Functions in `src/api/dependencies.py`:**
   * `get_repositorio() -> Generator[ReviewRepository, None, None]`: Context manager yielding a live `ReviewRepository` instance and ensuring proper connection closure.
   * `get_classificador() -> Classificador`: Singleton provider cached via `@lru_cache(maxsize=1)` to ensure the ML model artifact is loaded exactly once into memory.
2. **Endpoint Inversion of Control:**
   * Handlers receive instances exclusively through parameters:
     ```python
     def criar_avaliacao(
         payload: AvaliacaoEntrada,
         repo: ReviewRepository = Depends(get_repositorio),
         classificador: Classificador = Depends(get_classificador),
     ):
     ```
3. **In-Memory Testing with `app.dependency_overrides`:**
   * Pytest fixtures override providers with lightweight fake implementations (`FakeReviewRepository` and `FakeClassificador`), testing routes with 100% database isolation in RAM.

---

## 3. Considered Alternatives

* **Monkeypatching (`unittest.mock.patch`):**
  * *Pros:* Standard Python approach.
  * *Cons:* Brittle; tightly coupled to import paths and prone to silent failures when internal filenames or package imports change.
* **Global Singleton Instances:**
  * *Pros:* Easy to implement.
  * *Cons:* Causes state leakage between concurrent test executions and makes mocking difficult and error-prone.

---

## 4. Consequences and Trade-offs

* **Positive:**
  * 100% test isolation: tests run in ~1.5 seconds with zero external network or database dependencies.
  * Deterministic test scenarios: allows simulating database failures or model errors cleanly by injecting test doubles configured to fail, verifying HTTP 503 error handling.
* **Negative / Mitigated Risks:**
  * Slight learning curve for developers unfamiliar with FastAPI's `Depends` dependency graph.
