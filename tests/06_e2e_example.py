"""
Test End-to-End: flujo completo a través de RabbitMQ, MongoDB y MinIO
=====================================================================

Este test recorre el sistema de extremo a extremo:

    [POST /readings]  →  MongoDB  →  [GET /readings]
    [queue.publish()] →  RabbitMQ  →  [worker]  →  MongoDB  →  [GET /readings]
    [GET /readings/stats]  →  agregación en tiempo real
    [GET /export]          →  CSV de todos los datos
    [POST /reports/generate] →  MinIO  →  [GET /reports]  →  [GET /reports/{name}]

Es exactamente lo que NO pueden probar los tests unitarios ni los de integración,
porque el worker es un proceso separado que consume la cola de forma asíncrona,
y los reportes dependen de MinIO corriendo de verdad.

Por qué este test está al final de la pirámide:
  - Necesita 4 servicios levantados (MongoDB, RabbitMQ, MinIO, worker)
  - Tiene que esperar a que el worker procese mensajes (asíncrono)
  - Si cualquier servicio tarda más de lo normal, el test falla aunque el código esté bien
  - Tarda ~20s frente a los 0.06s de los unit tests

Ejecutar: pytest 06_e2e_example.py -v -s
"""

import os
import subprocess
import time
from pathlib import Path

import pytest
import requests
from dotenv import dotenv_values
from fastapi.testclient import TestClient
from pymongo import MongoClient

# ---------------------------------------------------------------------------
# Setup — las vars de entorno deben cargarse ANTES de importar sensorhub
# ---------------------------------------------------------------------------

_ROOT = Path(__file__).parent
TEST_ENV = dotenv_values(_ROOT / ".env.test")
os.environ.update(TEST_ENV)

from sensorhub.api import app  # noqa: E402
from sensorhub.queue import publish  # noqa: E402

MONGO_URI = (
    f"mongodb://{TEST_ENV['MONGO_USERNAME']}:{TEST_ENV['MONGO_ROOT_PASSWORD']}"
    f"@{TEST_ENV['MONGO_IP']}:{TEST_ENV['MONGO_PORT']}"
)
RABBITMQ_URL = TEST_ENV["RABBITMQ_URL"]
MINIO_URL = f"http://{TEST_ENV['MINIO_IP']}:{TEST_ENV['MINIO_PORT']}"


# ---------------------------------------------------------------------------
# Fixtures de infraestructura
# ---------------------------------------------------------------------------


@pytest.fixture(scope="session")
def docker_compose_file():
    return str(_ROOT / "docker-compose.e2e.yml")


@pytest.fixture(scope="session")
def docker_compose_project_name():
    return "sensorhub-e2e"


def _mongo_ok() -> bool:
    try:
        MongoClient(MONGO_URI, serverSelectionTimeoutMS=500).admin.command("ping")
        return True
    except Exception:
        return False


def _rabbitmq_ok() -> bool:
    try:
        import pika

        pika.BlockingConnection(pika.URLParameters(RABBITMQ_URL)).close()
        return True
    except Exception:
        return False


def _minio_ok() -> bool:
    try:
        r = requests.get(f"{MINIO_URL}/minio/health/live", timeout=1)
        return r.status_code == 200
    except Exception:
        return False


@pytest.fixture(scope="session")
def infraestructura(docker_services):
    """Espera a que MongoDB, RabbitMQ y MinIO estén listos."""
    docker_services.wait_until_responsive(check=_mongo_ok, timeout=60, pause=1)
    docker_services.wait_until_responsive(check=_rabbitmq_ok, timeout=60, pause=1)
    docker_services.wait_until_responsive(check=_minio_ok, timeout=60, pause=1)


@pytest.fixture(scope="session")
def worker(infraestructura):
    """
    Arranca el worker como subproceso — igual que en producción.
    Se para automáticamente al terminar la sesión de tests.
    """
    proceso = subprocess.Popen(
        ["uv", "run", "python", "-m", "sensorhub.worker"],
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )
    time.sleep(2)  # damos tiempo a que conecte con RabbitMQ
    yield proceso
    proceso.terminate()
    proceso.wait()


@pytest.fixture(scope="session")
def client(infraestructura):
    return TestClient(app)


@pytest.fixture(autouse=True)
def clean_db(infraestructura):
    """Limpia la colección antes de cada test para que sean independientes."""
    MongoClient(MONGO_URI)["sensorhub"]["sensor_data"].delete_many({})
    yield


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _esperar_lecturas(client, n: int, timeout: int = 15) -> list:
    """
    Hace polling a GET /readings hasta que haya al menos n documentos.

    Necesario porque publish() es asíncrono: el worker puede tardar segundos.
    """
    for _ in range(timeout):
        datos = client.get("/readings").json()
        if len(datos) >= n:
            return datos
        time.sleep(1)
    raise TimeoutError(
        f"Solo llegaron {len(client.get('/readings').json())} de {n} lecturas en {timeout}s"
    )


# ---------------------------------------------------------------------------
# Tests E2E
# ---------------------------------------------------------------------------


def test_post_directo_persiste_y_aparece_en_get(client, infraestructura):
    """
    El camino síncrono: POST /readings → MongoDB → GET /readings.
    Si falla aquí el problema está en la API o en Mongo, no en el worker.
    """
    payload = {
        "device_id": "sala-a",
        "location": "planta-1",
        "temperature": 22.0,
        "humidity": 50.0,
        "co2": 700,
        "timestamp": "2024-06-01T10:00:00",
    }

    r = client.post("/readings", json=payload)
    assert r.status_code == 201

    datos = client.get("/readings").json()
    assert len(datos) == 1
    assert datos[0]["device_id"] == "sala-a"
    assert datos[0]["temperature"] == 22.0


def test_flujo_cola_llega_a_mongodb_y_a_api(client, worker):
    """
    El camino asíncrono: publish() → RabbitMQ → worker → MongoDB → GET /readings.
    Prueba que el worker consume la cola y persiste el documento correctamente.
    """
    publish(
        {
            "device_id": "sala-b",
            "location": "planta-2",
            "temperature": 19.0,
            "humidity": 45.0,
            "co2": 850,
            "timestamp": "2024-06-01T10:05:00",
        }
    )

    datos = _esperar_lecturas(client, n=1)
    lectura = next(r for r in datos if r["device_id"] == "sala-b")
    assert lectura["temperature"] == 19.0
    assert lectura["co2"] == 850


def test_worker_marca_source_queue(client, worker):
    """
    El worker añade source="queue" a cada documento.
    Solo verificable en E2E — el unit test mockea el worker.
    """
    publish(
        {
            "device_id": "sala-c",
            "location": "planta-1",
            "temperature": 21.0,
            "humidity": 55.0,
            "co2": 600,
        }
    )

    datos = _esperar_lecturas(client, n=1)
    lectura = next(r for r in datos if r["device_id"] == "sala-c")
    assert lectura["source"] == "queue"


def test_flujo_completo_api_cola_stats_export_reporte(client, worker):
    """
    El test gordo: todos los servicios, todos los endpoints.

        POST /readings × 2   (camino directo, dos dispositivos)
        publish() × 2        (camino cola, mismo timestamp para el reporte)
        GET /readings        → 4 documentos en total
        GET /readings?device_id=sala-a  → solo los de sala-a
        GET /readings/stats  → media y max_co2 por dispositivo
        GET /export          → CSV con cabecera y filas
        POST /reports/generate → sube reporte a MinIO
        GET /reports         → lista el reporte recién generado
        GET /reports/{name}  → descarga el CSV del reporte
    """
    HORA = "2024-06-01T10:00:00"

    # --- Insertar datos por los dos caminos ---
    client.post(
        "/readings",
        json={
            "device_id": "sala-a",
            "location": "planta-1",
            "temperature": 20.0,
            "humidity": 50.0,
            "co2": 700,
            "timestamp": HORA,
        },
    )
    client.post(
        "/readings",
        json={
            "device_id": "sala-a",
            "location": "planta-1",
            "temperature": 24.0,
            "humidity": 52.0,
            "co2": 750,
            "timestamp": "2024-06-01T10:30:00",
        },
    )

    publish(
        {
            "device_id": "sala-b",
            "location": "planta-2",
            "temperature": 18.0,
            "humidity": 60.0,
            "co2": 900,
            "timestamp": HORA,
        }
    )
    publish(
        {
            "device_id": "sala-b",
            "location": "planta-2",
            "temperature": 22.0,
            "humidity": 58.0,
            "co2": 950,
            "timestamp": "2024-06-01T10:45:00",
        }
    )

    # Esperamos a que el worker procese las dos publicaciones de cola
    todos = _esperar_lecturas(client, n=4)
    assert len(todos) == 4

    # --- Filtro por device_id ---
    r = client.get("/readings", params={"device_id": "sala-a"})
    sala_a = r.json()
    assert len(sala_a) == 2
    assert all(d["device_id"] == "sala-a" for d in sala_a)

    # --- Stats: media y max_co2 ---
    stats = client.get("/readings/stats").json()
    assert len(stats) == 2
    by_device = {s["device_id"]: s for s in stats}

    assert by_device["sala-a"]["avg_temperature"] == pytest.approx(22.0)
    assert by_device["sala-a"]["max_co2"] == 750
    assert by_device["sala-b"]["max_co2"] == 950

    # --- Export CSV ---
    r = client.get("/export")
    assert r.status_code == 200
    assert "text/csv" in r.headers["content-type"]
    lineas = r.content.decode().strip().splitlines()
    assert lineas[0].startswith("device_id")  # cabecera
    assert len(lineas) == 5  # 1 cabecera + 4 filas

    # --- Generar reporte y subirlo a MinIO ---
    r = client.post("/reports/generate", params={"hour": HORA})
    assert r.status_code == 200
    body = r.json()
    assert "object_key" in body
    assert "link" in body
    object_key = body["object_key"]

    # --- Listar reportes ---
    r = client.get("/reports")
    assert r.status_code == 200
    lista = r.json()
    nombres = [rep["name"] for rep in lista]
    assert object_key in nombres

    # --- Descargar el reporte ---
    r = client.get(f"/reports/{object_key}")
    assert r.status_code == 200
    assert "text/csv" in r.headers["content-type"]

    lineas = r.content.decode().strip().splitlines()
    # Un dispositivo por fila → 1 cabecera + 2 filas de datos
    assert len(lineas) == 3

    cabecera = lineas[0].split(",")
    assert cabecera == [
        "device_id",
        "location",
        "count",
        "avg_temperature",
        "avg_humidity",
        "avg_co2",
        "max_co2",
    ]

    # Parseamos las filas en un dict para no depender del orden de las filas
    reporte = {}
    for fila in lineas[1:]:
        cols = fila.split(",")
        reporte[cols[0]] = dict(zip(cabecera, cols))

    # sala-a: (20+24)/2 = 22°, co2 max 750
    assert float(reporte["sala-a"]["avg_temperature"]) == pytest.approx(22.0)
    assert float(reporte["sala-a"]["avg_humidity"]) == pytest.approx(51.0)
    assert float(reporte["sala-a"]["avg_co2"]) == pytest.approx(725.0)
    assert float(reporte["sala-a"]["max_co2"]) == pytest.approx(750.0)
    assert int(reporte["sala-a"]["count"]) == 2

    # sala-b: (18+22)/2 = 20°, co2 max 950
    assert float(reporte["sala-b"]["avg_temperature"]) == pytest.approx(20.0)
    assert float(reporte["sala-b"]["avg_humidity"]) == pytest.approx(59.0)
    assert float(reporte["sala-b"]["avg_co2"]) == pytest.approx(925.0)
    assert float(reporte["sala-b"]["max_co2"]) == pytest.approx(950.0)
    assert int(reporte["sala-b"]["count"]) == 2
