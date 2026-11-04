# api/routers/schedule.py
"""
Flight schedule generation endpoint.

Admin-only. Triggers bulk generation of flights for a date range.
"""

from datetime import date

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from app.models.user import User, UserRole
from app.services.schedule.service import (
    FlightScheduleGenerator,
    ScheduleGenerationError,
)
from api.deps import get_db, get_current_user


router = APIRouter()


# ------------------------------------------------------------------
# Schemas
# ------------------------------------------------------------------

class GenerateScheduleRequest(BaseModel):
    start_date: date
    end_date: date
    overwrite_existing: bool = False


class GenerateScheduleResponse(BaseModel):
    created: int
    deleted_existing: int
    skipped_no_aircraft: int
    skipped_duplicate: int
    errors: list[str]
    duration_seconds: float
    by_route: dict[int, int]


# ------------------------------------------------------------------
# Auth helper
# ------------------------------------------------------------------

def require_admin(user: User = Depends(get_current_user)) -> User:
    if user.role != UserRole.ADMIN:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin access required.",
        )
    return user


# ------------------------------------------------------------------
# Endpoint
# ------------------------------------------------------------------

@router.post(
    "/generate",
    response_model=GenerateScheduleResponse,
)
def generate_schedule(
    payload: GenerateScheduleRequest,
    _user: User = Depends(require_admin),
    db: Session = Depends(get_db),
):
    """
    Generate flights for the given date range across all active routes.

    Uses aircraft round-trip pairing, dynamic fares, and skips flights
    when no aircraft is available.
    """
    try:
        generator = FlightScheduleGenerator(db)
        result = generator.generate(
            start_date=payload.start_date,
            end_date=payload.end_date,
            overwrite_existing=payload.overwrite_existing,
        )
    except ScheduleGenerationError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(exc),
        )
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Generation failed: {exc}",
        )

    return GenerateScheduleResponse(
        created=result["created"],
        deleted_existing=result["deleted_existing"],
        skipped_no_aircraft=result["skipped_no_aircraft"],
        skipped_duplicate=result["skipped_duplicate"],
        errors=result["errors"],
        duration_seconds=result["duration_seconds"],
        by_route=result["by_route"],
    )