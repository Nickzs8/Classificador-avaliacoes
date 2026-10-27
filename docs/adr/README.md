# Registros de Decisões de Arquitetura (ADR)

Este diretório contém os **Architecture Decision Records (ADRs)** do projeto *Classificador de Avaliações*, registrando o histórico de decisões estruturais, tecnologias adotadas, justificativas técnicas e compensações (*trade-offs*).

Os documentos seguem a estrutura padrão estabelecida por Michael Nygard e templates MADR (*Markdown Any Decision Records*).

---

## Índice de Decisões

| ID | Título | Status | Data | Escopo |
|---|---|---|---|---|
| [ADR-0001](0001-armazenamento-analitico-e-repository-pattern-com-mongodb.md) | Armazenamento Analítico e Repository Pattern com MongoDB | **Aceito** | 2026-10-21 | V1 / Core |
| [ADR-0002](0002-pipeline-de-classificacao-com-tfidf-e-regressao-logistica.md) | Pipeline de Classificação com TF-IDF e Regressão Logística | **Aceito** | 2026-10-22 | V1 / ML |
| [ADR-0003](0003-adocao-do-fastapi-com-rotas-sincronas.md) | Adoção do FastAPI com Rotas Síncronas (`def`) | **Aceito** | 2026-10-26 | V2 / API |
| [ADR-0004](0004-contratos-de-dados-e-validacao-com-pydantic-v2.md) | Contratos de Dados e Validação Estrita com Pydantic V2 | **Aceito** | 2026-10-27 | V2 / API |
| [ADR-0005](0005-injecao-de-dependencias-para-testabilidade-da-api.md) | Injeção de Dependências (`Depends`) para Isolamento de Testes | **Aceito** | 2026-10-26 | V2 / Testes |
| [ADR-0006](0006-orquestracao-da-esteira-com-run-pipeline.md) | Orquestração da Esteira de Treinamento com `run_pipeline.py` | **Aceito** | 2026-10-27 | V1 / Tooling |
| [ADR-0007](0007-padronizacao-de-comandos-de-desenvolvimento-com-makefile.md) | Padronização de Comandos de Desenvolvimento com `Makefile` | **Aceito** | 2026-10-27 | V2 / Tooling |

---

## Estrutura Padrão de um ADR

Cada documento neste diretório é composto pelas seguintes seções:
1. **Contexto e Problema:** Qual desafio técnico ou requisito de negócio motivou a decisão.
2. **Decisão:** O que foi escolhido e como será implementado.
3. **Alternativas Consideradas:** Quais outras opções foram avaliadas e os motivos do descarte.
4. **Consequências e Trade-offs:** Benefícios obtidos e custos/responsabilidades operacionais aceitos.
