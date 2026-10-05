import pytest
from app.services.classifier import classify_email, cache_domain_rule

def test_classify_otp_and_security_emails():
    # OTP Subject
    cls, reason = classify_email("no-reply@instagram.com", "instagram.com", "123456 is your Instagram code", "Verification code")
    assert cls == "irrelevant"
    assert "instagram" in reason.lower() or "irrelevant" in reason.lower()

    # Google Security Alert
    cls, reason = classify_email("security@account.google.com", "accounts.google.com", "Security alert for your account", "A new sign-in attempt was detected.")
    assert cls == "irrelevant"

def test_classify_newsletter_and_marketing():
    cls, reason = classify_email("promo@marketing.com", "marketing.com", "Weekly Deals Newsletter", "Click here to unsubscribe")
    assert cls == "irrelevant"

def test_classify_relevant_supplier_quotation():
    cls, reason = classify_email(
        "sales@shenzhen-tech.com", "shenzhen-tech.com",
        "Official Quotation: High Precision Step Motors",
        "Unit price: $14.50 USD. MOQ: 100 pcs. Lead time: 15 days."
    )
    assert cls == "relevant"

def test_classify_uncertain_email_fallback():
    # Uncertain email should NOT be discarded as irrelevant
    cls, reason = classify_email("john@generic.com", "generic.com", "Meeting follow up", "Let's catch up tomorrow.")
    assert cls == "uncertain"
