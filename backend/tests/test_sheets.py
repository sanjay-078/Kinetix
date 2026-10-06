import pytest

from app.database import AsyncSessionLocal
from app.services.sheets import (
    batch_sync_to_google_sheets,
    prepare_attachments_sheet_rows,
    prepare_attributes_sheet_rows,
    prepare_emails_sheet_rows,
    prepare_products_sheet_rows,
)


@pytest.mark.asyncio
async def test_sheets_rows_structure():
    async with AsyncSessionLocal() as session:
        prod_rows = await prepare_products_sheet_rows(session)
        assert len(prod_rows) >= 1
        assert "Product ID" in prod_rows[0]
        assert "Additional Specifications" in prod_rows[0]
        assert "Catalogue Link" in prod_rows[0]

        email_rows = await prepare_emails_sheet_rows(session)
        assert len(email_rows) >= 1
        assert "Email ID" in email_rows[0]
        assert "Classification" in email_rows[0]

        att_rows = await prepare_attachments_sheet_rows(session)
        assert len(att_rows) >= 1
        assert "Attachment ID" in att_rows[0]
        assert "PDF Link" in att_rows[0]

        attr_rows = await prepare_attributes_sheet_rows(session)
        assert len(attr_rows) >= 1
        assert "Attribute ID" in attr_rows[0]
        assert "Attribute Name" in attr_rows[0]

@pytest.mark.asyncio
async def test_batch_sync_local_execution():
    async with AsyncSessionLocal() as session:
        res = await batch_sync_to_google_sheets(session)
        assert res["status"] == "success"
        assert "spreadsheet_url" in res
        assert "products_synced" in res
