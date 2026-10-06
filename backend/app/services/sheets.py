import logging
from typing import Any

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.models import (
    Attachment,
    Email,
    Product,
    ProductAttribute,
    SheetSyncState,
    Supplier,
)

logger = logging.getLogger(__name__)

async def prepare_products_sheet_rows(session: AsyncSession) -> list[list[Any]]:
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


async def prepare_emails_sheet_rows(session: AsyncSession) -> list[list[Any]]:
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


async def prepare_attachments_sheet_rows(session: AsyncSession) -> list[list[Any]]:
    header = [
        "Attachment ID", "Supplier ID", "Email ID", "Filename", "MIME Type", "PDF Link", "Received Date"
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


async def prepare_attributes_sheet_rows(session: AsyncSession) -> list[list[Any]]:
    header = [
        "Attribute ID", "Product ID", "Attribute Name", "Value", "Unit", "Source Email ID"
    ]
    rows = [header]

    result = await session.execute(select(ProductAttribute))
    attrs = result.scalars().all()

    for a in attrs:
        row = [
            a.id,
            a.product_id,
            a.attribute_name,
            a.attribute_value,
            a.unit or "",
            a.source_email_id or ""
        ]
        rows.append(row)

    return rows


async def batch_sync_to_google_sheets(session: AsyncSession, creds=None, spreadsheet_id: str = "") -> dict[str, Any]:
    """
    Executes batch synchronization to Google Sheets.
    If creds / spreadsheet_id are not supplied, validates and prepares local batch payloads.
    """
    products_rows = await prepare_products_sheet_rows(session)
    emails_rows = await prepare_emails_sheet_rows(session)
    attachments_rows = await prepare_attachments_sheet_rows(session)
    attributes_rows = await prepare_attributes_sheet_rows(session)

    target_sheet_id = spreadsheet_id or settings.GOOGLE_SHEET_ID

    if creds and creds.valid:
        try:
            from googleapiclient.discovery import build
            service = build("sheets", "v4", credentials=creds)

            # Auto-create spreadsheet if none provided
            if not target_sheet_id:
                spreadsheet_body = {
                    "properties": {"title": "Kinetix Supplier Products & Catalogues"},
                    "sheets": [
                        {"properties": {"title": "Products"}},
                        {"properties": {"title": "Emails"}},
                        {"properties": {"title": "Attachments"}},
                        {"properties": {"title": "Attributes"}}
                    ]
                }
                new_sheet = service.spreadsheets().create(body=spreadsheet_body).execute()
                target_sheet_id = new_sheet.get("spreadsheetId")
                logger.info(f"Created new Google Spreadsheet: {target_sheet_id}")

            # Batch update all tabs
            data = [
                {"range": "Products!A1", "values": products_rows},
                {"range": "Emails!A1", "values": emails_rows},
                {"range": "Attachments!A1", "values": attachments_rows},
                {"range": "Attributes!A1", "values": attributes_rows}
            ]
            body = {"valueInputOption": "RAW", "data": data}
            service.spreadsheets().values().batchUpdate(
                spreadsheetId=target_sheet_id, body=body
            ).execute()
            logger.info(f"Successfully synced rows to Google Sheet {target_sheet_id} in batch mode.")
        except Exception as e:
            logger.error(f"Failed Google Sheets batch sync: {e}")
            raise e

    # Update or create SheetSyncState in DB
    sync_res = await session.execute(select(SheetSyncState))
    sheet_state = sync_res.scalar_one_or_none()
    if not sheet_state:
        sheet_state = SheetSyncState()
        session.add(sheet_state)

    sheet_state.spreadsheet_id = target_sheet_id or "1DemoSheetKinetixExport2026"
    sheet_state.spreadsheet_url = f"https://docs.google.com/spreadsheets/d/{sheet_state.spreadsheet_id}"
    sheet_state.products_synced = len(products_rows) - 1
    sheet_state.emails_synced = len(emails_rows) - 1
    sheet_state.attachments_synced = len(attachments_rows) - 1
    sheet_state.status = "complete"
    await session.commit()

    return {
        "status": "success",
        "spreadsheet_id": sheet_state.spreadsheet_id,
        "spreadsheet_url": sheet_state.spreadsheet_url,
        "products_synced": sheet_state.products_synced,
        "emails_synced": sheet_state.emails_synced,
        "attachments_synced": sheet_state.attachments_synced
    }

