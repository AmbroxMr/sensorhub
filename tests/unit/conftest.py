import os
from unittest.mock import MagicMock, patch

import pytest
from fastapi.testclient import TestClient

# Env vars dummy para que Settings() no falle al importar sensorhub
os.environ.setdefault("MONGO_USERNAME", "test")
os.environ.setdefault("MONGO_ROOT_PASSWORD", "test")
os.environ.setdefault("MONGO_PORT", "27017")
os.environ.setdefault("MONGO_IP", "localhost")
os.environ.setdefault("MONGO_DB", "sensorhub")
os.environ.setdefault("MINIO_ACCESS_KEY", "test")
os.environ.setdefault("MINIO_SECRET_KEY", "test")
os.environ.setdefault("MINIO_PORT", "9000")
os.environ.setdefault("MINIO_IP", "localhost")
os.environ.setdefault("MINIO_BUCKET", "test")
os.environ.setdefault("API_PORT", "8000")

from sensorhub.api import app, get_db  # noqa: E402


@pytest.fixture
def mock_db():
    return MagicMock()


@pytest.fixture
def mock_minio():
    with patch("sensorhub.reports.MinioClient") as mock_cls:
        instance = MagicMock()
        mock_cls.return_value = instance
        yield instance


@pytest.fixture
def client(mock_db):
    app.dependency_overrides[get_db] = lambda: mock_db
    yield TestClient(app)
    app.dependency_overrides.clear()
