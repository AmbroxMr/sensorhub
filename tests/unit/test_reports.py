import pytest
from fastapi import HTTPException
from unittest.mock import MagicMock, patch

from sensorhub.reports import generate


def test_generate_lanza_404_sin_datos():
    mock_db = MagicMock()
    mock_db.read_sensor_data_by_time.return_value = []
    with patch("sensorhub.reports.MinioClient"):
        with pytest.raises(HTTPException) as exc:
            generate(mock_db, hour="2024-01-15T14:00:00")
    assert exc.value.status_code == 404


def test_generate_ventana_de_hora_correcta():
    mock_db = MagicMock()
    mock_db.read_sensor_data_by_time.return_value = []
    with patch("sensorhub.reports.MinioClient"):
        with pytest.raises(HTTPException):
            generate(mock_db, hour="2024-01-15T14:30:00")
    call_args = mock_db.read_sensor_data_by_time.call_args
    start, end = call_args[0]
    assert "14:00:00" in start
    assert "14:59:59" in end


def test_generate_retorna_object_key_y_link():
    mock_db = MagicMock()
    mock_db.read_sensor_data_by_time.return_value = [
        {
            "device_id": "s1",
            "location": "office",
            "temperature": 22.0,
            "humidity": 55.0,
            "co2": 400.0,
        }
    ]
    with patch("sensorhub.reports.MinioClient") as mock_cls:
        mock_cls.return_value.upload_csv.return_value = None
        result = generate(mock_db, hour="2024-01-15T14:00:00")
    assert "object_key" in result
    assert "link" in result


def test_generate_llama_a_minio_upload():
    mock_db = MagicMock()
    mock_db.read_sensor_data_by_time.return_value = [
        {
            "device_id": "s1",
            "location": "office",
            "temperature": 22.0,
            "humidity": 55.0,
            "co2": 400.0,
        }
    ]
    with patch("sensorhub.reports.MinioClient") as mock_cls:
        mock_instance = MagicMock()
        mock_cls.return_value = mock_instance
        generate(mock_db, hour="2024-01-15T14:00:00")
    mock_instance.upload_csv.assert_called_once()


def test_generate_object_key_contiene_fecha_y_hora():
    mock_db = MagicMock()
    mock_db.read_sensor_data_by_time.return_value = [
        {
            "device_id": "s1",
            "location": "office",
            "temperature": 22.0,
            "humidity": 55.0,
            "co2": 400.0,
        }
    ]
    with patch("sensorhub.reports.MinioClient"):
        result = generate(mock_db, hour="2024-01-15T14:00:00")
    assert result["object_key"] == "2024-01-15/1400.csv"
