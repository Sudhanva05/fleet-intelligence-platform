
import json
import redis
import threading

from datetime import datetime, timezone
from confluent_kafka import Consumer


# Vehicle is considered stale after 30 seconds without telemetry.
INACTIVITY_THRESHOLD_SECONDS = 30

# Run stale vehicle cleanup every 10 seconds.
CLEANUP_INTERVAL_SECONDS = 10

GEO_INDEX_KEY = "fleet:locations"


class RedisTelemetryConsumer:

    def __init__(self):

        # Connect to Redis
        self.redis_client = redis.Redis(
            host="localhost",
            port=6379,
            decode_responses=True
        )

        # Connect to Redpanda
        config = {
            "bootstrap.servers": "localhost:19092",
            "group.id": "fleet-redis-consumer-v1",
            "auto.offset.reset": "earliest",
            "enable.auto.commit": False
        }

        self.consumer = Consumer(config)

        self.topic = "vehicle-telemetry"
        self.consumer.subscribe([self.topic])

        self.stop_cleanup = threading.Event()
        self.cleanup_thread = None

        # Atomic cleanup: delete only if the timestamp has not changed.
        self.cleanup_script = self.redis_client.register_script("""
            local current_timestamp =
                redis.call('HGET', KEYS[1], 'timestamp')

            if current_timestamp == ARGV[1] then
                redis.call('DEL', KEYS[1])
                redis.call('ZREM', KEYS[2], ARGV[2])
                return 1
            end

            return 0
        """)

    def process_event(self, event):

        vehicle_id = event["vehicle_id"]

        # Store latest vehicle state
        key = f"vehicle:{vehicle_id}:latest"

        self.redis_client.hset(
            key,
            mapping={
                "latitude": event["latitude"],
                "longitude": event["longitude"],
                "speed": event["speed"],
                "heading": event["heading"],
                "fuel_level": event["fuel_level"],
                "timestamp": event["timestamp"]
            }
        )

        # Update Redis geospatial index
        self.redis_client.geoadd(
            GEO_INDEX_KEY,
            (
                event["longitude"],
                event["latitude"],
                vehicle_id
            )
        )

    def cleanup_stale_vehicles(self):

        print("Stale vehicle cleanup started...")

        while not self.stop_cleanup.wait(
            CLEANUP_INTERVAL_SECONDS
        ):

            try:
                now = datetime.now(timezone.utc)
                removed_count = 0

                # Iterate without blocking Redis with KEYS.
                for key in self.redis_client.scan_iter(
                    match="vehicle:*:latest",
                    count=200
                ):

                    timestamp = self.redis_client.hget(
                        key,
                        "timestamp"
                    )

                    if not timestamp:
                        continue

                    try:
                        last_seen = datetime.fromisoformat(
                            timestamp.replace("Z", "+00:00")
                        )

                        # Handle timestamps without timezone information.
                        if last_seen.tzinfo is None:
                            last_seen = last_seen.replace(
                                tzinfo=timezone.utc
                            )

                        age = (now - last_seen).total_seconds()

                        if age <= INACTIVITY_THRESHOLD_SECONDS:
                            continue

                        vehicle_id = key[
                            len("vehicle:"):-len(":latest")
                        ]

                        # Atomically verify the timestamp and remove
                        # both the hash and GEO index entry.
                        removed = self.cleanup_script(
                            keys=[key, GEO_INDEX_KEY],
                            args=[timestamp, vehicle_id]
                        )

                        if removed:
                            removed_count += 1

                    except (ValueError, TypeError) as error:
                        print(
                            f"Invalid timestamp in {key}: {error}"
                        )

                if removed_count:
                    print(
                        f"Stale cleanup: removed "
                        f"{removed_count} vehicles"
                    )

            except Exception as error:
                print("Cleanup error:", error)

    def run(self):

        print("Redis consumer started...")
        print("Waiting for telemetry events...")

        # Start cleanup independently from Kafka processing.
        self.cleanup_thread = threading.Thread(
            target=self.cleanup_stale_vehicles,
            daemon=True
        )
        self.cleanup_thread.start()

        try:
            while True:

                message = self.consumer.poll(1.0)

                if message is None:
                    continue

                if message.error():
                    print("Consumer error:", message.error())
                    continue

                try:
                    event = json.loads(message.value())

                    self.process_event(event)

                    # Commit only after successful Redis writes.
                    self.consumer.commit(
                        message=message,
                        asynchronous=False
                    )

                    print(
                        f"Processed vehicle: "
                        f"{event['vehicle_id']}"
                    )

                except Exception as error:
                    print("Processing failed:", error)

        except KeyboardInterrupt:
            print("\nConsumer stopped.")

        finally:
            self.stop_cleanup.set()

            if self.cleanup_thread:
                self.cleanup_thread.join(timeout=5)

            self.consumer.close()
            self.redis_client.close()


if __name__ == "__main__":
    consumer = RedisTelemetryConsumer()
    consumer.run()
