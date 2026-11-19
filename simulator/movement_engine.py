
import math
import random
from datetime import datetime, timezone

from .vehicle import Vehicle


# Simulation configuration
EARTH_RADIUS_KM = 6371.0

MIN_SPEED = 0.0
MAX_SPEED = 110.0

MAX_ACCELERATION = 1.5
MAX_TURN_RATE = 3.0

FUEL_CONSUMPTION_PER_KM = 0.12


def set_vehicle_state(vehicle: Vehicle, state: str):
    """Set a new operating state and its duration."""

    vehicle.state = state

    if state == "moving":
        vehicle.speed = random.uniform(25, 85)
        vehicle.state_duration_remaining = random.uniform(30, 120)

    elif state == "slow":
        vehicle.speed = random.uniform(5, 20)
        vehicle.state_duration_remaining = random.uniform(15, 45)

    elif state == "idle":
        vehicle.speed = 0.0
        vehicle.state_duration_remaining = random.uniform(20, 90)


def transition_vehicle_state(vehicle: Vehicle):
    """Choose the next operating state."""

    next_state = random.choices(
        ["moving", "slow", "idle"],
        weights=[60, 20, 20],
        k=1
    )[0]

    set_vehicle_state(vehicle, next_state)


def move_vehicle(vehicle: Vehicle, elapsed_seconds: float):
    """
    Simulate vehicle movement with operating states,
    heading changes, GPS updates and fuel consumption.
    """

    # Prevent invalid or excessively large time steps
    dt = max(0.0, min(elapsed_seconds, 5.0))

    if dt == 0:
        return vehicle

    # ------------------------------------------------
    # 1. Update operating state duration
    # ------------------------------------------------

    vehicle.state_duration_remaining -= dt

    if vehicle.state_duration_remaining <= 0:
        transition_vehicle_state(vehicle)

    # ------------------------------------------------
    # 2. Update speed according to operating state
    # ------------------------------------------------

    if vehicle.state == "moving":

        acceleration = random.uniform(
            -MAX_ACCELERATION,
            MAX_ACCELERATION
        )

        vehicle.speed += acceleration * dt

        vehicle.speed = max(
            20.0,
            min(vehicle.speed, 90.0)
        )

    elif vehicle.state == "slow":

        acceleration = random.uniform(-0.5, 0.5)

        vehicle.speed += acceleration * dt

        vehicle.speed = max(
            5.0,
            min(vehicle.speed, 20.0)
        )

    elif vehicle.state == "idle":

        vehicle.speed = 0.0

    # ------------------------------------------------
    # 3. Update heading for moving vehicles
    # ------------------------------------------------

    if vehicle.state != "idle":

        heading_change = random.gauss(
            0,
            MAX_TURN_RATE * math.sqrt(dt)
        )

        vehicle.heading = (
            vehicle.heading + heading_change
        ) % 360

    # ------------------------------------------------
    # 4. Calculate distance travelled
    # ------------------------------------------------

    distance_km = vehicle.speed * dt / 3600

    # ------------------------------------------------
    # 5. Update GPS coordinates
    # ------------------------------------------------

    if distance_km > 0:

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
    # 6. Simulate fuel consumption
    # ------------------------------------------------

    fuel_used = (
        distance_km * FUEL_CONSUMPTION_PER_KM
    )

    vehicle.fuel_level = max(
        0.0,
        vehicle.fuel_level - fuel_used
    )

    # ------------------------------------------------
    # 7. Update timestamp
    # ------------------------------------------------

    vehicle.timestamp = datetime.now(timezone.utc)

    return vehicle
