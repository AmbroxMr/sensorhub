import pytest
from unittest.mock import MagicMock

from sensorhub.readings import compute_stats


# Fixture: pytest crea un MagicMock nuevo antes de cada test.
# Sin esto, tendríamos que repetir MagicMock() en cada función
# y, peor, el estado acumulado de un test (llamadas registradas, return_value)
# podría contaminar el siguiente.
@pytest.fixture
def mock_db():
    return MagicMock()


def test_retorna_lista_vacia_si_no_hay_datos(mock_db):
    mock_db.read_sensor_data.return_value = []

    resultado = compute_stats(mock_db)

    assert resultado == []


def test_agrupa_por_device_id(mock_db):
    mock_db.read_sensor_data.return_value = [
        {
            "device_id": "s1",
            "location": "office",
            "temperature": 20.0,
            "humidity": 50.0,
            "co2": 400.0,
        },
        {
            "device_id": "s2",
            "location": "warehouse",
            "temperature": 18.0,
            "humidity": 60.0,
            "co2": 350.0,
        },
    ]

    resultado = compute_stats(mock_db)

    device_ids = {row["device_id"] for row in resultado}
    assert device_ids == {"s1", "s2"}


def test_calcula_media_temperatura(mock_db):
    mock_db.read_sensor_data.return_value = [
        {
            "device_id": "s1",
            "location": "office",
            "temperature": 20.0,
            "humidity": 50.0,
            "co2": 400.0,
        },
        {
            "device_id": "s1",
            "location": "office",
            "temperature": 24.0,
            "humidity": 50.0,
            "co2": 400.0,
        },
    ]

    resultado = compute_stats(mock_db)

    assert resultado[0]["avg_temperature"] == 22.0


def test_calcula_max_co2(mock_db):
    mock_db.read_sensor_data.return_value = [
        {
            "device_id": "s1",
            "location": "office",
            "temperature": 21.0,
            "humidity": 50.0,
            "co2": 400.0,
        },
        {
            "device_id": "s1",
            "location": "office",
            "temperature": 21.0,
            "humidity": 50.0,
            "co2": 800.0,
        },
        {
            "device_id": "s1",
            "location": "office",
            "temperature": 21.0,
            "humidity": 50.0,
            "co2": 600.0,
        },
    ]

    resultado = compute_stats(mock_db)

    assert resultado[0]["max_co2"] == 800.0


def test_count_por_dispositivo(mock_db):
    mock_db.read_sensor_data.return_value = [
        {
            "device_id": "s1",
            "location": "office",
            "temperature": 21.0,
            "humidity": 50.0,
            "co2": 400.0,
        },
        {
            "device_id": "s1",
            "location": "office",
            "temperature": 22.0,
            "humidity": 50.0,
            "co2": 410.0,
        },
        {
            "device_id": "s1",
            "location": "office",
            "temperature": 23.0,
            "humidity": 50.0,
            "co2": 420.0,
        },
    ]

    resultado = compute_stats(mock_db)

    assert resultado[0]["count"] == 3


def test_llama_a_la_base_de_datos_exactamente_una_vez(mock_db):
    mock_db.read_sensor_data.return_value = []

    compute_stats(mock_db)

    mock_db.read_sensor_data.assert_called_once()
