from pymongo import MongoClient
from sensorhub.config import Settings
from sensorhub.sensor_data import SensorData

settings = Settings()  # type: ignore[call-arg]


class MongoDB:
    def __init__(self):
        self.client = MongoClient(
            host=settings.mongo_ip,
            port=settings.mongo_port,
            username=settings.mongo_username,
            password=settings.mongo_root_password,
        )
        self.db = "sensorhub"
        self.collection = "sensor_data"
        self.client_collection = self.client.get_database(self.db).get_collection(self.collection)

    def upload_sensor_data(self, sensor_data: SensorData):
        self.client_collection.insert_one(sensor_data.model_dump())

    def read_sensor_data(self, device_id: str | None = None, max_records: int | None = None):
        query = {"device_id": device_id} if device_id else {}
        limit = max_records if max_records is not None else 0
        return self.client_collection.find(query, limit=limit)

    def read_sensor_data_by_time(self, start_iso: str, end_iso: str):
        from datetime import datetime
        start = datetime.fromisoformat(start_iso)
        end = datetime.fromisoformat(end_iso)
        query = {"timestamp": {"$gte": start, "$lte": end}}
        return self.client_collection.find(query)

    def insert_many(self, documents: list[dict]) -> int:
        result = self.client_collection.insert_many(documents)
        return len(result.inserted_ids)
