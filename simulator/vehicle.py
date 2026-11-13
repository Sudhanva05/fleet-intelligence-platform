
from dataclasses import dataclass
from datetime import datetime, timezone
import uuid


@dataclass
class Vehicle:
    vehicle_id: str
    latitude: float
    longitude: float
    speed: float
    heading: float
    fuel_level: float
    timestamp: datetime

    @staticmethod
    def create():
        return Vehicle(
            vehicle_id=str(uuid.uuid4()),
            latitude=12.9716,
            longitude=77.5946,
            speed=40.0,
            heading=90.0,
            fuel_level=100.0,
            timestamp=datetime.now(timezone.utc)
        )
