import io

from minio import Minio

from sensorhub.config import Settings

settings = Settings()  # type: ignore[call-arg]


class MinioClient:
    def __init__(self):
        self.client = Minio(
            f"{settings.minio_ip}:{settings.minio_port}",
            access_key=settings.minio_access_key,
            secret_key=settings.minio_secret_key,
            secure=False,
        )
        self.bucket = settings.minio_bucket
        self._ensure_bucket()

    def _ensure_bucket(self):
        if not self.client.bucket_exists(self.bucket):
            self.client.make_bucket(self.bucket)

    def upload_csv(self, object_name: str, csv_bytes: bytes) -> str:
        data = io.BytesIO(csv_bytes)
        self.client.put_object(
            self.bucket,
            object_name,
            data,
            length=len(csv_bytes),
            content_type="text/csv",
        )
        return object_name

    def list_reports(self) -> list[dict]:
        objects = self.client.list_objects(self.bucket, recursive=True)
        return [
            {
                "name": obj.object_name,
                "size": obj.size,
                "last_modified": obj.last_modified.isoformat() if obj.last_modified else None,
            }
            for obj in objects
        ]

    def get_report(self, report_name: str) -> bytes:
        response = self.client.get_object(self.bucket, report_name)
        try:
            return response.read()
        finally:
            response.close()
            response.release_conn()
