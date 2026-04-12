from unittest.mock import MagicMock

from fastapi.responses import StreamingResponse

from sensorhub.readings import compute_stats, export_csv, list_readings


def test_list_readings_returns_empty_when_no_data():
    mock_db = MagicMock()
    mock_db.read_sensor_data.return_value = []
    assert list_readings(mock_db) == []


def test_list_readings_serializes_object_id():
    from bson import ObjectId

    mock_db = MagicMock()
    mock_db.read_sensor_data.return_value = [
        {"_id": ObjectId(), "device_id": "sensor-01", "temperature": 22.5}
    ]
    result = list_readings(mock_db)
    assert isinstance(result[0]["_id"], str)


def test_list_readings_passes_device_id_filter():
    mock_db = MagicMock()
    mock_db.read_sensor_data.return_value = []
    list_readings(mock_db, device_id="sensor-01")
    mock_db.read_sensor_data.assert_called_once_with(
        device_id="sensor-01", max_records=None
    )


def test_list_readings_passes_limit():
    mock_db = MagicMock()
    mock_db.read_sensor_data.return_value = []
    list_readings(mock_db, limit=5)
    mock_db.read_sensor_data.assert_called_once_with(device_id=None, max_records=5)


def test_compute_stats_returns_empty_when_no_data():
    mock_db = MagicMock()
    mock_db.read_sensor_data.return_value = []
    assert compute_stats(mock_db) == []


def test_compute_stats_groups_by_device_id(sample_readings):
    mock_db = MagicMock()
    mock_db.read_sensor_data.return_value = sample_readings
    result = compute_stats(mock_db)
    device_ids = {row["device_id"] for row in result}
    assert device_ids == {"sensor-01", "sensor-02"}


def test_compute_stats_calculates_average_temperature(sample_readings):
    mock_db = MagicMock()
    mock_db.read_sensor_data.return_value = sample_readings
    result = compute_stats(mock_db)
    sensor01 = next(r for r in result if r["device_id"] == "sensor-01")
    assert sensor01["avg_temperature"] == 22.0


def test_compute_stats_calculates_max_co2(sample_readings):
    mock_db = MagicMock()
    mock_db.read_sensor_data.return_value = sample_readings
    result = compute_stats(mock_db)
    sensor01 = next(r for r in result if r["device_id"] == "sensor-01")
    assert sensor01["max_co2"] == 500.0


def test_compute_stats_count_per_device(sample_readings):
    mock_db = MagicMock()
    mock_db.read_sensor_data.return_value = sample_readings
    result = compute_stats(mock_db)
    sensor01 = next(r for r in result if r["device_id"] == "sensor-01")
    assert sensor01["count"] == 2


def test_compute_stats_calls_db_once(sample_readings):
    mock_db = MagicMock()
    mock_db.read_sensor_data.return_value = sample_readings
    compute_stats(mock_db)
    mock_db.read_sensor_data.assert_called_once()


def test_export_csv_returns_streaming_response():
    mock_db = MagicMock()
    mock_db.read_sensor_data.return_value = [
        {
            "device_id": "sensor-01",
            "location": "office",
            "temperature": 22.5,
            "humidity": 55.0,
            "co2": 420.0,
        }
    ]
    result = export_csv(mock_db)
    assert isinstance(result, StreamingResponse)


def test_export_csv_content_type_is_csv():
    mock_db = MagicMock()
    mock_db.read_sensor_data.return_value = []
    result = export_csv(mock_db)
    assert result.media_type == "text/csv"
