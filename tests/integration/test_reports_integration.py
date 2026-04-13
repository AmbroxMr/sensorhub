from unittest.mock import patch


HOUR = "2024-01-15T14:00:00"

READING = {
    "device_id": "sensor-01",
    "location": "office",
    "temperature": 22.5,
    "humidity": 55.0,
    "co2": 420.0,
    "timestamp": "2024-01-15T14:30:00",
}


def test_generate_retorna_404_sin_datos(client):
    response = client.post(f"/reports/generate?hour={HOUR}")
    assert response.status_code == 404


def test_generate_retorna_object_key_y_link(client):
    client.post("/readings", json=READING)

    with patch("sensorhub.reports.MinioClient") as mock_cls:
        mock_cls.return_value.upload_csv.return_value = None
        response = client.post(f"/reports/generate?hour={HOUR}")

    assert response.status_code == 200
    assert "object_key" in response.json()
    assert "link" in response.json()


def test_generate_object_key_contiene_fecha(client):
    client.post("/readings", json=READING)

    with patch("sensorhub.reports.MinioClient"):
        response = client.post(f"/reports/generate?hour={HOUR}")

    assert response.json()["object_key"] == "2024-01-15/1400.csv"


def test_list_reports_retorna_lista(client):
    with patch("sensorhub.reports.MinioClient") as mock_cls:
        mock_cls.return_value.list_reports.return_value = []
        response = client.get("/reports")
    assert response.status_code == 200
    assert isinstance(response.json(), list)


def test_get_report_retorna_csv(client):
    with patch("sensorhub.reports.MinioClient") as mock_cls:
        mock_cls.return_value.get_report.return_value = b"device_id\nsensor-01\n"
        response = client.get("/reports/2024-01-15/1400.csv")
    assert response.status_code == 200
    assert "text/csv" in response.headers["content-type"]


def test_get_report_404_si_no_existe(client):
    with patch("sensorhub.reports.MinioClient") as mock_cls:
        mock_cls.return_value.get_report.side_effect = Exception("not found")
        response = client.get("/reports/nonexistent.csv")
    assert response.status_code == 404
