from .vehicle import Vehicle

vehicle = Vehicle.create()

print("Vehicle Created!")
print(vehicle)
print("Vehicle ID:", vehicle.vehicle_id)
print("Location:", vehicle.latitude, vehicle.longitude)
