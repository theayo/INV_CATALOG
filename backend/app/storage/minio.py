from io import BytesIO

from minio import Minio
from urllib3 import PoolManager, Timeout

from app.config import Settings


class ObjectStorage:
    def __init__(self, settings: Settings):
        self.bucket = settings.minio_bucket
        self.client = Minio(
            settings.minio_endpoint,
            access_key=settings.minio_access_key,
            secret_key=settings.minio_secret_key.get_secret_value(),
            secure=settings.minio_secure,
            http_client=PoolManager(timeout=Timeout(connect=5, read=30), retries=False, maxsize=4),
        )

    def put(self, key: str, photo: bytes, content_type: str) -> None:
        self.client.put_object(
            self.bucket, key, BytesIO(photo), len(photo), content_type=content_type
        )

    def remove(self, key: str) -> None:
        self.client.remove_object(self.bucket, key)

    def open(self, key: str):
        return self.client.get_object(self.bucket, key)

    def ensure_bucket(self) -> None:
        if not self.client.bucket_exists(self.bucket):
            self.client.make_bucket(self.bucket)


if __name__ == "__main__":
    from app.config import get_settings

    ObjectStorage(get_settings()).ensure_bucket()
    print("MinIO bucket is ready")
