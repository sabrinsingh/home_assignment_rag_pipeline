import os
import json
from datetime import datetime
from io import BytesIO
from typing import List, Optional, Dict, Any
from minio import Minio
import requests


LINEAGE_PREFIX = "lineage"


def get_minio_client() -> tuple[Minio, str]:
    """
    Initialize and return a MinIO client and bucket name from environment variables.
    Creates bucket if it doesn't exist.
    """
    url = os.getenv("MINIO_URL", "localhost:9000")
    access_key = os.getenv("MINIO_ACCESS_KEY", "minioadmin")
    secret_key = os.getenv("MINIO_SECRET_KEY", "minioadmin")
    bucket = os.getenv("MINIO_BUCKET", "mydata")

    client = Minio(url, access_key=access_key, secret_key=secret_key, secure=False)
    if not client.bucket_exists(bucket):
        client.make_bucket(bucket)

    return client, bucket


def upload_to_minio(client: Minio, data: bytes, object_name: str, content_type: str = "application/octet-stream") -> None:
    """
    Upload bytes data to MinIO bucket with specified object name.
    """
    client.put_object(
        bucket_name=os.getenv("MINIO_BUCKET", "mydata"),
        object_name=object_name,
        data=BytesIO(data),
        length=len(data),
        content_type=content_type,
    )


def emit_lineage(client: Minio, stage: str, processed_files: List[str], quality_metrics: Dict[str, Any], extra: Optional[Dict] = None) -> None:
    """
    Emit data lineage JSON file to MinIO for a given ETL stage.
    """
    lineage_data = extra if extra else {
        "stage": stage,
        "timestamp": datetime.utcnow().isoformat(),
        "file_count": len(processed_files),
        "processed_files": processed_files,
        "quality_metrics": quality_metrics,
    }

    lineage_json = json.dumps(lineage_data, indent=2)
    timestamp = datetime.utcnow().strftime("%Y%m%dT%H%M%SZ")
    object_name = f"{LINEAGE_PREFIX}/{stage}_{timestamp}.json"

    upload_to_minio(client, lineage_json.encode("utf-8"), object_name, content_type="application/json")

    print(f"✅ Lineage for stage '{stage}' uploaded to MinIO as '{object_name}'")


def safe_get(url: str, headers: Optional[dict] = None, retries: int = 3, timeout: int = 10) -> Optional["requests.Response"]:
    """
    Perform HTTP GET request with retries, returns Response or None if failed.
    """
    import requests
    from requests.exceptions import RequestException

    for attempt in range(1, retries + 1):
        try:
            response = requests.get(url, headers=headers, timeout=timeout)
            if response.status_code == 200:
                return response
            else:
                print(f"⚠️ HTTP {response.status_code} for {url}")
        except RequestException as e:
            print(f"❌ Request attempt {attempt} failed for {url}: {e}")
    return None
