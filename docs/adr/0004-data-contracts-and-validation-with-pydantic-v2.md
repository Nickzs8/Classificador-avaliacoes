# ADR 0004: Strict Data Contracts and Validation with Pydantic V2

* **Status:** Accepted
* **Date:** 2026-10-27
* **Context:** Version 2 (API Contracts & Schemas)

---

## 1. Context and Problem Statement

Allowing arbitrary or malformed user input to reach the Machine Learning model or the database poses significant operational risks:
1. Empty strings, single-letter characters, or excessive inputs (> 100k characters) waste compute resources and may generate nonsensical vectorization results.
2. Inconsistent return payloads across different endpoints make frontend and third-party integration error-prone.
3. MongoDB's schemaless flexibility requires defensive data validation at the application boundary to maintain long-term document integrity.

---

## 2. Decision

Adopt **Pydantic V2** to define strict, type-safe Data Transfer Objects (DTOs) in `src/api/schemas.py`:

1. **`AvaliacaoEntrada` (Input DTO):**
   * Field `texto`: `str = Field(..., min_length=3, max_length=2000)`.
   * Field `produto`: `Optional[str] = Field(None, max_length=200)`.
   * Custom `@field_validator("texto")`: strips leading and trailing whitespace automatically and ensures the resulting text contains at least 3 non-whitespace characters, rejecting pure whitespace payloads with HTTP `422 Unprocessable Entity`.
2. **`AvaliacaoSaida` (Output DTO):**
   * Strict response structure containing `id` (hex string), `texto`, `produto`, `classe`, `confianca` (rounded to 3 decimal places), `modelo`, and UTC `data`.
3. **`SaudeSaida` (Healthcheck DTO):**
   * Standardized health payload containing `status`, `banco`, and `modelo`.

---

## 3. Considered Alternatives

* **Manual validation with Python dictionaries:**
  * *Pros:* Zero external dependencies.
  * *Cons:* Verbose, repetitive, lacks automatic Swagger schema generation, and easily allows subtle validation bugs to slip through.
* **Cerberus / Marshmallow:**
  * *Pros:* Mature Python validation frameworks.
  * *Cons:* Slower execution compared to Pydantic V2's compiled Rust core (`pydantic-core`) and lacks native, seamless integration with FastAPI.

---

## 4. Consequences and Trade-offs

* **Positive:**
  * Automatic schema enforcement and informative HTTP 422 error responses with field-level error messages.
  * Interactive OpenAPI documentation automatically displays request/response examples and constraints.
  * Clean domain separation: persistence details (e.g., MongoDB `_id` and internal `rotulo_real` audit fields) are never leaked to external API consumers.
* **Negative / Mitigated Risks:**
  * Minor memory overhead for validating input objects (negligible due to Pydantic V2's Rust implementation).
