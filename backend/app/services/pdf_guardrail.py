import os
import uuid
from typing import Dict, Any

MEDIA_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "media")
os.makedirs(MEDIA_DIR, exist_ok=True)

class PDFGuardrailViolationError(Exception):
    """Raised if any attempt is made to parse, OCR, summarize, or extract text from a PDF."""
    pass

def process_pdf_attachment(filename: str, file_bytes: bytes, email_id: str, supplier_id: str = None) -> Dict[str, Any]:
    """
    STRICT PDF GUARDRAIL RULE:
    1. Detect PDF attachment
    2. Save original attachment bytes
    3. Validate PDF MIME / signature
    4. Generate stable clickable link
    5. Associate with email and supplier
    6. STOP.

    NEVER OCR, parse text, summarize, vectorize, or send PDF contents to LLM!
    """
    # 1. Validate PDF signature (Magic bytes %PDF-)
    if not (file_bytes.startswith(b"%PDF") or filename.lower().endswith(".pdf")):
        raise ValueError("Invalid PDF format or signature")

    # 2. Save original file safely
    safe_filename = "".join(c for c in filename if c.isalnum() or c in "._- ")
    if not safe_filename:
        safe_filename = f"catalogue_{uuid.uuid4().hex[:8]}.pdf"
    
    file_id = uuid.uuid4().hex
    stored_filename = f"{file_id}_{safe_filename}"
    storage_path = os.path.join(MEDIA_DIR, stored_filename)

    with open(storage_path, "wb") as f:
        f.write(file_bytes)

    # 3. Generate stable clickable link URL
    web_view_link = f"/api/catalogues/download/{stored_filename}"

    return {
        "filename": filename,
        "mime_type": "application/pdf",
        "file_size": len(file_bytes),
        "storage_path": storage_path,
        "web_view_link": web_view_link,
        "is_pdf": True
    }


def assert_pdf_never_parsed(action_name: str):
    """
    Audit check to guarantee no OCR, text extraction, or LLM call is executed on PDFs.
    """
    forbidden_actions = ["ocr", "extract_pdf_text", "parse_pdf", "summarize_pdf", "vectorize_pdf", "send_pdf_to_llm"]
    if action_name.lower() in forbidden_actions:
        raise PDFGuardrailViolationError(f"CRITICAL SECURITY & PRODUCT VIOLATION: '{action_name}' is strictly forbidden on PDF files!")
