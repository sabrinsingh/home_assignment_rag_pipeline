from airflow import DAG
from airflow.operators.python import PythonOperator
from datetime import datetime
import sys
import os
sys.path.append('/opt/src')  

from scraper import scrape_books_to_minio
from etl import etl_raw_to_bronze, etl_bronze_to_silver, etl_silver_to_gold, run_data_quality_task


default_args = {
    'owner': 'airflow',
    'start_date': datetime(2024, 1, 1),
    'retries': 1,
}

with DAG(
    dag_id="rag_pipeline",
    default_args=default_args,
    schedule_interval=None,
    catchup=False,
    tags=["RAG", "ETL"]
) as dag:
    

    scrape_task = PythonOperator(
        task_id="extract_raw_data",
        python_callable=scrape_books_to_minio
    )

    bronze_task = PythonOperator(
        task_id="transform_raw_to_bronze",
        python_callable=etl_raw_to_bronze
    )

    silver_task = PythonOperator(
        task_id="transform_bronze_to_silver",
        python_callable=etl_bronze_to_silver
    )

    gold_task = PythonOperator(
        task_id="transform_silver_to_gold",
        python_callable=etl_silver_to_gold
    )


    dq_task = PythonOperator(
    task_id="run_data_quality_checks",
    python_callable=run_data_quality_task
)

    scrape_task >> bronze_task >> silver_task >> gold_task >> dq_task




