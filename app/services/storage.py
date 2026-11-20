from __future__ import annotations
import io
from pathlib import Path
from app.config import settings

def store_ifc_bytes(revision_id: str, filename: str, data: bytes) -> str:
    object_key = f"{revision_id}/{Path(filename).name}"
    if settings.minio_endpoint:
        try:
            from minio import Minio
            ep = settings.minio_endpoint.replace("http://", "").replace("https://", "")
            client = Minio(ep, access_key=settings.minio_access_key, secret_key=settings.minio_secret_key, secure=settings.minio_endpoint.startswith("https://"))
            if not client.bucket_exists(settings.minio_bucket):
                client.make_bucket(settings.minio_bucket)
            client.put_object(settings.minio_bucket, object_key, io.BytesIO(data), length=len(data))
            return f"s3://{settings.minio_bucket}/{object_key}"
        except Exception:
            pass
    target = Path(settings.local_storage_dir) / object_key
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_bytes(data)
    return str(target.resolve())
