
import asyncio
import json

from .vehicle_generator import generate_fleet
from .movement_engine import move_vehicle
from .telemetry import create_telemetry


async def run_simulation():

    fleet = generate_fleet(100)

    print(f"Fleet initialized: {len(fleet)} vehicles")

    iteration = 0

    while True:
        iteration += 1

        telemetry_events = []

        for vehicle in fleet:

            # Move vehicle for one second
            move_vehicle(vehicle, 1)

            # Generate telemetry
            event = create_telemetry(vehicle)

            telemetry_events.append(event)

        print(f"\nIteration: {iteration}")
        print(f"Events generated: {len(telemetry_events)}")

        # Display only two sample events
        for event in telemetry_events[:2]:
            print(json.dumps(event, indent=2))

        await asyncio.sleep(1)


if __name__ == "__main__":
    try:
        asyncio.run(run_simulation())
    except KeyboardInterrupt:
        print("\nSimulation stopped.")
