"""
Storage Tools: Interacts with MinIO (S3-compatible object storage) or local fallback.
Satisfies Deliverable 1 (Tools/Function Calling).
"""

import os
import io
import logging
from typing import Optional, Dict, Any

logger = logging.getLogger("StorageTools")


def get_minio_client():
    """Initializes MinIO client if configured."""
    endpoint = os.getenv("MINIO_ENDPOINT", "localhost:9000")
    access_key = os.getenv("MINIO_ACCESS_KEY", "minioadmin")
    secret_key = os.getenv("MINIO_SECRET_KEY", "minioadmin")
    secure = os.getenv("MINIO_SECURE", "false").lower() == "true"

    try:
        from minio import Minio
        client = Minio(endpoint, access_key=access_key, secret_key=secret_key, secure=secure)
        return client
    except Exception as e:
        logger.warning(f"Could not initialize MinIO client: {e}")
        return None


def fetch_contract_from_minio(bucket_name: str, object_name: str, local_save_path: Optional[str] = None) -> bytes:
    """
    Downloads contract PDF from MinIO bucket.
    If MinIO is unavailable, checks local data/contracts directory.
    """
    client = get_minio_client()
    if client:
        try:
            response = client.get_object(bucket_name, object_name)
            data = response.read()
            response.close()
            response.release_conn()
            logger.info(f"Successfully fetched {object_name} from MinIO bucket {bucket_name}")
            if local_save_path:
                os.makedirs(os.path.dirname(local_save_path), exist_ok=True)
                with open(local_save_path, "wb") as f:
                    f.write(data)
            return data
        except Exception as e:
            logger.warning(f"Failed to fetch {object_name} from MinIO ({e}). Checking local storage...")

    # Fallback to local filesystem if MinIO fails
    possible_paths = [
        object_name,
        os.path.join("data", "contracts", object_name),
        os.path.join("data", object_name)
    ]
    for path in possible_paths:
        if os.path.exists(path):
            with open(path, "rb") as f:
                logger.info(f"Fetched {object_name} from local path: {path}")
                return f.read()

    raise FileNotFoundError(f"Contract file '{object_name}' not found in MinIO bucket '{bucket_name}' or local storage.")


def upload_contract_to_minio(bucket_name: str, object_name: str, file_data: bytes) -> str:
    """
    Uploads contract PDF to MinIO bucket.
    """
    client = get_minio_client()
    if client:
        try:
            if not client.bucket_exists(bucket_name):
                client.make_bucket(bucket_name)
            
            client.put_object(
                bucket_name,
                object_name,
                io.BytesIO(file_data),
                length=len(file_data),
                content_type="application/pdf"
            )
            logger.info(f"Uploaded {object_name} to MinIO bucket {bucket_name}")
            return f"s3://{bucket_name}/{object_name}"
        except Exception as e:
            logger.warning(f"Could not upload to MinIO: {e}. Saving locally.")

    # Local fallback save
    local_dir = os.path.join("data", "contracts")
    os.makedirs(local_dir, exist_ok=True)
    local_path = os.path.join(local_dir, object_name)
    with open(local_path, "wb") as f:
        f.write(file_data)
    return local_path
