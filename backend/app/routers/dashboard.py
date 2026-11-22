"""
Dashboard endpoint: pulls together numbers from Doctors, Visits,
Sales, and Targets into ONE summary response — exactly what a
frontend dashboard screen needs in a single API call, instead of
making the frontend fire off 6 separate requests and stitch them
together itself.
"""

from datetime import date, datetime, timedelta, timezone

from fastapi import APIRouter, Depends
from sqlalchemy import and_, func
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.deps import get_current_user, require_role
from app.models.visit_log import VisitLog
from app.models.doctor import Doctor
from app.models.sale import Sale
from app.models.sales_target import SalesTarget
from app.models.user import User, UserRole
from app.schemas.dashboard import (
    DashboardSummary, UpcomingTaskItem, RecentActivityItem, TeamMemberStats,
)

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
    # One entry per doctor per day: two visits to the same doctor with
    # the same follow-up date should show up as ONE task, not two.
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


# Only managers and admins may see the whole team.
can_view_team = require_role(
    UserRole.ADMIN, UserRole.REGIONAL_MANAGER, UserRole.AREA_SALES_MANAGER
)


@router.get(
    "/team", response_model=list[TeamMemberStats],
    dependencies=[Depends(can_view_team)],
)
def get_team_summary(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    One row per MR: visits, doctors covered, sales, target and
    achievement % for the current month.

    Admins see every MR. Regional/Area managers see only the MRs in
    their own region.
    """
    month_start = date.today().replace(day=1)

    # Pile 1: visits, dealt into one pile per MR (GROUP BY).
    visit_stats = (
        db.query(
            VisitLog.mr_id.label("mr_id"),
            func.count(VisitLog.id).label("visits"),
            func.count(func.distinct(VisitLog.doctor_id)).label("doctors"),
        )
        .filter(VisitLog.visit_date >= month_start)
        .group_by(VisitLog.mr_id)
        .subquery()
    )

    # Pile 2: sales, one pile per MR.
    sales_stats = (
        db.query(
            Sale.mr_id.label("mr_id"),
            func.sum(Sale.amount).label("total"),
        )
        .filter(Sale.sale_date >= month_start)
        .group_by(Sale.mr_id)
        .subquery()
    )

    visits_col = func.coalesce(visit_stats.c.visits, 0)
    doctors_col = func.coalesce(visit_stats.c.doctors, 0)
    sales_col = func.coalesce(sales_stats.c.total, 0)

    # Start from USERS (everyone on the team), then LEFT JOIN each
    # pile on, so an MR with no activity still appears, as zeros.
    query = (
        db.query(
            User.id, User.full_name, User.region,
            visits_col, doctors_col, sales_col,
            SalesTarget.target_amount,
        )
        .select_from(User)
        .outerjoin(visit_stats, visit_stats.c.mr_id == User.id)
        .outerjoin(sales_stats, sales_stats.c.mr_id == User.id)
        .outerjoin(
            SalesTarget,
            and_(SalesTarget.mr_id == User.id, SalesTarget.month == month_start),
        )
        .filter(
            User.role == UserRole.MEDICAL_REPRESENTATIVE,
            User.is_active.is_(True),
        )
    )

    if current_user.role != UserRole.ADMIN:
        # A manager with no region set sees nobody, rather than everybody.
        if current_user.region is None:
            return []
        query = query.filter(User.region == current_user.region)

    rows = query.order_by(sales_col.desc(), User.full_name).all()

    return [
        TeamMemberStats(
            mr_id=mr_id,
            mr_name=name,
            region=region,
            visits_this_month=visits,
            doctors_covered_this_month=doctors,
            sales_this_month=sales,
            monthly_target=target,
            achievement_percent=(
                round(float(sales) / float(target) * 100, 1)
                if target and target > 0
                else None
            ),
        )
        for mr_id, name, region, visits, doctors, sales, target in rows
    ]