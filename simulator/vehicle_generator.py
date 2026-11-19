
import random
from .vehicle import Vehicle


def generate_fleet(count: int):
    vehicles = []

    for _ in range(count):
        vehicle = Vehicle.create()

        # Random starting position around Bengaluru
        vehicle.latitude = 12.9716 + random.uniform(-0.05, 0.05)
        vehicle.longitude = 77.5946 + random.uniform(-0.05, 0.05)

        # Random vehicle properties
        vehicle.heading = random.uniform(0, 360)
        vehicle.fuel_level = random.uniform(20, 100)

        # Assign initial operating state
        vehicle.state = random.choices(
            ["moving", "slow", "idle"],
            weights=[60, 20, 20],
            k=1
        )[0]

        if vehicle.state == "moving":
            vehicle.speed = random.uniform(25, 85)
            vehicle.state_duration_remaining = random.uniform(30, 120)

        elif vehicle.state == "slow":
            vehicle.speed = random.uniform(5, 20)
            vehicle.state_duration_remaining = random.uniform(15, 45)

        else:
            vehicle.speed = 0.0
            vehicle.state_duration_remaining = random.uniform(20, 90)

        vehicles.append(vehicle)

    return vehicles
