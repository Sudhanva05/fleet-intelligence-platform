import clickhouse_connect

client = clickhouse_connect.get_client(
    host="localhost",
    port=8123,
    username="fleet_user",
    password="fleet_dev_password",
    database="fleet_analytics"
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