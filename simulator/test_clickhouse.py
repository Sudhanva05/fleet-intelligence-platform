
import clickhouse_connect

client = clickhouse_connect.get_client(
    host="localhost",
    port=8123,
    username="fleet_user",
    password="fleet_dev_password",
    database="fleet_analytics"
)

result = client.query("SELECT version()")

print("Connected to ClickHouse!")
print("Server version:", result.result_rows[0][0])

client.close()
