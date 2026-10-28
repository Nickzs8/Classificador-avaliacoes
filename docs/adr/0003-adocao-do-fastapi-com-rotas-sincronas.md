# ADR 0003: Adoção do FastAPI com Rotas Síncronas (`def`)

* **Status:** Aceito
* **Data:** 2026-10-26
* **Contexto:** Versão 2 (API RESTful)

---

## 1. Contexto e Problema

Na Versão 2, o sistema precisa disponibilizar endpoints HTTP para classificação de avaliações enviadas por usuários em tempo real. O ecossistema Python moderno oferece frameworks assíncronos (como FastAPI) que operam sobre um loop de eventos (*event loop*).

No entanto, as bibliotecas centrais do projeto:
* `pymongo` (driver de banco de dados)
* `scikit-learn` / `numpy` (inferência matemática do modelo)

são estritamente **síncronas e bloqueantes**. Se executadas diretamente dentro de uma corrotina `async def`, elas bloqueiam a thread principal do event loop, travando todas as requisições concorrentes da API.

---

## 2. Decisão

1. **Adotar o FastAPI com servidor Uvicorn:**
   * Validação automática por tipagem via Pydantic.
   * Documentação OpenAPI / Swagger interativa gerada automaticamente em `/docs`.
2. **Declarar todas as rotas com `def` padrão (síncronas), nunca com `async def`:**
   * Ao declarar funções de rota com `def`, o FastAPI automaticamente as encaminha para execução em um pool de threads secundárias (*external threadpool* via AnyIO).
   * O loop de eventos principal permanece livre para receber novas conexões e gerenciar I/O de rede.

---

## 3. Alternativas Consideradas

* **Migrar para `motor` (driver assíncrono do MongoDB):**
  * *Prós:* I/O nativo não bloqueante no MongoDB.
  * *Contras:* O `scikit-learn` continuaria bloqueante na etapa de inferência. Além disso, quebraria a compatibilidade e reuso direto da classe `ReviewRepository` construída na V1.
* **Flask:**
  * *Prós:* Modelo puramente síncrono por padrão.
  * *Contras:* Não possui suporte nativo a validação por Pydantic nem geração automática de OpenAPI/Swagger sem plugins legados (ex.: Flask-RESTX).

---

## 4. Consequências e Trade-offs

* **Positivas:**
  * Reaproveitamento de 100% do código da V1 (`ReviewRepository` e `Classificador`) sem reescrita assíncrona.
  * Proteção do event loop contra travamentos por operações intensivas de CPU e chamadas bloqueantes de rede.
  * Alta capacidade de requisições concorrentes gerenciada pelo pool de threads do FastAPI.
* **Negativas / Riscos Mitigados:**
  * Limite superior de concorrência atrelado ao tamanho do threadpool padrão (ajustável via configurações do AnyIO/Starlette caso a demanda cresça).
