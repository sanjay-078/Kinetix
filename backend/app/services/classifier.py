import re

# Cached domain and sender rules
DOMAIN_CACHE: dict[str, str] = {
    "instagram.com": "irrelevant",
    "facebookmail.com": "irrelevant",
    "linkedin.com": "irrelevant",
    "twitter.com": "irrelevant",
    "x.com": "irrelevant",
    "github.com": "irrelevant",
    "anthropic.com": "irrelevant",
    "accounts.google.com": "irrelevant",
    "google.com": "irrelevant",
    "no-reply@google.com": "irrelevant",
    "security-noreply@account.google.com": "irrelevant",
    "mail.instagram.com": "irrelevant",
}

SENDER_CACHE: dict[str, str] = {}

# Patterns indicating irrelevant emails (OTPs, Security, Social, Newsletters, Service alerts)
IRRELEVANT_PATTERNS = [
    r"\bOTP\b",
    r"\bverification code\b",
    r"\bsecurity code\b",
    r"\bconfirm your account\b",
    r"\blogin alert\b",
    r"\bpassword reset\b",
    r"\bsecurity alert\b",
    r"\b2-step verification\b",
    r"\b2FA\b",
    r"\bsign-in attempt\b",
    r"\bnewsletter\b",
    r"\bunsubscribe\b",
    r"\bview in browser\b",
    r"\bpromotional offer\b",
]

# Patterns indicating relevant supplier / product emails
RELEVANT_PATTERNS = [
    r"\bquotation\b",
    r"\bquote\b",
    r"\bproforma invoice\b",
    r"\bprice list\b",
    r"\bcatalogue\b",
    r"\bcatalog\b",
    r"\bspecification\b",
    r"\bdatasheet\b",
    r"\bMOQ\b",
    r"\bFOB\b",
    r"\bCIF\b",
    r"\bEXW\b",
    r"\bunit price\b",
    r"\blead time\b",
    r"\bproduct specification\b",
    r"\bpart number\b",
    r"\bSKU\b",
    r"\bmodel no\b",
    r"\bmodel number\b",
    r"\bRFQ\b",
    r"\brequest for quotation\b",
    r"\bsample cost\b",
    r"\bpayment terms\b"
]

def classify_email(sender: str, sender_domain: str, subject: str, body_text: str, headers: dict = None) -> tuple[str, str]:
    """
    Fast two-stage Python email classifier.
    Returns (classification, reason):
      classification: "relevant" | "irrelevant" | "uncertain"
      reason: string explaining classification
    """
    sender_lower = (sender or "").lower()
    domain_lower = (sender_domain or "").lower()
    subject_lower = (subject or "").lower()
    body_lower = (body_text or "").lower()[:2000]  # First 2000 chars for fast classification

    # Check sender cache
    if sender_lower in SENDER_CACHE:
        return SENDER_CACHE[sender_lower], "Cached sender classification"

    # Check domain cache
    if domain_lower in DOMAIN_CACHE:
        return DOMAIN_CACHE[domain_lower], f"Cached domain classification ({domain_lower})"

    # Check auto-generated headers
    if headers:
        if headers.get("List-Unsubscribe") or headers.get("Precedence") in ["bulk", "junk", "list"]:
            return "irrelevant", "Newsletter or mass mail header detected"

    # Stage 1: Check irrelevant patterns (Subject & Body)
    for pattern in IRRELEVANT_PATTERNS:
        if re.search(pattern, subject_lower, re.IGNORECASE):
            return "irrelevant", f"Subject matched irrelevant pattern '{pattern}'"
        if re.search(pattern, body_lower, re.IGNORECASE):
            return "irrelevant", f"Body matched irrelevant pattern '{pattern}'"

    # Stage 2: Check relevant product/supplier patterns
    relevant_matches = 0
    matched_patterns = []
    for pattern in RELEVANT_PATTERNS:
        if re.search(pattern, subject_lower, re.IGNORECASE):
            relevant_matches += 2
            matched_patterns.append(pattern)
        elif re.search(pattern, body_lower, re.IGNORECASE):
            relevant_matches += 1
            matched_patterns.append(pattern)

    if relevant_matches >= 2:
        return "relevant", f"Matched supplier keywords: {', '.join(matched_patterns[:3])}"

    # Check for price/currency indicators or table-like quotation structures in body
    if re.search(r"(\$|€|£|¥|USD|EUR|GBP|RMB|INR)\s?\d+(\.\d{2})?", body_lower) and re.search(r"\b(qty|quantity|pcs|pieces|units|price|model)\b", body_lower):
        return "relevant", "Detected pricing, quantities, and product keywords"

    # If uncertain, preserve email for deeper processing / human review rather than discarding
    return "uncertain", "Ambiguous email content; reserved for deeper extraction/review"


def cache_sender_rule(sender: str, classification: str):
    if sender:
        SENDER_CACHE[sender.lower()] = classification

def cache_domain_rule(domain: str, classification: str):
    if domain:
        DOMAIN_CACHE[domain.lower()] = classification
