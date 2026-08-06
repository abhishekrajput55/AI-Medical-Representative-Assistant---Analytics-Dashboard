import uuid
from datetime import datetime, date
from pydantic import BaseModel, Field


class VisitLogCreate(BaseModel):
    doctor_id: uuid.UUID
    visit_date: date
    products_discussed: list[str] | None = None
    raw_notes: str = Field(min_length=1)
    outcome: str | None = None
    next_follow_up_date: date | None = None


class VisitLogUpdate(BaseModel):
    visit_date: date | None = None
    products_discussed: list[str] | None = None
    raw_notes: str | None = None
    outcome: str | None = None
    next_follow_up_date: date | None = None


class VisitLogOut(BaseModel):
    id: uuid.UUID
    doctor_id: uuid.UUID
    mr_id: uuid.UUID
    visit_date: date
    products_discussed: list[str] | None
    raw_notes: str
    outcome: str | None
    next_follow_up_date: date | None
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class VisitReportResponse(BaseModel):
    """The AI-polished, professional version of a visit log."""
    visit_log_id: uuid.UUID
    report_text: str


class PeriodReportResponse(BaseModel):
    """A summarized report covering multiple visits over a date range."""
    period_start: date
    period_end: date
    total_visits: int
    report_text: str
