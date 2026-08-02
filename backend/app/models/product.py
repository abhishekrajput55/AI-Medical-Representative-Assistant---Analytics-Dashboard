"""
Product model — represents a medicine/product in the company's catalog.

Unlike doctors (owned by whoever added them), products are shared,
official company data — that's why write access will be restricted
to Product Managers and Admins only, enforced in routers/products.py.
"""

import uuid
from datetime import datetime, timezone

from sqlalchemy import String, DateTime, Text, Numeric
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base


class Product(Base):
    __tablename__ = "products"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )

    brand_name: Mapped[str] = mapped_column(String(150), nullable=False, index=True)
    generic_name: Mapped[str | None] = mapped_column(String(150), nullable=True)
    composition: Mapped[str | None] = mapped_column(Text, nullable=True)

    indications: Mapped[str | None] = mapped_column(Text, nullable=True)       # what it treats
    contraindications: Mapped[str | None] = mapped_column(Text, nullable=True)  # when NOT to use it
    side_effects: Mapped[str | None] = mapped_column(Text, nullable=True)
    competitors: Mapped[str | None] = mapped_column(Text, nullable=True)

    # Numeric(10, 2) = up to 10 digits total, 2 after the decimal point.
    # Using a plain float for money is a classic bug — floats can't
    # represent amounts like 19.99 exactly, so we use Numeric instead.
    price: Mapped[float | None] = mapped_column(Numeric(10, 2), nullable=True)
    pack_size: Mapped[str | None] = mapped_column(String(100), nullable=True)

    literature_url: Mapped[str | None] = mapped_column(String(500), nullable=True)
    image_url: Mapped[str | None] = mapped_column(String(500), nullable=True)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc)
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
    )

    def __repr__(self) -> str:
        return f"<Product {self.brand_name}>"
