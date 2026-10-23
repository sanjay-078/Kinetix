"""Regression tests for real-data-only ingestion and original PDF storage."""

from unittest.mock import MagicMock

import httpx
import pytest

from app.main import app
from app.services.ingestion import GLOBAL_PROGRESS
from app.services.worker import (
    discover_all_gmail_message_ids,
    run_mailbox_sync_worker,
)


class FakeRequest:
    def __init__(self, payload):
        self.payload = payload

    def execute(self):
        return self.payload


@pytest.mark.asyncio
async def test_mailbox_discovery_does_not_stop_at_200_messages():
    # Every page must be visited even when the mailbox contains >1000 messages.
    pages = {
        None: {
            "messages": [{"id": str(i)} for i in range(500)],
            "nextPageToken": "second",
        },
        "second": {
            "messages": [{"id": str(i)} for i in range(500, 1000)],
            "nextPageToken": "third",
        },
        "third": {"messages": [{"id": "1000"}]},
    }
    gmail = MagicMock()
    mailbox_messages = gmail.users.return_value.messages.return_value
    mailbox_messages.list.side_effect = lambda **kwargs: FakeRequest(
        pages[kwargs.get("pageToken")]
    )
    result = await discover_all_gmail_message_ids(gmail)
    assert len(result) == 1001
    assert len({message["id"] for message in result}) == 1001
    assert mailbox_messages.list.call_count == 3


@pytest.mark.asyncio
async def test_disconnected_mailbox_never_processes_demo_emails():
    await run_mailbox_sync_worker("not-connected-for-test@invalid.example")
    assert GLOBAL_PROGRESS["status"] == "awaiting_connection"
    assert GLOBAL_PROGRESS["total_discovered"] == 0
    assert GLOBAL_PROGRESS["processed_count"] == 0
    assert GLOBAL_PROGRESS["products_extracted_count"] == 0


@pytest.mark.asyncio
async def test_missing_original_pdf_returns_404_without_creating_a_fake(tmp_path, monkeypatch):
    from app.api import catalogues_routes

    monkeypatch.setattr(catalogues_routes, "MEDIA_DIR", str(tmp_path))
    filename = "supplier-original-does-not-exist.pdf"
    async with httpx.AsyncClient(
        transport=httpx.ASGITransport(app=app),
        base_url="http://test",
    ) as client:
        response = await client.get(f"/api/catalogues/download/{filename}")

    assert response.status_code == 404
    assert not (tmp_path / filename).exists()


@pytest.mark.asyncio
async def test_missing_pdf_attachment_bytes_never_create_a_catalogue(monkeypatch):
    from app.database import AsyncSessionLocal
    from app.services import ingestion

    def forbidden_fake_pdf(*args, **kwargs):
        raise AssertionError("No synthetic or missing PDF may be stored")

    monkeypatch.setattr(ingestion, "process_pdf_attachment", forbidden_fake_pdf)
    source_mail = {
        "id": "missing-original-pdf-fixture-20261023",
        "threadId": "missing-original-pdf-fixture-thread",
        "sender": "quotes@fixturesupplier.invalid",
        "subject": "Quotation for Model SAMPLE-42",
        "body_text": "Product: Test Actuator\nModel: SAMPLE-42\nPrice: USD 24.00",
        "attachments": [
            {"filename": "claimed-catalogue.pdf", "mime_type": "application/pdf"}
        ],
    }
    async with AsyncSessionLocal() as session:
        result = await ingestion.process_single_email(session, source_mail)
    assert result["pdf_count"] == 0
