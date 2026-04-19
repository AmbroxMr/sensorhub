import os

import pytest
from dotenv import dotenv_values
from fastapi.testclient import TestClient
from pymongo import MongoClient

TEST_ENV = dotenv_values(".env.test")
os.environ.update(TEST_ENV)

from sensorhub.api import app  # noqa: E402


MONGO_URI = (
    f"mongodb://{TEST_ENV['MONGO_USERNAME']}:{TEST_ENV['MONGO_ROOT_PASSWORD']}"
    f"@{TEST_ENV['MONGO_IP']}:{TEST_ENV['MONGO_PORT']}"
)


@pytest.fixture(scope="session")
def docker_compose_file():
    return "docker-compose.test.yml"


@pytest.fixture(scope="session")
def docker_compose_project_name():
    return "sensorhub-test"


def _mongo_ok() -> bool:
    try:
        MongoClient(MONGO_URI, serverSelectionTimeoutMS=500).admin.command("ping")
        return True
    except Exception:
        return False


@pytest.fixture(scope="session")
def client(docker_services):
    docker_services.wait_until_responsive(check=_mongo_ok, timeout=60, pause=1)
    return TestClient(app)


@pytest.fixture(autouse=True)
def clean_db(client):
    MongoClient(MONGO_URI)["sensorhub"]["sensor_data"].delete_many({})
    yield


# ---------------------------------------------------------------------------

READING = {
    "device_id": "sensor-01",
    "location": "office",
    "temperature": 22.5,
    "humidity": 55.0,
    "co2": 420.0,
}


def test_reading_se_guarda_en_mongo(client):
    client.post("/readings", json=READING)

    response = client.get("/readings")

    assert len(response.json()) == 1
    assert response.json()[0]["temperature"] == 22.5


def test_base_de_datos_vacia_entre_tests(client):
    response = client.get("/readings")

    assert response.json() == []
