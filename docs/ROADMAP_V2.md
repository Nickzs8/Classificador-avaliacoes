# Roadmap da V2: Classificar Avaliações Enviadas pelo Usuário

## 1. Visão Geral

Na V1, o modelo classificava dados estáticos já persistidos no banco de dados. Na V2, as avaliações chegam do usuário externo em tempo real:

```
Usuário → Interface → API (FastAPI) → Serviço de classificação → modelo (.joblib)
                          │
                          └→ ReviewRepository → MongoDB (salva a avaliação já classificada)
```

Todo o ecossistema construído na V1 (repositório, modelo, banco de dados, análises) é reaproveitado. A V2 acrescenta duas camadas superiores: a **API REST** e a **Interface de Usuário**.

---

## 2. Registro de Decisões de Arquitetura (ADR)

| Decisão | Motivo |
|---|---|
| **FastAPI + Uvicorn** | Ecossistema nativo Python, validação automática por tipagem e documentação interativa OpenAPI em `/docs` sem esforço. |
| **Modelo carregado uma vez, na inicialização** | Carregar o arquivo binário `.joblib` a cada requisição causaria latência inaceitável. |
| **Rotas síncronas (`def`, não `async def`)** | Os drivers `pymongo` e `scikit-learn` são bloqueantes. Com `def`, o FastAPI delega a execução para uma thread separada do pool, impedindo o bloqueio do event loop. |
| **Lógica de predição desacoplada (`classificador.py`)** | Centraliza a inferência em uma camada de serviço (*Service Layer*), permitindo que tanto o batch da V1 (`predict.py`) quanto a API utilizem o mesmo código sem duplicação. |
| **Injeção de dependência (`Depends`)** | Desacopla o ciclo de vida do repositório e do classificador, viabilizando testes unitários e de integração com mocks sem dependência do MongoDB ativo. |
| **Schemas Pydantic na entrada e na saída (DTOs)** | Estabelece contratos de dados rígidos com validação de payload e documentação explícita. |
| **Interface desacoplada via HTTP** | A interface comunica-se estritamente através da API REST, sem acesso direto ao banco ou ao modelo de ML. |

**Padrões de projeto aplicados:** *Repository Pattern*, *Service Layer* (`classificador.py`), *Data Transfer Object / Schema* (Pydantic) e *Dependency Injection* (`Depends`).

---

## 3. Contrato da API

| Método e Rota | Descrição | Resposta Esperada |
|---|---|---|
| `POST /avaliacoes` | Recebe o texto, classifica via ML, persiste no banco e retorna o resultado consolidado | `201 Created` |
| `GET /avaliacoes/{id}` | Busca uma avaliação específica pelo ID | `200 OK` ou `404 Not Found` |
| `GET /avaliacoes?limite=10` | Lista as últimas avaliações cadastradas em ordem cronológica | `200 OK` (lista) |
| `GET /saude` | Healthcheck de conectividade da API, modelo e banco | `200 OK` ou `503 Service Unavailable` |

### Exemplos de Payload

**Requisição (`POST /avaliacoes`):**
```json
{
  "texto": "Chegou rápido, mas a embalagem veio amassada",
  "produto": "Fone Bluetooth X"
}
```

**Resposta (`201 Created`):**
```json
{
  "id": "6720c1f2e4b0a1d2c3e4f5a6",
  "texto": "Chegou rápido, mas a embalagem veio amassada",
  "produto": "Fone Bluetooth X",
  "classe": "negativo",
  "confianca": 0.71,
  "modelo": "modelo_v1",
  "data": "2026-10-26T14:05:00Z"
}
```

* O campo `produto` é opcional.
* Textos vazios ou menores que 3 caracteres, assim como maiores que 2000 caracteres, devolvem erro `422 Unprocessable Entity`.

### Estrutura do Documento no MongoDB

```json
{
  "texto": "Chegou rápido, mas a embalagem veio amassada",
  "produto": "Fone Bluetooth X",
  "data": "2026-10-26T14:05:00Z",
  "nota": null,
  "rotulo": null,
  "rotulo_real": null,
  "predicao": {
    "classe": "negativo",
    "confianca": 0.71,
    "modelo": "modelo_v1",
    "data": "2026-10-26T14:05:00Z"
  },
  "origem": "api"
}
```

> **Atenção:** Como `rotulo` e `rotulo_real` são gravados como `null`, essas avaliações **nunca entram no retreino**. Para evitar distorções na métrica de `taxa_acerto` (que compara com `rotulo_real`), o pipeline de agregação ignora registros com `rotulo_real: null`.

---

## 4. Estrutura de Pastas (Novidades da V2)

```
src/
├─ (arquivos da V1)
├─ classificador.py        # Serviço: carrega o modelo e classifica textos
├─ api/
│  ├─ main.py              # Aplicação FastAPI, ciclo de vida e rotas
│  ├─ schemas.py           # Schemas Pydantic (validação de entrada e saída)
│  └─ dependencias.py      # Provedores de injeção de dependência (Depends)
└─ interface/
   └─ app.py               # Interface gráfica de usuário
tests/
├─ (testes da V1)
├─ test_classificador.py   # Testes unitários do serviço de inferência
└─ test_api.py             # Testes de integração dos endpoints (com TestClient)
```

---

## 5. Etapas de Implementação

### Fase 1: API RESTful

* **Etapa 1: Contrato e Planejamento**
  * Fechamento de endpoints, schemas e validações.
  * Criação da branch `v2` e abertura das issues no GitHub.
* **Etapa 2: Preparação do Projeto**
  * Instalar dependências (`fastapi`, `uvicorn[standard]`, `httpx`).
  * Atualizar `ReviewRepository`: `inserir_avaliacao()`, `buscar_por_id()`, `listar_recentes()`, `ping()` e índice em `data`.
  * Ajustar pipeline da `taxa_acerto` para ignorar `rotulo_real: null`.
* **Etapa 3: Serviço de Classificação (`classificador.py`)**
  * Criar classe `Classificador` isolada da API.
  * Refatorar `predict.py` para consumir o novo serviço compartilhado.
* **Etapa 4: Endpoints da API**
  * Implementação de `schemas.py`, `main.py` e `dependencias.py`.
  * Tratamento de erros HTTP (`422`, `404`, `503`).
* **Etapa 5: Testes Automatizados da API**
  * Suíte com `TestClient` e repositório mockado em memória.
  * Garantir execução isolada sem necessidade do MongoDB ativo.

### Fase 2: Interface de Usuário

* **Etapa 6: Interface de Envio e Resultado**
  * Formulário interativo com input de texto e produto opcional.
  * Exibição visual da classe predita e barra de confiança.
* **Etapa 7: Histórico e Experiência do Usuário (UX)**
  * Listagem das últimas avaliações via `GET /avaliacoes`.
  * Alertas de baixa confiança (< 60%) e tratamento de indisponibilidade da API.
* **Etapa 8: Documentação e Release V2**
  * Atualização dos READMEs com exemplos de `curl` e documentação interativa.
  * Merge na branch principal e criação da tag `v2.0`.

---

## 6. Fora do Escopo (Ideias para V3)

- Feedback loop de correção de rótulo pelo usuário com retreino automático.
- Autenticação JWT e rate limiting por IP/API key.
- Deploy em nuvem (Render / AWS / GCP).
- Classificação em lote via upload de arquivos CSV/Excel.
