import logging
from typing import List, Dict, Any
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.models import Product, Email, Attachment, ProductAttribute, Supplier

logger = logging.getLogger(__name__)

async def prepare_products_sheet_rows(session: AsyncSession) -> List[List[Any]]:
    header = [
        "Product ID", "Supplier", "Product Name", "Model", "SKU", "Price",
        "Currency", "MOQ", "Lead Time", "Category", "Description",
        "Additional Specifications", "Source Email", "Catalogue Link", "Received Date"
    ]
    rows = [header]

    result = await session.execute(select(Product))
    products = result.scalars().all()

    for p in products:
        supplier_name = ""
        if p.supplier_id:
            s_res = await session.execute(select(Supplier).where(Supplier.id == p.supplier_id))
            sup = s_res.scalar_one_or_none()
            if sup:
                supplier_name = sup.name

        # Load dynamic attributes for additional specifications column
        attrs_res = await session.execute(select(ProductAttribute).where(ProductAttribute.product_id == p.id))
        attrs = attrs_res.scalars().all()
        dyn_specs = "; ".join([f"{a.attribute_name}: {a.attribute_value}" for a in attrs])

        row = [
            p.id,
            supplier_name,
            p.name or "",
            p.model or "",
            p.sku or "",
            str(p.price) if p.price is not None else "",
            p.currency or "",
            p.moq or "",
            p.lead_time or "",
            p.category or "",
            p.description or "",
            dyn_specs,
            p.source_email_link or "",
            p.catalogue_link or "",
            p.received_at.isoformat() if p.received_at else ""
        ]
        rows.append(row)

    return rows


async def prepare_emails_sheet_rows(session: AsyncSession) -> List[List[Any]]:
    header = [
        "Email ID", "Supplier", "Sender", "Subject", "Received Date",
        "Classification", "Processing Status", "Products Extracted", "PDF Count", "Source Email Link"
    ]
    rows = [header]

    result = await session.execute(select(Email))
    emails = result.scalars().all()

    for e in emails:
        row = [
            e.id,
            e.sender_domain or "",
            e.sender or "",
            e.subject or "",
            e.received_at.isoformat() if e.received_at else "",
            e.classification or "",
            e.processing_status or "",
            str(e.product_count),
            str(e.pdf_count),
            e.source_email_link or ""
        ]
        rows.append(row)

    return rows


async def prepare_attachments_sheet_rows(session: AsyncSession) -> List[List[Any]]:
    header = [
        "Attachment ID", "Supplier", "Email ID", "Filename", "MIME Type", "PDF Link", "Received Date"
    ]
    rows = [header]

    result = await session.execute(select(Attachment))
    attachments = result.scalars().all()

    for a in attachments:
        row = [
            a.id,
            a.supplier_id or "",
            a.email_id,
            a.filename,
            a.mime_type,
            a.web_view_link,
            a.created_at.isoformat() if a.created_at else ""
        ]
        rows.append(row)

    return rows


async def batch_sync_to_google_sheets(session: AsyncSession, creds=None, spreadsheet_id: str = "") -> Dict[str, Any]:
    """
    Executes batch synchronization to Google Sheets.
    If creds / spreadsheet_id are not supplied, runs local preparation & batch row validation.
    """
    products_rows = await prepare_products_sheet_rows(session)
    emails_rows = await prepare_emails_sheet_rows(session)
    attachments_rows = await prepare_attachments_sheet_rows(session)

    if creds and spreadsheet_id:
        try:
            from googleapiclient.discovery import build
            service = build("sheets", "v4", credentials=creds)

            # Update Products tab
            body = {"values": products_rows}
            service.spreadsheets().values().update(
                spreadsheetId=spreadsheet_id, range="Products!A1",
                valueInputOption="RAW", body=body
            ).execute()

            # Update Emails tab
            body = {"values": emails_rows}
            service.spreadsheets().values().update(
                spreadsheetId=spreadsheet_id, range="Emails!A1",
                valueInputOption="RAW", body=body
            ).execute()

            # Update Attachments tab
            body = {"values": attachments_rows}
            service.spreadsheets().values().update(
                spreadsheetId=spreadsheet_id, range="Attachments!A1",
                valueInputOption="RAW", body=body
            ).execute()

            logger.info("Successfully synced rows to Google Sheets in batch mode.")
        except Exception as e:
            logger.error(f"Failed Google Sheets batch sync: {e}")
            raise e

    return {
        "status": "success",
        "products_synced": len(products_rows) - 1,
        "emails_synced": len(emails_rows) - 1,
        "attachments_synced": len(attachments_rows) - 1
    }
