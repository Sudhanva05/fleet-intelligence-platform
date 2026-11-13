
from .vehicle import Vehicle
from .telemetry import create_telemetry
from .kafka_producer import TelemetryProducer


vehicle = Vehicle.create()

event = create_telemetry(vehicle)

producer = TelemetryProducer()

try:
    producer.publish(event)
    producer.poll()

    print("Telemetry event submitted!")
    print("Vehicle ID:", vehicle.vehicle_id)

finally:
    producer.close()
