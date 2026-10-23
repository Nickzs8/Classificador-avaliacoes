# Classificador de avaliações

Projeto que classifica avaliações de produtos em português como **positivas** ou **negativas**.

---

## Como funciona

1. As avaliações são carregadas no banco de dados como documentos.
2. Os documentos que já têm rótulo são usados para treinar um modelo (TF-IDF + regressão logística).
3. O modelo classifica os documentos sem rótulo.
4. A predição é gravada de volta no mesmo documento.
5. Consultas de agregação no BD analisam os resultados (ex.: negativas por produto).

## Stack

| Parte | Ferramenta |
|---|---|
| Linguagem | Python 3.11+ |
| Banco de dados | MongoDB (Docker) + MongoDB Compass |
| Acesso ao banco | pymongo |
| Dados | pandas |
| Machine learning | scikit-learn, joblib |
| Qualidade | pytest, Git |
| Opcionais | FastAPI, Streamlit |

## Arquitetura

Em camadas, cada uma conversando apenas com a vizinha:

```
┌─────────────────────────────────┐
│  Interface (CLI / API opcional) │
├─────────────────────────────────┤
│  Serviços: ingestão, treino,    │
│  predição, análise              │
├─────────────────────────────────┤
│  Repositório (único uso de      │
│  pymongo)                       │
├─────────────────────────────────┤
│  MongoDB (Docker)               │
└─────────────────────────────────┘
```

**Padrões de projeto**

- **Repository:** uma classe concentra todas as operações no MongoDB.
- **Pipeline (scikit-learn):** TF-IDF e classificador encadeados em um único objeto.
- **Service Layer:** cada etapa (ingerir, treinar, prever, analisar) é uma unidade separada.

## Estrutura do projeto

```
analise-avaliacoes/
├─ docker-compose.yml
├─ requirements.txt
├─ .env
├─ data/
│  ├─ raw/B2W-Reviews01.csv   # dataset original (não versionado)
│  └─ reviews.csv             # dataset limpo e rotulado
├─ models/                    # modelo treinado (.joblib)
├─ src/
│  ├─ config.py               # variáveis de ambiente
│  ├─ prepare_data.py         # etapa 1
│  ├─ repository.py           # acesso ao MongoDB
│  ├─ ingest.py               # etapa 3
│  ├─ train.py                # etapa 4
│  ├─ predict.py              # etapa 5
│  └─ analytics.py            # etapa 6
└─ tests/
```

## Dataset

**B2W-Reviews01**: corpus aberto de avaliações de produtos em português, com cerca de 132 mil registros e notas de 1 a 5.

- Colunas usadas: `review_text`, `overall_rating`, `product_name`, `submission_date`.
- Baixe o CSV do repositório oficial no GitHub e salve em `data/raw/B2W-Reviews01.csv`.
- O carregamento via `datasets` do Hugging Face pode falhar nas versões recentes (o dataset usa script de carregamento), por isso o CSV direto é o caminho recomendado.
- Confira a licença e a forma de citação no repositório oficial do dataset.

### Regras de rotulagem e limpeza

| Regra | Motivo |
|---|---|
| Nota 4 ou 5 → `positivo` | Cliente satisfeito |
| Nota 1 ou 2 → `negativo` | Cliente insatisfeito |
| Nota 3 descartada | Neutro e ambíguo |
| Textos nulos, com menos de 10 caracteres ou duplicados removidos | Pouca informação / repetição |
| Amostra de 20 mil linhas (`random_state=42`) | Treino rápido e reprodutível |

As classes ficam desbalanceadas (mais positivos), então o treino usa `class_weight="balanced"`.

## Modelo do documento no BD

```json
{
  "texto": "Chegou rápido, mas a embalagem veio amassada",
  "produto": "fone-bluetooth",
  "data": "2026-10-15",
  "nota": 2,
  "rotulo": "negativo",
  "predicao": { "classe": "negativo", "confianca": 0.71, "modelo": "v1" }
}
```

Parte dos documentos entra com `rotulo: null`, simulando dados novos que serão classificados pelo modelo.

## Como rodar

### Pré-requisitos

- Python 3.11+
- Docker e Docker Compose

### Instalação

```bash
git clone <url-do-repositorio>
cd projeto-sentimento

python -m venv .venv
source .venv/bin/activate        # Windows: .venv\Scripts\activate
pip install -r requirements.txt
```

### Passo a passo

```bash
# 1) Preparar os dados (gera data/reviews.csv)
python src/prepare_data.py

# 2) Subir o MongoDB
docker compose up -d

# 3) Carregar os dados no banco
python src/ingest.py

# 4) Treinar o modelo
python src/train.py

# 5) Classificar os documentos sem predição
python src/predict.py

# 6) Rodar as análises
python src/analytics.py
```

> Os passos 2 a 6 serão adicionados conforme as etapas do roadmap forem concluídas.

### Configuração

Crie um arquivo `.env` na raiz:

```env
MONGO_URI=mongodb://localhost:27017
MONGO_DB=reviews_db
MONGO_COLLECTION=reviews
MODEL_PATH=models/modelo_v1.joblib
```

## Métricas

A métrica principal é o **F1-score por classe**, porque as classes são desbalanceadas. Uma meta realista para este modelo simples é em torno de 85-90%.

Resultados:

| Classe | Precisão | Recall | F1 |
|---|---|---|---|
| positivo | 0.98 | 0.93 | 0.95 |
| negativo | 0.84 | 0.94 | 0.89 |
