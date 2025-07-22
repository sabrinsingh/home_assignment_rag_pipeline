import os
import duckdb
import pandas as pd
import tempfile
import uuid
from io import BytesIO
from datetime import datetime
from minio import Minio
from sentence_transformers import SentenceTransformer
import chromadb
import json
import numpy as np


from data_quality import run_data_quality_checks  # import your DQ functions

# -----------------------------
# ENV + MinIO Configuration
# -----------------------------
MINIO_URL = os.getenv("MINIO_URL", "localhost:9000")
MINIO_ACCESS_KEY = os.getenv("MINIO_ACCESS_KEY", "minioadmin")
MINIO_SECRET_KEY = os.getenv("MINIO_SECRET_KEY", "minioadmin")
MINIO_BUCKET = os.getenv("MINIO_BUCKET", "mydata")
CHROMA_DIR = os.getenv("CHROMA_DIR", "/opt/data/gold/chroma")
os.makedirs(CHROMA_DIR, exist_ok=True)

RAW_FOLDER = "raw"
BRONZE_FOLDER = "bronze"
SILVER_FOLDER = "silver"

client = Minio(
    MINIO_URL,
    access_key=MINIO_ACCESS_KEY,
    secret_key=MINIO_SECRET_KEY,
    secure=False
)

# -----------------------------
# MinIO Helpers
# -----------------------------
def list_files(folder, suffix=".txt"):
    objects = client.list_objects(MINIO_BUCKET, prefix=f"{folder}/", recursive=True)
    return sorted([obj.object_name for obj in objects if obj.object_name.endswith(suffix)])

def download_file(object_name):
    response = client.get_object(MINIO_BUCKET, object_name)
    data = response.read()
    response.close()
    response.release_conn()
    return data

def upload_to_minio(data: bytes, object_name: str, content_type="application/octet-stream"):
    bytes_io = BytesIO(data)
    bytes_io.seek(0)
    client.put_object(
        bucket_name=MINIO_BUCKET,
        object_name=object_name,
        data=bytes_io,
        length=len(data),
        content_type=content_type
    )
    print(f"✅ Uploaded to MinIO: {object_name}")

# -----------------------------
# ETL Stage 1: RAW → BRONZE
# -----------------------------
def etl_raw_to_bronze():
    txt_files = list_files(RAW_FOLDER, suffix=".txt")
    processed_files = []
    total_lines = 0

    for file in txt_files:
        print(f"📥 Processing RAW file: {file}")
        raw_text = download_file(file).decode("utf-8")

        lines = [line.strip().lower() for line in raw_text.splitlines() if line.strip()]
        clean_text = "\n".join(lines)
        total_lines += len(lines)

        df = pd.DataFrame({
            "file": [file],
            "content": [clean_text]
        })

        parquet_buffer = BytesIO()
        df.to_parquet(parquet_buffer, index=False)
        parquet_buffer.seek(0)

        bronze_path = file.replace(RAW_FOLDER, BRONZE_FOLDER).replace(".txt", ".parquet")
        upload_to_minio(parquet_buffer.read(), bronze_path)
        processed_files.append(bronze_path)

    quality_metrics = {
        "total_files": len(txt_files),
        "processed_files": len(processed_files),
        "total_lines": total_lines,
        "avg_lines_per_file": total_lines / len(txt_files) if txt_files else 0
    }

    print(f"📊 RAW→BRONZE quality metrics: {quality_metrics}")
    return processed_files

# -----------------------------
# ETL Stage 2: BRONZE → SILVER
# -----------------------------
def etl_bronze_to_silver():
    parquet_files = list_files(BRONZE_FOLDER, suffix=".parquet")
    processed_files = []
    word_counts = []

    for file in parquet_files:
        print(f"🔄 Processing BRONZE file: {file}")

        parquet_data = download_file(file)

        with tempfile.NamedTemporaryFile(suffix=".parquet") as tmp_file:
            tmp_file.write(parquet_data)
            tmp_file.flush()

            con = duckdb.connect(database=':memory:')
            con.execute(f"CREATE TABLE bronze AS SELECT * FROM parquet_scan('{tmp_file.name}')")

            con.execute("""
                CREATE TABLE silver AS
                SELECT
                    file,
                    content,
                    array_length(string_split(content, ' ')) AS word_count
                FROM bronze
            """)

            df_silver = con.execute("SELECT * FROM silver").df()

            word_counts.extend(df_silver["word_count"].tolist())

            parquet_buffer = BytesIO()
            df_silver.to_parquet(parquet_buffer, index=False)
            parquet_buffer.seek(0)

            silver_path = file.replace(BRONZE_FOLDER, SILVER_FOLDER)
            upload_to_minio(parquet_buffer.read(), silver_path)
            processed_files.append(silver_path)

    processed_files.sort()

    avg_word_count = sum(word_counts) / len(word_counts) if word_counts else 0
    quality_metrics = {
        "total_files": len(parquet_files),
        "processed_files": len(processed_files),
        "avg_word_count": avg_word_count
    }

    print(f"📊 BRONZE→SILVER quality metrics: {quality_metrics}")
    return processed_files

# -----------------------------
# ETL Stage 3: SILVER → GOLD (Embeddings)
# -----------------------------
def etl_silver_to_gold():
    print("🟡 Starting SILVER → GOLD embedding process")

    model_name = "all-MiniLM-L6-v2"
    model = SentenceTransformer(model_name)

    chroma_client = chromadb.PersistentClient(path=CHROMA_DIR)
    collection = chroma_client.get_or_create_collection(name="rag_docs")

    parquet_files = list_files(SILVER_FOLDER, suffix=".parquet")
    processed_files = []
    total_chunks = 0

    for file in parquet_files:
        print(f"🔍 Embedding SILVER file: {file}")
        parquet_data = download_file(file)

        with tempfile.NamedTemporaryFile(suffix=".parquet") as tmp_file:
            tmp_file.write(parquet_data)
            tmp_file.flush()

            df = pd.read_parquet(tmp_file.name)

            for _, row in df.iterrows():
                text = row.get("content", "").strip()
                source = row.get("file", "unknown")

                if not text:
                    continue

                chunks = [text[i:i+512] for i in range(0, len(text), 512)]
                embeddings = model.encode(chunks).tolist()
                ids = [str(uuid.uuid4()) for _ in chunks]

                collection.add(
                    documents=chunks,
                    embeddings=embeddings,
                    ids=ids,
                    metadatas=[{"source": source}] * len(chunks)
                )
                total_chunks += len(chunks)

        print(f"✅ Embedded into GOLD: {file}")
        processed_files.append(file)

    processed_files.sort()

    quality_metrics = {
        "total_files": len(parquet_files),
        "processed_files": len(processed_files),
        "total_embedding_chunks": total_chunks,
        "avg_embedding_chunks_per_file": total_chunks / len(processed_files) if processed_files else 0,
    }

    lineage_data = {
        "stage": "silver_to_gold",
        "timestamp": datetime.utcnow().isoformat(),
        "file_count": len(parquet_files),
        "processed_files": processed_files,
        "quality_metrics": quality_metrics,
        "embedding_model": model_name,
    }

    # Upload lineage data JSON to MinIO under lineage folder
    try:
        lineage_json = json.dumps(lineage_data, indent=2).encode('utf-8')
        lineage_path = "lineage/silver_to_gold_lineage.json"
        upload_to_minio(lineage_json, lineage_path, content_type="application/json")
        print(f"✅ Lineage data saved to MinIO at {lineage_path}")
    except Exception as e:
        print(f"❌ Failed to upload lineage data to MinIO: {e}")

    print(f"🎉 GOLD embedding complete. Vector DB saved at `{CHROMA_DIR}`")
    return processed_files

# -----------------------------
# Data Quality Task
# -----------------------------

def convert_np_types(obj):
    if isinstance(obj, dict):
        return {k: convert_np_types(v) for k, v in obj.items()}
    elif isinstance(obj, list):
        return [convert_np_types(i) for i in obj]
    elif isinstance(obj, np.integer):
        return int(obj)
    elif isinstance(obj, np.floating):
        return float(obj)
    elif isinstance(obj, np.ndarray):
        return obj.tolist()
    else:
        return obj

def run_data_quality_task():
    parquet_files = list_files(SILVER_FOLDER, suffix=".parquet")
    dfs = []
    for file in parquet_files:
        parquet_data = download_file(file)
        with tempfile.NamedTemporaryFile(suffix=".parquet") as tmp_file:
            tmp_file.write(parquet_data)
            tmp_file.flush()
            df = pd.read_parquet(tmp_file.name)
            dfs.append(df)

    if dfs:
        combined_df = pd.concat(dfs, ignore_index=True)
    else:
        combined_df = pd.DataFrame()

    if combined_df.empty:
        print("⚠️ Combined dataframe is empty. Skipping data quality checks.")
        dq_results = {}
    else:
        dq_results = run_data_quality_checks(combined_df)
        print("🧪 Data Quality Report:\n", dq_results)

    # Convert numpy types to native python before JSON serialization
    try:
        sanitized_results = convert_np_types(dq_results)
        dq_json_bytes = json.dumps(sanitized_results, indent=2).encode('utf-8')
        dq_minio_path = "data_quality/dq_report.json"
        upload_to_minio(dq_json_bytes, dq_minio_path, content_type="application/json")
        print(f"✅ Data Quality report saved to MinIO at {dq_minio_path}")
    except Exception as e:
        print(f"❌ Failed to upload DQ report to MinIO: {e}")

    return dq_results


# -----------------------------
# Main ETL wrapper for import (optional)
# -----------------------------
def run_etl_pipeline():
    bronze_files = etl_raw_to_bronze()
    silver_files = etl_bronze_to_silver()
    gold_files = etl_silver_to_gold()

    dq_results = run_data_quality_task()

    return dq_results

# -----------------------------
# CLI entrypoint
# -----------------------------
if __name__ == "__main__":
    print("🚀 Running Full ETL Pipeline: RAW → BRONZE → SILVER → GOLD")
    dq_results = run_etl_pipeline()
    print(f"Pipeline finished. Data Quality Results:\n{dq_results}")
