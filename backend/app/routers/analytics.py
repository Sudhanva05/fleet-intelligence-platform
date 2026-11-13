from fastapi import APIRouter

from backend.app.services.clickhouse_service import (
    get_fleet_statistics,
    get_total_events
)

router = APIRouter(
    prefix="/analytics",
    tags=["Analytics"]
)


@router.get("/overview")
def analytics_overview():
    stats = get_fleet_statistics()

    return {
        "total_events": stats[0],
        "total_vehicles": stats[1],
        "average_speed": stats[2],
        "average_fuel": stats[3]
    }


@router.get("/events")
def total_events():
    return {
        "total_events": get_total_events()
    }