def test_health(client):
    assert client.get("/health").json() == {"status": "ok"}


def test_post_reading_persiste_en_mongodb(client, sample_reading):
    client.post("/readings", json=sample_reading)

    datos = client.get("/readings").json()

    assert len(datos) == 1
    assert datos[0]["device_id"] == "sensor-01"
    assert datos[0]["temperature"] == 22.5


def test_post_reading_retorna_mensaje(client, sample_reading):
    response = client.post("/readings", json=sample_reading)
    assert "message" in response.json()


def test_get_readings_vacio_inicialmente(client):
    assert client.get("/readings").json() == []


def test_get_readings_devuelve_todas_las_lecturas(client, sample_reading):
    client.post("/readings", json={**sample_reading, "device_id": "sensor-01"})
    client.post("/readings", json={**sample_reading, "device_id": "sensor-02"})

    assert len(client.get("/readings").json()) == 2


def test_get_readings_filtra_por_device_id(client, sample_reading):
    client.post("/readings", json={**sample_reading, "device_id": "sensor-01"})
    client.post("/readings", json={**sample_reading, "device_id": "sensor-02"})

    datos = client.get("/readings?device_id=sensor-01").json()

    assert len(datos) == 1
    assert datos[0]["device_id"] == "sensor-01"


def test_get_readings_respeta_limit(client, sample_reading):
    for i in range(5):
        client.post("/readings", json={**sample_reading, "device_id": f"sensor-0{i}"})

    assert len(client.get("/readings?limit=3").json()) == 3


def test_get_stats_vacio_sin_datos(client):
    assert client.get("/readings/stats").json() == []


def test_get_stats_calcula_media_real(client, sample_reading):
    client.post("/readings", json={**sample_reading, "temperature": 20.0})
    client.post("/readings", json={**sample_reading, "temperature": 24.0})

    stats = client.get("/readings/stats").json()

    assert stats[0]["avg_temperature"] == 22.0


def test_get_stats_agrupa_por_device(client, sample_readings):
    for r in sample_readings:
        client.post("/readings", json=r)

    stats = client.get("/readings/stats").json()
    device_ids = {s["device_id"] for s in stats}

    assert device_ids == {"sensor-01", "sensor-02"}


def test_export_csv_content_type(client, sample_reading):
    client.post("/readings", json=sample_reading)
    response = client.get("/export")
    assert "text/csv" in response.headers["content-type"]


def test_export_csv_contiene_device_id(client, sample_reading):
    client.post("/readings", json=sample_reading)
    assert "sensor-01" in client.get("/export").text


def test_post_reading_payload_invalido_retorna_422(client):
    assert client.post("/readings", json={"temperatura": 22.5}).status_code == 422


def test_db_vacia_entre_tests(client):
    assert client.get("/readings").json() == []
