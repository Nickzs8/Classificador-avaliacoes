# Guia Operacional para Agentes de IA (`AGENTS.md`)

Este documento define as diretrizes técnicas, regras de arquitetura, comandos frequentes e convenções de código que **qualquer agente de IA** (Antigravity, Cursor, Claude Code, Aider, etc.) deve seguir rigorosamente ao interagir, desenvolver ou refatorar este repositório.

---

## 1. Visão Geral do Projeto

* **Nome do Projeto:** Classificador de Avaliações
* **Objetivo:** Ingestão, classificação de sentimento (*positivo* / *negativo*) de avaliações em português, armazenamento analítico no MongoDB e disponibilização via API REST e Dashboard.
* **Stack Principal:** Python 3.11+, MongoDB 8.2 (Docker), PyMongo, Pandas, Scikit-Learn, Joblib, FastAPI, Streamlit e Pytest.
* **Repositório GitHub:** `Nickzs8/Classificador-avaliacoes`

---

## 2. Regras de Arquitetura Inegociáveis

1. **Repository Pattern Estrito:**
   * **Apenas** o arquivo `src/repository.py` pode importar e utilizar o `pymongo` ou `MongoClient`.
   * Qualquer nova consulta, inserção ou agregação analítica deve ser implementada como um método de `ReviewRepository`.
2. **Rotas da API com `def` (Síncronas):**
   * Como `pymongo` e `scikit-learn` realizam operações síncronas bloqueantes, **nunca declare rotas do FastAPI com `async def`** se elas invocarem o repositório ou o classificador.
   * Use sempre `def` padrão para que o FastAPI execute as requisições no pool de threads secundárias (*threadpool*), impedindo o travamento do event loop da API.
3. **Service Layer Compartilhado (`src/services/classificador.py`):**
   * A inferência do modelo deve ficar centralizada no serviço `Classificador` em `src/services/`. Tanto o script batch da V1 (`predict.py`) quanto a API da V2 consomem esse mesmo serviço para evitar duplicação de lógica.
   * O modelo `.joblib` deve ser carregado uma única vez na inicialização da aplicação, nunca a cada requisição HTTP.
4. **Injeção de Dependências (`Depends`):**
   * As rotas do FastAPI devem receber instâncias de `ReviewRepository` e `Classificador` via `Depends`. Isso é essencial para que os testes automatizados possam injetar mocks em memória sem subir o banco de dados.
5. **Prevenção de Module Shadowing:**
   * **Nunca** nomeie scripts ou módulos locais com o mesmo nome de bibliotecas instaladas (ex.: `streamlit.py`, `fastapi.py`, `pytest.py`). Use nomes descritivos como `dashboard.py` ou `app.py`.
6. **Integridade de Esquema BSON & Agregações:**
   * Toda avaliação gravada via API deve conter `origem: "api"`, `nota: null`, `rotulo: null` e `rotulo_real: null`.
   * O pipeline da métrica `taxa_acerto` no repositório deve filtrar explicitamente `rotulo_real: {"$ne": null}` para que avaliações da API não sejam contabilizadas como erros na acurácia global.

---

## 3. Isolamento Total dos Testes Automatizados

* **Independência do Banco:** A suíte de testes em `tests/` **NUNCA** deve depender do contêiner do MongoDB estar rodando.
* **Testes de Pré-Processamento e Ingestão:** Utilize fixtures geradoras de dados sintéticos em memória e a fixture nativa `tmp_path` do Pytest para leitura/escrita de arquivos temporários.
* **Testes da API:** Utilize o `TestClient` do FastAPI aplicando `app.dependency_overrides` para substituir o `ReviewRepository` por uma implementação falsa em memória.
* **Configuração:** O arquivo `pytest.ini` deve manter `pythonpath = . src` e `testpaths = tests`.

---

## 4. Comandos de Desenvolvimento Frequentes

```bash
# Ativar o ambiente virtual
source .venv/bin/activate

# Executar a suíte de testes completa
pytest -v

# Iniciar o banco de dados MongoDB
docker compose up -d
docker compose ps

# Rodar a esteira completa da V1 (Batch)
python run_pipeline.py

# Ou rodar etapas individuais:
python src/prepare_data.py
python src/ingest.py
python src/train.py
python src/predict.py
python src/analytics.py

# Iniciar o Dashboard Web (Streamlit)
streamlit run src/interface/dashboard.py
# ou via make:
make dashboard

# Iniciar o servidor da API (FastAPI)
uvicorn api.main:app --reload --app-dir src
```

---

## 5. Convenções de Git, Commits e Arquivos Sensíveis

* **Arquivos Estritamente Ignorados (Nunca Commitar):**
  * Ambientes e chaves: `.venv/`, `.env`
  * Caches: `__pycache__/`, `.pytest_cache/`
  * Datasets volumosos: `data/raw/`, `data/reviews.csv`
  * Artefatos pesados de Machine Learning: `models/`, `*.joblib`
* **Padronização de Mensagens de Commit (Conventional Commits):**
  * `feat:` Novas funcionalidades ou endpoints
  * `fix:` Correção de bugs
  * `test:` Adição ou modificação de testes
  * `docs:` Alterações em documentação (`README.md`, `ARCHITECTURE.md`, `ROADMAP_V2.md`)
  * `refactor:` Refatoração de código sem alteração de comportamento
  * `chore:` Tarefas de manutenção, dependências ou `.gitignore`

---

## 6. Integração com a Base de Conhecimento (Obsidian / Second Brain)

O desenvolvedor mantém um cofre de documentação técnica contínua (Obsidian Vault) conectado ao ambiente de desenvolvimento para consolidação e retenção de aprendizado.

**Diretrizes para o agente de IA:**
* O agente principal pode delegar pesquisas e redação de notas ao subagente especializado **`vault-researcher`**, que opera concorrentemente em background enquanto o fluxo de código prossegue.
* Sempre que um conceito novo, framework, padrão arquitetural ou boa prática for introduzido ou discutido, verifique a base de notas e registre-o.
* Siga rigorosamente a estrutura do cofre e os templates em `Templates/`:
  * Frontmatter YAML padronizado com `tags:`
  * Conexões internas e transversais utilizando wikilinks do Obsidian (`[[Nome da Nota]]`)
  * Blocos de código com linguagem explícita e syntax highlighting
  * Preservação da hierarquia de pastas e integração com o plugin Waypoint (`%% Begin Waypoint %%`)
