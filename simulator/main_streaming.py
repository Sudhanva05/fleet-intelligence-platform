
import asyncio
import time

from .vehicle_generator import generate_fleet
from .movement_engine import move_vehicle
from .telemetry import create_telemetry
from .kafka_producer import TelemetryProducer


async def run_simulation():

    fleet = generate_fleet(100)
    producer = TelemetryProducer()

    print(f"Fleet initialized: {len(fleet)} vehicles")
    print("Publishing telemetry to Redpanda...")

    iteration = 0
    total_events = 0

    last_tick = time.monotonic() - 1.0

    try:
        while True:

            tick_start = time.monotonic()
            elapsed = tick_start - last_tick
            last_tick = tick_start

            iteration += 1

            for vehicle in fleet:

                move_vehicle(vehicle, elapsed)

                event = create_telemetry(vehicle)

                producer.publish(event)

                total_events += 1

            if iteration % 5 == 0:
                print(
                    f"Iteration: {iteration} | "
                    f"Generated: {total_events} | "
                    f"Delivered: {producer.delivered_count} | "
                    f"Failed: {producer.failed_count}"
                )

            # Maintain approximately one-second intervals
            processing_time = time.monotonic() - tick_start
            await asyncio.sleep(max(0, 1.0 - processing_time))

    finally:
        producer.close()


if __name__ == "__main__":
    try:
        asyncio.run(run_simulation())
    except KeyboardInterrupt:
        print("\nFleet simulation stopped.")
