import pytest


@pytest.fixture
def sample_reading() -> dict:
    return {
        "device_id": "sensor-01",
        "location": "office",
        "temperature": 22.5,
        "humidity": 55.0,
        "co2": 420.0,
    }


@pytest.fixture
def sample_readings() -> list[dict]:
    return [
        {
            "device_id": "sensor-01",
            "location": "office",
            "temperature": 20.0,
            "humidity": 50.0,
            "co2": 400.0,
        },
        {
            "device_id": "sensor-01",
            "location": "office",
            "temperature": 24.0,
            "humidity": 60.0,
            "co2": 500.0,
        },
        {
            "device_id": "sensor-02",
            "location": "warehouse",
            "temperature": 18.0,
            "humidity": 70.0,
            "co2": 350.0,
        },
    ]
