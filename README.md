# Review Classifier with MongoDB

<p align="center">
  <b>English</b> | <a href="README.pt-br.md">Português</a>
</p>

<p align="center">
  <img src="https://img.shields.io/badge/Python-3.11+-blue.svg" alt="Python 3.11+">
  <img src="https://img.shields.io/badge/MongoDB-8.2-green.svg" alt="MongoDB 8.2">
  <img src="https://img.shields.io/badge/Docker-compose-2496ED.svg?logo=docker&logoColor=white" alt="Docker">
  <img src="https://img.shields.io/badge/Tests-20%20passed-brightgreen.svg" alt="Pytest">
  <img src="https://img.shields.io/badge/Streamlit-1.35+-FF4B4B.svg?logo=streamlit&logoColor=white" alt="Streamlit">
  <img src="https://img.shields.io/badge/License-MIT-yellow.svg" alt="License: MIT">
</p>

Python AI project that classifies Portuguese product reviews as **positive** or **negative**, using **MongoDB** as a central analytical storage for raw texts, metadata, and batch predictions.

---

## Interactive Dashboard (Streamlit)

The project features a graphical user interface built with Streamlit for monitoring analytical KPIs, ranking products with the highest customer dissatisfaction, and tracking time series:

<!-- SPACE FOR DASHBOARD SCREENSHOT: Saved in docs/images/dashboard.png -->
<p align="center">
  <img src="docs/images/dashboard.png" alt="Streamlit Dashboard Preview" width="850"/>
</p>

---

## How it works

1. **Ingestion:** E-commerce reviews are loaded into MongoDB as semi-structured documents.
2. **Training:** Previously labeled documents are used to train an NLP pipeline (TF-IDF + Logistic Regression).
3. **Batch Classification:** The model predicts the sentiment of unlabeled documents (simulating production data).
4. **Retroactive Storage:** The prediction (class, confidence, version, and timestamp) is saved back into the original document via `UpdateOne`.
5. **Analytical Aggregations:** MongoDB aggregation pipelines compute business metrics (e.g., dissatisfaction ranking per product and monthly sentiment trends).

---

## Tech Stack

| Layer | Tool | Purpose |
|---|---|---|
| **Language** | Python 3.11+ | Backend services and data scripts |
| **Database** | MongoDB 8.2 (Docker) | Flexible document store and aggregation pipelines |
| **Database Driver** | PyMongo | Official connection driver and bulk operations |
| **Data Processing** | Pandas | Data cleaning, sampling, and reshaping (`pivot`) |
| **Machine Learning** | Scikit-Learn & Joblib | TF-IDF pipeline, Logistic Regression, and serialization |
| **Automated Testing** | Pytest | Unit tests for data labeling, ingestion, and ML |
| **Interface / BI** | Streamlit | Reactive web analytical dashboard |

---

## System Architecture

Layered architecture with loose coupling (*Repository Pattern*), where each component interacts only with its adjacent layer:

```
┌─────────────────────────────────────────┐
│     Interface (Terminal / Dashboard)    │
├─────────────────────────────────────────┤
│   Services: ingestion, train, predict,  │
│               analytics                 │
├─────────────────────────────────────────┤
│  Repository (single point of PyMongo)   │
├─────────────────────────────────────────┤
│           MongoDB (Docker)              │
└─────────────────────────────────────────┘
```

> 📖 **Comprehensive Architecture Documentation:** For complete specifications on design patterns (*Service Layer*, *DTOs*, *Dependency Injection*), data flows, and BSON indexing strategies, refer to **[docs/ARCHITECTURE.md](docs/ARCHITECTURE.md)**.

---

## Project Structure

```
classificador-avaliacoes/
├─ docker-compose.yml         # MongoDB 8.2 container definition
├─ requirements.txt           # Project dependencies
├─ pytest.ini                 # Pytest path and runner configuration
├─ LICENSE                    # MIT License
├─ AGENTS.md                  # Operational guidelines for AI coding agents
├─ .env.example               # Environment variables template
├─ docs/
│  ├─ ARCHITECTURE.md         # Detailed architectural specifications
│  ├─ ROADMAP_V2.md           # Full Version 2 implementation roadmap
│  └─ images/                 # Documentation screenshots and assets
├─ data/
│  ├─ raw/B2W-Reviews01.csv   # Raw original dataset (not versioned)
│  └─ reviews.csv             # Cleaned and labeled sample (not versioned)
├─ models/                    # Serialized model artifact (.joblib)
├─ src/
│  ├─ config.py               # Environment configuration loader
│  ├─ check_connection.py     # MongoDB connectivity diagnostic script
│  ├─ prepare_data.py         # Step 1: Cleaning, business rules, and labeling
│  ├─ repository.py           # Step 2: Repository with Aggregation Pipelines
│  ├─ ingest.py               # Step 3: BSON ingestion from CSV to MongoDB
│  ├─ train.py                # Step 4: Model training and evaluation
│  ├─ predict.py              # Step 5: Batch inference and auditing
│  ├─ analytics.py            # Step 6: Console tabular reports
│  └─ dashboard.py            # Step 6: Streamlit interactive web application
└─ tests/                     # Automated unit tests (isolated from the database)
   ├─ test_rotulagem.py
   ├─ test_ingest.py
   └─ test_modelo.py
```

---

## Dataset

Uses [B2W-Reviews01](https://github.com/b2wdigital/b2w-reviews01), an open corpus of over 130,000 Brazilian e-commerce reviews with user ratings from 1 to 5.

* **Selected columns:** `review_text`, `overall_rating`, `product_name`, `submission_date`.
* **Download:** Download `B2W-Reviews01.csv` from the official repository and save it to `data/raw/B2W-Reviews01.csv`.
* *Note:* Direct loading via local CSV is recommended to avoid dataset loader script incompatibilities in recent versions of Hugging Face's `datasets`.

### Business Rules & Data Sanitization

| Rule | Action | Rationale |
|---|---|---|
| **Rating 4 or 5** | Label `positivo` (positive) | Clear customer satisfaction |
| **Rating 1 or 2** | Label `negativo` (negative) | Customer complaint or order issue |
| **Rating 3** | Dropped | Neutral or ambiguous reviews |
| **Texts < 10 chars or Null** | Dropped | Insufficient semantic information for NLP |
| **Duplicate Texts** | Removed | Prevention of spam or repetition bias |
| **Reproducible Sample** | 20,000 rows (`seed=42`) | Fast training and controlled class distribution |

---

## MongoDB Document Schema

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
  }
}
```

* **Production Simulation:** Approximately 10% of documents are ingested with `rotulo: null`.
* **Auditing:** The `rotulo_real` field stores the ground truth and is never exposed during training.
* **Optimized Indexes:** Automatic index creation on `rotulo` and `produto` fields for fast query and aggregation performance.

---

## How to Run

### Prerequisites
* Python 3.11 or higher
* Docker and Docker Compose

> [!NOTE]
> **Linux Kernel Compatibility:** Linux kernel versions 6.19+ have a known incompatibility with the `mongo:8.0` image (SERVER-121912). This project explicitly uses the stable **`mongo:8.2`** image.

### 1. Clone & Environment Setup

```bash
git clone https://github.com/Nickzs8/Classificador-avaliacoes.git
cd classificador-avaliacoes

python -m venv .venv
source .venv/bin/activate        # On Windows: .venv\Scripts\activate
pip install -r requirements.txt
```

### 2. Configure Environment Variables

Copy the example file:
```bash
cp .env.example .env
```

Suggested default configuration:
```env
MONGO_USER=admin
MONGO_PASSWORD=change_this_password
MONGO_HOST=localhost
MONGO_PORT=27017
MONGO_DB=reviews_db
MONGO_COLLECTION=reviews
MODEL_PATH=models/modelo_v1.joblib
```
*(Avoid using `$` characters in passwords due to Docker Compose variable interpolation).*

### 3. Step-by-Step Execution Pipeline

```bash
# 1) Clean and label raw data (generates data/reviews.csv)
python src/prepare_data.py

# 2) Start the MongoDB database container
docker compose up -d
docker compose ps
python src/check_connection.py      # Confirms database connectivity

# 3) Ingest documents into MongoDB
python src/ingest.py

# 4) Train the model and save the artifact models/modelo_v1.joblib
python src/train.py

# 5) Perform batch inference on pending documents
python src/predict.py

# 6) Inspect Analysis Results
python src/analytics.py              # Consolidated terminal tabular report
streamlit run src/dashboard.py       # Interactive web dashboard in browser
```

---

## Automated Tests

The project includes an automated unit test suite covering sanitization rules, document schema integrity, and the machine learning pipeline. **Tests do not require a running MongoDB instance.**

```bash
pytest -v
```

---

## Performance Metrics

Due to class imbalance (higher volume of positive reviews), the evaluation focuses on **F1-Score per class** with `class_weight="balanced"`:

| Class | Precision | Recall | F1-Score |
|---|---|---|---|
| **Positive** | 0.98 | 0.93 | 0.95 |
| **Negative** | 0.84 | 0.94 | 0.89 |

* **Model Behavior:** The high recall on negative reviews (0.94) ensures that nearly all customer dissatisfaction cases are detected by the analytics pipeline.
* **Generalization on Unseen Data:** **92.7% accuracy** measured on the 2,000 unlabeled documents compared against `rotulo_real` (with an average confidence of **92.4%** for negatives and **97.7%** for positives).

---

## V2 Roadmap: Real-Time Inference with REST API

In **V2**, the system expands beyond batch processing to allow users to submit external reviews in real time via **FastAPI** and receive instantaneous classification:

```
User → Interface → API (FastAPI) → Classification Service → Model (.joblib)
                      │
                      └→ ReviewRepository → MongoDB (stores the classified review)
```

### Architecture Decision Records (ADR)
* **FastAPI + Uvicorn:** Automatic Pydantic validation and interactive OpenAPI docs at `/docs`.
* **Synchronous Route Handlers (`def`):** Protects the event loop by running blocking `pymongo` and `scikit-learn` calls in a separate threadpool.
* **Service Layer (`classificador.py`):** Centralizes inference logic shared by both batch jobs and API endpoints.
* **Dependency Injection (`Depends`):** Enables isolated unit and integration testing with in-memory mocks.

See the full specification, data schemas, and endpoint contracts in: **[docs/ROADMAP_V2.md](docs/ROADMAP_V2.md)**.

---

## License

Distributed under the MIT License. See [LICENSE](LICENSE) for more details.
The [B2W-Reviews01](https://github.com/b2wdigital/b2w-reviews01) dataset follows its original repository license.
