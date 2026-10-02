# api/schemas/auth.py
from datetime import date
from typing import Optional

from pydantic import BaseModel, EmailStr, Field


# ---------- Shared ----------

class UserPublic(BaseModel):
    id: int
    email: str
    role: str


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: UserPublic


# ---------- Login ----------

class LoginRequest(BaseModel):
    email: EmailStr
    password: str


# ---------- Register ----------

class RegisterRequest(BaseModel):
    email: EmailStr
    password: str = Field(min_length=6, max_length=128)

    first_name: str = Field(min_length=1, max_length=100)
    last_name: str = Field(min_length=1, max_length=100)
    phone: str = Field(min_length=3, max_length=30)
    date_of_birth: date
    passport_number: str = Field(min_length=3, max_length=50)
    address: Optional[str] = Field(default=None, max_length=500)