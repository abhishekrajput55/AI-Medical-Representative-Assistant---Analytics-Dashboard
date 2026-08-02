"""
Pydantic schemas for Doctor endpoints.

DoctorCreate/DoctorUpdate = what the frontend sends us.
DoctorOut = what we're allowed to send back.
"""

import uuid
from datetime import datetime
from pydantic import BaseModel, Field


class DoctorCreate(BaseModel):
    full_name: str = Field(min_length=2, max_length=150)
    specialization: str | None = None
    hospital: str | None = None
    clinic: str | None = None
    address: str | None = None
    phone: str | None = None
    email: str | None = None
    preferred_visit_time: str | None = None
    notes: str | None = None
    region: str | None = None


class DoctorUpdate(BaseModel):
    """
    Every field is optional here, since an update might only change
    ONE field (e.g. just the phone number). This is called a
    'partial update' or PATCH-style schema.
    """
    full_name: str | None = None
    specialization: str | None = None
    hospital: str | None = None
    clinic: str | None = None
    address: str | None = None
    phone: str | None = None
    email: str | None = None
    preferred_visit_time: str | None = None
    notes: str | None = None
    region: str | None = None


class DoctorOut(BaseModel):
    id: uuid.UUID
    full_name: str
    specialization: str | None
    hospital: str | None
    clinic: str | None
    address: str | None
    phone: str | None
    email: str | None
    preferred_visit_time: str | None
    notes: str | None
    ai_summary: str | None
    region: str | None
    created_by_id: uuid.UUID
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True
