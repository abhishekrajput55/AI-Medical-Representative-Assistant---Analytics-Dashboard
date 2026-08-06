"""
VisitLog model — one row per doctor visit an MR records.

This is the raw, factual record of what happened during a visit.
The AI-polished "report" (Module 4's other feature) is generated
FROM this data on demand, not stored separately — that way the
report always reflects the latest edits to the underlying visit.
"""

import uuid
from datetime import datetime, date, timezone

from sqlalchemy import String, DateTime, Date, Text, ForeignKey
from sqlalchemy.dialects.postgresql import UUID, ARRAY
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base


class VisitLog(Base):
    __tablename__ = "visit_logs"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )

    doctor_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("doctors.id"), nullable=False
    )
    mr_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id"), nullable=False
    )

    visit_date: Mapped[date] = mapped_column(Date, nullable=False)

    # Which products were discussed during this specific visit —
    # stored as plain brand-name strings for simplicity rather than
    # a separate join table, since we only need names for reporting.
    products_discussed: Mapped[list[str] | None] = mapped_column(ARRAY(String), nullable=True)

    raw_notes: Mapped[str] = mapped_column(Text, nullable=False)
    outcome: Mapped[str | None] = mapped_column(String(200), nullable=True)  # e.g. "Positive", "Follow-up needed"
    next_follow_up_date: Mapped[date | None] = mapped_column(Date, nullable=True)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc)
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
    )

    def __repr__(self) -> str:
        return f"<VisitLog doctor={self.doctor_id} date={self.visit_date}>"
