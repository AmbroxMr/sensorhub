import io
from datetime import datetime

import pandas as pd
from fastapi import HTTPException
from fastapi.responses import StreamingResponse

from sensorhub.minio import MinioClient
from sensorhub.mongo import MongoDB


def generate(db: MongoDB, hour: str | None = None) -> dict:
    if hour:
        start = datetime.fromisoformat(hour).replace(minute=0, second=0, microsecond=0)
    else:
        now = datetime.now()
        start = now.replace(minute=0, second=0, microsecond=0)
    end = start.replace(minute=59, second=59, microsecond=999999)

    docs = list(db.read_sensor_data_by_time(start.isoformat(), end.isoformat()))
    if not docs:
        raise HTTPException(
            status_code=404, detail="No data found for the specified hour"
        )
    for doc in docs:
        doc.pop("_id", None)

    df = pd.DataFrame(docs)
    report = (
        df.groupby(["device_id", "location"])
        .agg(
            count=("temperature", "count"),
            avg_temperature=("temperature", "mean"),
            avg_humidity=("humidity", "mean"),
            avg_co2=("co2", "mean"),
            max_co2=("co2", "max"),
        )
        .reset_index()
    )

    csv_bytes = report.to_csv(index=False).encode()
    object_name = f"{start.strftime('%Y-%m-%d')}/{start.strftime('%H%M')}.csv"
    MinioClient().upload_csv(object_name, csv_bytes)
    return {"object_key": object_name, "link": f"/reports/{object_name}"}


def list_all() -> list[dict]:
    return MinioClient().list_reports()


def get(report_name: str) -> StreamingResponse:
    try:
        csv_bytes = MinioClient().get_report(report_name)
    except Exception:
        raise HTTPException(status_code=404, detail="Report not found")
    filename = report_name.split("/")[-1]
    return StreamingResponse(
        io.BytesIO(csv_bytes),
        media_type="text/csv",
        headers={"Content-Disposition": f"attachment; filename={filename}"},
    )
