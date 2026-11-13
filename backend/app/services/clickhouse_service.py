
import os

import clickhouse_connect
from dotenv import load_dotenv

load_dotenv()

client = clickhouse_connect.get_client(
    host=os.getenv("CLICKHOUSE_HOST", "localhost"),
    port=int(os.getenv("CLICKHOUSE_PORT", "8123")),
    username=os.getenv("CLICKHOUSE_USER"),
    password=os.getenv("CLICKHOUSE_PASSWORD"),
    database=os.getenv("CLICKHOUSE_DATABASE")
)


def check_clickhouse_connection():
    result = client.query("SELECT version()")
    return result.result_rows[0][0]


def get_total_events():
    result = client.query("""
        SELECT count()
        FROM vehicle_telemetry
    """)

    return result.result_rows[0][0]


def get_fleet_statistics():
    result = client.query("""
        SELECT
            count() AS total_events,
            uniqExact(vehicle_id) AS total_vehicles,
            round(avg(speed), 2) AS average_speed,
            round(avg(fuel_level), 2) AS average_fuel
        FROM vehicle_telemetry
    """)

    return result.result_rows[0]
