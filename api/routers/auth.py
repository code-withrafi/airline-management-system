# api/routers/auth.py
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.models.user import User, UserRole
from app.repositories.user_repository import UserRepository
from app.services.auth_service import AuthService
from app.services.exceptions import (
    AuthenticationError,
    DatabaseOperationError,
    ResourceConflictError,
    ValidationError,
)
from app.services.passenger_service import PassengerService
from api.deps import get_db, get_current_user
from api.schemas.auth import (
    LoginRequest,
    RegisterRequest,
    TokenResponse,
    UserPublic,
)
from api.security_jwt import create_access_token

router = APIRouter()


# ---------- Helpers ----------

def _to_user_public(user: User) -> UserPublic:
    return UserPublic(
        id=user.id,
        email=user.email,
        role=user.role.value,
    )


def _build_token(user_id: int, role: UserRole) -> str:
    return create_access_token(subject=user_id, extra={"role": role.value})


# ---------- Login ----------

@router.post("/login", response_model=TokenResponse)
def login(payload: LoginRequest, db: Session = Depends(get_db)):
    """Passenger login. Non-passengers receive 403."""
    try:
        result = AuthService(db).authenticate(
            email=payload.email,
            password=payload.password,
        )
    except AuthenticationError as exc:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=str(exc),
        )

    if result.role != UserRole.PASSENGER:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="This app is for passengers only.",
        )

    return TokenResponse(
        access_token=_build_token(result.user_id, result.role),
        user=UserPublic(
            id=result.user_id,
            email=result.email,
            role=result.role.value,
        ),
    )


# ---------- Register ----------

@router.post(
    "/register",
    response_model=TokenResponse,
    status_code=status.HTTP_201_CREATED,
)
def register(payload: RegisterRequest, db: Session = Depends(get_db)):
    """
    Create a new passenger account and return a JWT immediately,
    so the user is logged in right after signing up.
    """
    try:
        passenger = PassengerService(db).create_passenger_with_user(
            email=payload.email,
            password=payload.password,
            first_name=payload.first_name,
            last_name=payload.last_name,
            phone=payload.phone,
            date_of_birth=payload.date_of_birth,
            passport_number=payload.passport_number,
            address=payload.address,
        )
    except ValidationError as exc:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=str(exc),
        )
    except ResourceConflictError as exc:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=str(exc),
        )
    except DatabaseOperationError as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(exc),
        )

    # passenger.user_id points to the freshly created User
    user = UserRepository(db).get_by_id(passenger.user_id)

    return TokenResponse(
        access_token=_build_token(user.id, user.role),
        user=_to_user_public(user),
    )


# ---------- Me ----------

@router.get("/me", response_model=UserPublic)
def me(user: User = Depends(get_current_user)):
    return _to_user_public(user)