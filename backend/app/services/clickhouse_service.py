
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



def get_speed_trend():
    result = client.query("""
        SELECT
            toStartOfMinute(timestamp) AS time,
            round(avg(speed), 2) AS average_speed
        FROM vehicle_telemetry
        GROUP BY time
        ORDER BY time
    """)

    return [
        {
            "time": str(row[0]),
            "average_speed": row[1]
        }
        for row in result.result_rows
    ]


def get_fuel_trend():
    result = client.query("""
        SELECT
            toStartOfMinute(timestamp) AS time,
            round(avg(fuel_level), 2) AS average_fuel
        FROM vehicle_telemetry
        GROUP BY time
        ORDER BY time
    """)

    return [
        {
            "time": str(row[0]),
            "average_fuel": row[1]
        }
        for row in result.result_rows
    ]


def get_vehicle_analytics(vehicle_id: str):
    result = client.query("""
        SELECT
            count() AS total_events,
            round(avg(speed), 2) AS average_speed,
            round(min(speed), 2) AS minimum_speed,
            round(max(speed), 2) AS maximum_speed,
            round(avg(fuel_level), 2) AS average_fuel,
            min(timestamp) AS first_recorded,
            max(timestamp) AS last_recorded
        FROM vehicle_telemetry
        WHERE vehicle_id = {vehicle_id:UUID}
    """, parameters={"vehicle_id": vehicle_id})

    row = result.result_rows[0]

    if row[0] == 0:
        return None

    return {
        "total_events": row[0],
        "average_speed": row[1],
        "minimum_speed": row[2],
        "maximum_speed": row[3],
        "average_fuel": row[4],
        "first_recorded": str(row[5]),
        "last_recorded": str(row[6])
    }



def get_vehicle_history(vehicle_id: str):
    result = client.query("""
        SELECT
            timestamp,
            latitude,
            longitude,
            speed,
            heading,
            fuel_level
        FROM vehicle_telemetry
        WHERE vehicle_id = {vehicle_id:UUID}
        ORDER BY timestamp ASC
    """, parameters={"vehicle_id": vehicle_id})

    return [
        {
            "timestamp": str(row[0]),
            "latitude": row[1],
            "longitude": row[2],
            "speed": row[3],
            "heading": row[4],
            "fuel_level": row[5]
        }
        for row in result.result_rows
    ]
