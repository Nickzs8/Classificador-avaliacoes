# ADR 0001: Analytical Storage and Repository Pattern with MongoDB

* **Status:** Accepted
* **Date:** 2026-10-21
* **Context:** Version 1 (Foundation & Ingestion)

---

## 1. Context and Problem Statement

The system requires persistent storage for semi-structured e-commerce reviews with optional attributes (`produto`), dynamic inference metadata (`predicao.classe`, `predicao.confianca`, `predicao.modelo`), and high-performance analytical aggregation capabilities (global model accuracy, dissatisfaction ranking per product, and monthly review volume).

Furthermore, database access logic must not be scattered across application scripts to avoid coupling to the driver and to enable seamless mocking in automated unit test suites.

---

## 2. Decision

1. **Adopt MongoDB 8.2 (provisioned via Docker Compose):**
   * Flexible BSON document schema to accommodate variable attributes and nested prediction subdocuments without requiring schema migrations.
   * Native MongoDB Aggregation Framework support to compute business metrics directly inside the database engine.
2. **Enforce a Strict Repository Pattern (`src/repository.py`):**
   * All query operations, insertions, index management, and BSON aggregation pipelines reside exclusively within the `ReviewRepository` class.
   * No other module in the codebase is permitted to import or instantiate `pymongo` or `MongoClient`.

---

## 3. Considered Alternatives

* **PostgreSQL / MySQL (Relational):**
  * *Pros:* Strict referential integrity and mature ACID compliance.
  * *Cons:* Requires frequent schema migration scripts (*Alembic*) when iterating on experimental ML metadata, or using unstructured JSONB columns without native typed ergonomics.
* **SQLite:**
  * *Pros:* Zero external dependencies, single file on disk.
  * *Cons:* Limited write concurrency during batch ingestion and lacks advanced in-memory analytical aggregation pipelines.

---

## 4. Consequences and Trade-offs

* **Positive:**
  * Complete centralization of persistence logic: query optimizations and index definitions do not leak into service or API layers.
  * Testability: services and route handlers can easily replace `ReviewRepository` with in-memory test doubles (*mocks*).
  * High analytical throughput: aggregation pipelines execute server-side in MongoDB, avoiding transferring thousands of raw documents to Python memory.
* **Negative / Mitigated Risks:**
  * Requires an active MongoDB daemon for local runtime (mitigated by automated container orchestration with Docker Compose and complete database isolation in unit tests).
