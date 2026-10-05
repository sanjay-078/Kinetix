from typing import Optional
from fastapi import APIRouter, Depends, Query, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, or_
from sqlalchemy.orm import selectinload
from app.database import get_db
from app.models import Product, ProductAttribute, Supplier

router = APIRouter(prefix="/api/products", tags=["products"])

@router.get("", include_in_schema=False)
@router.get("/")
async def list_products(
    q: Optional[str] = Query(None, description="Search by name, model, SKU, or category"),
    supplier_id: Optional[str] = None,
    currency: Optional[str] = None,
    db: AsyncSession = Depends(get_db)
):
    stmt = select(Product).options(
        selectinload(Product.supplier),
        selectinload(Product.dynamic_attributes)
    ).order_by(Product.received_at.desc())

    if q:
        search_pattern = f"%{q}%"
        stmt = stmt.where(
            or_(
                Product.name.ilike(search_pattern),
                Product.model.ilike(search_pattern),
                Product.sku.ilike(search_pattern),
                Product.category.ilike(search_pattern),
                Product.description.ilike(search_pattern)
            )
        )

    if supplier_id:
        stmt = stmt.where(Product.supplier_id == supplier_id)

    if currency:
        stmt = stmt.where(Product.currency == currency)

    result = await db.execute(stmt)
    products = result.scalars().all()

    output = []
    for p in products:
        output.append({
            "id": p.id,
            "name": p.name,
            "model": p.model,
            "sku": p.sku,
            "supplier": p.supplier.name if p.supplier else "Unknown",
            "supplier_id": p.supplier_id,
            "price": p.price,
            "currency": p.currency or "USD",
            "quantity": p.quantity,
            "moq": p.moq,
            "unit": p.unit,
            "lead_time": p.lead_time,
            "description": p.description,
            "catalogue_link": p.catalogue_link,
            "source_email_link": p.source_email_link,
            "received_at": p.received_at.isoformat() if p.received_at else None,
            "dynamic_attributes_count": len(p.dynamic_attributes)
        })

    return output


@router.get("/{product_id}")
async def get_product_detail(product_id: str, db: AsyncSession = Depends(get_db)):
    stmt = select(Product).options(
        selectinload(Product.supplier),
        selectinload(Product.dynamic_attributes),
        selectinload(Product.email)
    ).where(Product.id == product_id)

    result = await db.execute(stmt)
    p = result.scalar_one_or_none()

    if not p:
        raise HTTPException(status_code=404, detail="Product not found")

    return {
        "id": p.id,
        "name": p.name,
        "title": p.title,
        "category": p.category,
        "brand": p.brand,
        "manufacturer": p.manufacturer,
        "model": p.model,
        "sku": p.sku,
        "series": p.series,
        "variant": p.variant,
        "description": p.description,
        "price": p.price,
        "unit_price": p.unit_price,
        "currency": p.currency or "USD",
        "quantity": p.quantity,
        "moq": p.moq,
        "unit": p.unit,
        "lead_time": p.lead_time,
        "warranty": p.warranty,
        "incoterms": p.incoterms,
        "payment_terms": p.payment_terms,
        "dimensions": p.dimensions,
        "weight": p.weight,
        "material": p.material,
        "voltage": p.voltage,
        "power": p.power,
        "certifications": p.certifications,
        "supplier": {
            "id": p.supplier.id,
            "name": p.supplier.name,
            "domain": p.supplier.domain
        } if p.supplier else None,
        "dynamic_attributes": [
            {
                "id": attr.id,
                "name": attr.attribute_name,
                "value": attr.attribute_value,
                "unit": attr.unit
            } for attr in p.dynamic_attributes
        ],
        "catalogue_link": p.catalogue_link,
        "source_email_link": p.source_email_link,
        "received_at": p.received_at.isoformat() if p.received_at else None,
        "confidence_score": p.confidence_score,
        "review_status": p.review_status
    }
