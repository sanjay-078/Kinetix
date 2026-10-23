import asyncio
import base64
import logging
import time
from datetime import datetime, timedelta, timezone
from typing import Any

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.models import (
    Attachment,
    Email,
    Product,
    ProductAttribute,
    ReviewItem,
    Supplier,
)
from app.services.classifier import classify_email
from app.services.extractor import extract_products_from_email
from app.services.pdf_guardrail import process_pdf_attachment

logger = logging.getLogger(__name__)

GLOBAL_PROGRESS: dict[str, Any] = {
    "status": "idle",
    "account_email": "exportdtp@gmail.com",
    "total_discovered": 0,
    "scanned_count": 0,
    "irrelevant_count": 0,
    "supplier_email_count": 0,
    "processed_count": 0,
    "products_extracted_count": 0,
    "pdfs_saved_count": 0,
    "failure_count": 0,
    "retry_count": 0,
    "current_speed": 0.0,
    "elapsed_seconds": 0.0,
    "eta_seconds": 0.0,
    "estimated_completion": None,
    "current_status_label": "Ready to connect"
}

def calculate_eta(total: int, scanned: int, start_time: float) -> tuple[float, float, str | None]:
    """
    Calculates current processing speed (msgs/sec) and real remaining ETA in seconds.
    Smooths throughput calculations.
    """
    elapsed = time.time() - start_time
    if scanned <= 0 or elapsed <= 0:
        return 0.0, 0.0, None

    speed = scanned / elapsed
    remaining = max(0, total - scanned)

    if speed <= 0:
        return round(speed, 2), round(elapsed, 1), None

    eta_sec = remaining / speed
    now_utc = datetime.now(timezone.utc)
    completion_dt = (now_utc + timedelta(seconds=eta_sec)).isoformat()
    return round(speed, 2), round(elapsed, 1), completion_dt


def decode_base64url(data: str) -> bytes:
    if not data:
        return b""
    padded = data + "=" * ((4 - len(data) % 4) % 4)
    return base64.urlsafe_b64decode(padded.encode("ascii"))


def parse_mime_payload(payload: dict[str, Any]) -> tuple[str, str, list[dict[str, Any]]]:
    """
    Recursively extracts text/plain, text/html, and attachment metadata from a Gmail payload.
    """
    body_text = ""
    body_html = ""
    attachments = []

    mime_type = payload.get("mimeType", "")
    parts = payload.get("parts", [])
    body_data = payload.get("body", {}).get("data")
    filename = payload.get("filename", "")

    if body_data and not filename:
        try:
            decoded = decode_base64url(body_data).decode("utf-8", errors="replace")
            if mime_type == "text/plain":
                body_text += decoded + "\n"
            elif mime_type == "text/html":
                body_html += decoded + "\n"
        except Exception:
            pass

    if filename and payload.get("body", {}).get("attachmentId"):
        attachments.append({
            "id": payload["body"]["attachmentId"],
            "filename": filename,
            "mime_type": mime_type or "application/octet-stream",
            "size": payload.get("body", {}).get("size", 0)
        })

    for part in parts:
        sub_text, sub_html, sub_att = parse_mime_payload(part)
        if sub_text:
            body_text += sub_text + "\n"
        if sub_html:
            body_html += sub_html + "\n"
        attachments.extend(sub_att)

    return body_text.strip(), body_html.strip(), attachments


async def process_single_email(
    session: AsyncSession, raw_msg: dict[str, Any], google_creds=None
) -> dict[str, Any]:
    """
    Durable, idempotent processing of a single Gmail message.
    """
    msg_id = raw_msg.get("id")
    thread_id = raw_msg.get("threadId", "")
    sender = raw_msg.get("sender", "unknown@supplier.com")
    subject = raw_msg.get("subject", "No Subject")
    body_text = raw_msg.get("body_text", "")
    body_html = raw_msg.get("body_html", "")
    received_at = raw_msg.get("received_at") or datetime.now(timezone.utc)
    if isinstance(received_at, str):
        try:
            received_at = datetime.fromisoformat(received_at.replace("Z", "+00:00"))
        except Exception:
            received_at = datetime.now(timezone.utc)

    attachments_raw = raw_msg.get("attachments", [])
    sender_domain = sender.split("@")[-1] if "@" in sender else "unknown.com"

    # Idempotency check: Skip if email already exists
    res = await session.execute(select(Email).where(Email.gmail_message_id == msg_id))
    existing_email = res.scalar_one_or_none()
    if existing_email:
        return {"status": "skipped", "reason": "duplicate", "email_id": existing_email.id}

    # Step 1: Fast Python classification
    classification, reason = classify_email(sender, sender_domain, subject, body_text)

    email_record = Email(
        gmail_message_id=msg_id,
        gmail_thread_id=thread_id,
        account_email=raw_msg.get("account_email", "exportdtp@gmail.com"),
        sender=sender,
        sender_domain=sender_domain,
        subject=subject,
        snippet=raw_msg.get("snippet", body_text[:100]),
        body_text=body_text,
        body_html_sanitized=body_html,
        received_at=received_at,
        classification=classification,
        classification_reason=reason,
        processing_status="pending",
        source_email_link=f"https://mail.google.com/mail/u/0/#inbox/{msg_id}"
    )
    session.add(email_record)
    await session.flush()

    # Step 2: Handle Irrelevant Email
    if classification == "irrelevant":
        email_record.processing_status = "ignored"
        await session.commit()
        return {"status": "ignored", "reason": reason}

    # Step 3: Get or create Supplier
    sup_res = await session.execute(select(Supplier).where(Supplier.domain == sender_domain))
    supplier = sup_res.scalar_one_or_none()
    if not supplier:
        supplier_name = sender_domain.split(".")[0].title() if "." in sender_domain else sender_domain
        supplier = Supplier(
            name=supplier_name,
            domain=sender_domain,
            primary_email=sender,
            email_count=1
        )
        session.add(supplier)
        await session.flush()
    else:
        supplier.email_count += 1

    # Step 4: PDF Attachment Guardrail handling
    pdf_count = 0
    first_pdf_link = None
    for att in attachments_raw:
        filename = att.get("filename", "attachment.pdf")
        att_bytes = att.get("bytes")

        if filename.lower().endswith(".pdf") or att.get("mime_type") == "application/pdf":
            if not isinstance(att_bytes, (bytes, bytearray)) or not att_bytes:
                logger.error("Skipping PDF attachment without original downloaded bytes")
                continue
            try:
                if settings.APP_ENV.lower() == "production":
                    if not google_creds or not getattr(google_creds, "valid", False):
                        raise RuntimeError("Google Drive authorization is required for PDF storage")
                    from app.services.drive import upload_original_pdf

                    pdf_info = await asyncio.to_thread(
                        upload_original_pdf, google_creds, filename, att_bytes
                    )
                    pdf_info["storage_path"] = None
                else:
                    pdf_info = process_pdf_attachment(
                        filename, att_bytes, email_record.id, supplier.id
                    )
                pdf_count += 1
                if not first_pdf_link:
                    first_pdf_link = pdf_info["web_view_link"]

                attachment_rec = Attachment(
                    email_id=email_record.id,
                    supplier_id=supplier.id,
                    gmail_attachment_id=att.get("id", uuid_hex()),
                    filename=filename,
                    mime_type="application/pdf",
                    file_size=pdf_info["file_size"],
                    is_pdf=True,
                    storage_path=pdf_info["storage_path"],
                    drive_file_id=pdf_info.get("drive_file_id"),
                    web_view_link=pdf_info["web_view_link"]
                )
                session.add(attachment_rec)
            except Exception:
                logger.exception("Unable to store original PDF attachment")
                # No pretend success: roll back the email so it can be retried.
                if settings.APP_ENV.lower() == "production":
                    raise

    email_record.pdf_count = pdf_count
    supplier.catalogue_count += pdf_count

    # Step 5: Product Extraction
    extracted_products = extract_products_from_email(body_text, body_html)
    product_count = 0

    for prod_data in extracted_products:
        product_rec = Product(
            email_id=email_record.id,
            supplier_id=supplier.id,
            name=prod_data.get("name", "Quoted Item"),
            model=prod_data.get("model"),
            sku=prod_data.get("sku"),
            price=prod_data.get("price"),
            currency=prod_data.get("currency", "USD"),
            quantity=prod_data.get("quantity"),
            moq=prod_data.get("moq"),
            lead_time=prod_data.get("lead_time"),
            description=prod_data.get("description"),
            catalogue_link=first_pdf_link,
            source_email_link=email_record.source_email_link,
            received_at=received_at,
            confidence_score=0.95 if prod_data.get("price") or prod_data.get("model") else 0.6
        )
        session.add(product_rec)
        await session.flush()
        product_count += 1

        for dyn_attr in prod_data.get("dynamic_attributes", []):
            attr_rec = ProductAttribute(
                product_id=product_rec.id,
                attribute_name=dyn_attr.get("attribute_name", "Spec"),
                attribute_value=str(dyn_attr.get("attribute_value", "")),
                unit=dyn_attr.get("unit"),
                source_email_id=email_record.id
            )
            session.add(attr_rec)

    # Step 6: Uncertainty & Review Queue
    if classification == "uncertain" or (product_count == 0 and pdf_count == 0):
        email_record.processing_status = "review_required"
        review_item = ReviewItem(
            email_id=email_record.id,
            issue_type="extraction_uncertainty",
            uncertainty_reason="Multiple pricing structures or ambiguous key values",
            candidate_values={"subject": subject, "extracted": extracted_products},
            confidence=0.5
        )
        session.add(review_item)
    else:
        email_record.processing_status = "processed"

    email_record.product_count = product_count
    supplier.product_count += product_count

    await session.commit()

    return {
        "status": "processed",
        "email_id": email_record.id,
        "classification": classification,
        "product_count": product_count,
        "pdf_count": pdf_count
    }


def uuid_hex() -> str:
    import uuid
    return uuid.uuid4().hex

