def test_health(client):
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_post_reading_returns_201(client, sample_reading):
    response = client.post("/readings", json=sample_reading)
    assert response.status_code == 201


def test_post_reading_calls_db(client, mock_db, sample_reading):
    client.post("/readings", json=sample_reading)
    mock_db.upload_sensor_data.assert_called_once()


def test_post_reading_rejects_missing_device_id(client):
    response = client.post("/readings", json={"temperature": 22.5})
    assert response.status_code == 422


def test_get_readings_returns_200(client, mock_db):
    mock_db.read_sensor_data.return_value = []
    response = client.get("/readings")
    assert response.status_code == 200


def test_get_readings_passes_device_id_filter(client, mock_db):
    mock_db.read_sensor_data.return_value = []
    client.get("/readings?device_id=sensor-01")
    mock_db.read_sensor_data.assert_called_once_with(
        device_id="sensor-01", max_records=None
    )


def test_get_readings_passes_limit(client, mock_db):
    mock_db.read_sensor_data.return_value = []
    client.get("/readings?limit=10")
    mock_db.read_sensor_data.assert_called_once_with(device_id=None, max_records=10)


def test_get_readings_rejects_limit_zero(client):
    response = client.get("/readings?limit=0")
    assert response.status_code == 422


def test_get_stats_returns_200(client, mock_db):
    mock_db.read_sensor_data.return_value = []
    response = client.get("/readings/stats")
    assert response.status_code == 200


def test_export_returns_csv_content_type(client, mock_db):
    mock_db.read_sensor_data.return_value = []
    response = client.get("/export")
    assert "text/csv" in response.headers["content-type"]


def test_generate_report_404_when_no_data(client, mock_db, mock_minio):
    mock_db.read_sensor_data_by_time.return_value = []
    response = client.post("/reports/generate?hour=2024-01-15T14:00:00")
    assert response.status_code == 404


def test_list_reports_returns_200(client, mock_minio):
    mock_minio.list_reports.return_value = []
    response = client.get("/reports")
    assert response.status_code == 200


def test_get_report_404_when_not_found(client, mock_minio):
    mock_minio.get_report.side_effect = Exception("not found")
    response = client.get("/reports/nonexistent.csv")
    assert response.status_code == 404
