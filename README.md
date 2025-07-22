> Home assignment for **Senior Big Data Engineer – AI-Focused Data Infrastructure**

RAG Pipeline
RAG Pipeline is a Retrieval-Augmented Generation (RAG) project that scrapes book data, processes it through multiple ETL stages, generates embeddings for semantic search, and exposes a FastAPI-based API to query the knowledge base. The pipeline uses MinIO as object storage, Apache Airflow for orchestration, and ChromaDB for vector embeddings.

Project Overview
•	Scraper: Scrapes book data from https://books.toscrape.com website.
•	ETL Pipeline:
•	  - RAW: Raw text files from scraper.
•	  - BRONZE: Cleaned Parquet files.
•	  - SILVER: Enhanced Parquet files with word counts.
•	  - GOLD: Embedded text chunks stored in ChromaDB vector store.
•	Data Quality Checks: Runs automated data quality validations on SILVER data.
•	FastAPI Service: Provides an API endpoint for querying the RAG knowledge base.
•	Airflow: Orchestrates the pipeline DAG.


Folder Structure
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


⚙️ Setup Instructions
Prerequisites
•	Docker and Docker Compose installed
•	Python 3.11 (for local runs)
•	MinIO credentials set in .env file

Environment Variables
Create a .env file with the following content (already included in your project):
MINIO_URL=minio:9000
MINIO_ACCESS_KEY=minioadmin
MINIO_SECRET_KEY=minioadmin
MINIO_BUCKET=mydata
FERNET_KEY=l2ckboQEnybXHIMXgwprr_GSQUwkzyuqJ0R2ZFunTLY=
SECRET_KEY=l2ckboQEnybXHIMXgwprr_GSQUwkzyuqJ0R2ZFunTLY=
CHROMA_DIR=/opt/data/gold/chroma


🐳 Running with Docker Compose
Build and start all services (MinIO, API, Airflow):
$ make docker-up

Stop and remove all containers:
$ make docker-down

Start Airflow components:
$ make airflow_up

View Airflow scheduler and webserver logs:
$ make airflow_logs

Trigger the Airflow DAG manually:
$ make airflow_dag_trigger

Airflow UI will be available at http://localhost:8080
FastAPI API will be available at http://localhost:8000
MinIO Console UI available at http://localhost:9001 (login with your MinIO credentials)


🧰 Running Locally (without Docker)
### 1. Clone and configure
```bash
git clone https://github.com/sabrinsingh/home_assignment_rag_pipeline.git
cd rag-pipeline
Create a Python virtual environment and install dependencies:
$ python3 -m venv env
source env/bin/activate
pip install -r requirements.txt

ollama serve

Run scraper:
$ make scrape

Run full ETL pipeline:
$ make etl

Start FastAPI server:
$ make api

Run tests:
$ make test

🧩 Makefile Commands
Command	Description
make scrape	Run scraper to collect raw book data
make etl	Run full ETL pipeline (RAW → GOLD + DQ)
make api	Start FastAPI server locally
make docker-up	Build and start Docker containers
make docker-down	Stop and remove Docker containers
make airflow_up	Start Airflow webserver, scheduler, init
make airflow_dag_trigger	Trigger Airflow DAG manually
make airflow_logs	Tail Airflow scheduler and webserver logs
make test	Run pytest tests
make clean	Remove temporary files
📄 API Usage
Root
GET /
Returns welcome message.
Query Endpoint
POST /query/
Content-Type: application/json

{
  "query": "Your question here"
}

Response:
{
  "question": "Your question here",
  "answer": "Generated answer from RAG",
  "context": "Context documents used"
}


🛠️ Project Components
•	Scraper (src/scraper.py): Scrapes book info from the web and uploads raw text to MinIO.
•	ETL Pipeline (src/etl.py): Processes data through RAW → BRONZE → SILVER → GOLD stages.
•	Data Quality Checks (src/data_quality.py): Performs checks like nulls, duplicates, empty strings.
•	Vector DB: Uses ChromaDB to store sentence embeddings for fast retrieval.
•	API (rag_api.py): FastAPI app serving RAG answers with local vector DB and Ollama LLM.
•	Airflow DAG (airflow/dags/rag_pipeline.py): Orchestrates scraping and ETL tasks.


🖼️ Architecture Diagram
Refer to architecture.png in the project root folder.

Feel free to open issues or pull requests for improvements or bug fixes.

👨‍💻 Author
Sabrin Lal Singh
sabrinlalsingh@gmail.com
