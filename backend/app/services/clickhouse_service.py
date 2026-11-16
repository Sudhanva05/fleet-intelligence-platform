
import os
from datetime import datetime, timezone

import clickhouse_connect
from dotenv import load_dotenv

load_dotenv()


# --------------------------------------------------
# CLICKHOUSE CONNECTION
# --------------------------------------------------

def execute_query(query, parameters=None):
    client = clickhouse_connect.get_client(
        host=os.getenv("CLICKHOUSE_HOST", "localhost"),
        port=int(os.getenv("CLICKHOUSE_PORT", "8123")),
        username=os.getenv("CLICKHOUSE_USER"),
        password=os.getenv("CLICKHOUSE_PASSWORD"),
        database=os.getenv("CLICKHOUSE_DATABASE")
    )

    try:
        return client.query(query, parameters=parameters)
    finally:
        client.close()


def check_clickhouse_connection():
    result = execute_query("SELECT version()")
    return result.result_rows[0][0]


# --------------------------------------------------
# REUSABLE DATE FILTER
# --------------------------------------------------

def normalize_datetime(value: datetime) -> str:
    """
    Convert datetime into UTC ISO format.

    Naive datetimes are treated as UTC.
    Timezone-aware datetimes are converted to UTC.
    """
    if value.tzinfo is None:
        value = value.replace(tzinfo=timezone.utc)
    else:
        value = value.astimezone(timezone.utc)

    return value.isoformat()


def build_time_filters(
    start_time: datetime | None = None,
    end_time: datetime | None = None
):
    """
    Build reusable ClickHouse timestamp conditions.
    """

    conditions = []
    parameters = {}

    if start_time is not None:
        conditions.append(
            "timestamp >= parseDateTime64BestEffort("
            "{start_time:String}, 6, 'UTC')"
        )

        parameters["start_time"] = normalize_datetime(start_time)

    if end_time is not None:
        conditions.append(
            "timestamp <= parseDateTime64BestEffort("
            "{end_time:String}, 6, 'UTC')"
        )

        parameters["end_time"] = normalize_datetime(end_time)

    return conditions, parameters


# --------------------------------------------------
# TOTAL EVENTS
# --------------------------------------------------

def get_total_events(
    start_time: datetime | None = None,
    end_time: datetime | None = None
):
    conditions, parameters = build_time_filters(
        start_time,
        end_time
    )

    where_clause = (
        f"WHERE {' AND '.join(conditions)}"
        if conditions else ""
    )

    query = f"""
        SELECT count()
        FROM vehicle_telemetry
        {where_clause}
    """

    result = execute_query(
        query,
        parameters=parameters
    )

    return result.result_rows[0][0]


# --------------------------------------------------
# FLEET STATISTICS
# --------------------------------------------------

def get_fleet_statistics(
    start_time: datetime | None = None,
    end_time: datetime | None = None
):
    conditions, parameters = build_time_filters(
        start_time,
        end_time
    )

    where_clause = (
        f"WHERE {' AND '.join(conditions)}"
        if conditions else ""
    )

    query = f"""
        SELECT
            count() AS total_events,
            uniqExact(vehicle_id) AS total_vehicles,
            ifNull(round(avgOrNull(speed), 2), 0) AS average_speed,
            ifNull(round(avgOrNull(fuel_level), 2), 0) AS average_fuel
        FROM vehicle_telemetry
        {where_clause}
    """

    result = execute_query(
        query,
        parameters=parameters
    )

    return result.result_rows[0]


# --------------------------------------------------
# SPEED TREND
# --------------------------------------------------

def get_speed_trend(
    start_time: datetime | None = None,
    end_time: datetime | None = None
):
    conditions, parameters = build_time_filters(
        start_time,
        end_time
    )

    where_clause = (
        f"WHERE {' AND '.join(conditions)}"
        if conditions else ""
    )

    query = f"""
        SELECT
            toStartOfMinute(timestamp) AS time,
            round(avg(speed), 2) AS average_speed
        FROM vehicle_telemetry
        {where_clause}
        GROUP BY time
        ORDER BY time
    """

    result = execute_query(
        query,
        parameters=parameters
    )

    return [
        {
            "time": str(row[0]),
            "average_speed": row[1]
        }
        for row in result.result_rows
    ]


# --------------------------------------------------
# FUEL TREND
# --------------------------------------------------

def get_fuel_trend(
    start_time: datetime | None = None,
    end_time: datetime | None = None
):
    conditions, parameters = build_time_filters(
        start_time,
        end_time
    )

    where_clause = (
        f"WHERE {' AND '.join(conditions)}"
        if conditions else ""
    )

    query = f"""
        SELECT
            toStartOfMinute(timestamp) AS time,
            round(avg(fuel_level), 2) AS average_fuel
        FROM vehicle_telemetry
        {where_clause}
        GROUP BY time
        ORDER BY time
    """

    result = execute_query(
        query,
        parameters=parameters
    )

    return [
        {
            "time": str(row[0]),
            "average_fuel": row[1]
        }
        for row in result.result_rows
    ]


# --------------------------------------------------
# INDIVIDUAL VEHICLE ANALYTICS
# --------------------------------------------------

def get_vehicle_analytics(vehicle_id: str):
    result = execute_query("""
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


# --------------------------------------------------
# INDIVIDUAL VEHICLE HISTORY
# --------------------------------------------------

def get_vehicle_history(
    vehicle_id: str,
    start_time: datetime | None = None,
    end_time: datetime | None = None
):
    conditions = ["vehicle_id = {vehicle_id:UUID}"]

    parameters = {
        "vehicle_id": vehicle_id
    }

    time_conditions, time_parameters = build_time_filters(
        start_time,
        end_time
    )

    conditions.extend(time_conditions)
    parameters.update(time_parameters)

    query = f"""
        SELECT
            timestamp,
            latitude,
            longitude,
            speed,
            heading,
            fuel_level
        FROM vehicle_telemetry
        WHERE {" AND ".join(conditions)}
        ORDER BY timestamp ASC
    """

    result = execute_query(
        query,
        parameters=parameters
    )

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


# --------------------------------------------------
# ANALYTICS VEHICLES
# --------------------------------------------------

def get_analytics_vehicles():
    result = execute_query("""
        SELECT DISTINCT vehicle_id
        FROM vehicle_telemetry
        ORDER BY vehicle_id
    """)

    return [
        str(row[0])
        for row in result.result_rows
    ]
