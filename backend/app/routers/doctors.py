"""
Doctor endpoints: list, get, create, update, delete.

Permission rule: any logged-in user can VIEW all doctors (it's a
shared team CRM), but only the person who ADDED a doctor — or an
Admin — can edit or delete that doctor's record. This is called
'ownership-based' permission, different from Module 1's role-based
permission. Both patterns are common; you'll use whichever fits.
"""

import uuid

from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from sqlalchemy import or_

from app.core.database import get_db
from app.core.deps import get_current_user
from app.models.doctor import Doctor
from app.models.user import User, UserRole
from app.schemas.doctor import DoctorCreate, DoctorUpdate, DoctorOut

router = APIRouter(prefix="/api/doctors", tags=["Doctors"])


def _get_doctor_or_404(doctor_id: uuid.UUID, db: Session) -> Doctor:
    doctor = db.query(Doctor).filter(Doctor.id == doctor_id).first()
    if not doctor:
        raise HTTPException(status_code=404, detail="Doctor not found.")
    return doctor


def _ensure_can_edit(doctor: Doctor, current_user: User) -> None:
    """The gate: only the doctor's creator or an Admin may modify it."""
    is_owner = doctor.created_by_id == current_user.id
    is_admin = current_user.role == UserRole.ADMIN
    if not (is_owner or is_admin):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only the MR who added this doctor, or an Admin, can modify this record.",
        )


@router.post("", response_model=DoctorOut, status_code=status.HTTP_201_CREATED)
def create_doctor(
    payload: DoctorCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    doctor = Doctor(**payload.model_dump(), created_by_id=current_user.id)
    db.add(doctor)
    db.commit()
    db.refresh(doctor)
    return doctor


@router.get("", response_model=list[DoctorOut])
def list_doctors(
    search: str | None = Query(None, description="Search by name, hospital, or specialization"),
    region: str | None = Query(None),
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=200),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Pagination explained: skip/limit lets the frontend request data
    in pages instead of all at once — e.g. skip=0&limit=50 is 'page 1',
    skip=50&limit=50 is 'page 2'. Essential once there are thousands
    of doctors; without it, one request could try to load everything.
    """
    query = db.query(Doctor)

    if search:
        # ilike = case-insensitive "contains" search (SQL LIKE).
        # Wrapping in %...% means it matches ANYWHERE in the text.
        pattern = f"%{search}%"
        query = query.filter(
            or_(
                Doctor.full_name.ilike(pattern),
                Doctor.hospital.ilike(pattern),
                Doctor.specialization.ilike(pattern),
            )
        )

    if region:
        query = query.filter(Doctor.region == region)

    return query.order_by(Doctor.full_name).offset(skip).limit(limit).all()


@router.get("/{doctor_id}", response_model=DoctorOut)
def get_doctor(
    doctor_id: uuid.UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return _get_doctor_or_404(doctor_id, db)


@router.put("/{doctor_id}", response_model=DoctorOut)
def update_doctor(
    doctor_id: uuid.UUID,
    payload: DoctorUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    doctor = _get_doctor_or_404(doctor_id, db)
    _ensure_can_edit(doctor, current_user)

    # exclude_unset=True means: only update fields the frontend
    # actually sent, leaving everything else untouched.
    updates = payload.model_dump(exclude_unset=True)
    for field, value in updates.items():
        setattr(doctor, field, value)

    db.commit()
    db.refresh(doctor)
    return doctor


@router.delete("/{doctor_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_doctor(
    doctor_id: uuid.UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    doctor = _get_doctor_or_404(doctor_id, db)
    _ensure_can_edit(doctor, current_user)
    db.delete(doctor)
    db.commit()
    return None
