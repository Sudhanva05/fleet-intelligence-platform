
from datetime import datetime

from fastapi import APIRouter, Query

from backend.app.services.alert_service import (
    get_active_alerts,
    get_alert_history,
    get_alert_summary
)


router = APIRouter(
    prefix="/alerts",
    tags=["Alerts"]
)


# --------------------------------------------------
# 1. ACTIVE ALERTS
# --------------------------------------------------

@router.get("/active")
def active_alerts():

    alerts = get_active_alerts()

    return {
        "total": len(alerts),
        "alerts": alerts
    }


# --------------------------------------------------
# 2. ALERT SUMMARY
# --------------------------------------------------

@router.get("/summary")
def alert_summary():

    return get_alert_summary()


# --------------------------------------------------
# 3. ALERT HISTORY
# --------------------------------------------------

@router.get("/history")
def alert_history(

    vehicle_id: str | None = None,

    alert_type: str | None = None,

    severity: str | None = None,

    event_status: str | None = None,

    start_time: datetime | None = None,

    end_time: datetime | None = None,

    limit: int = Query(
        default=100,
        ge=1,
        le=500
    ),

    offset: int = Query(
        default=0,
        ge=0
    )

):

    if (
        start_time is not None
        and end_time is not None
        and start_time > end_time
    ):
        from fastapi import HTTPException

        raise HTTPException(
            status_code=400,
            detail="start_time cannot be after end_time"
        )

    return get_alert_history(
        vehicle_id=vehicle_id,
        alert_type=alert_type,
        severity=severity,
        event_status=event_status,
        start_time=(
            start_time.isoformat()
            if start_time else None
        ),
        end_time=(
            end_time.isoformat()
            if end_time else None
        ),
        limit=limit,
        offset=offset
    )


# --------------------------------------------------
# 4. VEHICLE-SPECIFIC ALERT HISTORY
# --------------------------------------------------

@router.get("/vehicle/{vehicle_id}")
def vehicle_alert_history(

    vehicle_id: str,

    limit: int = Query(
        default=100,
        ge=1,
        le=500
    ),

    offset: int = Query(
        default=0,
        ge=0
    )

):

    return get_alert_history(
        vehicle_id=vehicle_id,
        limit=limit,
        offset=offset
    )
