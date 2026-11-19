from fastapi import APIRouter, HTTPException

from backend.app.services.redis_service import (
    get_all_vehicles,
    get_vehicle_by_id
)

from backend.app.services.redis_service import (
    get_operational_summary
)
router = APIRouter(
    prefix="/vehicles",
    tags=["Vehicles"]
)


# 1. List all vehicles
@router.get("/")
def list_vehicles():
    vehicles = get_all_vehicles()

    return {
        "total_vehicles": len(vehicles),
        "vehicles": vehicles
    }


# 2. Vehicle summary
@router.get("/summary")
def vehicle_summary():
    vehicles = get_all_vehicles()

    active = sum(
        1 for vehicle in vehicles
        if vehicle["status"] == "active"
    )

    stale = len(vehicles) - active

    return {
        "total_vehicles": len(vehicles),
        "active_vehicles": active,
        "stale_vehicles": stale
    }

@router.get("/operational-summary")
def operational_summary():
    return get_operational_summary()


# 3. Individual vehicle details — keep this LAST
@router.get("/{vehicle_id}")
def vehicle_details(vehicle_id: str):
    vehicle = get_vehicle_by_id(vehicle_id)

    if not vehicle:
        raise HTTPException(
            status_code=404,
            detail="Vehicle not found"
        )

    return vehicle