# api/routers/passengers.py
from datetime import date
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, EmailStr, Field
from sqlalchemy.orm import Session

from app.models.passenger import Passenger
from app.services.exceptions import (
    DatabaseOperationError,
    ResourceConflictError,
    ResourceNotFoundError,
    ValidationError,
)
from app.services.passenger_service import PassengerService
from api.deps import get_db, require_passenger_profile

router = APIRouter()


# ------------------------------------------------------------------
# Schemas
# ------------------------------------------------------------------

class PassengerProfile(BaseModel):
    id: int
    user_id: int
    email: EmailStr
    first_name: str
    last_name: str
    phone: str
    date_of_birth: Optional[date] = None
    passport_number: str
    address: Optional[str] = None
    created_at: str
    updated_at: str


class ProfileUpdateRequest(BaseModel):
    first_name: str = Field(min_length=1, max_length=100)
    last_name: str = Field(min_length=1, max_length=100)
    phone: str = Field(min_length=3, max_length=30)
    date_of_birth: Optional[date] = None
    passport_number: str = Field(min_length=3, max_length=50)
    address: Optional[str] = Field(default=None, max_length=500)


class PasswordChangeRequest(BaseModel):
    old_password: str = Field(min_length=1)
    new_password: str = Field(min_length=6, max_length=128)


class MessageResponse(BaseModel):
    message: str


# ------------------------------------------------------------------
# Helpers
# ------------------------------------------------------------------

def _to_profile(passenger: Passenger) -> PassengerProfile:
    return PassengerProfile(
        id=passenger.id,
        user_id=passenger.user_id,
        email=passenger.user.email,
        first_name=passenger.first_name,
        last_name=passenger.last_name,
        phone=passenger.phone,
        date_of_birth=passenger.date_of_birth,
        passport_number=passenger.passport_number,
        address=passenger.address,
        created_at=passenger.created_at.isoformat() if passenger.created_at else "",
        updated_at=passenger.updated_at.isoformat() if passenger.updated_at else "",
    )


# ------------------------------------------------------------------
# Endpoints
# ------------------------------------------------------------------

@router.get("/me", response_model=PassengerProfile)
def get_my_profile(
    passenger: Passenger = Depends(require_passenger_profile),
):
    """Return the logged-in passenger's profile."""
    return _to_profile(passenger)


@router.put("/me", response_model=PassengerProfile)
def update_my_profile(
    payload: ProfileUpdateRequest,
    passenger: Passenger = Depends(require_passenger_profile),
    db: Session = Depends(get_db),
):
    """Update the logged-in passenger's profile."""
    try:
        updated = PassengerService(db).update_passenger(
            passenger.id,
            first_name=payload.first_name,
            last_name=payload.last_name,
            phone=payload.phone,
            date_of_birth=payload.date_of_birth,
            passport_number=payload.passport_number,
            address=payload.address,
        )
    except ResourceNotFoundError as exc:
        raise HTTPException(404, str(exc))
    except ResourceConflictError as exc:
        raise HTTPException(409, str(exc))
    except ValidationError as exc:
        raise HTTPException(422, str(exc))
    except DatabaseOperationError as exc:
        raise HTTPException(500, str(exc))

    return _to_profile(updated)


@router.post("/me/password", response_model=MessageResponse)
def change_my_password(
    payload: PasswordChangeRequest,
    passenger: Passenger = Depends(require_passenger_profile),
    db: Session = Depends(get_db),
):
    """
    Change the logged-in passenger's password.
    NOTE: service expects `user_id`, not `passenger_id`.
    """
    try:
        PassengerService(db).change_password(
            passenger.user_id,
            old_password=payload.old_password,
            new_password=payload.new_password,
        )
    except ResourceNotFoundError as exc:
        raise HTTPException(404, str(exc))
    except ResourceConflictError as exc:
        # Typically raised when current password is wrong
        raise HTTPException(400, str(exc))
    except ValidationError as exc:
        raise HTTPException(422, str(exc))
    except DatabaseOperationError as exc:
        raise HTTPException(500, str(exc))

    return MessageResponse(message="Password updated successfully.")