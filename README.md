# 🧠 RAG Pipeline – Home Assignment  
**Senior Big Data Engineer – AI-Focused Data Infrastructure**

## 📌 Overview

**RAG Pipeline** is a Retrieval-Augmented Generation (RAG) system that scrapes book data, processes it through multiple ETL stages, generates semantic embeddings, and exposes a FastAPI-based API for querying the knowledge base.  
It utilizes:

- **MinIO** as object storage  
- **Apache Airflow** for orchestration  
- **ChromaDB** as a vector database  

---

## 🚀 Project Workflow

### Components:
- **Scraper:** Scrapes book data from [Books to Scrape](https://books.toscrape.com)
- **ETL Pipeline:**
  - `RAW:` Raw scraped text files
  - `BRONZE:` Cleaned Parquet files
  - `SILVER:` Enhanced Parquet files with word count
  - `GOLD:` Embedded text chunks stored in ChromaDB
- **Data Quality Checks:** Runs automated validations on SILVER data
- **FastAPI Service:** Exposes endpoints to query the RAG system
- **Airflow DAG:** Automates the entire pipeline

---

## 📂 Folder Structure

```
rag_pipeline
├── Dockerfile.airflow
├── Dockerfile.api
├── Makefile
├── README.md
├── airflow/
│   ├── dags/
│   │   └── rag_pipeline.py
│   └── airflow.db
├── architecture.png
├── data/
│   ├── bronze/
│   ├── gold/
│   ├── lineage/
│   ├── raw/
│   └── silver/
├── docker-compose.yaml
├── downloads/
├── mydata/
│   ├── metadata.json
│   └── silver/
├── rag_api.py
├── src/
│   ├── data/
│   │   └── gold/
│   ├── data_quality.py
│   ├── etl.py
│   ├── rag_utils.py
│   └── scraper.py
└── tests/
    ├── conftest.py
    └── test_scraper.py
```

---

## ⚙️ Setup Instructions

### ✅ Prerequisites
- Docker & Docker Compose
- Python 3.11 (for local development)
- `.env` file with MinIO and app credentials

### 🌍 Environment Variables

```dotenv
MINIO_URL=minio:9000
MINIO_ACCESS_KEY=user_name
MINIO_SECRET_KEY=password123
MINIO_BUCKET=mydata
FERNET_KEY=l2ckboQEnybXHIMXgwprr_GSQUwkzyuqJ0R2ZFunTLY=
SECRET_KEY=l2ckboQEnybXHIMXgwprr_GSQUwkzyuqJ0R2ZFunTLY=
CHROMA_DIR=/opt/data/gold/chroma
```

---

## 📥 Clone and Configure

```bash
git clone https://github.com/sabrinsingh/home_assignment_rag_pipeline.git
cd rag-pipeline

python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt

ollama serve
```

### 🐳 Start Docker-based System

```bash
make docker-up
```

- Airflow UI: http://localhost:8080  
- FastAPI: http://localhost:8000  
- MinIO Console: http://localhost:9001

---

## 🧠 RAG Flow (via Airflow)

Trigger the DAG from Airflow UI. It performs:

1. Scraping book data → stores in MinIO `/raw`
2. ETL transformation: RAW → BRONZE → SILVER → GOLD
3. Data Quality checks on SILVER, uploads results to MinIO
4. Lineage metadata written to MinIO
5. ChromaDB populated with embedded documents
6. FastAPI queries this semantic index via local Ollama LLM

Example query:

```json
{
  "query": "What is the most expensive book and give also the price?"
}
```

---

## 🐳 Docker Makefile Commands

| Command                    | Description                                        |
|----------------------------|----------------------------------------------------|
| `make docker-up`           | Build & run all Docker services                    |
| `make docker-down`         | Stop and remove all Docker containers              |
| `make airflow_up`          | Start Airflow services                             |
| `make airflow_logs`        | Tail logs of Airflow components                    |
| `make airflow_dag_trigger` | Trigger DAG manually                               |

---

## 🖥️ Running Locally (without Docker)

# Start API server
make api

# Run unit tests
make test
```

---

## 🧩 Project Components

- **Scraper** (`src/scraper.py`)  
  Scrapes book info from the site and stores raw data in MinIO

- **ETL Pipeline** (`src/etl.py`)  
  Runs RAW → BRONZE → SILVER → GOLD stages

- **Data Quality Checker** (`src/data_quality.py`)  
  Validates nulls, duplicates, empty values

- **Vector DB**:  
  Uses **ChromaDB** for fast retrieval using embeddings

- **API** (`rag_api.py`)  
  FastAPI app that serves RAG responses using Ollama

- **Airflow DAG** (`airflow/dags/rag_pipeline.py`)  
  Orchestrates scraping + ETL + DQ + lineage

---

## 📄 API Usage

### GET `/`
Returns a welcome message.

### POST `/query/`
```json
{
  "query": "Your question here"
}
```

#### Response:
```json
{
  "question": "Your question here",
  "answer": "Generated answer from RAG",
  "context": "Context documents used"
}
```

---

## 🖼️ Architecture Diagram

See `architecture.png` in the project root folder.

---

## 👨‍💻 Author

**Sabrin Lal Singh**  
📧 [sabrinlalsingh@gmail.com](mailto:sabrinlalsingh@gmail.com)