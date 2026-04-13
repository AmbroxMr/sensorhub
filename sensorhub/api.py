from fastapi import Depends, FastAPI, Query, status

from sensorhub import readings, reports
from sensorhub.mongo import MongoDB
from sensorhub.sensor_data import SensorData

app = FastAPI(title="SensorHub API")


def get_db() -> MongoDB:
    return MongoDB()


@app.get("/health")
def health():
    return {"status": "ok"}


@app.post("/readings", status_code=status.HTTP_201_CREATED)
def upload_readings(sensor_data: SensorData, db: MongoDB = Depends(get_db)):
    db.upload_sensor_data(sensor_data)
    return {"message": "Sensor data uploaded successfully"}


@app.get("/readings")
def get_readings(
    device_id: str = Query(default=None),
    limit: int = Query(default=None, ge=1),
    db: MongoDB = Depends(get_db),
):
    return readings.list_readings(db, device_id=device_id, limit=limit)


@app.get("/readings/stats")
def get_stats(db: MongoDB = Depends(get_db)):
    return readings.compute_stats(db)


@app.get("/export")
def export_csv(db: MongoDB = Depends(get_db)):
    return readings.export_csv(db)


@app.post("/reports/generate")
def generate_report(hour: str = Query(default=None), db: MongoDB = Depends(get_db)):
    return reports.generate(db, hour=hour)


@app.get("/reports")
def list_reports():
    return reports.list_all()


@app.get("/reports/{report_name:path}")
def get_report(report_name: str):
    return reports.get(report_name)
