from fastapi import APIRouter, HTTPException

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

@router.get("/speed")
def speed_trend():
    return {
        "speed_trend": get_speed_trend()
    }

@router.get("/fuel")
def fuel_trend():
    return {
        "fuel_trend": get_fuel_trend()
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
def vehicle_history(vehicle_id: str):
    history = get_vehicle_history(vehicle_id)

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