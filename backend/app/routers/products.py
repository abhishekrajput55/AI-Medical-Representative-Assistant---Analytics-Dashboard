"""
Product endpoints: list, get, create, update, delete.

Permission rule: EVERYONE logged in can view products (MRs need to
look up medicine details constantly). Only Product Managers and
Admins can create, edit, or delete — this uses Module 1's
require_role() gate, since it's role-based, not ownership-based.
"""

import uuid

from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from sqlalchemy import or_

from app.core.database import get_db
from app.core.deps import get_current_user, require_role
from app.models.product import Product
from app.models.user import User, UserRole
from app.schemas.product import ProductCreate, ProductUpdate, ProductOut

router = APIRouter(prefix="/api/products", tags=["Products"])

# Reused across all three write endpoints below — defined once so
# the allowed-roles list only needs to be changed in one place.
can_manage_products = require_role(UserRole.PRODUCT_MANAGER, UserRole.ADMIN)


def _get_product_or_404(product_id: uuid.UUID, db: Session) -> Product:
    product = db.query(Product).filter(Product.id == product_id).first()
    if not product:
        raise HTTPException(status_code=404, detail="Product not found.")
    return product


@router.post(
    "", response_model=ProductOut, status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(can_manage_products)],
)
def create_product(payload: ProductCreate, db: Session = Depends(get_db)):
    product = Product(**payload.model_dump())
    db.add(product)
    db.commit()
    db.refresh(product)
    return product


@router.get("", response_model=list[ProductOut])
def list_products(
    search: str | None = Query(None, description="Search by brand or generic name"),
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=200),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    query = db.query(Product)
    if search:
        pattern = f"%{search}%"
        query = query.filter(
            or_(Product.brand_name.ilike(pattern), Product.generic_name.ilike(pattern))
        )
    return query.order_by(Product.brand_name).offset(skip).limit(limit).all()


@router.get("/{product_id}", response_model=ProductOut)
def get_product(
    product_id: uuid.UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return _get_product_or_404(product_id, db)


@router.put(
    "/{product_id}", response_model=ProductOut,
    dependencies=[Depends(can_manage_products)],
)
def update_product(product_id: uuid.UUID, payload: ProductUpdate, db: Session = Depends(get_db)):
    product = _get_product_or_404(product_id, db)
    updates = payload.model_dump(exclude_unset=True)
    for field, value in updates.items():
        setattr(product, field, value)
    db.commit()
    db.refresh(product)
    return product


@router.delete(
    "/{product_id}", status_code=status.HTTP_204_NO_CONTENT,
    dependencies=[Depends(can_manage_products)],
)
def delete_product(product_id: uuid.UUID, db: Session = Depends(get_db)):
    product = _get_product_or_404(product_id, db)
    db.delete(product)
    db.commit()
    return None
