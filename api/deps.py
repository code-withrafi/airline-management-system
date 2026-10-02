# api/deps.py
from typing import Generator

from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError
from sqlalchemy.orm import Session

from app.config.database import SessionLocal
from app.models.passenger import Passenger
from app.models.user import User, UserRole
from app.repositories.passenger_repository import PassengerRepository
from app.repositories.user_repository import UserRepository
from api.security_jwt import decode_access_token


oauth2_scheme = OAuth2PasswordBearer(
    tokenUrl="/api/auth/login",
    auto_error=False,
)


# ------------------------------------------------------------------
# Database
# ------------------------------------------------------------------

def get_db() -> Generator[Session, None, None]:
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


# ------------------------------------------------------------------
# Authentication — User level
# ------------------------------------------------------------------

def get_current_user(
    token: str | None = Depends(oauth2_scheme),
    db: Session = Depends(get_db),
) -> User:
    """Return the authenticated User ORM object, or raise 401."""
    credentials_exc = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Not authenticated",
        headers={"WWW-Authenticate": "Bearer"},
    )

    if not token:
        raise credentials_exc

    try:
        payload = decode_access_token(token)
        user_id = payload.get("sub")
        if user_id is None:
            raise credentials_exc
    except JWTError:
        raise credentials_exc

    user = UserRepository(db).get_by_id(int(user_id))
    if user is None or not user.is_active:
        raise credentials_exc

    return user


def require_passenger(user: User = Depends(get_current_user)) -> User:
    """Only allow role == PASSENGER. Admin/Staff tokens get 403."""
    if user.role != UserRole.PASSENGER:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="This API is for passengers only.",
        )
    return user


# ------------------------------------------------------------------
# Authentication — Passenger profile level
# ------------------------------------------------------------------

def get_current_passenger(
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> Passenger:
    """
    Return the Passenger profile linked to the authenticated User.

    Raises 404 if the passenger profile doesn't exist yet.
    """
    passenger = PassengerRepository(db).get_by_user_id(user.id)
    if passenger is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Passenger profile not found. Complete your profile first.",
        )
    return passenger


def require_passenger_profile(
    user: User = Depends(require_passenger),
    db: Session = Depends(get_db),
) -> Passenger:
    """
    Combined dependency for protected passenger endpoints.

    1. Rejects non-passengers (403).
    2. Rejects tokens without a linked Passenger profile (404).
    3. Returns the Passenger ORM object — perfect for /api/bookings/*,
       /api/payments, and any endpoint that needs passenger.id.
    """
    passenger = PassengerRepository(db).get_by_user_id(user.id)
    if passenger is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Passenger profile not found.",
        )
    return passenger