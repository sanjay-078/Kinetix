from typing import Optional
from fastapi import APIRouter, Depends, Query, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.database import get_db
from app.models import Email

router = APIRouter(prefix="/api/emails", tags=["emails"])

@router.get("", include_in_schema=False)
@router.get("/")
async def list_emails(
    status: Optional[str] = Query(None, description="Filter: relevant, ignored, processed, review_required, failed"),
    db: AsyncSession = Depends(get_db)
):
    stmt = select(Email).order_by(Email.received_at.desc())
    
    if status == "relevant":
        stmt = stmt.where(Email.classification == "relevant")
    elif status == "ignored":
        stmt = stmt.where(Email.classification == "irrelevant")
    elif status == "review_required":
        stmt = stmt.where(Email.processing_status == "review_required")
    elif status == "processed":
        stmt = stmt.where(Email.processing_status == "processed")
    elif status == "failed":
        stmt = stmt.where(Email.processing_status == "failed")

    result = await db.execute(stmt)
    emails = result.scalars().all()

    return [
        {
            "id": e.id,
            "gmail_message_id": e.gmail_message_id,
            "sender": e.sender,
            "sender_domain": e.sender_domain,
            "subject": e.subject,
            "snippet": e.snippet,
            "received_at": e.received_at.isoformat() if e.received_at else None,
            "classification": e.classification,
            "classification_reason": e.classification_reason,
            "processing_status": e.processing_status,
            "product_count": e.product_count,
            "pdf_count": e.pdf_count,
            "source_email_link": e.source_email_link
        } for e in emails
    ]

@router.get("/{email_id}")
async def get_email_detail(email_id: str, db: AsyncSession = Depends(get_db)):
    stmt = select(Email).where(Email.id == email_id)
    e = (await db.execute(stmt)).scalar_one_or_none()

    if not e:
        raise HTTPException(status_code=404, detail="Email not found")

    return {
        "id": e.id,
        "gmail_message_id": e.gmail_message_id,
        "sender": e.sender,
        "sender_domain": e.sender_domain,
        "subject": e.subject,
        "snippet": e.snippet,
        "body_text": e.body_text,
        "received_at": e.received_at.isoformat() if e.received_at else None,
        "classification": e.classification,
        "classification_reason": e.classification_reason,
        "processing_status": e.processing_status,
        "product_count": e.product_count,
        "pdf_count": e.pdf_count,
        "source_email_link": e.source_email_link
    }
