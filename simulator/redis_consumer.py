
import json
import redis

from confluent_kafka import Consumer


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
            "fleet:locations",
            (
                event["longitude"],
                event["latitude"],
                vehicle_id
            )
        )

    def run(self):

        print("Redis consumer started...")
        print("Waiting for telemetry events...")

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

                    # Commit only after successful Redis writes
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
            self.consumer.close()
            self.redis_client.close()


if __name__ == "__main__":
    consumer = RedisTelemetryConsumer()
    consumer.run()
