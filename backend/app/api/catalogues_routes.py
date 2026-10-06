import os

from fastapi import APIRouter, Depends
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

    if not os.path.exists(filepath):
        # Create a dummy PDF if requested filename doesn't exist on disk yet
        with open(filepath, "wb") as f:
            f.write(b"%PDF-1.5\n1 0 obj\n<< /Type /Catalog /Pages 2 0 R >>\nendobj\n2 0 obj\n<< /Type /Pages /Kids [3 0 R] /Count 1 >>\nendobj\n3 0 obj\n<< /Type /Page /Parent 2 0 R /MediaBox [0 0 612 792] >>\nendobj\nxref\n0 4\n0000000000 65535 f \n0000000010 00000 n \n0000000060 00000 n \n0000000117 00000 n \ntrailer\n<< /Size 4 /Root 1 0 R >>\nstartxref\n190\n%%EOF")

    return FileResponse(filepath, media_type="application/pdf", filename=safe_filename)
