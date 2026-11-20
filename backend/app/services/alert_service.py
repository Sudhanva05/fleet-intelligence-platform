
from collections import Counter

from backend.app.services.redis_service import redis_client
from backend.app.services.clickhouse_service import execute_query


# --------------------------------------------------
# CONFIGURATION
# --------------------------------------------------

ACTIVE_ALERT_PREFIX = "fleet:alerts:active:"

ALERT_TABLE = "vehicle_alert_events"


# --------------------------------------------------
# HELPERS
# --------------------------------------------------

def format_alert_row(row):

    return {
        "event_id": str(row[0]),
        "alert_id": str(row[1]),
        "vehicle_id": str(row[2]),
        "alert_type": str(row[3]),
        "severity": str(row[4]),
        "event_status": str(row[5]),
        "current_value": float(row[6]),
        "threshold": float(row[7]),
        "event_time": str(row[8])
    }


# --------------------------------------------------
# GET ACTIVE ALERTS
# --------------------------------------------------

def get_active_alerts():

    active_refs = []

    # Redis is the source of truth for current active state.
    for key in redis_client.scan_iter(
        match=f"{ACTIVE_ALERT_PREFIX}*"
    ):

        active_alerts = redis_client.hgetall(key)

        if not active_alerts:
            continue

        vehicle_id = key[len(ACTIVE_ALERT_PREFIX):]

        for alert_type, alert_id in active_alerts.items():

            active_refs.append({
                "vehicle_id": vehicle_id,
                "alert_type": alert_type,
                "alert_id": alert_id
            })

    if not active_refs:
        return []

    alert_ids = [
        item["alert_id"]
        for item in active_refs
    ]

    # Fetch the latest persisted event for each active alert.
    result = execute_query(
        f"""
        SELECT
            toString(event_id),
            toString(alert_id),
            vehicle_id,
            alert_type,
            severity,
            event_status,
            current_value,
            threshold,
            event_time
        FROM {ALERT_TABLE} FINAL
        WHERE toString(alert_id) IN {{alert_ids:Array(String)}}
        ORDER BY event_time DESC
        LIMIT 1 BY alert_id
        """,
        parameters={
            "alert_ids": alert_ids
        }
    )

    persisted_alerts = {
        str(row[1]): format_alert_row(row)
        for row in result.result_rows
    }

    alerts = []

    for item in active_refs:

        alert_id = item["alert_id"]

        alert = persisted_alerts.get(alert_id)

        if alert:

            alerts.append(alert)

        else:

            # The Redis trigger may exist before the
            # ClickHouse history writer persists its event.
            alerts.append({
                "event_id": None,
                "alert_id": alert_id,
                "vehicle_id": item["vehicle_id"],
                "alert_type": item["alert_type"],
                "severity": "UNKNOWN",
                "event_status": "TRIGGERED",
                "current_value": None,
                "threshold": None,
                "event_time": None
            })

    return alerts


# --------------------------------------------------
# GET ALERT HISTORY
# --------------------------------------------------

def get_alert_history(
    vehicle_id=None,
    alert_type=None,
    severity=None,
    event_status=None,
    start_time=None,
    end_time=None,
    limit=100,
    offset=0
):

    conditions = []
    parameters = {}

    # Vehicle filter
    if vehicle_id:

        conditions.append(
            "vehicle_id = {vehicle_id:String}"
        )

        parameters["vehicle_id"] = vehicle_id

    # Alert type filter
    if alert_type:

        conditions.append(
            "alert_type = {alert_type:String}"
        )

        parameters["alert_type"] = alert_type

    # Severity filter
    if severity:

        conditions.append(
            "severity = {severity:String}"
        )

        parameters["severity"] = severity

    # Event status filter
    if event_status:

        conditions.append(
            "event_status = {event_status:String}"
        )

        parameters["event_status"] = event_status

    # Start time filter
    if start_time:

        conditions.append(
            """
            event_time >= parseDateTime64BestEffort(
                {start_time:String}, 3, 'UTC'
            )
            """
        )

        parameters["start_time"] = start_time

    # End time filter
    if end_time:

        conditions.append(
            """
            event_time <= parseDateTime64BestEffort(
                {end_time:String}, 3, 'UTC'
            )
            """
        )

        parameters["end_time"] = end_time

    where_clause = (
        f"WHERE {' AND '.join(conditions)}"
        if conditions else ""
    )

    # Total matching records
    count_result = execute_query(
        f"""
        SELECT count()
        FROM {ALERT_TABLE} FINAL
        {where_clause}
        """,
        parameters=parameters
    )

    total = count_result.result_rows[0][0]

    # Paginated alert history
    history_result = execute_query(
        f"""
        SELECT
            toString(event_id),
            toString(alert_id),
            vehicle_id,
            alert_type,
            severity,
            event_status,
            current_value,
            threshold,
            event_time
        FROM {ALERT_TABLE} FINAL
        {where_clause}
        ORDER BY event_time DESC, event_id DESC
        LIMIT {{limit:UInt32}}
        OFFSET {{offset:UInt32}}
        """,
        parameters={
            **parameters,
            "limit": limit,
            "offset": offset
        }
    )

    alerts = [
        format_alert_row(row)
        for row in history_result.result_rows
    ]

    return {
        "total": total,
        "limit": limit,
        "offset": offset,
        "alerts": alerts
    }


# --------------------------------------------------
# ALERT SUMMARY
# --------------------------------------------------

def get_alert_summary():

    active_alerts = get_active_alerts()

    total_active = len(active_alerts)

    severity_counts = Counter(
        alert["severity"]
        for alert in active_alerts
    )

    type_counts = Counter(
        alert["alert_type"]
        for alert in active_alerts
    )

    return {
        "total_active_alerts": total_active,
        "critical_alerts": severity_counts.get(
            "CRITICAL", 0
        ),
        "warning_alerts": severity_counts.get(
            "WARNING", 0
        ),
        "unknown_severity_alerts": severity_counts.get(
            "UNKNOWN", 0
        ),
        "alerts_by_type": dict(type_counts),
        "alerts_by_severity": dict(severity_counts)
    }
