"""
User model — represents anyone who can log into the system.

Think of this as the master ID card template. Every employee
(Admin, Product Manager, Regional Manager, Area Sales Manager,
Medical Representative) uses the SAME table, but a `role` column
decides what they're allowed to do. This is called
Role-Based Access Control (RBAC).
"""

import uuid
import enum
from datetime import datetime, timezone

from sqlalchemy import String, Boolean, DateTime, Enum as SqlEnum
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base


class UserRole(str, enum.Enum):
    """
    The 5 job titles in the system.
    str + enum.Enum means it behaves like text in the database
    AND gives us auto-complete + typo protection in code.
    """
    ADMIN = "admin"
    PRODUCT_MANAGER = "product_manager"
    REGIONAL_MANAGER = "regional_manager"
    AREA_SALES_MANAGER = "area_sales_manager"
    MEDICAL_REPRESENTATIVE = "medical_representative"


class User(Base):
    """
    One row in this table = one person who can log in.

    Why UUID instead of a simple number (1, 2, 3...) for the id?
    UUIDs are unguessable random IDs. If we used 1, 2, 3, someone
    could try /api/users/4, /api/users/5... and snoop on other
    people's data. UUIDs prevent that kind of guessing attack.
    """
    __tablename__ = "users"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )

    full_name: Mapped[str] = mapped_column(String(120), nullable=False)
    email: Mapped[str] = mapped_column(String(150), unique=True, index=True, nullable=False)

    # We NEVER store the real password. Only a one-way scrambled
    # ("hashed") version. Explained fully in core/security.py.
    hashed_password: Mapped[str] = mapped_column(String(255), nullable=False)

    role: Mapped[UserRole] = mapped_column(
        SqlEnum(UserRole, name="user_role"), nullable=False,
        default=UserRole.MEDICAL_REPRESENTATIVE
    )

    phone: Mapped[str | None] = mapped_column(String(20), nullable=True)
    region: Mapped[str | None] = mapped_column(String(100), nullable=True)  # sales territory
    profile_image_url: Mapped[str | None] = mapped_column(String(500), nullable=True)

    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    is_email_verified: Mapped[bool] = mapped_column(Boolean, default=False)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc)
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
    )

    def __repr__(self) -> str:
        return f"<User {self.email} ({self.role.value})>"
