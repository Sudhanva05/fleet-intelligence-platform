
import json
import uuid
import threading

from pathlib import Path
from datetime import datetime, timezone

import redis
from dotenv import load_dotenv
from confluent_kafka import Consumer, KafkaError


# --------------------------------------------------
# Environment Configuration
# --------------------------------------------------

PROJECT_ROOT = Path(__file__).resolve().parents[1]
load_dotenv(dotenv_path=PROJECT_ROOT / ".env")


# --------------------------------------------------
# Kafka Configuration
# --------------------------------------------------

KAFKA_CONFIG = {
    "bootstrap.servers": "localhost:19092",
    "group.id": "fleet-alert-consumer-v1",
    "auto.offset.reset": "latest",
    "enable.auto.commit": False
}

KAFKA_TOPIC = "vehicle-telemetry"


# --------------------------------------------------
# Alert Thresholds
# --------------------------------------------------

LOW_FUEL_THRESHOLD = 20.0
OVERSPEED_THRESHOLD = 85.0
INACTIVITY_THRESHOLD_SECONDS = 30
PROLONGED_IDLE_SECONDS = 60

INACTIVITY_CHECK_INTERVAL = 5


# --------------------------------------------------
# Redis Alert Transition Script
# --------------------------------------------------

ALERT_TRANSITION_SCRIPT = """
local active_key = KEYS[1]
local outbox_key = KEYS[2]

local alert_type = ARGV[1]
local should_be_active = ARGV[2]
local new_alert_id = ARGV[3]
local event_id = ARGV[4]
local vehicle_id = ARGV[5]
local severity = ARGV[6]
local current_value = ARGV[7]
local threshold = ARGV[8]
local event_time = ARGV[9]

local existing_alert_id = redis.call(
    'HGET', active_key, alert_type
)

if should_be_active == '1' then

    if existing_alert_id then
        return 0
    end

    redis.call(
        'HSET', active_key, alert_type, new_alert_id
    )

    redis.call(
        'XADD', outbox_key, '*',
        'event_id', event_id,
        'alert_id', new_alert_id,
        'vehicle_id', vehicle_id,
        'alert_type', alert_type,
        'severity', severity,
        'event_status', 'TRIGGERED',
        'current_value', current_value,
        'threshold', threshold,
        'event_time', event_time
    )

    return 1

else

    if not existing_alert_id then
        return 0
    end

    redis.call(
        'HDEL', active_key, alert_type
    )

    redis.call(
        'XADD', outbox_key, '*',
        'event_id', event_id,
        'alert_id', existing_alert_id,
        'vehicle_id', vehicle_id,
        'alert_type', alert_type,
        'severity', severity,
        'event_status', 'RESOLVED',
        'current_value', current_value,
        'threshold', threshold,
        'event_time', event_time
    )

    return 1

end
"""


# --------------------------------------------------
# Alert Consumer
# --------------------------------------------------

class AlertConsumer:

    def __init__(self):

        # Redis connection
        self.redis_client = redis.Redis(
            host="localhost",
            port=6379,
            decode_responses=True
        )

        # Kafka connection
        self.consumer = Consumer(KAFKA_CONFIG)
        self.consumer.subscribe([KAFKA_TOPIC])

        # Register atomic Redis transition script
        self.alert_transition_script = (
            self.redis_client.register_script(
                ALERT_TRANSITION_SCRIPT
            )
        )

        # Inactivity monitor controls
        self.stop_monitor = threading.Event()
        self.monitor_thread = None

        print("Alert consumer initialized.")

    # --------------------------------------------------
    # Connection Checks
    # --------------------------------------------------

    def check_connections(self):

        self.redis_client.ping()
        print("Redis connection: OK")

        print("Kafka topic:", KAFKA_TOPIC)
        print("Consumer group:", KAFKA_CONFIG["group.id"])

    # --------------------------------------------------
    # Alert Lifecycle Management
    # --------------------------------------------------

    def transition_alert(
        self,
        vehicle_id,
        alert_type,
        should_be_active,
        severity,
        current_value,
        threshold,
        source_event_id,
        event_time
    ):

        active_key = f"fleet:alerts:active:{vehicle_id}"
        outbox_key = "fleet:alerts:outbox"

        status = (
            "TRIGGERED"
            if should_be_active
            else "RESOLVED"
        )

        # Deterministic event ID for replay protection
        event_id = str(
            uuid.uuid5(
                uuid.NAMESPACE_URL,
                f"{source_event_id}:{alert_type}:{status}"
            )
        )

        new_alert_id = str(uuid.uuid4())

        result = self.alert_transition_script(
            keys=[
                active_key,
                outbox_key
            ],
            args=[
                alert_type,
                "1" if should_be_active else "0",
                new_alert_id,
                event_id,
                vehicle_id,
                severity,
                str(float(current_value)),
                str(float(threshold)),
                event_time
            ]
        )

        if result == 1:

            print(
                f"{status}: {alert_type} "
                f"| Vehicle: {vehicle_id} "
                f"| Value: {current_value}"
            )

        return result == 1

    # --------------------------------------------------
    # Telemetry Processing
    # --------------------------------------------------

    def process_telemetry(self, event):

        vehicle_id = event["vehicle_id"]
        event_id = event["event_id"]
        event_time = event["timestamp"]

        speed = float(event["speed"])
        fuel_level = float(event["fuel_level"])

        # Parse telemetry timestamp
        timestamp = datetime.fromisoformat(
            event_time.replace("Z", "+00:00")
        )

        if timestamp.tzinfo is None:
            timestamp = timestamp.replace(
                tzinfo=timezone.utc
            )

        event_epoch = timestamp.timestamp()

        # Track vehicle last seen independently
        # of the live Redis vehicle hashes

        self.redis_client.zadd(
            "fleet:alerts:last_seen",
            {vehicle_id: event_epoch}
        )

        self.redis_client.sadd(
            "fleet:alerts:vehicles",
            vehicle_id
        )

        # Fresh telemetry resolves an existing inactive alert

        self.transition_alert(
            vehicle_id=vehicle_id,
            alert_type="INACTIVE",
            should_be_active=False,
            severity="WARNING",
            current_value=0,
            threshold=INACTIVITY_THRESHOLD_SECONDS,
            source_event_id=event_id,
            event_time=event_time
        )

        # 1. LOW FUEL ALERT

        low_fuel = fuel_level <= LOW_FUEL_THRESHOLD

        self.transition_alert(
            vehicle_id=vehicle_id,
            alert_type="LOW_FUEL",
            should_be_active=low_fuel,
            severity="WARNING",
            current_value=fuel_level,
            threshold=LOW_FUEL_THRESHOLD,
            source_event_id=event_id,
            event_time=event_time
        )

        # 2. OVERSPEED ALERT

        overspeed = speed > OVERSPEED_THRESHOLD

        self.transition_alert(
            vehicle_id=vehicle_id,
            alert_type="OVERSPEED",
            should_be_active=overspeed,
            severity="CRITICAL",
            current_value=speed,
            threshold=OVERSPEED_THRESHOLD,
            source_event_id=event_id,
            event_time=event_time
        )

        # 3. PROLONGED IDLE ALERT

        idle_key = f"fleet:alerts:idle_since:{vehicle_id}"

        if speed <= 0:

            # Set idle start time only once
            self.redis_client.set(
                idle_key,
                event_epoch,
                nx=True
            )

            idle_since = float(
                self.redis_client.get(idle_key)
            )

            idle_duration = max(
                0,
                event_epoch - idle_since
            )

            prolonged_idle = (
                idle_duration >= PROLONGED_IDLE_SECONDS
            )

            self.transition_alert(
                vehicle_id=vehicle_id,
                alert_type="PROLONGED_IDLE",
                should_be_active=prolonged_idle,
                severity="WARNING",
                current_value=idle_duration,
                threshold=PROLONGED_IDLE_SECONDS,
                source_event_id=event_id,
                event_time=event_time
            )

        else:

            # Vehicle started moving: reset idle timer
            self.redis_client.delete(idle_key)

            self.transition_alert(
                vehicle_id=vehicle_id,
                alert_type="PROLONGED_IDLE",
                should_be_active=False,
                severity="WARNING",
                current_value=0,
                threshold=PROLONGED_IDLE_SECONDS,
                source_event_id=event_id,
                event_time=event_time
            )

    # --------------------------------------------------
    # Kafka Processing Loop
    # --------------------------------------------------

    def run(self):

        print("\nStarting live alert processing...")
        print("Listening to:", KAFKA_TOPIC)
        print("Press CTRL+C to stop.\n")

        # Start inactivity monitoring
        self.start_inactivity_monitor()

        try:

            while True:

                message = self.consumer.poll(1.0)

                if message is None:
                    continue

                # Kafka message errors
                if message.error():

                    if message.error().code() == KafkaError._PARTITION_EOF:
                        continue

                    raise RuntimeError(
                        f"Kafka error: {message.error()}"
                    )

                try:

                    # Decode JSON telemetry
                    event = json.loads(
                        message.value().decode("utf-8")
                    )

                    if not isinstance(event, dict):
                        raise ValueError(
                            "Telemetry must be a JSON object"
                        )

                    # Process all alert conditions
                    self.process_telemetry(event)

                    # Commit only after successful Redis processing
                    self.consumer.commit(
                        message=message,
                        asynchronous=False
                    )

                except Exception as error:

                    print(
                        "\nTelemetry processing failed:",
                        error
                    )

                    print(
                        "Stopping consumer without committing "
                        "the failed message."
                    )

                    # Fail-stop: the message remains uncommitted
                    # and can be replayed after restart.
                    raise

        finally:

            self.stop_monitor.set()

    # --------------------------------------------------
    # Inactivity Detection
    # --------------------------------------------------

    def sweep_inactive_vehicles(self):

        now = datetime.now(timezone.utc)
        now_epoch = now.timestamp()

        cutoff = (
            now_epoch - INACTIVITY_THRESHOLD_SECONDS
        )

        stale_vehicles = self.redis_client.zrangebyscore(
            "fleet:alerts:last_seen",
            "-inf",
            cutoff,
            withscores=True
        )

        for vehicle_id, last_seen_epoch in stale_vehicles:

            age = now_epoch - last_seen_epoch

            last_seen = datetime.fromtimestamp(
                last_seen_epoch,
                tz=timezone.utc
            ).isoformat()

            # Stable ID for this inactivity episode
            source_event_id = (
                f"inactive:{vehicle_id}:{last_seen}"
            )

            self.transition_alert(
                vehicle_id=vehicle_id,
                alert_type="INACTIVE",
                should_be_active=True,
                severity="WARNING",
                current_value=age,
                threshold=INACTIVITY_THRESHOLD_SECONDS,
                source_event_id=source_event_id,
                event_time=now.isoformat()
            )

    # --------------------------------------------------
    # Background Inactivity Monitor
    # --------------------------------------------------

    def run_inactivity_monitor(self):

        print("Inactivity monitor started...")

        while not self.stop_monitor.wait(
            INACTIVITY_CHECK_INTERVAL
        ):

            try:

                self.sweep_inactive_vehicles()

            except Exception as error:

                print(
                    "Inactivity monitor error:",
                    error
                )

    def start_inactivity_monitor(self):

        if (
            self.monitor_thread
            and self.monitor_thread.is_alive()
        ):
            return

        self.stop_monitor.clear()

        self.monitor_thread = threading.Thread(
            target=self.run_inactivity_monitor,
            daemon=True
        )

        self.monitor_thread.start()

    # --------------------------------------------------
    # Cleanup
    # --------------------------------------------------

    def close(self):

        self.stop_monitor.set()

        if self.monitor_thread:
            self.monitor_thread.join(timeout=5)

        self.consumer.close()
        self.redis_client.close()

        print("Alert consumer closed.")


# --------------------------------------------------
# Entry Point
# --------------------------------------------------

if __name__ == "__main__":

    alert_consumer = AlertConsumer()

    try:

        alert_consumer.check_connections()
        alert_consumer.run()

    except KeyboardInterrupt:

        print("\nStopping alert consumer...")

    finally:

        alert_consumer.close()
