.PHONY: help scrape etl embed api docker-up docker-down clean airflow_up airflow_dag_trigger airflow_logs test

help:
	@echo "Available commands:"
	@echo "  make scrape      - Run the scraper script"
	@echo "  make etl         - Run the full ETL pipeline"
	@echo "  make embed       - Run the embedding step separately"
	@echo "  make api         - Start FastAPI server locally"
	@echo "  make docker-up   - Build and start all containers via docker-compose"
	@echo "  make docker-down - Stop and remove docker containers"
	@echo "  make clean       - Clean temporary files"

scrape:
	python src/scraper.py

etl:
	python src/etl.py

# Run both scrape and etl sequentially
run_all: scrape etl

api:
	uvicorn rag_api:app --reload --host 0.0.0.0 --port 8000; 

docker-up:
	docker-compose up --build -d

docker-down:
	docker-compose down

# Start Airflow webserver, scheduler and init containers
airflow_up:
	docker-compose up -d airflow-webserver airflow-scheduler airflow-init

# Trigger the rag_pipeline DAG manually in Airflow container
airflow_dag_trigger:
	docker exec airflow-webserver airflow dags trigger rag_pipeline

# View logs of Airflow scheduler and webserver
airflow_logs:
	docker-compose logs -f airflow-scheduler airflow-webserver

test:
	pytest tests

clean:
	rm -rf temp/*
