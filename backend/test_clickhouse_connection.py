from backend.app.services.clickhouse_service import (
    check_clickhouse_connection,
    get_fleet_statistics
)

print("ClickHouse version:", check_clickhouse_connection())

print("Fleet statistics:")
print(get_fleet_statistics())