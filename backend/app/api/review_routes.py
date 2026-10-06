from typing import Any

from fastapi import APIRouter, Body, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models import Email, ReviewItem

router = APIRouter(prefix="/api/review", tags=["review"])

@router.get("", include_in_schema=False)
@router.get("/")
async def list_review_items(db: AsyncSession = Depends(get_db)):
    stmt = select(ReviewItem).where(ReviewItem.status == "pending").order_by(ReviewItem.created_at.desc())
    result = await db.execute(stmt)
    items = result.scalars().all()

    output = []
    for item in items:
        e_res = await db.execute(select(Email).where(Email.id == item.email_id))
        email = e_res.scalar_one_or_none()

        output.append({
            "id": item.id,
            "email_id": item.email_id,
            "product_id": item.product_id,
            "issue_type": item.issue_type,
            "uncertainty_reason": item.uncertainty_reason,
            "candidate_values": item.candidate_values,
            "confidence": item.confidence,
            "status": item.status,
            "created_at": item.created_at.isoformat() if item.created_at else None,
            "email": {
                "subject": email.subject if email else "Unknown",
                "sender": email.sender if email else "Unknown",
                "source_email_link": email.source_email_link if email else None
            } if email else None
        })

    return output

@router.post("/{item_id}/confirm")
async def confirm_review_item(
    item_id: str,
    corrections: dict[str, Any] = Body(...),
    db: AsyncSession = Depends(get_db)
):
    stmt = select(ReviewItem).where(ReviewItem.id == item_id)
    item = (await db.execute(stmt)).scalar_one_or_none()

    if not item:
        raise HTTPException(status_code=404, detail="Review item not found")

    item.status = "resolved"

    # If associated product exists or corrections provided, create/update product
    if item.email_id:
        e_res = await db.execute(select(Email).where(Email.id == item.email_id))
        email = e_res.scalar_one_or_none()
        if email:
            email.processing_status = "processed"

    await db.commit()

    return {"status": "resolved", "id": item_id}
