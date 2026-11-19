
import json
import time
import uuid
import os
from datetime import datetime

from dotenv import load_dotenv
import clickhouse_connect
from confluent_kafka import Consumer, TopicPartition

load_dotenv()


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
# Batch insertion and offset commit
# -------------------------------

def flush_batch(batch, offsets):
    if not batch:
        return

    batch_size = len(batch)

    # Step 1: Insert into ClickHouse first.
    # If this fails, do not commit Kafka offsets.
    clickhouse.insert(
        TABLE,
        batch,
        column_names=COLUMNS
    )

    print(f"Inserted {batch_size} telemetry records into ClickHouse")

    # Step 2: Prepare explicit Kafka offsets.
    # Kafka commits the NEXT offset to read, hence offset + 1.
    commit_offsets = [
        TopicPartition(topic, partition, next_offset)
        for (topic, partition), next_offset in offsets.items()
    ]

    # Step 3: Clear the inserted batch before committing.
    # This prevents the shutdown handler from inserting it again
    # if the Kafka commit fails.
    batch.clear()
    offsets.clear()

    # Step 4: Commit only after successful ClickHouse insertion.
    try:
        consumer.commit(
            offsets=commit_offsets,
            asynchronous=False
        )

        print("Kafka offsets committed successfully")

    except Exception as error:
        print(f"WARNING: Kafka offset commit failed: {error}")
        print(
            "Records were inserted into ClickHouse, but Kafka may "
            "replay them after restart."
        )
        raise


# -------------------------------
# Main consumer
# -------------------------------

def main():
    batch = []

    # Tracks the next offset to commit for each partition.
    offsets = {}

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

                payload = json.loads(
                    message.value().decode("utf-8")
                )

                row = parse_telemetry(payload)
                batch.append(row)

                # Record the next offset for this message's partition.
                offsets[
                    (message.topic(), message.partition())
                ] = message.offset() + 1

            elapsed = time.monotonic() - last_flush

            if batch and (
                len(batch) >= BATCH_SIZE
                or elapsed >= FLUSH_INTERVAL
            ):

                flush_batch(batch, offsets)
                last_flush = time.monotonic()

    except KeyboardInterrupt:
        print("\nStopping ClickHouse consumer...")

    finally:
        try:
            # Insert any remaining records before shutting down.
            if batch:
                print("Flushing remaining records...")
                flush_batch(batch, offsets)

        finally:
            consumer.close()
            clickhouse.close()

        print("ClickHouse consumer stopped.")


if __name__ == "__main__":
    main()
