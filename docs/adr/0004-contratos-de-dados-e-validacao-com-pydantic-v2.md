# ADR 0004: Contratos de Dados e Validação Estrita com Pydantic V2

* **Status:** Aceito
* **Data:** 2026-10-27
* **Contexto:** Versão 2 (API RESTful)

---

## 1. Contexto e Problema

Ao expor a API para usuários externos, o sistema precisa:
1. Rejeitar payloads maliciosos, textos em branco ou dados fora dos limites aceitos antes que atinjam a camada de serviço ou persistência.
2. Definir contratos de dados (*Data Transfer Objects* - DTOs) explícitos para requisição e resposta.
3. Garantir que a documentação de schema (OpenAPI) reflita fielmente as regras de negócio:
   * Texto da avaliação obrigatório: entre 3 e 2000 caracteres.
   * Produto opcional: até 200 caracteres.
   * Resposta padronizada com ID, classe inferida, confiança (0.0 a 1.0), versão do modelo e timestamp UTC.

---

## 2. Decisão

1. **Centralizar os schemas em `src/api/schemas.py` utilizando Pydantic V2:**
   * `AvaliacaoEntrada`: Modelo de entrada com restrições semânticas via `Field(min_length=3, max_length=2000)`.
   * `AvaliacaoSaida`: Modelo de resposta consolidada incluindo inferência e metadados.
   * `SaudeSaida`: Modelo de healthcheck para status do banco e do modelo.
2. **Sanitização com `@field_validator`:**
   * Utilizar `@field_validator("texto")` para aplicar `.strip()` e impedir avaliações compostas exclusivamente por espaços em branco, lançando `ValueError` que o FastAPI converte em HTTP `422 Unprocessable Entity`.
3. **Manter em arquivo único (`schemas.py`):**
   * Pela coesão e volume enxuto (3 DTOs), evitar pulverização de arquivos em subpastas.

---

## 3. Alternativas Consideradas

* **Dataclasses nativas do Python (`@dataclass`):**
  * *Prós:* Sem dependências de bibliotecas externas.
  * *Contras:* Não realiza validação em tempo de execução (*runtime*), não gera esquemas JSON Schema para o OpenAPI e não sanitiza dados automaticamente.
* **Marshmallow / Cerberus:**
  * *Prós:* Bibliotecas tradicionais de validação em Python.
  * *Contras:* Desempenho muito inferior ao núcleo em Rust do Pydantic V2 (`pydantic-core`) e integração não nativa com o FastAPI.

---

## 4. Consequências e Trade-offs

* **Positivas:**
  * Validação instantânea em runtime antes de qualquer processamento de negócio.
  * Respostas de erro padronizadas pelo FastAPI com detalhes exatos do campo inválido (`422 Unprocessable Entity`).
  * Contratos documentados com exemplos nos esquemas Swagger/OpenAPI interativos.
* **Negativas / Riscos Mitigados:**
  * Necessidade de seguir a sintaxe do Pydantic V2 (`@field_validator` e `@classmethod`, `.model_dump()`), evitando métodos descontinuados da V1 (`.dict()`, `@validator`).
