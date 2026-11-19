
import redis

from datetime import datetime, timezone, timedelta


# --------------------------------------------------
# REDIS CONNECTION
# --------------------------------------------------

redis_client = redis.Redis(
    host="localhost",
    port=6379,
    decode_responses=True
)

INACTIVITY_THRESHOLD_SECONDS = 30
LOW_FUEL_THRESHOLD = 20.0


def check_redis_connection():
    return redis_client.ping()


# --------------------------------------------------
# GET ALL VEHICLES
# --------------------------------------------------

def get_all_vehicles():

    vehicles = []

    current_time = datetime.now(timezone.utc)
    threshold = timedelta(
        seconds=INACTIVITY_THRESHOLD_SECONDS
    )

    for key in redis_client.scan_iter(
        match="vehicle:*:latest"
    ):

        vehicle_data = redis_client.hgetall(key)

        if not vehicle_data:
            continue

        vehicle_id = key.split(":")[1]
        vehicle_data["vehicle_id"] = vehicle_id

        try:
            timestamp = datetime.fromisoformat(
                vehicle_data["timestamp"].replace(
                    "Z", "+00:00"
                )
            )

            if timestamp.tzinfo is None:
                timestamp = timestamp.replace(
                    tzinfo=timezone.utc
                )

            age = current_time - timestamp

            vehicle_data["status"] = (
                "active" if age <= threshold else "stale"
            )

        except (ValueError, KeyError):
            vehicle_data["status"] = "stale"

        vehicles.append(vehicle_data)

    return vehicles


# --------------------------------------------------
# GET VEHICLE BY ID
# --------------------------------------------------

def get_vehicle_by_id(vehicle_id: str):

    key = f"vehicle:{vehicle_id}:latest"

    vehicle_data = redis_client.hgetall(key)

    if vehicle_data:
        vehicle_data["vehicle_id"] = vehicle_id
        return vehicle_data

    return None


# --------------------------------------------------
# OPERATIONAL FLEET SUMMARY
# --------------------------------------------------

def get_operational_summary():

    vehicles = get_all_vehicles()

    total_vehicles = len(vehicles)

    active_vehicles = [
        vehicle
        for vehicle in vehicles
        if vehicle["status"] == "active"
    ]

    inactive_vehicles = total_vehicles - len(
        active_vehicles
    )

    moving = 0
    slow = 0
    idle = 0
    low_fuel = 0

    for vehicle in active_vehicles:

        speed = float(vehicle.get("speed", 0))
        fuel_level = float(
            vehicle.get("fuel_level", 0)
        )

        if speed >= 20:
            moving += 1

        elif speed > 0:
            slow += 1

        else:
            idle += 1

        if fuel_level <= LOW_FUEL_THRESHOLD:
            low_fuel += 1

    fleet_utilization = (
        round(
            (moving / len(active_vehicles)) * 100,
            2
        )
        if active_vehicles else 0
    )

    return {
        "total_vehicles": total_vehicles,
        "active_vehicles": len(active_vehicles),
        "inactive_vehicles": inactive_vehicles,
        "moving": moving,
        "slow": slow,
        "idle": idle,
        "fleet_utilization": fleet_utilization,
        "low_fuel_vehicles": low_fuel
    }
