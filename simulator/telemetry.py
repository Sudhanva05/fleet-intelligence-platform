
import uuid


def create_telemetry(vehicle):
    return {
        "event_id": str(uuid.uuid4()),
        "vehicle_id": vehicle.vehicle_id,
        "latitude": vehicle.latitude,
        "longitude": vehicle.longitude,
        "speed": vehicle.speed,
        "heading": vehicle.heading,
        "fuel_level": vehicle.fuel_level,
        "timestamp": vehicle.timestamp.isoformat()
    }
