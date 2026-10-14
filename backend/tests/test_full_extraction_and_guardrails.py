import pytest

from app.services.classifier import classify_email
from app.services.extractor import parse_html_tables, parse_key_value_pairs
from app.services.pdf_guardrail import (
    PDFGuardrailViolationError,
    assert_pdf_never_parsed,
    process_pdf_attachment,
)


def test_multi_product_html_table_parsing():
    html_content = """
    <table>
      <thead>
        <tr><th>Product</th><th>Model</th><th>SKU</th><th>Price</th><th>MOQ</th><th>Lead Time</th></tr>
      </thead>
      <tbody>
        <tr><td>CNC Spindle Motor 2.2kW</td><td>GDZ-80-2.2</td><td>SKU-SPINDLE-80</td><td>$185.00</td><td>5 pcs</td><td>7 days</td></tr>
        <tr><td>VFD Inverter 2.2kW</td><td>YL-620-A</td><td>SKU-VFD-2200</td><td>$75.00</td><td>10 pcs</td><td>5 days</td></tr>
        <tr><td>Water Cooling Pump 75W</td><td>WP-75W</td><td>SKU-PUMP-75</td><td>$16.50</td><td>20 pcs</td><td>3 days</td></tr>
      </tbody>
    </table>
    """
    products = parse_html_tables(html_content)
    assert len(products) == 3
    assert products[0]["model"] == "GDZ-80-2.2"
    assert products[0]["price"] == 185.00
    assert products[1]["model"] == "YL-620-A"
    assert products[1]["price"] == 75.00
    assert products[2]["model"] == "WP-75W"
    assert products[2]["price"] == 16.50

def test_dynamic_technical_attributes_extraction():
    quotation_text = """
    Model: BLDC-48V-1000W
    Product: High Torque Brushless DC Motor
    Price: $64.00
    Currency: USD
    MOQ: 50 pcs
    Rated Power: 1000W
    Rated Speed: 3000 RPM
    Operating Voltage: 48V DC
    Peak Torque: 3.2 Nm
    Insulation Class: Class F
    Protection Level: IP65
    Efficiency: 88%
    Dimensions: 110mm x 110mm x 165mm
    Weight: 4.8 kg
    Incoterms: FOB Ningbo
    Payment Terms: T/T 30% deposit, 70% before delivery
    """
    data = parse_key_value_pairs(quotation_text)
    assert data["model"] == "BLDC-48V-1000W"
    assert data["price"] == 64.00
    assert data["power"] == "1000W"
    assert data["voltage"] == "48V DC"
    assert data["speed_rpm"] == "3000 RPM"

    attr_names = {a["attribute_name"].lower(): a["attribute_value"] for a in data["dynamic_attributes"]}
    assert "peak torque" in attr_names
    assert "efficiency" in attr_names
    assert "insulation class" in attr_names


def test_pdf_guardrail_absolute_prohibition():
    # Attempting any forbidden PDF action MUST raise PDFGuardrailViolationError
    forbidden_actions = [
        "ocr",
        "extract_pdf_text",
        "parse_pdf",
        "summarize_pdf",
        "vectorize_pdf",
        "send_pdf_to_llm"
    ]
    for action in forbidden_actions:
        with pytest.raises(PDFGuardrailViolationError) as exc_info:
            assert_pdf_never_parsed(action)
        assert "strictly forbidden" in str(exc_info.value).lower()

def test_pdf_store_and_link_preservation(tmp_path):
    pdf_content = b"%PDF-1.4\n1 0 obj\n<<>>\nendobj\ntrailer\n<<>>\n%%EOF"
    res = process_pdf_attachment("SpecSheet_2026.pdf", pdf_content, "email-msg-999")
    assert res["is_pdf"] is True
    assert res["filename"] == "SpecSheet_2026.pdf"
    assert res["mime_type"] == "application/pdf"
    assert res["file_size"] == len(pdf_content)
    assert res["web_view_link"].startswith("/api/catalogues/download/")

def test_irrelevant_email_exclusion_fast_classifier():
    # Instagram / Social OTP
    res, reason = classify_email(
        "security@instagram.com", "instagram.com",
        "891 024 is your Instagram code", "Enter your code to verify your account"
    )
    assert res == "irrelevant"

    # Google Security Notification
    res, reason = classify_email(
        "no-reply@accounts.google.com", "accounts.google.com",
        "Security alert: New device sign-in", "Someone signed in to exportdtp@gmail.com on Chrome"
    )
    assert res == "irrelevant"

    # Newsletter with unsubscribe header
    res, reason = classify_email(
        "weekly@industryinsights.org", "industryinsights.org",
        "Top 10 Global Trends This Month", "To stop receiving these emails click unsubscribe",
        headers={"List-Unsubscribe": "<mailto:unsub@industryinsights.org>"}
    )
    assert res == "irrelevant"

    # Legitimate supplier quotation MUST be classified as relevant
    res, reason = classify_email(
        "export@hightech-bearing.cn", "hightech-bearing.cn",
        "Quotation: Deep Groove Ball Bearings (6204-2RS)",
        "Please check our quotation below: Unit price: $1.20 USD. MOQ: 1000 pcs. FOB Qingdao. Lead time: 10 days."
    )
    assert res == "relevant"
