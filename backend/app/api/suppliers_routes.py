from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.orm import selectinload
from app.database import get_db
from app.models import Supplier, Product, Email, Attachment

router = APIRouter(prefix="/api/suppliers", tags=["suppliers"])

@router.get("", include_in_schema=False)
@router.get("/")
async def list_suppliers(db: AsyncSession = Depends(get_db)):
    stmt = select(Supplier).order_by(Supplier.name.asc())
    result = await db.execute(stmt)
    suppliers = result.scalars().all()

    return [
        {
            "id": s.id,
            "name": s.name,
            "domain": s.domain,
            "primary_email": s.primary_email,
            "phone": s.phone,
            "country": s.country,
            "product_count": s.product_count,
            "email_count": s.email_count,
            "catalogue_count": s.catalogue_count
        } for s in suppliers
    ]

@router.get("/{supplier_id}")
async def get_supplier_detail(supplier_id: str, db: AsyncSession = Depends(get_db)):
    stmt = select(Supplier).where(Supplier.id == supplier_id)
    s = (await db.execute(stmt)).scalar_one_or_none()

    if not s:
        raise HTTPException(status_code=404, detail="Supplier not found")

    prods_stmt = select(Product).where(Product.supplier_id == supplier_id).order_by(Product.received_at.desc())
    products = (await db.execute(prods_stmt)).scalars().all()

    emails_stmt = select(Email).where(Email.sender_domain == s.domain).order_by(Email.received_at.desc())
    emails = (await db.execute(emails_stmt)).scalars().all()

    catalogues_stmt = select(Attachment).where(Attachment.supplier_id == supplier_id, Attachment.is_pdf == True)
    catalogues = (await db.execute(catalogues_stmt)).scalars().all()

    return {
        "id": s.id,
        "name": s.name,
        "domain": s.domain,
        "primary_email": s.primary_email,
        "phone": s.phone,
        "address": s.address,
        "country": s.country,
        "product_count": len(products),
        "email_count": len(emails),
        "catalogue_count": len(catalogues),
        "products": [
            {
                "id": p.id,
                "name": p.name,
                "model": p.model,
                "price": p.price,
                "currency": p.currency or "USD",
                "received_at": p.received_at.isoformat() if p.received_at else None
            } for p in products
        ],
        "recent_emails": [
            {
                "id": e.id,
                "subject": e.subject,
                "classification": e.classification,
                "received_at": e.received_at.isoformat() if e.received_at else None
            } for e in emails[:10]
        ],
        "catalogues": [
            {
                "id": c.id,
                "filename": c.filename,
                "web_view_link": c.web_view_link
            } for c in catalogues
        ]
    }
