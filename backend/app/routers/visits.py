"""
Visit log endpoints: log visits, view them, and generate AI reports.

Permission pattern: same ownership model as Doctors (Module 2) —
an MR manages their own visit logs; Admins can see/edit everything.
"""

import uuid
from datetime import date

from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.deps import get_current_user
from app.models.visit_log import VisitLog
from app.models.doctor import Doctor
from app.models.user import User, UserRole
from app.schemas.visit_log import (
    VisitLogCreate,
    VisitLogUpdate,
    VisitLogOut,
    VisitReportResponse,
    PeriodReportResponse,
)
from app.ai.report_service import generate_visit_report, generate_period_report

router = APIRouter(prefix="/api/visits", tags=["Visit Logs"])


def _get_visit_or_404(visit_id: uuid.UUID, db: Session) -> VisitLog:
    visit = db.query(VisitLog).filter(VisitLog.id == visit_id).first()
    if not visit:
        raise HTTPException(status_code=404, detail="Visit log not found.")
    return visit


def _ensure_can_edit(visit: VisitLog, current_user: User) -> None:
    is_owner = visit.mr_id == current_user.id
    is_admin = current_user.role == UserRole.ADMIN
    if not (is_owner or is_admin):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only the MR who logged this visit, or an Admin, can modify it.",
        )


@router.post("", response_model=VisitLogOut, status_code=status.HTTP_201_CREATED)
def create_visit(
    payload: VisitLogCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    doctor = db.query(Doctor).filter(Doctor.id == payload.doctor_id).first()
    if not doctor:
        raise HTTPException(status_code=404, detail="Doctor not found.")

    visit = VisitLog(**payload.model_dump(), mr_id=current_user.id)
    db.add(visit)
    db.commit()
    db.refresh(visit)
    return visit


@router.get("", response_model=list[VisitLogOut])
def list_visits(
    doctor_id: uuid.UUID | None = Query(None),
    date_from: date | None = Query(None),
    date_to: date | None = Query(None),
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=200),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    By default, MRs see only their OWN visits (their personal
    activity log). Admins and Regional/Area managers see everyone's,
    since they need visibility across the team.
    """
    query = db.query(VisitLog)

    management_roles = (UserRole.ADMIN, UserRole.REGIONAL_MANAGER, UserRole.AREA_SALES_MANAGER)
    if current_user.role not in management_roles:
        query = query.filter(VisitLog.mr_id == current_user.id)

    if doctor_id:
        query = query.filter(VisitLog.doctor_id == doctor_id)
    if date_from:
        query = query.filter(VisitLog.visit_date >= date_from)
    if date_to:
        query = query.filter(VisitLog.visit_date <= date_to)

    return query.order_by(VisitLog.visit_date.desc()).offset(skip).limit(limit).all()


@router.get("/{visit_id}", response_model=VisitLogOut)
def get_visit(
    visit_id: uuid.UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return _get_visit_or_404(visit_id, db)


@router.put("/{visit_id}", response_model=VisitLogOut)
def update_visit(
    visit_id: uuid.UUID,
    payload: VisitLogUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    visit = _get_visit_or_404(visit_id, db)
    _ensure_can_edit(visit, current_user)

    updates = payload.model_dump(exclude_unset=True)
    for field, value in updates.items():
        setattr(visit, field, value)

    db.commit()
    db.refresh(visit)
    return visit


@router.delete("/{visit_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_visit(
    visit_id: uuid.UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    visit = _get_visit_or_404(visit_id, db)
    _ensure_can_edit(visit, current_user)
    db.delete(visit)
    db.commit()
    return None


@router.get("/{visit_id}/report", response_model=VisitReportResponse)
def get_visit_report(
    visit_id: uuid.UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Generates a polished, professional report from one visit's raw notes."""
    visit = _get_visit_or_404(visit_id, db)
    doctor = db.query(Doctor).filter(Doctor.id == visit.doctor_id).first()

    report_text = generate_visit_report(visit, doctor)
    return VisitReportResponse(visit_log_id=visit.id, report_text=report_text)


@router.get("/reports/period", response_model=PeriodReportResponse)
def get_period_report(
    date_from: date = Query(..., description="Start of the reporting period"),
    date_to: date = Query(..., description="End of the reporting period"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Generates a summarized report across ALL of the current user's
    visits within a date range — e.g. a weekly or monthly report.
    """
    visits = (
        db.query(VisitLog)
        .filter(
            VisitLog.mr_id == current_user.id,
            VisitLog.visit_date >= date_from,
            VisitLog.visit_date <= date_to,
        )
        .order_by(VisitLog.visit_date)
        .all()
    )

    visit_doctor_pairs = []
    for visit in visits:
        doctor = db.query(Doctor).filter(Doctor.id == visit.doctor_id).first()
        visit_doctor_pairs.append((visit, doctor))

    period_label = f"{date_from} to {date_to}"
    report_text = generate_period_report(visit_doctor_pairs, period_label)

    return PeriodReportResponse(
        period_start=date_from,
        period_end=date_to,
        total_visits=len(visits),
        report_text=report_text,
    )
