import uuid
from datetime import date, datetime
from decimal import Decimal
from pydantic import BaseModel


class RecentActivityItem(BaseModel):
    type: str  # "visit" or "sale"
    description: str
    occurred_at: datetime


class UpcomingTaskItem(BaseModel):
    doctor_id: uuid.UUID
    doctor_name: str
    follow_up_date: date
    notes: str | None


class DashboardSummary(BaseModel):
    # Visit metrics
    todays_visits: int
    pending_visits_today: int  # visits with a follow-up due today or overdue, not yet re-visited
    doctors_covered_total: int
    doctors_covered_this_month: int

    # Sales metrics
    total_sales_this_month: Decimal
    monthly_target: Decimal | None
    achievement_percent: float | None

    # Feeds
    upcoming_tasks: list[UpcomingTaskItem]
    recent_activities: list[RecentActivityItem]


class TeamMemberStats(BaseModel):
    """One row of the manager's team table: one MR's month so far."""
    mr_id: uuid.UUID
    mr_name: str
    region: str | None
    visits_this_month: int
    doctors_covered_this_month: int
    sales_this_month: Decimal
    monthly_target: Decimal | None
    achievement_percent: float | None