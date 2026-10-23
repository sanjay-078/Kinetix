"""Asynchronous Gmail mailbox ingestion. No synthetic data in production."""

import asyncio
import logging
import random
import time
from datetime import datetime, timezone

from sqlalchemy import select

from app.config import settings
from app.database import AsyncSessionLocal
from app.models import ConnectedAccount, Email
from app.services.auth import get_valid_credentials
from app.services.ingestion import (
    GLOBAL_PROGRESS,
    calculate_eta,
    decode_base64url,
    parse_mime_payload,
    process_single_email,
)

logger = logging.getLogger(__name__)
_WORKER_TASK = None


async def discover_all_gmail_message_ids(gmail_service) -> list[dict]:
    """Discover all pages in the authorized mailbox without an arbitrary cap."""
    loop = asyncio.get_running_loop()
    discovered = []
    token = None
    seen_tokens = set()

    while True:
        response = await loop.run_in_executor(
            None,
            lambda current=token: gmail_service.users().messages().list(
                userId="me", maxResults=500, pageToken=current
            ).execute(),
        )
        discovered.extend(response.get("messages", []))
        token = response.get("nextPageToken")
        if not token:
            return discovered
        if token in seen_tokens:
            raise RuntimeError("Repeated Gmail pagination token; sync interrupted safely")
        seen_tokens.add(token)


async def fetch_gmail_message_full(gmail_service, msg_id: str) -> dict:
    loop = asyncio.get_running_loop()
    raw = await loop.run_in_executor(
        None,
        lambda: gmail_service.users().messages().get(
            userId="me", id=msg_id, format="full"
        ).execute(),
    )
    headers = {
        h["name"].lower(): h["value"]
        for h in raw.get("payload", {}).get("headers", [])
    }
    body_text, body_html, attachments_meta = parse_mime_payload(raw.get("payload", {}))
    attachments = []

    for meta in attachments_meta:
        attachment_id = meta.get("id")
        filename = meta.get("filename", "")
        if not attachment_id:
            continue
        if not (
            filename.lower().endswith(".pdf")
            or meta.get("mime_type") == "application/pdf"
        ):
            continue
        try:
            data = await loop.run_in_executor(
                None,
                lambda attachment=attachment_id: gmail_service.users()
                .messages().attachments().get(
                    userId="me", messageId=msg_id, id=attachment
                ).execute(),
            )
            attachments.append(
                {
                    "id": attachment_id,
                    "filename": filename,
                    "mime_type": "application/pdf",
                    # PDFs are saved byte-for-byte; contents must never be parsed.
                    "bytes": decode_base64url(data.get("data", "")),
                }
            )
        except Exception:
            logger.exception("Unable to fetch an original Gmail attachment")

    received_ms = raw.get("internalDate")
    received_at = (
        datetime.fromtimestamp(int(received_ms) / 1000, tz=timezone.utc)
        if received_ms else datetime.now(timezone.utc)
    )
    return {
        "id": msg_id,
        "threadId": raw.get("threadId", msg_id),
        "sender": headers.get("from", "unknown"),
        "subject": headers.get("subject", "No Subject"),
        "snippet": raw.get("snippet", ""),
        "body_text": body_text or raw.get("snippet", ""),
        "body_html": body_html,
        "received_at": received_at,
        "attachments": attachments,
    }


async def run_mailbox_sync_worker(account_email: str = "exportdtp@gmail.com"):
    """Process the authorized mailbox; duplicates are skipped on restart."""
    started = time.time()
    GLOBAL_PROGRESS.update(
        {
            "status": "discovering",
            "current_status_label": "Discovering Gmail messages",
            "started_at": started,
            "total_discovered": 0,
            "scanned_count": 0,
            "processed_count": 0,
            "irrelevant_count": 0,
            "supplier_email_count": 0,
            "products_extracted_count": 0,
            "pdfs_saved_count": 0,
            "failure_count": 0,
            "current_speed": 0.0,
            "elapsed_seconds": 0.0,
            "eta_seconds": None,
            "estimated_completion": None,
        }
    )

    async with AsyncSessionLocal() as session:
        query = await session.execute(
            select(ConnectedAccount).where(ConnectedAccount.email == account_email)
        )
        account = query.scalar_one_or_none()
        creds = await get_valid_credentials(account, session) if account else None

    if not creds or not creds.valid:
        GLOBAL_PROGRESS["status"] = "awaiting_connection"
        GLOBAL_PROGRESS["current_status_label"] = (
            "Connect Gmail to begin scanning real supplier messages"
        )
        return

    try:
        from googleapiclient.discovery import build

        gmail = await asyncio.get_running_loop().run_in_executor(
            None, lambda: build("gmail", "v1", credentials=creds, cache_discovery=False)
        )
        messages = await discover_all_gmail_message_ids(gmail)
        total = len(messages)
        GLOBAL_PROGRESS["total_discovered"] = total
        GLOBAL_PROGRESS["status"] = "processing"
        GLOBAL_PROGRESS["current_status_label"] = "Processing real Gmail messages"

        for index, message in enumerate(messages, 1):
            message_id = message["id"]
            async with AsyncSessionLocal() as session:
                previous = await session.execute(
                    select(Email.id).where(Email.gmail_message_id == message_id)
                )
                is_duplicate = previous.scalar_one_or_none() is not None

            if not is_duplicate:
                raw_msg = None
                for attempt in range(max(1, settings.MAX_RETRIES)):
                    try:
                        raw_msg = await fetch_gmail_message_full(gmail, message_id)
                        break
                    except Exception as exc:
                        if "429" in str(exc) or "503" in str(exc):
                            delay = min(60, (2 ** attempt) + random.uniform(0.1, 0.5))
                            GLOBAL_PROGRESS["current_status_label"] = "Rate limit; retrying"
                            await asyncio.sleep(delay)
                        else:
                            logger.exception("Gmail message fetch failed")
                            break
                if raw_msg is None:
                    GLOBAL_PROGRESS["failure_count"] += 1
                else:
                    try:
                        async with AsyncSessionLocal() as session:
                            result = await process_single_email(session, raw_msg)
                        if result.get("status") == "ignored":
                            GLOBAL_PROGRESS["irrelevant_count"] += 1
                        else:
                            GLOBAL_PROGRESS["supplier_email_count"] += 1
                            GLOBAL_PROGRESS["processed_count"] += 1
                            GLOBAL_PROGRESS["products_extracted_count"] += result.get(
                                "product_count", 0
                            )
                            GLOBAL_PROGRESS["pdfs_saved_count"] += result.get(
                                "pdf_count", 0
                            )
                    except Exception:
                        logger.exception("Supplier message processing failed")
                        GLOBAL_PROGRESS["failure_count"] += 1

            GLOBAL_PROGRESS["scanned_count"] = index
            speed, elapsed, completion = calculate_eta(total, index, started)
            GLOBAL_PROGRESS["current_speed"] = speed
            GLOBAL_PROGRESS["elapsed_seconds"] = elapsed
            GLOBAL_PROGRESS["eta_seconds"] = max(
                0.0, round((total - index) / max(speed, 0.1), 1)
            )
            GLOBAL_PROGRESS["estimated_completion"] = completion

        if GLOBAL_PROGRESS["failure_count"]:
            GLOBAL_PROGRESS["status"] = "partial_failure"
            GLOBAL_PROGRESS["current_status_label"] = (
                "Some messages failed; rerun to retry missing messages"
            )
        else:
            GLOBAL_PROGRESS["status"] = "complete"
            GLOBAL_PROGRESS["current_status_label"] = "Mailbox processing complete"
    except Exception:
        logger.exception("Mailbox synchronization failed")
        GLOBAL_PROGRESS["failure_count"] += 1
        GLOBAL_PROGRESS["status"] = "error"
        GLOBAL_PROGRESS["current_status_label"] = "Gmail synchronization failed"


def start_background_worker(account_email: str = "exportdtp@gmail.com"):
    global _WORKER_TASK
    if _WORKER_TASK is None or _WORKER_TASK.done():
        _WORKER_TASK = asyncio.create_task(run_mailbox_sync_worker(account_email))
    return _WORKER_TASK
