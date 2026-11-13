
import time

from .vehicle import Vehicle
from .movement_engine import move_vehicle


vehicle = Vehicle.create()

print("INITIAL VEHICLE STATE")
print(f"Latitude: {vehicle.latitude}")
print(f"Longitude: {vehicle.longitude}")
print(f"Speed: {vehicle.speed:.2f} km/h")
print(f"Heading: {vehicle.heading:.2f} degrees")
print(f"Fuel: {vehicle.fuel_level:.2f}%")

print("\nSIMULATING MOVEMENT\n")

for iteration in range(10):
    move_vehicle(vehicle, 1.0)

    print(
        f"Iteration {iteration + 1:02d} | "
        f"Speed: {vehicle.speed:.2f} km/h | "
        f"Heading: {vehicle.heading:.2f} | "
        f"Fuel: {vehicle.fuel_level:.4f}% | "
        f"Lat: {vehicle.latitude:.6f} | "
        f"Lon: {vehicle.longitude:.6f}"
    )

print("\nFINAL VEHICLE STATE")
print(f"Fuel remaining: {vehicle.fuel_level:.2f}%")
