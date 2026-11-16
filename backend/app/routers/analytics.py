
from datetime import datetime

from fastapi import APIRouter, HTTPException, Query

from backend.app.services.clickhouse_service import (
    get_fleet_statistics,
    get_total_events,
    get_speed_trend,
    get_fuel_trend,
    get_vehicle_analytics,
    get_vehicle_history,
    get_analytics_vehicles
)

router = APIRouter(
    prefix="/analytics",
    tags=["Analytics"]
)


def parse_datetime(value: str | None):
    if not value or not value.strip():
        return None

    try:
        return datetime.fromisoformat(
            value.strip().replace("Z", "+00:00")
        )
    except ValueError:
        raise HTTPException(
            status_code=422,
            detail="Invalid datetime format. Use ISO 8601."
        )


def validate_date_range(start_time, end_time):
    if start_time and end_time and start_time > end_time:
        raise HTTPException(
            status_code=400,
            detail="start_time must be before end_time"
        )


@router.get("/overview")
def analytics_overview(
    start_time: str | None = Query(default=None),
    end_time: str | None = Query(default=None)
):
    start = parse_datetime(start_time)
    end = parse_datetime(end_time)
    validate_date_range(start, end)

    stats = get_fleet_statistics(start, end)

    return {
        "total_events": stats[0],
        "total_vehicles": stats[1],
        "average_speed": stats[2],
        "average_fuel": stats[3]
    }


@router.get("/events")
def total_events(
    start_time: str | None = Query(default=None),
    end_time: str | None = Query(default=None)
):
    start = parse_datetime(start_time)
    end = parse_datetime(end_time)
    validate_date_range(start, end)

    return {
        "total_events": get_total_events(start, end)
    }


@router.get("/speed")
def speed_trend(
    start_time: str | None = Query(default=None),
    end_time: str | None = Query(default=None)
):
    start = parse_datetime(start_time)
    end = parse_datetime(end_time)
    validate_date_range(start, end)

    return {
        "speed_trend": get_speed_trend(start, end)
    }


@router.get("/fuel")
def fuel_trend(
    start_time: str | None = Query(default=None),
    end_time: str | None = Query(default=None)
):
    start = parse_datetime(start_time)
    end = parse_datetime(end_time)
    validate_date_range(start, end)

    return {
        "fuel_trend": get_fuel_trend(start, end)
    }


@router.get("/vehicle/{vehicle_id}")
def vehicle_analytics(vehicle_id: str):
    result = get_vehicle_analytics(vehicle_id)

    if result is None:
        raise HTTPException(
            status_code=404,
            detail="No analytics found for this vehicle"
        )

    return {
        "vehicle_id": vehicle_id,
        "analytics": result
    }


@router.get("/vehicle/{vehicle_id}/history")
def vehicle_history(
    vehicle_id: str,
    start_time: str | None = Query(default=None),
    end_time: str | None = Query(default=None)
):
    start = parse_datetime(start_time)
    end = parse_datetime(end_time)
    validate_date_range(start, end)

    history = get_vehicle_history(
        vehicle_id,
        start,
        end
    )

    if not history:
        raise HTTPException(
            status_code=404,
            detail="No history found for this vehicle"
        )

    return {
        "vehicle_id": vehicle_id,
        "total_records": len(history),
        "history": history
    }


@router.get("/vehicles")
def analytics_vehicles():
    return {
        "vehicles": get_analytics_vehicles()
    }
