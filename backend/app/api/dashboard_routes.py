import asyncio
import json
from fastapi import APIRouter, Depends
from fastapi.responses import StreamingResponse
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from app.database import get_db
from app.models import Product, Supplier, Email, Attachment, ReviewItem
from app.services.ingestion import GLOBAL_PROGRESS
from app.services.worker import start_background_worker

router = APIRouter(prefix="/api/dashboard", tags=["dashboard"])

@router.get("/stats")
async def get_dashboard_stats(db: AsyncSession = Depends(get_db)):
    products_count = (await db.execute(select(func.count(Product.id)))).scalar() or 0
    suppliers_count = (await db.execute(select(func.count(Supplier.id)))).scalar() or 0
    emails_count = (await db.execute(select(func.count(Email.id)))).scalar() or 0
    catalogues_count = (await db.execute(select(func.count(Attachment.id)).where(Attachment.is_pdf == True))).scalar() or 0
    review_count = (await db.execute(select(func.count(ReviewItem.id)).where(ReviewItem.status == "pending"))).scalar() or 0

    return {
        "cards": {
            "products": products_count,
            "suppliers": suppliers_count,
            "emails_processed": emails_count,
            "catalogues": catalogues_count,
            "needs_review": review_count
        },
        "live_progress": GLOBAL_PROGRESS
    }

@router.post("/start-sync")
async def start_sync():
    start_background_worker()
    return {"status": "started", "message": "Mailbox sync started"}

@router.get("/stream")
async def sse_dashboard_stream(db: AsyncSession = Depends(get_db)):
    """
    Server-Sent Events (SSE) endpoint providing real-time dashboard updates & ETA calculation.
    """
    async def event_generator():
        while True:
            data = json.dumps(GLOBAL_PROGRESS)
            yield f"data: {data}\n\n"
            await asyncio.sleep(1)

    return StreamingResponse(event_generator(), media_type="text/event-stream")
