# ADR 0003: FastAPI Adoption with Synchronous Route Handlers (`def`)

* **Status:** Accepted
* **Date:** 2026-10-26
* **Context:** Version 2 (REST API & Concurrency)

---

## 1. Context and Problem Statement

The system requires exposing the classification pipeline over HTTP so that external clients and web interfaces can submit customer reviews in real time.

However, the primary backend dependencies (`pymongo` for MongoDB access, and `scikit-learn` / `joblib` for vectorized inference) perform synchronous, CPU-bound or socket-blocking operations without native `asyncio` support. Declaring `async def` routes around blocking code would freeze the ASGI event loop, severely degrading concurrent request throughput.

---

## 2. Decision

1. **Adopt FastAPI as the REST Framework:**
   * High performance, automatic OpenAPI / Swagger generation, and native integration with Pydantic for request/response serialization.
2. **Declare Route Handlers with Standard Synchronous `def`:**
   * Handlers that invoke `ReviewRepository` or `Classificador` must use `def`, **never `async def`**.
   * FastAPI automatically offloads synchronous `def` routes to an external threadpool (via AnyIO), allowing the main event loop to remain fully responsive for incoming connections and concurrent I/O.

---

## 3. Considered Alternatives

* **Async Drivers (`motor` for MongoDB):**
  * *Pros:* Native coroutines and async I/O.
  * *Cons:* Scikit-Learn inference remains inherently CPU-blocking. Introducing `motor` would duplicate repository methods without fully solving the blocking nature of ML computation.
* **Flask:**
  * *Pros:* Simple, mature, and synchronous by default.
  * *Cons:* Lacks native OpenAPI/Swagger documentation, requires manual integration with validation libraries like marshmallow, and lacks modern dependency injection mechanisms.

---

## 4. Consequences and Trade-offs

* **Positive:**
  * Non-blocking concurrency: blocking PyMongo calls and ML inference execute on worker threads without starving the main event loop.
  * Code simplicity: the repository remains identical and shared between batch CLI scripts and API routes without code duplication or dual async/sync implementations.
  * Automatic OpenAPI documentation at `/docs` and `/redoc`.
* **Negative / Mitigated Risks:**
  * Worker threadpool has a finite concurrency cap (defaulting to AnyIO thread limits), which is well-suited for moderate throughput and can be horizontally scaled via multiple Uvicorn worker processes in production.
