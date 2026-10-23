import os

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import FileResponse
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models import Attachment, Supplier
from app.services.pdf_guardrail import MEDIA_DIR

router = APIRouter(prefix="/api/catalogues", tags=["catalogues"])

@router.get("", include_in_schema=False)
@router.get("/")
async def list_catalogues(db: AsyncSession = Depends(get_db)):
    stmt = select(Attachment).where(Attachment.is_pdf.is_(True)).order_by(Attachment.created_at.desc())
    result = await db.execute(stmt)
    attachments = result.scalars().all()

    output = []
    for att in attachments:
        supplier_name = "Unknown"
        if att.supplier_id:
            s_res = await db.execute(select(Supplier).where(Supplier.id == att.supplier_id))
            sup = s_res.scalar_one_or_none()
            if sup:
                supplier_name = sup.name

        output.append({
            "id": att.id,
            "filename": att.filename,
            "supplier": supplier_name,
            "supplier_id": att.supplier_id,
            "email_id": att.email_id,
            "mime_type": att.mime_type,
            "file_size": att.file_size,
            "web_view_link": att.web_view_link,
            "created_at": att.created_at.isoformat() if att.created_at else None
        })

    return output

@router.get("/download/{filename}")
async def download_pdf_catalogue(filename: str):
    safe_filename = os.path.basename(filename)
    filepath = os.path.join(MEDIA_DIR, safe_filename)

    # Never synthesize or overwrite a missing supplier document.
    if not os.path.isfile(filepath):
        raise HTTPException(status_code=404, detail="Original PDF catalogue not found")

    return FileResponse(filepath, media_type="application/pdf", filename=safe_filename)
