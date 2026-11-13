
import math
import random
from datetime import datetime, timezone

from .vehicle import Vehicle


# Simulation configuration
EARTH_RADIUS_KM = 6371.0

MIN_SPEED = 0.0
MAX_SPEED = 110.0

MAX_ACCELERATION = 1.5       # km/h change per second
MAX_TURN_RATE = 3.0          # Approximate degrees per second

FUEL_CONSUMPTION_PER_KM = 0.12  # Percentage points per km


def move_vehicle(vehicle: Vehicle, elapsed_seconds: float):
    """
    Simulate vehicle movement with dynamic speed,
    heading changes and fuel consumption.
    """

    # Prevent invalid or excessively large time steps
    dt = max(0.0, min(elapsed_seconds, 5.0))

    if dt == 0:
        return vehicle

    # ------------------------------------------------
    # 1. Update speed: acceleration / deceleration
    # ------------------------------------------------

    acceleration = random.uniform(
        -MAX_ACCELERATION,
        MAX_ACCELERATION
    )

    vehicle.speed += acceleration * dt

    vehicle.speed = max(
        MIN_SPEED,
        min(vehicle.speed, MAX_SPEED)
    )

    # ------------------------------------------------
    # 2. Update heading: small directional changes
    # ------------------------------------------------

    heading_change = random.gauss(
        0,
        MAX_TURN_RATE * math.sqrt(dt)
    )

    vehicle.heading = (
        vehicle.heading + heading_change
    ) % 360

    # ------------------------------------------------
    # 3. Calculate distance travelled
    # ------------------------------------------------

    distance_km = vehicle.speed * dt / 3600

    # ------------------------------------------------
    # 4. Update GPS coordinates
    # ------------------------------------------------

    heading_rad = math.radians(vehicle.heading)
    lat_rad = math.radians(vehicle.latitude)

    delta_lat = (
        distance_km * math.cos(heading_rad)
    ) / EARTH_RADIUS_KM

    delta_lon = (
        distance_km * math.sin(heading_rad)
    ) / (
        EARTH_RADIUS_KM * math.cos(lat_rad)
    )

    vehicle.latitude += math.degrees(delta_lat)
    vehicle.longitude += math.degrees(delta_lon)

    # ------------------------------------------------
    # 5. Simulate fuel consumption
    # ------------------------------------------------

    fuel_used = (
        distance_km * FUEL_CONSUMPTION_PER_KM
    )

    vehicle.fuel_level = max(
        0.0,
        vehicle.fuel_level - fuel_used
    )

    # ------------------------------------------------
    # 6. Update timestamp
    # ------------------------------------------------

    vehicle.timestamp = datetime.now(timezone.utc)

    return vehicle
