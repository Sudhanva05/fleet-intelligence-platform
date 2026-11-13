from .vehicle_generator import generate_fleet

fleet = generate_fleet(100)

print("Total vehicles:", len(fleet))
print("\nFirst 5 vehicles:\n")

for vehicle in fleet[:5]:
    print(
        f"ID: {vehicle.vehicle_id[:8]} | "
        f"Lat: {vehicle.latitude:.5f} | "
        f"Lon: {vehicle.longitude:.5f} | "
        f"Speed: {vehicle.speed:.2f} km/h | "
        f"Heading: {vehicle.heading:.2f}° | "
        f"Fuel: {vehicle.fuel_level:.2f}%"
    )
