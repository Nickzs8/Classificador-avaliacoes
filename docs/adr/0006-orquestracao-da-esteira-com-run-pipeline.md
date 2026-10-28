# ADR 0006: Orquestração da Esteira de Treinamento com `run_pipeline.py`

* **Status:** Aceito
* **Data:** 2026-10-27
* **Contexto:** Versão 1 (Tooling & Operação)

---

## 1. Contexto e Problema

O ciclo completo de preparação e treinamento do modelo de Machine Learning requer 3 etapas sequenciais e interdependentes:
1. `src/prepare_data.py` (Limpeza do CSV bruto e rotulagem).
2. `src/ingest.py` (Ingestão BSON no MongoDB).
3. `src/train.py` (Treinamento do classificador e exportação do `.joblib`).

A execução manual desses comandos no terminal gerava atrito, dependia da memorização da ordem exata e podia falhar de forma silenciosa ou desordenada caso o banco de dados não estivesse ativo.

---

## 2. Decisão

1. **Criar um orquestrador central em Python na raiz (`run_pipeline.py`):**
   * Utilizar `sys.executable` para garantir a execução no ambiente virtual (`.venv`) ativo em qualquer sistema operacional (Linux, macOS ou Windows).
   * Executar os scripts sequencialmente via `subprocess.run`, interrompendo o fluxo imediatamente se qualquer etapa retornar código de saída diferente de zero (`returncode != 0`).
2. **Validador de Integridade de Infraestrutura:**
   * Verificar se o contêiner do MongoDB está ativo via `docker compose ps` antes de acionar etapas dependentes de rede/banco, exibindo instruções de remediação clara caso esteja desligado.
3. **Formatação Padronizada de Logs:**
   * Saída de terminal profissional sem caracteres incompatíveis ou emojis, utilizando marcadores padrão (`[INFO]`, `[OK]`, `[AVISO]`, `[ERRO]`, `[ETAPA]`).

---

## 3. Alternativas Consideradas

* **Scripts Shell Bash (`scripts/executar_pipeline.sh`):**
  * *Prós:* Simples e conciso.
  * *Contras:* Não é multiplataforma (falha em ambientes Windows sem WSL/Git Bash) e exige ativação manual explícita do ambiente virtual.
* **Makefile / Taskfile:**
  * *Prós:* Padrão comum em ecossistemas backend.
  * *Contras:* Requer a instalação do binário `make` (não nativo em Windows) e sintaxe propensa a erros com tabs.
* **Orquestradores de Workflow de Dados (Airflow / Prefect / Dagster):**
  * *Prós:* Caching de tarefas e DAGs visuais.
  * *Contras:* Complexidade acidental desproporcional (*over-engineering*) para encadear 3 etapas de 5 segundos.

---

## 4. Consequências e Trade-offs

* **Positivas:**
  * **Golden Path em 1 Comando:** Qualquer desenvolvedor inicializa o projeto com `python run_pipeline.py`.
  * Multiplataforma e zero dependências externas adicionais.
  * Fail-fast: previne que erros de dados ou banco cascatem para o treinamento.
* **Negativas / Riscos Mitigados:**
  * Não implementa caching de artefatos por hash de arquivo (aceitável pelo tempo total de execução ser de apenas ~5 segundos).
