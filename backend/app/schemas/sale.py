import uuid
from datetime import datetime, date
from decimal import Decimal
from pydantic import BaseModel, Field


class SaleCreate(BaseModel):
    doctor_id: uuid.UUID | None = None
    product_id: uuid.UUID
    quantity: int = Field(default=1, ge=1)
    amount: Decimal = Field(gt=0)
    sale_date: date


class SaleOut(BaseModel):
    id: uuid.UUID
    mr_id: uuid.UUID
    doctor_id: uuid.UUID | None
    product_id: uuid.UUID
    quantity: int
    amount: Decimal
    sale_date: date
    created_at: datetime

    class Config:
        from_attributes = True


class SalesTargetCreate(BaseModel):
    mr_id: uuid.UUID
    month: date = Field(description="Any date within the target month, e.g. 2026-08-01")
    target_amount: Decimal = Field(gt=0)


class SalesTargetOut(BaseModel):
    id: uuid.UUID
    mr_id: uuid.UUID
    month: date
    target_amount: Decimal
    created_at: datetime

    class Config:
        from_attributes = True
