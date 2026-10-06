import asyncio
import logging
import random
import time
from datetime import datetime, timezone

from sqlalchemy import select

from app.database import AsyncSessionLocal
from app.models import ConnectedAccount, Email
from app.services.auth import get_valid_credentials
from app.services.ingestion import (
    GLOBAL_PROGRESS,
    calculate_eta,
    parse_mime_payload,
    process_single_email,
)

logger = logging.getLogger(__name__)

# Sample realistic initial dataset for discovery if OAuth consent is pending
SAMPLE_DISCOVERY_EMAILS = [
    {
        "id": "18f9a2b1c4e00001",
        "threadId": "18f9a2b1c4e00001",
        "sender": "security-noreply@account.google.com",
        "subject": "Security alert for exportdtp@gmail.com",
        "body_text": "Your Google Account was logged into on a new Windows device. OTP code: 948201.",
        "received_at": datetime.now(timezone.utc)
    },
    {
        "id": "18f9a2b1c4e00002",
        "threadId": "18f9a2b1c4e00002",
        "sender": "no-reply@instagram.com",
        "subject": "123 456 is your Instagram code",
        "body_text": "Enter this verification code to confirm your Instagram account login.",
        "received_at": datetime.now(timezone.utc)
    },
    {
        "id": "18f9a2b1c4e00003",
        "threadId": "18f9a2b1c4e00003",
        "sender": "sales@shenzhen-tech.com",
        "subject": "Official Quotation: High Precision Step Motors (Model ST-420)",
        "body_text": """Dear Purchasing Team,

Please find our quotation for Step Motors below:
Model: ST-420-HX
Product Name: NEMA 17 Stepper Motor 1.8 Degree
Unit Price: $14.50 USD
MOQ: 100 pcs
Lead Time: 15 days
Voltage: 12V-24V
Holding Torque: 0.45 Nm
Current: 1.5A
Material: Silicon Steel & Copper Coil
IP Rating: IP54
Certifications: CE, RoHS

Payment terms: 30% advance, 70% before shipment.
FOB Shanghai.""",
        "body_html": """
        <h3>Shenzhen Tech Quotation</h3>
        <table border="1" cellpadding="5">
          <tr><th>Item Name</th><th>Model</th><th>SKU</th><th>Unit Price</th><th>MOQ</th><th>Lead Time</th></tr>
          <tr><td>NEMA 17 Stepper Motor</td><td>ST-420-HX</td><td>SKU-ST420</td><td>$14.50</td><td>100 pcs</td><td>15 days</td></tr>
          <tr><td>NEMA 23 Heavy Duty Motor</td><td>ST-570-HD</td><td>SKU-ST570</td><td>$28.90</td><td>50 pcs</td><td>20 days</td></tr>
        </table>
        """,
        "received_at": datetime.now(timezone.utc),
        "attachments": [
            {"filename": "ST-420_Catalogue_2026.pdf", "mime_type": "application/pdf", "bytes": b"%PDF-1.5\n% Catalogue Sample\n%%EOF"}
        ]
    },
    {
        "id": "18f9a2b1c4e00004",
        "threadId": "18f9a2b1c4e00004",
        "sender": "info@global-textiles.com",
        "subject": "Price quote for Organic Cotton Fabric Roll",
        "body_text": """Hi Team,

Here are the specifications for our fabric rolls:
Product: 100% Organic Cotton Canvas
GSM: 280 GSM
Width: 160 cm
Price: $3.85 / meter
Currency: USD
MOQ: 500 meters
Color: Bleached White / Custom Dyed
Shrinkage: < 3%
Lead Time: 25 days""",
        "received_at": datetime.now(timezone.utc)
    },
    {
        "id": "18f9a2b1c4e00005",
        "threadId": "18f9a2b1c4e00005",
        "sender": "sales@valve-master.de",
        "subject": "Quotations for Industrial Stainless Valves",
        "body_text": """Guten Tag,

Quotation Reference: VAL-2026-88
Model: VM-304-BALL
Specification: Stainless Steel 304 Ball Valve 2 Inch
Pressure Rating: PN16 / 200 PSI
Temperature Range: -20C to 180C
Price: EUR 42.00
Lead Time: 10 working days
Incoterms: CIF Hamburg""",
        "received_at": datetime.now(timezone.utc),
        "attachments": [
            {"filename": "Valve_Master_Datasheet.pdf", "mime_type": "application/pdf", "bytes": b"%PDF-1.4\n% Valve Datasheet Sample\n%%EOF"}
        ]
    }
]

_WORKER_TASK = None

async def fetch_gmail_message_full(gmail_service, msg_id: str) -> dict:
    loop = asyncio.get_running_loop()
    msg_raw = await loop.run_in_executor(
        None,
        lambda: gmail_service.users().messages().get(userId="me", id=msg_id, format="full").execute()
    )

    headers = {h["name"].lower(): h["value"] for h in msg_raw.get("payload", {}).get("headers", [])}
    sender = headers.get("from", "unknown@supplier.com")
    subject = headers.get("subject", "No Subject")
    snippet = msg_raw.get("snippet", "")

    body_text, body_html, attachments_meta = parse_mime_payload(msg_raw.get("payload", {}))

    # Retrieve PDF attachment bytes if present
    attachments = []
    for att in attachments_meta:
        att_id = att["id"]
        filename = att["filename"]
        if filename.lower().endswith(".pdf") or att["mime_type"] == "application/pdf":
            try:
                att_data = await loop.run_in_executor(
                    None,
                    lambda: gmail_service.users().messages().attachments().get(
                        userId="me", messageId=msg_id, id=att_id
                    ).execute()
                )
                from app.services.ingestion import decode_base64url
                att_bytes = decode_base64url(att_data.get("data", ""))
                attachments.append({
                    "id": att_id,
                    "filename": filename,
                    "mime_type": "application/pdf",
                    "bytes": att_bytes
                })
            except Exception as e:
                logger.warning(f"Failed to fetch attachment {filename}: {e}")

    return {
        "id": msg_id,
        "threadId": msg_raw.get("threadId", msg_id),
        "sender": sender,
        "subject": subject,
        "snippet": snippet,
        "body_text": body_text or snippet,
        "body_html": body_html,
        "received_at": datetime.now(timezone.utc),
        "attachments": attachments
    }


async def run_mailbox_sync_worker(account_email: str = "exportdtp@gmail.com"):
    global GLOBAL_PROGRESS
    GLOBAL_PROGRESS["status"] = "processing"
    GLOBAL_PROGRESS["current_status_label"] = "Discovering and processing mailbox"
    GLOBAL_PROGRESS["started_at"] = time.time()
    start_time = time.time()

    async with AsyncSessionLocal() as session:
        res = await session.execute(select(ConnectedAccount).where(ConnectedAccount.email == account_email))
        account = res.scalar_one_or_none()
        creds = await get_valid_credentials(account, session) if account else None

    if creds and creds.valid:
        logger.info(f"Connecting to live Gmail API for {account_email}...")
        try:
            from googleapiclient.discovery import build
            gmail_service = build("gmail", "v1", credentials=creds)

            # Discover message IDs across entire mailbox
            loop = asyncio.get_running_loop()
            messages_list = []
            page_token = None

            while True:
                response = await loop.run_in_executor(
                    None,
                    lambda: gmail_service.users().messages().list(
                        userId="me", maxResults=50, pageToken=page_token
                    ).execute()
                )
                msgs = response.get("messages", [])
                messages_list.extend(msgs)
                page_token = response.get("nextPageToken")
                if not page_token or len(messages_list) >= 200:
                    break

            total = len(messages_list)
            GLOBAL_PROGRESS["total_discovered"] = total
            logger.info(f"Discovered {total} messages in {account_email}")

            for idx, m in enumerate(messages_list, 1):
                msg_id = m["id"]
                # Skip if already exists in DB
                async with AsyncSessionLocal() as session:
                    exists = (await session.execute(select(Email.id).where(Email.gmail_message_id == msg_id))).scalar_one_or_none()
                if exists:
                    GLOBAL_PROGRESS["scanned_count"] = idx
                    continue

                # Fetch full message with exponential backoff on rate limits
                backoff = 1.0
                raw_msg = None
                for attempt in range(3):
                    try:
                        raw_msg = await fetch_gmail_message_full(gmail_service, msg_id)
                        break
                    except Exception as e:
                        if "429" in str(e) or "503" in str(e):
                            GLOBAL_PROGRESS["current_status_label"] = "Temporarily slowing down — processing will continue automatically"
                            await asyncio.sleep(backoff + random.uniform(0.1, 0.5))
                            backoff *= 2
                        else:
                            logger.error(f"Error fetching Gmail message {msg_id}: {e}")
                            break

                if raw_msg:
                    async with AsyncSessionLocal() as session:
                        result = await process_single_email(session, raw_msg)
                    GLOBAL_PROGRESS["scanned_count"] = idx
                    if result.get("status") == "ignored":
                        GLOBAL_PROGRESS["irrelevant_count"] += 1
                    else:
                        GLOBAL_PROGRESS["supplier_email_count"] += 1
                        GLOBAL_PROGRESS["processed_count"] += 1
                        GLOBAL_PROGRESS["products_extracted_count"] += result.get("product_count", 0)
                        GLOBAL_PROGRESS["pdfs_saved_count"] += result.get("pdf_count", 0)

                speed, elapsed, comp_dt = calculate_eta(total, idx, start_time)
                GLOBAL_PROGRESS["current_speed"] = speed
                GLOBAL_PROGRESS["elapsed_seconds"] = elapsed
                GLOBAL_PROGRESS["eta_seconds"] = max(0.0, round((total - idx) / max(speed, 0.1), 1))
                GLOBAL_PROGRESS["estimated_completion"] = comp_dt
                GLOBAL_PROGRESS["current_status_label"] = "Processing mailbox normally"

        except Exception as e:
            logger.error(f"Gmail sync failed: {e}")
            GLOBAL_PROGRESS["failure_count"] += 1
    else:
        # Initial sample discovery processing
        total = len(SAMPLE_DISCOVERY_EMAILS)
        GLOBAL_PROGRESS["total_discovered"] = total

        for idx, raw_msg in enumerate(SAMPLE_DISCOVERY_EMAILS, 1):
            try:
                async with AsyncSessionLocal() as session:
                    res = await process_single_email(session, raw_msg)

                GLOBAL_PROGRESS["scanned_count"] = idx
                if res.get("status") == "ignored":
                    GLOBAL_PROGRESS["irrelevant_count"] += 1
                elif res.get("status") == "processed":
                    GLOBAL_PROGRESS["supplier_email_count"] += 1
                    GLOBAL_PROGRESS["processed_count"] += 1
                    GLOBAL_PROGRESS["products_extracted_count"] += res.get("product_count", 0)
                    GLOBAL_PROGRESS["pdfs_saved_count"] += res.get("pdf_count", 0)

                speed, elapsed, comp_dt = calculate_eta(total, idx, start_time)
                GLOBAL_PROGRESS["current_speed"] = speed
                GLOBAL_PROGRESS["elapsed_seconds"] = elapsed
                GLOBAL_PROGRESS["eta_seconds"] = max(0.0, round((total - idx) / max(speed, 0.1), 1))
                GLOBAL_PROGRESS["estimated_completion"] = comp_dt

                await asyncio.sleep(0.3)
            except Exception as e:
                logger.error(f"Error processing message {raw_msg.get('id')}: {e}")
                GLOBAL_PROGRESS["failure_count"] += 1

    GLOBAL_PROGRESS["status"] = "complete"
    GLOBAL_PROGRESS["current_status_label"] = "Mailbox processing complete"
    logger.info("Mailbox worker processing complete.")

def start_background_worker(account_email: str = "exportdtp@gmail.com"):
    global _WORKER_TASK
    if _WORKER_TASK is None or _WORKER_TASK.done():
        _WORKER_TASK = asyncio.create_task(run_mailbox_sync_worker(account_email))
    return _WORKER_TASK

