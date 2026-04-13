from pydantic import BaseModel, ConfigDict
from typing import Optional
from datetime import datetime


class SensorData(BaseModel):
    device_id: str
    location: str
    temperature: float
    humidity: float
    co2: float
    timestamp: Optional[str] = datetime.now().isoformat()
    model_config = ConfigDict(extra="allow")
