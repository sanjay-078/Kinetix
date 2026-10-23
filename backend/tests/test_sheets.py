from types import SimpleNamespace
from unittest.mock import MagicMock

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
async def test_sync_cannot_report_success_without_google_credentials():
    async with AsyncSessionLocal() as session:
        with pytest.raises(RuntimeError, match="authorized Google account"):
            await batch_sync_to_google_sheets(session)


@pytest.mark.asyncio
async def test_sync_with_google_credentials_writes_all_tabs(monkeypatch):
    from googleapiclient import discovery

    fake_service = MagicMock()
    fake_sheets = fake_service.spreadsheets.return_value
    fake_sheets.get.return_value.execute.return_value = {
        "sheets": [
            {"properties": {"title": name}}
            for name in ("Products", "Emails", "Attachments", "Attributes")
        ]
    }
    monkeypatch.setattr(discovery, "build", lambda *args, **kwargs: fake_service)

    async with AsyncSessionLocal() as session:
        result = await batch_sync_to_google_sheets(
            session,
            creds=SimpleNamespace(valid=True),
            spreadsheet_id="existing-provider-backed-sheet-id",
        )
        assert result["status"] == "success"
        assert result["spreadsheet_id"] == "existing-provider-backed-sheet-id"
        fake_sheets.values.return_value.batchClear.assert_called_once()
        fake_sheets.values.return_value.batchUpdate.assert_called_once()
        batch_body = fake_sheets.values.return_value.batchUpdate.call_args.kwargs["body"]
        assert {row["range"] for row in batch_body["data"]} == {
            "Products!A1", "Emails!A1", "Attachments!A1", "Attributes!A1"
        }
