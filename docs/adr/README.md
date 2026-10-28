# Architectural Decision Records (ADRs)

This directory contains the **Architectural Decision Records (ADRs)** for the *Review Sentiment Classifier* project, documenting structural decisions, technology choices, technical rationales, and architectural trade-offs.

Documents adhere to the MADR (*Markdown Any Decision Records*) standard format established by Michael Nygard.

---

## Decision Log Index

| ID | Title | Status | Date | Scope |
|---|---|---|---|---|
| [ADR-0001](0001-analytical-storage-and-repository-pattern-with-mongodb.md) | Analytical Storage and Repository Pattern with MongoDB | **Accepted** | 2026-10-21 | Core / Database |
| [ADR-0002](0002-classification-pipeline-with-tfidf-and-logistic-regression.md) | Classification Pipeline with TF-IDF and Logistic Regression | **Accepted** | 2026-10-22 | Core / ML |
| [ADR-0003](0003-fastapi-adoption-with-synchronous-routes.md) | FastAPI Adoption with Synchronous Route Handlers (`def`) | **Accepted** | 2026-10-26 | API / Transport |
| [ADR-0004](0004-data-contracts-and-validation-with-pydantic-v2.md) | Strict Data Contracts and Validation with Pydantic V2 | **Accepted** | 2026-10-27 | API / Contracts |
| [ADR-0005](0005-dependency-injection-for-api-testability.md) | Dependency Injection (`Depends`) for Test Isolation | **Accepted** | 2026-10-26 | Testing / API |
| [ADR-0006](0006-training-pipeline-orchestration-with-run-pipeline.md) | Training Pipeline Orchestration via `run_pipeline.py` | **Accepted** | 2026-10-27 | Tooling / Automation |
| [ADR-0007](0007-development-automation-with-makefile.md) | Development Workflow Automation with `Makefile` | **Accepted** | 2026-10-27 | Tooling / DX |

---

## Standard ADR Structure

Each document in this directory follows a structured 4-part format:
1. **Context and Problem Statement:** The technical challenge, architectural constraint, or business requirement.
2. **Decision:** The chosen design, technology, or pattern and how it is implemented.
3. **Considered Alternatives:** Other viable alternatives evaluated and the reasons for rejecting them.
4. **Consequences and Trade-offs:** Positive architectural outcomes and accepted operational costs or trade-offs.
