# api/routers/staff_auth.py
"""
Staff-side authentication.

The passenger `/api/auth/login` endpoint refuses non-passenger roles
by design. This router provides a parallel endpoint for admins and
staff to obtain a JWT so they can access admin-only ML endpoints.
"""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.models.user import UserRole
from app.services.auth_service import AuthService
from app.services.exceptions import AuthenticationError
from api.deps import get_db
from api.schemas.auth import LoginRequest, TokenResponse, UserPublic
from api.security_jwt import create_access_token

router = APIRouter()


@router.post("/staff-login", response_model=TokenResponse)
def staff_login(payload: LoginRequest, db: Session = Depends(get_db)):
    """
    Login for ADMIN or STAFF users.

    Rejects passengers (they must use the passenger endpoint).
    """
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

    if result.role not in (UserRole.ADMIN, UserRole.STAFF):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="This endpoint is for administrators and staff only.",
        )

    token = create_access_token(
        subject=result.user_id,
        extra={"role": result.role.value},
    )

    return TokenResponse(
        access_token=token,
        user=UserPublic(
            id=result.user_id,
            email=result.email,
            role=result.role.value,
        ),
    )