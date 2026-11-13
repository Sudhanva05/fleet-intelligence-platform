
import json
from confluent_kafka import Producer


class TelemetryProducer:

    def __init__(self):
        config = {
            "bootstrap.servers": "localhost:19092",
            "client.id": "fleet-simulator"
        }

        self.producer = Producer(config)
        self.topic = "vehicle-telemetry"

        self.delivered_count = 0
        self.failed_count = 0

    def delivery_report(self, error, message):
        if error is not None:
            self.failed_count += 1
            print(f"Delivery failed: {error}")
        else:
            self.delivered_count += 1

    def publish(self, event):
        self.producer.produce(
            topic=self.topic,
            key=event["vehicle_id"],
            value=json.dumps(event),
            on_delivery=self.delivery_report
        )

        self.producer.poll(0)

    def close(self):
        remaining = self.producer.flush(10)

        print("\nProducer shutdown")
        print("Delivered:", self.delivered_count)
        print("Failed:", self.failed_count)
        print("Pending:", remaining)
