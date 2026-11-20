CREATE TABLE IF NOT EXISTS fleet_analytics.vehicle_alert_events
(
    event_id UUID,
    alert_id UUID,
    vehicle_id String,
    alert_type LowCardinality(String),
    severity LowCardinality(String),
    event_status LowCardinality(String),
    current_value Float64,
    threshold Float64,
    event_time DateTime64(3, 'UTC')
)
ENGINE = ReplacingMergeTree
ORDER BY event_id;