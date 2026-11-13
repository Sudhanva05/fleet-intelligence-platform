
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
        vehicle.speed = random.uniform(20, 100)
        vehicle.heading = random.uniform(0, 360)
        vehicle.fuel_level = random.uniform(20, 100)

        vehicles.append(vehicle)

    return vehicles
