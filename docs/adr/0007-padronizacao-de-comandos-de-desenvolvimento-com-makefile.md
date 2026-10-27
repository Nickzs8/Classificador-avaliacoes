# ADR 0007: Padronização de Comandos de Desenvolvimento com `Makefile`

* **Status:** Aceito
* **Data:** 2026-10-27
* **Contexto:** Versão 2 (Developer Experience & Tooling)

---

## 1. Contexto e Problema

Com a evolução da Versão 2 do projeto, o fluxo de desenvolvimento local passou a envolver múltiplos processos e ferramentas independentes:
* Orquestração do contêiner MongoDB via Docker Compose (`docker compose up -d`).
* Inicialização do servidor backend FastAPI via Uvicorn com hot-reload (`uvicorn api.main:app --reload --app-dir src`).
* Inicialização da interface web Streamlit (`streamlit run src/interface/app.py`).
* Inicialização do dashboard analítico Streamlit (`streamlit run src/dashboard.py`).
* Execução da esteira de testes automatizados com Pytest (`pytest -v`).
* Execução do pipeline batch de dados (`python run_pipeline.py`).

A necessidade de memorizar e digitar comandos longos, flags de diretório (`--app-dir src`) e a exigência de abrir múltiplos terminais para rodar o backend e o frontend simultaneamente geravam atrito operacional e lentidão no ciclo de desenvolvimento diário (DX - *Developer Experience*).

---

## 2. Decisão

Adotar o **`Makefile` (GNU Make)** como a interface canônica de automação e atalhos de desenvolvimento na raiz do repositório:

1. **Auto-resolução do Ambiente Virtual (`.venv`):**
   * Os binários executáveis (`python`, `pytest`, `uvicorn`, `streamlit`) priorizam automaticamente os caminhos relativos de `.venv/bin/`, com fallback gracioso para o `PATH` do sistema.
   * Isso elimina a dependência de ativação prévia manual do ambiente (`source .venv/bin/activate`).

2. **Alvos Declarados como `.PHONY`:**
   * Todos os comandos (`help`, `up`, `down`, `test`, `api`, `ui`, `dashboard`, `dev`, `pipeline`, `status`) são registrados como `.PHONY`, prevenindo conflitos com eventuais pastas ou arquivos físicos de mesmo nome.

3. **Execução Paralela com `make dev`:**
   * Utilizar a diretiva de dependência `dev: up` para garantir que o MongoDB esteja ativo.
   * Disparar simultaneamente o backend FastAPI e a interface Streamlit no mesmo terminal via execução paralela nativa do Make (`@$(MAKE) -j 2 api ui`), propagando sinais de parada (`Ctrl + C`) para ambos os processos.

4. **Target Padrão Auto-documentado:**
   * Definir `.DEFAULT_GOAL := help` para exibir o menu de ajuda interativo ao digitar apenas `make`.

---

## 3. Alternativas Consideradas

* **Scripts Shell Bash (`scripts/dev.sh`):**
  * *Prós:* Sem necessidade de instalar novas ferramentas.
  * *Contras:* Difícil orquestração paralela com encerramento gracioso via `Ctrl+C` e sintaxe frágil para passagem de parâmetros.
* **Task runners em Python (`taskipy`, `invoke`):**
  * *Prós:* Sintaxe em Python ou TOML (`pyproject.toml`).
  * *Contras:* Dependências adicionais no `requirements.txt` sem suporte tão maduro a concorrência quanto o GNU Make.

---

## 4. Consequências e Trade-offs

* **Positivas:**
  * **Ergonomia Máxima:** Iniciar o ambiente completo com um único comando (`make dev`).
  * **Padrão Ouro no Linux:** Ferramenta nativa em sistemas operacionais Unix/Linux e ambientes de CI/CD.
  * **Independência de Ativação do venv:** Execução direta dos binários corretos em `.venv/bin/`.
* **Negativas / Custos:**
  * No Windows nativo (sem WSL), o utilitário `make` não é instalado por padrão, exigindo Git Bash, Chocolatey ou WSL para execução.
