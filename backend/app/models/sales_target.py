"""
SalesTarget model — one monthly revenue target per MR, used to
calculate "achievement %" on the dashboard (actual sales / target).
"""

import uuid
from datetime import datetime, date, timezone

from sqlalchemy import DateTime, Date, Numeric, ForeignKey, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base


class SalesTarget(Base):
    __tablename__ = "sales_targets"
    __table_args__ = (
        # Prevents accidentally creating two targets for the same
        # MR in the same month — the database enforces this, not
        # just application code.
        UniqueConstraint("mr_id", "month", name="uq_sales_target_mr_month"),
    )

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )

    mr_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id"), nullable=False
    )
    # Always stored as the 1st of the month, e.g. 2026-08-01,
    # representing "the target for August 2026".
    month: Mapped[date] = mapped_column(Date, nullable=False)
    target_amount: Mapped[float] = mapped_column(Numeric(12, 2), nullable=False)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc)
    )

    def __repr__(self) -> str:
        return f"<SalesTarget {self.mr_id} {self.month}: {self.target_amount}>"
