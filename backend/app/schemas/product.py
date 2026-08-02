"""
Pydantic schemas for Product endpoints.
"""

import uuid
from datetime import datetime
from decimal import Decimal
from pydantic import BaseModel, Field


class ProductCreate(BaseModel):
    brand_name: str = Field(min_length=1, max_length=150)
    generic_name: str | None = None
    composition: str | None = None
    indications: str | None = None
    contraindications: str | None = None
    side_effects: str | None = None
    competitors: str | None = None
    price: Decimal | None = None
    pack_size: str | None = None
    literature_url: str | None = None
    image_url: str | None = None


class ProductUpdate(BaseModel):
    brand_name: str | None = None
    generic_name: str | None = None
    composition: str | None = None
    indications: str | None = None
    contraindications: str | None = None
    side_effects: str | None = None
    competitors: str | None = None
    price: Decimal | None = None
    pack_size: str | None = None
    literature_url: str | None = None
    image_url: str | None = None


class ProductOut(BaseModel):
    id: uuid.UUID
    brand_name: str
    generic_name: str | None
    composition: str | None
    indications: str | None
    contraindications: str | None
    side_effects: str | None
    competitors: str | None
    price: Decimal | None
    pack_size: str | None
    literature_url: str | None
    image_url: str | None
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True
