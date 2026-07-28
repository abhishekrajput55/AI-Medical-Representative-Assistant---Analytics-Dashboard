"""
Pydantic schemas.

Models (in models/user.py) define what's stored in the DATABASE.
Schemas define what's allowed to travel over the API — the
"order ticket" format between frontend and backend.

Why separate them? Because we NEVER want to accidentally send
`hashed_password` back to the frontend in an API response. Schemas
let us whitelist exactly which fields go in and out.
"""

import uuid
from datetime import datetime
from pydantic import BaseModel, EmailStr, Field

from app.models.user import UserRole


class UserRegister(BaseModel):
    """What the frontend must send to create an account."""
    full_name: str = Field(min_length=2, max_length=120)
    email: EmailStr
    password: str = Field(min_length=8, max_length=72)
    role: UserRole = UserRole.MEDICAL_REPRESENTATIVE
    region: str | None = None


class UserLogin(BaseModel):
    email: EmailStr
    password: str


class UserOut(BaseModel):
    """What we're allowed to send BACK about a user. No password. Ever."""
    id: uuid.UUID
    full_name: str
    email: EmailStr
    role: UserRole
    region: str | None = None
    is_active: bool
    is_email_verified: bool
    created_at: datetime

    class Config:
        from_attributes = True  # lets Pydantic read directly from the SQLAlchemy model


class TokenResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    user: UserOut


class RefreshRequest(BaseModel):
    refresh_token: str
