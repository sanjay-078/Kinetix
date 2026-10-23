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
    Synchronize the current database with a *real* Google spreadsheet.

    A successful response always means the Google Sheets API accepted the writes.
    Offline payload validation belongs in tests; it must not masquerade as syncing.
    """
    if creds is None or not getattr(creds, "valid", False):
        raise RuntimeError("Google Sheets sync requires an authorized Google account")

    state_result = await session.execute(select(SheetSyncState))
    sheet_state = state_result.scalar_one_or_none()
    persisted_id = sheet_state.spreadsheet_id if sheet_state else ""
    # Discard the legacy demo ID from earlier simulated "successful" syncs.
    if persisted_id == "1DemoSheetKinetixExport2026":
        persisted_id = ""
    target_sheet_id = spreadsheet_id or settings.GOOGLE_SHEET_ID or persisted_id

    products_rows = await prepare_products_sheet_rows(session)
    emails_rows = await prepare_emails_sheet_rows(session)
    attachments_rows = await prepare_attachments_sheet_rows(session)
    attributes_rows = await prepare_attributes_sheet_rows(session)

    from googleapiclient.discovery import build

    try:
        service = build("sheets", "v4", credentials=creds, cache_discovery=False)
        sheets_api = service.spreadsheets()
        required_tabs = ("Products", "Emails", "Attachments", "Attributes")

        if not target_sheet_id:
            document = sheets_api.create(
                body={
                    "properties": {"title": "Kinetix Supplier Products & Catalogues"},
                    "sheets": [{"properties": {"title": name}} for name in required_tabs],
                }
            ).execute()
            target_sheet_id = document["spreadsheetId"]
            logger.info("Created a Google spreadsheet for supplier data")
        else:
            document = sheets_api.get(spreadsheetId=target_sheet_id).execute()
            existing_tabs = {
                sheet["properties"]["title"] for sheet in document.get("sheets", [])
            }
            missing_tabs = [name for name in required_tabs if name not in existing_tabs]
            if missing_tabs:
                sheets_api.batchUpdate(
                    spreadsheetId=target_sheet_id,
                    body={
                        "requests": [
                            {"addSheet": {"properties": {"title": name}}}
                            for name in missing_tabs
                        ]
                    },
                ).execute()

        # Clearing first prevents stale trailing rows when the dataset shrinks.
        sheets_api.values().batchClear(
            spreadsheetId=target_sheet_id,
            body={"ranges": list(required_tabs)},
        ).execute()
        sheets_api.values().batchUpdate(
            spreadsheetId=target_sheet_id,
            body={
                "valueInputOption": "RAW",
                "data": [
                    {"range": "Products!A1", "values": products_rows},
                    {"range": "Emails!A1", "values": emails_rows},
                    {"range": "Attachments!A1", "values": attachments_rows},
                    {"range": "Attributes!A1", "values": attributes_rows},
                ],
            },
        ).execute()
    except Exception:
        logger.exception("Google Sheets sync failed; no success state recorded")
        raise

    if sheet_state is None:
        sheet_state = SheetSyncState()
        session.add(sheet_state)

    sheet_state.spreadsheet_id = target_sheet_id
    sheet_state.spreadsheet_url = (
        f"https://docs.google.com/spreadsheets/d/{target_sheet_id}"
    )
    sheet_state.products_synced = len(products_rows) - 1
    sheet_state.emails_synced = len(emails_rows) - 1
    sheet_state.attachments_synced = len(attachments_rows) - 1
    sheet_state.status = "complete"
    sheet_state.error_message = None
    from datetime import datetime, timezone
    sheet_state.last_sync_at = datetime.now(timezone.utc)
    await session.commit()

    return {
        "status": "success",
        "spreadsheet_id": sheet_state.spreadsheet_id,
        "spreadsheet_url": sheet_state.spreadsheet_url,
        "products_synced": sheet_state.products_synced,
        "emails_synced": sheet_state.emails_synced,
        "attachments_synced": sheet_state.attachments_synced,
    }
