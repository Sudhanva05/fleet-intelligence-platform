
import os
import uuid

from pathlib import Path
from datetime import datetime, timezone

import redis
import clickhouse_connect

from dotenv import load_dotenv


# --------------------------------------------------
# Environment Configuration
# --------------------------------------------------

PROJECT_ROOT = Path(__file__).resolve().parents[1]

load_dotenv(
    dotenv_path=PROJECT_ROOT / ".env"
)


# --------------------------------------------------
# Redis Configuration
# --------------------------------------------------

REDIS_HOST = "localhost"
REDIS_PORT = 6379

REDIS_STREAM = "fleet:alerts:outbox"

REDIS_GROUP = "fleet-alert-history-writers"

# Keep this name stable so pending messages can
# be recovered after a worker restart.
REDIS_CONSUMER = "alert-history-writer-1"


# --------------------------------------------------
# ClickHouse Configuration
# --------------------------------------------------

CLICKHOUSE_HOST = os.getenv(
    "CLICKHOUSE_HOST", "localhost"
)

CLICKHOUSE_PORT = int(
    os.getenv("CLICKHOUSE_PORT", 8123)
)

CLICKHOUSE_USER = os.getenv(
    "CLICKHOUSE_USER", "default"
)

CLICKHOUSE_PASSWORD = os.getenv(
    "CLICKHOUSE_PASSWORD", ""
)

CLICKHOUSE_DATABASE = os.getenv(
    "CLICKHOUSE_DATABASE", "fleet_analytics"
)

CLICKHOUSE_TABLE = "vehicle_alert_events"


# --------------------------------------------------
# Stream Configuration
# --------------------------------------------------

BATCH_SIZE = 100
BLOCK_TIME_MS = 5000


# --------------------------------------------------
# ClickHouse Columns
# --------------------------------------------------

COLUMNS = [
    "event_id",
    "alert_id",
    "vehicle_id",
    "alert_type",
    "severity",
    "event_status",
    "current_value",
    "threshold",
    "event_time"
]


# --------------------------------------------------
# Alert History Writer
# --------------------------------------------------

class AlertHistoryWriter:

    def __init__(self):

        # Redis connection
        self.redis_client = redis.Redis(
            host=REDIS_HOST,
            port=REDIS_PORT,
            decode_responses=True
        )

        # ClickHouse connection
        self.clickhouse_client = (
            clickhouse_connect.get_client(
                host=CLICKHOUSE_HOST,
                port=CLICKHOUSE_PORT,
                username=CLICKHOUSE_USER,
                password=CLICKHOUSE_PASSWORD,
                database=CLICKHOUSE_DATABASE
            )
        )

        print("Alert history writer initialized.")

    # --------------------------------------------------
    # Connection Checks
    # --------------------------------------------------

    def check_connections(self):

        self.redis_client.ping()

        print("Redis connection: OK")

        result = self.clickhouse_client.query(
            "SELECT 1"
        )

        print(
            "ClickHouse connection: OK",
            "| Result:",
            result.result_rows[0][0]
        )

    # --------------------------------------------------
    # Create Redis Consumer Group
    # --------------------------------------------------

    def create_consumer_group(self):

        try:

            self.redis_client.xgroup_create(
                name=REDIS_STREAM,
                groupname=REDIS_GROUP,
                id="0-0",
                mkstream=True
            )

            print(
                "Redis consumer group created:",
                REDIS_GROUP
            )

        except redis.exceptions.ResponseError as error:

            if "BUSYGROUP" in str(error):

                print(
                    "Redis consumer group already exists:",
                    REDIS_GROUP
                )

            else:
                raise

    # --------------------------------------------------
    # Parse Redis Event
    # --------------------------------------------------

    def parse_event(self, event):

        event_time = datetime.fromisoformat(
            event["event_time"].replace(
                "Z", "+00:00"
            )
        )

        if event_time.tzinfo is None:

            event_time = event_time.replace(
                tzinfo=timezone.utc
            )

        event_time = event_time.astimezone(
            timezone.utc
        )

        return [
            uuid.UUID(event["event_id"]),
            uuid.UUID(event["alert_id"]),
            event["vehicle_id"],
            event["alert_type"],
            event["severity"],
            event["event_status"],
            float(event["current_value"]),
            float(event["threshold"]),
            event_time
        ]

    # --------------------------------------------------
    # Insert Event Into ClickHouse
    # --------------------------------------------------

    def insert_event(self, event):

        row = self.parse_event(event)

        self.clickhouse_client.insert(
            table=CLICKHOUSE_TABLE,
            data=[row],
            column_names=COLUMNS
        )

    # --------------------------------------------------
    # Process Redis Stream Message
    # --------------------------------------------------

    def process_message(self, message_id, event):

        # Insert into ClickHouse first
        self.insert_event(event)

        # Acknowledge only after successful insertion
        acknowledged = self.redis_client.xack(
            REDIS_STREAM,
            REDIS_GROUP,
            message_id
        )

        if acknowledged == 1:

            print(
                f"INSERTED: {event['alert_type']} "
                f"| {event['event_status']} "
                f"| Vehicle: {event['vehicle_id']} "
                f"| Value: {event['current_value']}"
            )

        else:

            print(
                "Warning: Event inserted but not acknowledged:",
                message_id
            )

    # --------------------------------------------------
    # Read Pending Messages
    # --------------------------------------------------

    def read_pending_messages(self):

        return self.redis_client.xreadgroup(
            groupname=REDIS_GROUP,
            consumername=REDIS_CONSUMER,
            streams={
                REDIS_STREAM: "0"
            },
            count=BATCH_SIZE
        )

    # --------------------------------------------------
    # Read New Messages
    # --------------------------------------------------

    def read_new_messages(self):

        return self.redis_client.xreadgroup(
            groupname=REDIS_GROUP,
            consumername=REDIS_CONSUMER,
            streams={
                REDIS_STREAM: ">"
            },
            count=BATCH_SIZE,
            block=BLOCK_TIME_MS
        )

    # --------------------------------------------------
    # Main Processing Loop
    # --------------------------------------------------


    def run(self):

        print("\nStarting alert history writer...")

        self.create_consumer_group()

        print("Redis stream:", REDIS_STREAM)
        print(
            "ClickHouse table:",
            f"{CLICKHOUSE_DATABASE}.{CLICKHOUSE_TABLE}"
        )

        print("\nWaiting for alert events...")
        print("Press CTRL+C to stop.\n")

        while True:

            # First recover messages previously delivered
            # to this consumer but not acknowledged.
            messages = self.read_pending_messages()

            entries = [
                (message_id, event)
                for stream_name, stream_entries in (messages or [])
                for message_id, event in stream_entries
            ]

            # If there are no actual pending messages,
            # read new messages from the stream.
            if not entries:

                messages = self.read_new_messages()

                entries = [
                    (message_id, event)
                    for stream_name, stream_entries in (messages or [])
                    for message_id, event in stream_entries
                ]

            for message_id, event in entries:

                try:

                    self.process_message(
                        message_id,
                        event
                    )

                except Exception as error:

                    print(
                        "\nAlert history processing failed:",
                        error
                    )

                    print(
                        "Message remains pending:",
                        message_id
                    )

                    raise

    # --------------------------------------------------
    # Cleanup
    # --------------------------------------------------

    def close(self):

        self.clickhouse_client.close()
        self.redis_client.close()

        print("Alert history writer closed.")


# --------------------------------------------------
# Entry Point
# --------------------------------------------------

if __name__ == "__main__":

    writer = AlertHistoryWriter()

    try:

        writer.check_connections()
        writer.run()

    except KeyboardInterrupt:

        print("\nStopping alert history writer...")

    finally:

        writer.close()
