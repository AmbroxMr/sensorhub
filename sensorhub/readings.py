import io

import numpy as np
import pandas as pd
from fastapi.responses import StreamingResponse

from sensorhub.mongo import MongoDB


def list_readings(db: MongoDB, device_id: str | None = None, limit: int | None = None) -> list[dict]:
    cursor = db.read_sensor_data(device_id=device_id, max_records=limit)
    readings = []
    for doc in cursor:
        doc["_id"] = str(doc["_id"])
        readings.append(doc)
    return readings


def compute_stats(db: MongoDB) -> list[dict]:
    docs = list(db.read_sensor_data())
    if not docs:
        return []
    for doc in docs:
        doc.pop("_id", None)
    df = pd.DataFrame(docs)
    stats = (
        df.groupby("device_id")
        .agg(
            count=("temperature", "count"),
            avg_temperature=("temperature", "mean"),
            std_temperature=("temperature", "std"),
            avg_humidity=("humidity", "mean"),
            avg_co2=("co2", "mean"),
            max_co2=("co2", "max"),
        )
        .reset_index()
    )
    return stats.replace({np.nan: None}).to_dict(orient="records")


def export_csv(db: MongoDB) -> StreamingResponse:
    docs = list(db.read_sensor_data())
    for doc in docs:
        doc.pop("_id", None)
    df = pd.DataFrame(docs)
    csv_bytes = df.to_csv(index=False).encode()
    return StreamingResponse(
        io.BytesIO(csv_bytes),
        media_type="text/csv",
        headers={"Content-Disposition": "attachment; filename=readings.csv"},
    )
