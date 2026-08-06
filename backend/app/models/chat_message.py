"""
ChatMessage model — stores every question and answer exchanged with
the AI assistant, so users can scroll back through past conversations
(and so we could later analyze what MRs are asking most often).
"""

import uuid
from datetime import datetime, timezone

from sqlalchemy import String, DateTime, Text, ForeignKey
from sqlalchemy.dialects.postgresql import UUID, ARRAY
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base


class ChatMessage(Base):
    __tablename__ = "chat_messages"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )

    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id"), nullable=False
    )

    question: Mapped[str] = mapped_column(Text, nullable=False)
    answer: Mapped[str] = mapped_column(Text, nullable=False)

    # Which products the AI used as sources for this answer —
    # stored as a simple list of brand names for transparency.
    sources: Mapped[list[str] | None] = mapped_column(ARRAY(String), nullable=True)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc)
    )

    def __repr__(self) -> str:
        return f"<ChatMessage {self.id} by {self.user_id}>"
