import redis

redis_client = redis.Redis(
    host="localhost",
    port=6379,
    decode_responses=True
)


def check_redis_connection():
    return redis_client.ping()


from datetime import datetime, timezone, timedelta


def get_all_vehicles():
    vehicles = []

    current_time = datetime.now(timezone.utc)
    threshold = timedelta(seconds=30)

    for key in redis_client.scan_iter(match="vehicle:*:latest"):
        vehicle_data = redis_client.hgetall(key)

        if not vehicle_data:
            continue

        vehicle_id = key.split(":")[1]
        vehicle_data["vehicle_id"] = vehicle_id

        timestamp = datetime.fromisoformat(
            vehicle_data["timestamp"]
        )

        age = current_time - timestamp

        vehicle_data["status"] = (
            "active" if age <= threshold else "stale"
        )

        vehicles.append(vehicle_data)

    return vehicles


def get_vehicle_by_id(vehicle_id: str):
    key = f"vehicle:{vehicle_id}:latest"
    vehicle_data = redis_client.hgetall(key)

    if vehicle_data:
        vehicle_data["vehicle_id"] = vehicle_id
        return vehicle_data

    return None