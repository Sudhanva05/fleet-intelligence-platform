
import json
import time
import uuid
from datetime import datetime
import os
from dotenv import load_dotenv

load_dotenv()

import clickhouse_connect
from confluent_kafka import Consumer


# -------------------------------
# ClickHouse connection
# -------------------------------

clickhouse = clickhouse_connect.get_client(
    host=os.getenv("CLICKHOUSE_HOST", "localhost"),
    port=int(os.getenv("CLICKHOUSE_PORT", "8123")),
    username=os.getenv("CLICKHOUSE_USER"),
    password=os.getenv("CLICKHOUSE_PASSWORD"),
    database=os.getenv("CLICKHOUSE_DATABASE")
)


# -------------------------------
# Kafka consumer configuration
# -------------------------------

config = {
    "bootstrap.servers": "localhost:19092",
    "group.id": "fleet-clickhouse-consumer-v1",
    "auto.offset.reset": "earliest",
    "enable.auto.commit": False
}

consumer = Consumer(config)

TOPIC = "vehicle-telemetry"
TABLE = "vehicle_telemetry"

BATCH_SIZE = 100
FLUSH_INTERVAL = 5

COLUMNS = [
    "event_id",
    "vehicle_id",
    "latitude",
    "longitude",
    "speed",
    "heading",
    "fuel_level",
    "timestamp"
]


# -------------------------------
# Convert JSON into a database row
# -------------------------------

def parse_telemetry(payload):
    return [
        uuid.UUID(payload["event_id"]),
        uuid.UUID(payload["vehicle_id"]),
        float(payload["latitude"]),
        float(payload["longitude"]),
        float(payload["speed"]),
        float(payload["heading"]),
        float(payload["fuel_level"]),
        datetime.fromisoformat(
            payload["timestamp"].replace("Z", "+00:00")
        )
    ]


# -------------------------------
# Batch insertion
# -------------------------------

def flush_batch(batch):
    if not batch:
        return

    # Insert telemetry into ClickHouse
    clickhouse.insert(
        TABLE,
        batch,
        column_names=COLUMNS
    )

    # Commit Kafka offsets only after successful insertion
    consumer.commit(asynchronous=False)

    print(f"Inserted {len(batch)} telemetry records into ClickHouse")


# -------------------------------
# Main consumer
# -------------------------------

def main():
    batch = []
    last_flush = time.monotonic()

    consumer.subscribe([TOPIC])

    print("ClickHouse consumer started...")
    print(f"Subscribed to topic: {TOPIC}")

    try:
        while True:

            message = consumer.poll(1.0)

            if message is not None:

                if message.error():
                    raise RuntimeError(str(message.error()))

                payload = json.loads(message.value().decode("utf-8"))

                row = parse_telemetry(payload)
                batch.append(row)

            elapsed = time.monotonic() - last_flush

            if batch and (
                len(batch) >= BATCH_SIZE
                or elapsed >= FLUSH_INTERVAL
            ):
                flush_batch(batch)
                batch.clear()
                last_flush = time.monotonic()

    except KeyboardInterrupt:
        print("\nStopping ClickHouse consumer...")

    finally:
        try:
            if batch:
                flush_batch(batch)
                batch.clear()

        finally:
            consumer.close()
            clickhouse.close()

        print("ClickHouse consumer stopped.")


if __name__ == "__main__":
    main()
