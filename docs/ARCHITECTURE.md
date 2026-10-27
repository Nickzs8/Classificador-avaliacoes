# Arquitetura do Sistema

Este documento descreve detalhadamente a arquitetura de software, os padrões de projeto, a modelagem de dados no MongoDB e as diretrizes técnicas do **Classificador de Avaliações**.

---

## 1. Princípios Arquiteturais e Padrões de Projeto

O projeto foi estruturado seguindo uma **Arquitetura em Camadas (Layered Architecture)** com foco em baixo acoplamento, alta coesão e facilidade de testes unitários:

```
┌────────────────────────────────────────────────────────┐
│             Camada de Apresentação / UI                │
│       (Scripts CLI, Dashboard e Interface Web)         │
├────────────────────────────────────────────────────────┤
│             Camada de API / Transporte                 │
│         (FastAPI: rotas, validações e DTOs)            │
├────────────────────────────────────────────────────────┤
│             Camada de Serviços / Domínio               │
│  (Ingestão, Classificador ML, Treino e Predição)       │
├────────────────────────────────────────────────────────┤
│             Camada de Acesso a Dados                   │
│   (ReviewRepository: único ponto de uso do PyMongo)    │
├────────────────────────────────────────────────────────┤
│             Banco de Dados / Armazenamento             │
│                 (MongoDB 8.2 em Docker)                │
└────────────────────────────────────────────────────────┘
```

### Padrões Adotados:
* **Repository Pattern (`ReviewRepository`):** Isola toda a complexidade de consultas, pipelines de agregação BSON e transações do MongoDB em um único ponto do sistema. Nenhum outro arquivo importa ou consome diretamente o `pymongo`.
* **Service Layer (`src/services/classificador.py`):** Centraliza o carregamento do modelo e as transformações de inferência NLP, compartilhando a mesma lógica entre as predições em lote da V1 e os endpoints em tempo real da V2.
* **DTO / Schemas (Pydantic):** Validação estrita e tipagem forte nos contratos de entrada e saída da API.
* **Dependency Injection (`Depends`):** Injeção de repositórios e serviços nas rotas HTTP do FastAPI, permitindo testes isolados com mocks em memória sem necessidade do banco ativo.
* **Threadpool Offloading:** Declaração de rotas com `def` para garantir que chamadas síncronas/bloqueantes do PyMongo e Scikit-Learn executem em threads secundárias, preservando o event loop da API.

---

## 2. Diagramas de Fluxo

### V1: Processamento em Lote (Batch Workflow)
```
Dataset Bruto (CSV)
        │
        ▼
[prepare_data.py] ── Limpeza e rotulagem ──► CSV Higienizado
                                                   │
                                                   ▼
                                           [ingest.py] ── Ingestão BSON ──► MongoDB
                                                                               │
       ┌───────────────────────────────────────────────────────────────────────┘
       ├─ Documentos rotulados (90%) ──► [train.py] ──► Artefato models/modelo_v1.joblib
       │                                                          │
       └─ Documentos sem rótulo (10%) ──► [predict.py] ◄──────────┘
                                                │
                                                ▼
                                   MongoDB (UpdateOne retroativo)
                                                │
                                                ▼
                                    [analytics.py / dashboard.py]
```

### V2: Inferência em Tempo Real (Real-Time API)
```
Usuário Final / Web Client
        │
        │ HTTP POST /avaliacoes {"texto": "...", "produto": "..."}
        ▼
   FastAPI (Rotas síncronas + Schemas Pydantic)
        │
        ├──► Classificador Service (carrega modelo_v1.joblib uma única vez)
        │         │
        │         ▼
        │    Previsão: classe ("positivo"/"negativo") + confiança (float)
        │
        └──► ReviewRepository (MongoDB)
                  │
                  ▼
          Salva documento BSON:
          - nota: null, rotulo: null, rotulo_real: null
          - predicao: { classe, confianca, modelo, data }
          - origem: "api"
```

---

## 3. Modelagem de Dados no MongoDB

O banco utiliza documentos flexíveis no formato BSON, garantindo compatibilidade entre dados históricos e novos dados de produção:

### Esquema Consolidado do Documento:
```json
{
  "_id": {"$oid": "653b1e7c8f9b2a1234567890"},
  "texto": "Chegou rápido, mas a embalagem veio amassada",
  "produto": "Fone Bluetooth X",
  "data": "2018-03-12T14:05:00.000Z",
  "nota": 2,
  "rotulo": null,
  "rotulo_real": "negativo",
  "predicao": {
    "classe": "negativo",
    "confianca": 0.71,
    "modelo": "modelo_v1",
    "data": "2026-10-24T14:05:00.000Z"
  },
  "origem": "api"
}
```

### Justificativa dos Campos:
* **`texto` (String):** Texto da avaliação já higienizado (sem espaços nas pontas e com mais de 10 caracteres).
* **`produto` (String / Null):** Nome do produto avaliado (opcional para usuários da API).
* **`data` (ISODate):** Objeto de data nativo BSON para viabilizar agregações e agrupamentos temporais via `$dateToString`.
* **`nota` (Int / Null):** Nota de 1 a 5 dada pelo cliente (nulo em avaliações vindas via API).
* **`rotulo` (String / Null):** Rótulo supervisionado (`"positivo"` ou `"negativo"`). Ingerido como `null` em 10% da base e em todas as avaliações da API para simular dados novos.
* **`rotulo_real` (String / Null):** Gabarito original do dataset para auditoria posterior. **Nunca é exposto no treinamento**.
* **`predicao` (Object / Null):** Subdocumento populado pelo classificador contendo `classe`, `confianca` (probabilidade), nome da versão do `modelo` e timestamp da inferência.
* **`origem` (String / Null):** Identifica a procedência do registro (ex: `"dataset"` ou `"api"`).

---

## 4. Otimização e Índices de Banco de Dados

Para assegurar alta performance nas buscas e nas agregações periódicas, o repositório provisiona índices dedicados:

```python
db.reviews.create_index([("rotulo", ASCENDING)])
db.reviews.create_index([("produto", ASCENDING)])
db.reviews.create_index([("data", ASCENDING)])
```

---

## 5. Estratégia de Agregação Analítica (*Aggregation Pipelines*)

O repositório utiliza o pipeline de agregação do MongoDB como esteira analítica primária, evitando transferir milhares de registros para a memória do servidor Python:

### A Constante `SENTIMENTO`:
```javascript
SENTIMENTO = {
  "$addFields": {
    "sentimento": {
      "$ifNull": ["$rotulo", "$predicao.classe"]
    }
  }
}
```
* **Coalescência Analítica:** Se a avaliação já possui rótulo consolidado, utiliza o `rotulo`. Se for nulo, utiliza a classe prevista pelo modelo de Machine Learning (`predicao.classe`), unificando a base em tempo de consulta.

### Proteção da Métrica de Acurácia:
O método `taxa_acerto()` filtra explicitamente registros onde `rotulo_real != null`:
```javascript
{
  "$match": {
    "predicao": { "$ne": null },
    "rotulo_real": { "$ne": null }
  }
}
```
Isso impede que dados vindos da API (que não possuem gabarito) sejam contados erroneamente como erros na métrica de acurácia global.

---

## 6. Estratégia de Testes Automatizados

O sistema foi concebido com isolamento total de testes:
* **Testes de Pré-Processamento (`test_rotulagem.py`):** Testam regras de sanitização, amostragem e mutabilidade sem interagir com arquivos de disco ou bancos de dados.
* **Testes de Ingestão (`test_ingest.py`):** Validam tipos BSON e particionamento dos 10% sem rótulo usando datasets sintéticos e a fixture `tmp_path`.
* **Testes de Modelo (`test_modelo.py`):** Treinam um mini-pipeline com 16 exemplos em memória via fixture com `scope="module"`, validando probabilidades e serialização `joblib`.
* **Testes da API (`test_api.py`):** Utilizam o `TestClient` do FastAPI substituindo a dependência do `ReviewRepository` por um mock em memória via `app.dependency_overrides`, dispensando instâncias do Docker.
