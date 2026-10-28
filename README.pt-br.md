# Classificador de Avaliações com MongoDB & FastAPI

<p align="center">
  <a href="README.md">English</a> | <b>Português</b>
</p>

<p align="center">
  <img src="https://img.shields.io/badge/Python-3.11+-blue.svg" alt="Python 3.11+">
  <img src="https://img.shields.io/badge/FastAPI-0.162.0-009688.svg?logo=fastapi&logoColor=white" alt="FastAPI">
  <img src="https://img.shields.io/badge/MongoDB-8.2-green.svg" alt="MongoDB 8.2">
  <img src="https://img.shields.io/badge/Docker-compose-2496ED.svg?logo=docker&logoColor=white" alt="Docker">
  <img src="https://img.shields.io/badge/Tests-39%20passed-brightgreen.svg" alt="Pytest">
  <img src="https://img.shields.io/badge/Streamlit-1.35+-FF4B4B.svg?logo=streamlit&logoColor=white" alt="Streamlit">
  <img src="https://img.shields.io/badge/License-MIT-yellow.svg" alt="Licença: MIT">
</p>

Sistema de Machine Learning pronto para produção que classifica avaliações de produtos em português como **positivas** ou **negativas**, contando com:
* **Esteira Analítica em Lote:** Higieniza, rotula e ingere mais de 20.000 documentos no **MongoDB 8.2**, com treinamento automatizado de modelo Scikit-Learn e pipelines de agregação analítica.
* **API REST em Tempo Real:** Desenvolvida com **FastAPI**, rotas síncronas em threadpool (*non-blocking event loop*), validação rigorosa de contratos com Pydantic V2 e documentação OpenAPI interativa.
* **Apresentação Web Interativa:** Construída em **Streamlit** com inferência de sentimento em tempo real para o cliente e dashboard analítico de BI.
* **Ergonomia para Desenvolvedores:** Gerenciamento unificado via **GNU Makefile** (`make dev`, `make api`, `make ui`, `make test`).

---

## Interfaces Web (Streamlit)

O projeto conta com duas camadas de apresentação visual web:
1. **Interface de Inferência em Tempo Real (`src/interface/app.py`):** Permite que usuários submetam avaliações e recebam a predição de sentimento, métrica de certeza e gravação no banco instantaneamente.
2. **Dashboard Analítico de BI (`src/interface/dashboard.py`):** Consolida KPIs de negócio, ranking de produtos com maior insatisfação, série temporal de sentimento e histórico das últimas avaliações registradas.

---

## Stack Tecnológica

| Camada | Ferramenta | Finalidade |
|---|---|---|
| **Linguagem** | Python 3.11+ | Serviços centrais, pipelines de dados e APIs |
| **API REST** | FastAPI & Uvicorn | API REST ASGI de alta performance com documentação OpenAPI interativa |
| **Contratos de Dados** | Pydantic V2 | Sanitização de entrada, validação de tipos e serialização de DTOs |
| **Banco de Dados** | MongoDB 8.2 (Docker) | Armazenamento de documentos flexíveis e pipelines analíticos |
| **Driver de Banco** | PyMongo | Driver nativo e operações em lote via Repository Pattern |
| **Machine Learning** | Scikit-Learn & Joblib | Pipeline TF-IDF, Regressão Logística e serialização de modelos |
| **Processamento de Dados** | Pandas | Limpeza, amostragem e reformatação tabular (`pivot`) |
| **Cliente HTTP** | HTTPX | Cliente síncrono resiliente integrando Streamlit ao FastAPI |
| **Apresentação Web** | Streamlit | Testador de sentimento em tempo real e dashboard analítico |
| **Testes Automatizados** | Pytest | 39 testes com mocks em memória (`TestClient`, zero dependência de banco) |
| **Automação** | GNU Make & Docker | Orquestração de comandos em 1 linha (`Makefile`, `docker-compose.yml`) |

---

## Arquitetura do Sistema

Arquitetura em camadas desacopladas aplicando **Repository Pattern**, **Service Layer** e **Injeção de Dependências**, garantindo isolamento total entre controladores HTTP, modelo de ML e persistência:

```
┌────────────────────────────────────────────────────────┐
│             Camada de Apresentação (Streamlit)         │
│   src/interface/app.py    │   src/interface/dashboard.py │
└───────────────────────┬──────────────────────┬─────────┘
                        │ (HTTP / httpx)       │ (Interno)
┌───────────────────────▼────────────────┐     │
│         Camada de API REST (FastAPI)   │     │
│   POST /avaliacoes  │  GET /avaliacoes │     │
└───────────────────────┬────────────────┘     │
                        ▼                      │
┌────────────────────────────────────────┐     │
│     Service Layer (Classificador)      │     │
│      Lógica Compartilhada de ML        │     │
└───────────────────────┬────────────────┘     │
                        ▼                      ▼
┌────────────────────────────────────────────────────────┐
│     Repository Layer (src/repository.py - PyMongo)     │
└───────────────────────────────┬────────────────────────┘
                                ▼
┌────────────────────────────────────────────────────────┐
│               MongoDB 8.2 (Contêiner Docker)           │
└────────────────────────────────────────────────────────┘
```

> Para diagramas detalhados, fluxos de dados e padrões de projeto, consulte **[docs/ARCHITECTURE.md](docs/ARCHITECTURE.md)** e os **[docs/adr/](docs/adr/)**.

---

## Estrutura do Projeto

```text
classificador-avaliacoes/
├── data/              # Datasets brutos e amostras processadas (ignorado no git)
├── docs/              # Registros de Decisões de Arquitetura (ADRs) e Roadmap do projeto
├── models/            # Modelos de Machine Learning serializados (.joblib, ignorado)
├── src/               # Código-fonte da aplicação
│   ├── api/           # Camada de API REST (endpoints FastAPI, schemas Pydantic e dependências)
│   ├── interface/     # Camada de apresentação web (UI Streamlit de classificação e dashboard de BI)
│   └── services/      # Camada de serviços e lógica compartilhada de inferência de ML
└── tests/             # Suíte de testes unitários e de integração automatizados (Pytest)
```

---

## Guia de Execução Rápida (Makefile)

O projeto conta com um **GNU Makefile** para simplificar todos os fluxos de trabalho com comandos de 1 linha:

| Comando | Ação |
|---|---|
| **`make dev`** | **Inicia a API FastAPI e a Interface Streamlit juntas em paralelo** |
| **`make api`** | Inicia o servidor backend FastAPI com auto-reload (`http://localhost:8000`) |
| **`make ui`** | Inicia a interface de classificação do cliente (`http://localhost:8501`) |
| **`make dashboard`** | Inicia o dashboard analítico de métricas |
| **`make test`** | Executa a suíte de 39 testes automatizados (~1.5s) |
| **`make up`** | Sobe o contêiner do MongoDB em segundo plano |
| **`make down`** | Para os contêineres do MongoDB |
| **`make pipeline`** | Executa a esteira de dados (preparar -> ingerir -> treinar) |
| **`make help`** | Exibe a lista completa de comandos |

> [!NOTE]
> **Compatibilidade com Windows:** O utilitário `make` é nativo de ambientes Linux e macOS. Em ambientes Windows puros (PowerShell / Prompt de Comando), o comando `make` não vem instalado por padrão. Usuários de Windows podem:
> 1. Utilizar o **WSL (Windows Subsystem for Linux)** ou o terminal do **Git Bash**.
> 2. Instalar o GNU Make via gerenciador de pacotes como **Chocolatey** (`choco install make`) ou **Winget**.
> 3. Ou executar os comandos originais do Python diretamente:
>    * API: `uvicorn api.main:app --reload --app-dir src`
>    * Interface: `streamlit run src/interface/app.py`
>    * Dashboard: `streamlit run src/interface/dashboard.py`
>    * Testes: `pytest -v`

---

## Documentação da API REST (FastAPI)

Com a API em execução (`make api` ou `make dev`), acesse a documentação OpenAPI interativa:
* **Swagger UI Interativo:** [http://localhost:8000/docs](http://localhost:8000/docs)
* **Documentação ReDoc:** [http://localhost:8000/redoc](http://localhost:8000/redoc)

### Visão Geral dos Endpoints

| Método | Endpoint | Descrição | Status Code |
|---|---|---|---|
| `POST` | `/avaliacoes` | Submete avaliação, infere sentimento em tempo real e salva no MongoDB | `201 Created` |
| `GET` | `/avaliacoes/{id}` | Busca avaliação por ObjectId hexadecimal do MongoDB | `200 OK` / `404 Not Found` |
| `GET` | `/avaliacoes?limite=10` | Lista as avaliações mais recentes em ordem decrescente de data | `200 OK` |
| `GET` | `/saude` | Healthcheck validando API, conectividade com MongoDB e modelo de ML | `200 OK` / `503 Unavailable` |

### Exemplos Práticos de Consumo com `curl`

#### 1. Submeter uma Avaliação (`POST /avaliacoes`)

```bash
curl -X POST "http://localhost:8000/avaliacoes" \
  -H "Content-Type: application/json" \
  -d '{
    "texto": "Entrega super rápida e o fone tem um som excelente! Recomendo muito.",
    "produto": "Fone Bluetooth Pro"
  }'
```

**Resposta (`201 Created`):**
```json
{
  "id": "6720d2a1e4b0a1d2c3e4f5b2",
  "texto": "Entrega super rápida e o fone tem um som excelente! Recomendo muito.",
  "produto": "Fone Bluetooth Pro",
  "classe": "positivo",
  "confianca": 0.965,
  "modelo": "modelo_v1",
  "data": "2026-10-27T20:30:00Z"
}
```

* Validação: O texto deve ter entre 3 e 2000 caracteres (retorna `422 Unprocessable Entity` se fora do intervalo).
* Gravado com `origem: "api"`, `nota: null` e `rotulo_real: null` (garantindo que entradas da API nunca contaminem o retreino do modelo nem distorçam as métricas de acurácia global).

#### 2. Buscar Avaliação por ID (`GET /avaliacoes/{id}`)

```bash
curl -X GET "http://localhost:8000/avaliacoes/6720d2a1e4b0a1d2c3e4f5b2"
```

#### 3. Listar Avaliações Recentes (`GET /avaliacoes?limite=5`)

```bash
curl -X GET "http://localhost:8000/avaliacoes?limite=5"
```

#### 4. Checagem de Saúde do Sistema (`GET /saude`)

```bash
curl -X GET "http://localhost:8000/saude"
```

**Resposta (`200 OK`):**
```json
{
  "status": "ok",
  "banco": "conectado",
  "modelo": "carregado"
}
```

---

## Testes Automatizados

A suíte de testes garante isolamento completo: **nenhum teste depende do MongoDB estar rodando**. O repositório e o classificador são substituídos em memória por mocks (`FakeReviewRepository` e `FakeClassificador`) via injeção de dependência (`app.dependency_overrides`).

```bash
make test
# ou:
pytest -v
```

Resultado:
```text
============================== 39 passed in 1.45s ==============================
```

---

## Registros de Decisões de Arquitetura (ADRs)

Todas as decisões arquiteturais fundamentais, escolhas tecnológicas e compensações (*trade-offs*) do projeto estão documentadas no padrão MADR (*Markdown Any Decision Records*).

Para consultar a tabela consolidada com o sumário de todas as decisões, status e escopos, consulte o **[Índice de Registros de Decisões de Arquitetura](docs/adr/README.md)**.

---

## Licença

Distribuído sob a licença MIT. Consulte o arquivo [LICENSE](LICENSE) para mais detalhes.
O dataset [B2W-Reviews01](https://github.com/b2wdigital/b2w-reviews01) segue a sua respectiva licença original.
