import pytest

from app.services.pdf_guardrail import (
    PDFGuardrailViolationError,
    assert_pdf_never_parsed,
    process_pdf_attachment,
)


def test_pdf_guardrail_downloads_and_links_only():
    pdf_bytes = b"%PDF-1.5 Sample test catalogue pdf byte contents"
    filename = "supplier_catalogue_2026.pdf"

    result = process_pdf_attachment(filename, pdf_bytes, email_id="email_123", supplier_id="sup_456")

    assert result["is_pdf"] is True
    assert result["filename"] == filename
    assert result["web_view_link"].startswith("/api/catalogues/download/")

def test_pdf_never_sent_to_ocr_or_llm():
    with pytest.raises(PDFGuardrailViolationError):
        assert_pdf_never_parsed("ocr")

    with pytest.raises(PDFGuardrailViolationError):
        assert_pdf_never_parsed("send_pdf_to_llm")

    with pytest.raises(PDFGuardrailViolationError):
        assert_pdf_never_parsed("parse_pdf")
