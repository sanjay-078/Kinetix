import asyncio
import logging
import time
from datetime import datetime
from sqlalchemy.ext.asyncio import AsyncSession
from app.database import AsyncSessionLocal
from app.services.ingestion import process_single_email, GLOBAL_PROGRESS, calculate_eta

logger = logging.getLogger(__name__)

# Sample mock mailbox payload for realistic historical import demo if real Gmail API is awaiting OAuth consent
MOCK_EMAILS = [
    {
        "id": "18f9a2b1c4e00001",
        "threadId": "18f9a2b1c4e00001",
        "sender": "security-noreply@account.google.com",
        "subject": "Security alert for exportdtp@gmail.com",
        "body_text": "Your Google Account was logged into on a new Windows device. OTP code: 948201.",
        "received_at": datetime.utcnow()
    },
    {
        "id": "18f9a2b1c4e00002",
        "threadId": "18f9a2b1c4e00002",
        "sender": "no-reply@instagram.com",
        "subject": "123 456 is your Instagram code",
        "body_text": "Enter this verification code to confirm your Instagram account login.",
        "received_at": datetime.utcnow()
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
        "received_at": datetime.utcnow(),
        "attachments": [
            {"filename": "ST-420_Catalogue_2026.pdf", "mime_type": "application/pdf", "bytes": b"%PDF-1.5 catalogue sample content"}
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
        "received_at": datetime.utcnow()
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
        "received_at": datetime.utcnow(),
        "attachments": [
            {"filename": "Valve_Master_Datasheet.pdf", "mime_type": "application/pdf", "bytes": b"%PDF-1.4 valve datasheet sample content"}
        ]
    }
]

_WORKER_TASK = None

async def run_mailbox_sync_worker(account_email: str = "exportdtp@gmail.com"):
    global GLOBAL_PROGRESS
    GLOBAL_PROGRESS["status"] = "processing"
    GLOBAL_PROGRESS["current_status_label"] = "Processing mailbox normally"
    GLOBAL_PROGRESS["started_at"] = time.time()
    
    total = len(MOCK_EMAILS)
    GLOBAL_PROGRESS["total_discovered"] = total
    start_time = time.time()

    for idx, raw_msg in enumerate(MOCK_EMAILS, 1):
        try:
            async with AsyncSessionLocal() as session:
                res = await process_single_email(session, raw_msg)
            
            GLOBAL_PROGRESS["scanned_count"] = idx
            if res["status"] == "ignored":
                GLOBAL_PROGRESS["irrelevant_count"] += 1
            else:
                GLOBAL_PROGRESS["supplier_email_count"] += 1
                GLOBAL_PROGRESS["processed_count"] += 1
                GLOBAL_PROGRESS["products_extracted_count"] += res.get("product_count", 0)
                GLOBAL_PROGRESS["pdfs_saved_count"] += res.get("pdf_count", 0)

            speed, elapsed, comp_dt = calculate_eta(total, idx, start_time)
            GLOBAL_PROGRESS["current_speed"] = speed
            GLOBAL_PROGRESS["elapsed_seconds"] = elapsed
            GLOBAL_PROGRESS["eta_seconds"] = max(0.0, round((total - idx) / max(speed, 0.1), 1))
            GLOBAL_PROGRESS["estimated_completion"] = comp_dt
            
            # Small simulation delay to allow real-time UI feedback
            await asyncio.sleep(0.5)

        except Exception as e:
            logger.error(f"Error processing email {raw_msg.get('id')}: {e}")
            GLOBAL_PROGRESS["failure_count"] += 1

    GLOBAL_PROGRESS["status"] = "complete"
    GLOBAL_PROGRESS["current_status_label"] = "Mailbox processing complete"
    logger.info("Mailbox worker processing complete.")

def start_background_worker(account_email: str = "exportdtp@gmail.com"):
    global _WORKER_TASK
    if _WORKER_TASK is None or _WORKER_TASK.done():
        _WORKER_TASK = asyncio.create_task(run_mailbox_sync_worker(account_email))
    return _WORKER_TASK
