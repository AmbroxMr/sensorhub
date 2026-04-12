from datetime import datetime

from sensorhub.worker import _parse_document


def test_parse_document_extrae_todos_los_campos():
    msg = {
        "device_id": "s1",
        "location": "office",
        "temperature": 22.5,
        "humidity": 55.0,
        "co2": 420,
        "timestamp": "2024-01-15T14:00:00",
    }
    result = _parse_document(msg)
    assert result["device_id"] == "s1"
    assert result["location"] == "office"
    assert "timestamp" in result
    assert "source" in result


def test_parse_document_convierte_temperature_a_float():
    msg = {
        "device_id": "s1",
        "location": "office",
        "temperature": "22",
        "humidity": "55",
        "co2": "400",
        "timestamp": "2024-01-15T14:00:00",
    }
    result = _parse_document(msg)
    assert isinstance(result["temperature"], float)
    assert result["temperature"] == 22.0


def test_parse_document_convierte_co2_a_int():
    msg = {
        "device_id": "s1",
        "location": "office",
        "temperature": "22",
        "humidity": "55",
        "co2": "420",
        "timestamp": "2024-01-15T14:00:00",
    }
    result = _parse_document(msg)
    assert isinstance(result["co2"], int)
    assert result["co2"] == 420


def test_parse_document_parsea_timestamp_iso():
    msg = {
        "device_id": "s1",
        "location": "office",
        "temperature": 22.0,
        "humidity": 55.0,
        "co2": 400,
        "timestamp": "2024-01-15T14:30:00",
    }
    result = _parse_document(msg)
    assert isinstance(result["timestamp"], datetime)


def test_parse_document_usa_utc_cuando_no_hay_timestamp():
    msg = {
        "device_id": "s1",
        "location": "office",
        "temperature": 22.0,
        "humidity": 55.0,
        "co2": 400,
    }
    result = _parse_document(msg)
    assert isinstance(result["timestamp"], datetime)


def test_parse_document_marca_source_como_queue():
    msg = {
        "device_id": "s1",
        "location": "office",
        "temperature": 22.0,
        "humidity": 55.0,
        "co2": 400,
    }
    result = _parse_document(msg)
    assert result["source"] == "queue"
