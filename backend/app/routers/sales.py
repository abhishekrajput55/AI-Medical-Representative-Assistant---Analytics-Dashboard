"""
Sales endpoints: log a sale, view your sales, and (managers only)
set monthly targets for an MR.
"""

import uuid

from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.deps import get_current_user, require_role
from app.models.sale import Sale
from app.models.sales_target import SalesTarget
from app.models.user import User, UserRole
from app.schemas.sale import SaleCreate, SaleOut, SalesTargetCreate, SalesTargetOut
from app.models.product import Product
from app.models.doctor import Doctor

router = APIRouter(prefix="/api/sales", tags=["Sales"])

can_set_targets = require_role(UserRole.ADMIN, UserRole.REGIONAL_MANAGER, UserRole.AREA_SALES_MANAGER)


@router.post("", response_model=SaleOut, status_code=status.HTTP_201_CREATED)
def create_sale(
    payload: SaleCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    # Check the product exists BEFORE saving, so a wrong id gives a
    # clear 404 instead of a database crash (500).
    if not db.query(Product).filter(Product.id == payload.product_id).first():
        raise HTTPException(status_code=404, detail="Product not found.")

    # doctor_id is optional, so only check it if one was sent.
    if payload.doctor_id and not db.query(Doctor).filter(Doctor.id == payload.doctor_id).first():
        raise HTTPException(status_code=404, detail="Doctor not found.")

    sale = Sale(**payload.model_dump(), mr_id=current_user.id)
    db.add(sale)
    db.commit()
    db.refresh(sale)
    return sale


@router.get("", response_model=list[SaleOut])
def list_sales(
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=200),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    query = db.query(Sale)
    management_roles = (UserRole.ADMIN, UserRole.REGIONAL_MANAGER, UserRole.AREA_SALES_MANAGER)
    if current_user.role not in management_roles:
        query = query.filter(Sale.mr_id == current_user.id)

    return query.order_by(Sale.sale_date.desc()).offset(skip).limit(limit).all()


@router.post(
    "/targets", response_model=SalesTargetOut, status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(can_set_targets)],
)
def set_target(payload: SalesTargetCreate, db: Session = Depends(get_db)):
    # Normalize to the 1st of the month, so lookups are consistent
    # regardless of which day of the month was passed in.
    normalized_month = payload.month.replace(day=1)

    existing = (
        db.query(SalesTarget)
        .filter(SalesTarget.mr_id == payload.mr_id, SalesTarget.month == normalized_month)
        .first()
    )
    if existing:
        existing.target_amount = payload.target_amount
        db.commit()
        db.refresh(existing)
        return existing

    target = SalesTarget(
        mr_id=payload.mr_id,
        month=normalized_month,
        target_amount=payload.target_amount,
    )
    db.add(target)
    db.commit()
    db.refresh(target)
    return target
