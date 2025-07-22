python3.11 -m venv venv311
source venv/bin/activate
pip install --upgrade pip
# reinstall your packages


pip install -r requirements.txt


# python -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"


ollama serve

ollama run llama3


 curl -X POST http://localhost:8000/query/ \
  -H "Content-Type: application/json" \
  -d '{"query": "What is the main theme of Gannibal?"}

  uvicorn rag_api:app --reload --host 0.0.0.0 --port 8000; 
  lsof -i :8000
   kill -9 90653    







📘 README.md
# 🧠 RAG Pipeline – AI-Focused Data Infrastructure

This project is a modular Retrieval-Augmented Generation (RAG) pipeline that scrapes data, processes it through an ETL workflow, embeds it using Sentence Transformers, stores vectors in ChromaDB, and exposes the system via a FastAPI for querying.

## 🏗️ Project Structure

├── airflow/ # Apache Airflow DAGs and configs
│ └── dags/ # Airflow workflows (Python DAG files)
├── data/ # Data folders used locally (also mirrored on MinIO)
│ ├── raw/ # Raw scraped HTML/text
│ ├── bronze/ # Cleaned & parsed data
│ ├── silver/ # Enriched & structured data
│ └── gold/ # Embedded vector store (ChromaDB)
├── docker/ # Docker-related config
├── etl/ # ETL scripts for scraping, cleaning, embedding
├── api/ # FastAPI code for querying vector DB
├── Makefile # CLI automation for running pipeline stages
├── requirements.txt # Python dependencies
└── README.md # Project documentation


---

## ⚙️ How It Works

### 1. Scrape
Use BeautifulSoup to extract data (e.g., from Project Gutenberg) and store in `raw/`.

### 2. ETL
Transform data from raw → bronze → silver stages. Each stage improves structure and enriches metadata.

### 3. Embedding
Use `sentence-transformers` to embed cleaned text into vector space.

### 4. Vector DB
Store embeddings in ChromaDB with metadata for similarity search.

### 5. Query API
FastAPI lets you query the Chroma vector DB with natural language.

---

## 🚀 Quickstart

### Prerequisites

- Python 3.11+
- Docker & Docker Compose
- `make`

### Setup

```bash
# Clone repository
git clone https://github.com/your-user/rag-pipeline.git
cd rag-pipeline

# Create virtual environment and install deps
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt

# Start MinIO, Airflow, etc.
make docker-up

# Run full pipeline
make etl

# Start API server
make api
🛠️ Makefile Commands

make scrape        # Run the scraper script
make etl           # Run the full ETL pipeline (raw → bronze → silver → gold)
make embed         # Run only the embedding step
make api           # Launch FastAPI server
make docker-up     # Start all services (MinIO, Airflow)
make docker-down   # Tear down all containers
make airflow_up    # Start Airflow webserver and scheduler
make airflow_dag_trigger DAG=my_dag_name
make clean         # Cleanup data folders
🌐 API Endpoint (via FastAPI)

POST /query
{
  "query": "What is the main theme of Pride and Prejudice?"
}
Returns: Top similar documents from the ChromaDB vector store.

📦 Dependencies

See requirements.txt for full list. Key packages:

requests, bs4 – Web scraping
sentence-transformers – Embedding
chromadb – Vector DB
fastapi, uvicorn – API server
minio – S3-compatible object storage
airflow – Workflow orchestration
📂 Data Flow Summary

Scrape → raw/
      → ETL → bronze/
               → silver/
               → gold/ (ChromaDB)
                        ↑
                     FastAPI
👨‍💻 Author

Sabrin Lal Singh
2025, Kathmandu, Nepal