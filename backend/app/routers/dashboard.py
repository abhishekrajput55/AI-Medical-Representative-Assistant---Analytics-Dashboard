"""
Dashboard endpoint: pulls together numbers from Doctors, Visits,
Sales, and Targets into ONE summary response — exactly what a
frontend dashboard screen needs in a single API call, instead of
making the frontend fire off 6 separate requests and stitch them
together itself.
"""

from datetime import date, datetime, timedelta, timezone

from fastapi import APIRouter, Depends
from sqlalchemy import func
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.deps import get_current_user
from app.models.visit_log import VisitLog
from app.models.doctor import Doctor
from app.models.sale import Sale
from app.models.sales_target import SalesTarget
from app.models.user import User
from app.schemas.dashboard import DashboardSummary, UpcomingTaskItem, RecentActivityItem

router = APIRouter(prefix="/api/dashboard", tags=["Dashboard"])


def _with_title(name: str) -> str:
    """Add 'Dr.' only if the saved name doesn't already start with it."""
    if name.lower().startswith(("dr.", "dr ")):
        return name
    return f"Dr. {name}"


@router.get("/summary", response_model=DashboardSummary)
def get_dashboard_summary(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    today = date.today()
    month_start = today.replace(day=1)

    # --- Visit metrics ---
    todays_visits = (
        db.query(func.count(VisitLog.id))
        .filter(VisitLog.mr_id == current_user.id, VisitLog.visit_date == today)
        .scalar()
    )

    # "Pending" = a follow-up was scheduled for today or earlier,
    # meaning it's due or overdue right now.
    pending_visits_today = (
        db.query(func.count(VisitLog.id))
        .filter(
            VisitLog.mr_id == current_user.id,
            VisitLog.next_follow_up_date.isnot(None),
            VisitLog.next_follow_up_date <= today,
        )
        .scalar()
    )

    doctors_covered_total = (
        db.query(func.count(func.distinct(VisitLog.doctor_id)))
        .filter(VisitLog.mr_id == current_user.id)
        .scalar()
    )

    doctors_covered_this_month = (
        db.query(func.count(func.distinct(VisitLog.doctor_id)))
        .filter(VisitLog.mr_id == current_user.id, VisitLog.visit_date >= month_start)
        .scalar()
    )

    # --- Sales metrics ---
    total_sales_this_month = (
        db.query(func.coalesce(func.sum(Sale.amount), 0))
        .filter(Sale.mr_id == current_user.id, Sale.sale_date >= month_start)
        .scalar()
    )

    target_row = (
        db.query(SalesTarget)
        .filter(SalesTarget.mr_id == current_user.id, SalesTarget.month == month_start)
        .first()
    )
    monthly_target = target_row.target_amount if target_row else None
    achievement_percent = (
        round(float(total_sales_this_month) / float(monthly_target) * 100, 1)
        if monthly_target and monthly_target > 0
        else None
    )

    # --- Upcoming tasks: follow-ups due in the next 7 days ---
    week_ahead = today + timedelta(days=7)
    upcoming_rows = (
        db.query(VisitLog, Doctor)
        .join(Doctor, VisitLog.doctor_id == Doctor.id)
        .filter(
            VisitLog.mr_id == current_user.id,
            VisitLog.next_follow_up_date.isnot(None),
            VisitLog.next_follow_up_date >= today,
            VisitLog.next_follow_up_date <= week_ahead,
        )
        .order_by(VisitLog.next_follow_up_date)
        .limit(10)
        .all()
    )
    upcoming_tasks = []
    seen = set()
    for visit, doctor in upcoming_rows:
        key = (doctor.id, visit.next_follow_up_date)
        if key in seen:
            continue
        seen.add(key)
        upcoming_tasks.append(
            UpcomingTaskItem(
                doctor_id=doctor.id,
                doctor_name=doctor.full_name,
                follow_up_date=visit.next_follow_up_date,
                notes=visit.outcome,
            )
        )
    # --- Recent activity feed: last 10 visits ---
    recent_visits = (
        db.query(VisitLog, Doctor)
        .join(Doctor, VisitLog.doctor_id == Doctor.id)
        .filter(VisitLog.mr_id == current_user.id)
        .order_by(VisitLog.created_at.desc())
        .limit(10)
        .all()
    )
    recent_activities = [
        RecentActivityItem(
            type="visit",
            description=f"Visited {_with_title(doctor.full_name)} ({doctor.specialization or 'N/A'})",
            occurred_at=visit.created_at,
        )
        for visit, doctor in recent_visits
    ]

    return DashboardSummary(
        todays_visits=todays_visits,
        pending_visits_today=pending_visits_today,
        doctors_covered_total=doctors_covered_total,
        doctors_covered_this_month=doctors_covered_this_month,
        total_sales_this_month=total_sales_this_month,
        monthly_target=monthly_target,
        achievement_percent=achievement_percent,
        upcoming_tasks=upcoming_tasks,
        recent_activities=recent_activities,
    )
