# ADR 0001: Armazenamento Analítico e Repository Pattern com MongoDB

* **Status:** Aceito
* **Data:** 2026-10-21
* **Contexto:** Versão 1 (Fundação e Ingestão)

---

## 1. Contexto e Problema

O sistema necessita armazenar avaliações de e-commerce semiestruturadas com campos opcionais (`produto`), metadados de inferência dinâmicos (`predicao.classe`, `predicao.confianca`, `predicao.modelo`) e permitir análises agregadas eficientes (taxa de acerto global, distribuição de sentimentos por produto e volume de predições).

Além disso, o acesso ao banco de dados não pode ficar disperso pelo código-fonte, sob risco de acoplamento com o driver e dificuldade de mock em suítes de testes automatizados.

---

## 2. Decisão

1. **Adotar o MongoDB 8.2 (executado via Docker Compose):**
   * Esquema flexível em BSON para comportar atributos variáveis e subdocumentos aninhados de predição.
   * Suporte nativo ao Aggregation Framework para computação de métricas analíticas no próprio banco.
2. **Aplicar o Repository Pattern Estrito (`src/repository.py`):**
   * Toda e qualquer operação de consulta, inserção, índice ou agregação BSON deve residir exclusivamente na classe `ReviewRepository`.
   * Nenhum outro módulo da aplicação tem permissão para importar `pymongo` ou `MongoClient`.

---

## 3. Alternativas Consideradas

* **PostgreSQL / MySQL (Relacional):**
  * *Prós:* Rígido em integridade referencial e conformidade ACID.
  * *Contras:* Exigiria migrações frequentes de schema (*Alembic*) para armazenar metadados experimentais de predições ou colunas do tipo JSONB sem tipagem estrita nativa.
* **SQLite:**
  * *Prós:* Arquivo local sem dependência de serviço externo.
  * *Contras:* Concorrência limitada para escrita em lote e ausência de um framework avançado de agregações analíticas em memória.

---

## 4. Consequências e Trade-offs

* **Positivas:**
  * Centralização total das regras de banco: otimizações de índices e consultas não vazam para camadas de serviço ou API.
  * Facilidade de teste: serviços e endpoints podem substituir `ReviewRepository` por implementações em memória (*mocks*).
  * Pipelines de agregação do MongoDB calculam métricas analíticas em alta velocidade sem sobrecarregar o Python.
* **Negativas / Riscos Mitigados:**
  * Dependência do serviço do MongoDB ativo para execução real (mitigado pelo isolamento total nos testes unitários e uso do Docker Compose padronizado).
