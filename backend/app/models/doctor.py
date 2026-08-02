"""
Doctor model — represents a doctor that a Medical Representative visits.

This is the digital version of the paper "doctor visiting card" MRs
used to carry. Every doctor is linked to the user (MR) who added
them via created_by_id, so we always know who's responsible for
that relationship.
"""

import uuid
from datetime import datetime, timezone

from sqlalchemy import String, DateTime, Text, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base


class Doctor(Base):
    __tablename__ = "doctors"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )

    full_name: Mapped[str] = mapped_column(String(150), nullable=False)
    specialization: Mapped[str | None] = mapped_column(String(120), nullable=True)
    hospital: Mapped[str | None] = mapped_column(String(200), nullable=True)
    clinic: Mapped[str | None] = mapped_column(String(200), nullable=True)
    address: Mapped[str | None] = mapped_column(String(300), nullable=True)
    phone: Mapped[str | None] = mapped_column(String(20), nullable=True)
    email: Mapped[str | None] = mapped_column(String(150), nullable=True)

    preferred_visit_time: Mapped[str | None] = mapped_column(String(50), nullable=True)
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)

    # Left blank for now — Module 8 (AI Assistant) will fill this in
    # automatically by summarizing visit history and notes with AI.
    ai_summary: Mapped[str | None] = mapped_column(Text, nullable=True)

    region: Mapped[str | None] = mapped_column(String(100), nullable=True)

    # Which user (MR) added this doctor. ForeignKey guarantees this
    # always points to a real row in the users table — the database
    # itself enforces this, not just our Python code.
    created_by_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id"), nullable=False
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc)
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
    )

    def __repr__(self) -> str:
        return f"<Doctor {self.full_name} ({self.specialization})>"
