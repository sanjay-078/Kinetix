import re
from typing import Any

from bs4 import BeautifulSoup

# Recognized standard specification field mapping keys
STANDARD_SPEC_KEYS = {
    "product": "name",
    "product name": "name",
    "item": "name",
    "title": "name",
    "description": "description",
    "category": "category",
    "brand": "brand",
    "manufacturer": "manufacturer",
    "model": "model",
    "model no": "model",
    "model number": "model",
    "part no": "sku",
    "part number": "sku",
    "sku": "sku",
    "series": "series",
    "variant": "variant",
    "quotation ref": "quotation_ref",
    "quote no": "quotation_ref",
    "quantity": "quantity",
    "qty": "quantity",
    "moq": "moq",
    "minimum order quantity": "moq",
    "unit": "unit",
    "unit price": "price",
    "price": "price",
    "fob price": "price",
    "total price": "total_price",
    "currency": "currency",
    "lead time": "lead_time",
    "production time": "lead_time",
    "dimensions": "dimensions",
    "weight": "weight",
    "material": "material",
    "capacity": "capacity",
    "voltage": "voltage",
    "current": "current",
    "power": "power",
    "speed": "speed_rpm",
    "rpm": "speed_rpm",
    "pressure": "pressure",
    "ip rating": "ip_rating",
    "certifications": "certifications",
    "country of origin": "country_of_origin",
    "origin": "country_of_origin",
    "hs code": "hs_code",
    "warranty": "warranty",
    "incoterms": "incoterms",
    "payment terms": "payment_terms",
    "shipping terms": "shipping_terms",
    "quotation validity": "quotation_validity"
}

def extract_currency_and_amount(val_str: str) -> tuple[float | None, str | None]:
    if not val_str:
        return None, None

    currency = None
    if "$" in val_str or "USD" in val_str.upper():
        currency = "USD"
    elif "€" in val_str or "EUR" in val_str.upper():
        currency = "EUR"
    elif "£" in val_str or "GBP" in val_str.upper():
        currency = "GBP"
    elif "¥" in val_str or "CNY" in val_str.upper() or "RMB" in val_str.upper():
        currency = "RMB"
    elif "₹" in val_str or "INR" in val_str.upper():
        currency = "INR"

    match = re.search(r"[\d,]+(\.\d+)?", val_str)
    if match:
        try:
            num = float(match.group(0).replace(",", ""))
            return num, currency
        except ValueError:
            pass
    return None, currency


def parse_html_tables(body_html: str) -> list[dict[str, Any]]:
    products = []
    if not body_html:
        return products

    soup = BeautifulSoup(body_html, "lxml")
    tables = soup.find_all("table")

    for table in tables:
        rows = table.find_all("tr")
        if len(rows) < 2:
            continue

        # Extract headers
        headers = []
        header_row = rows[0]
        cols = header_row.find_all(["th", "td"])
        for col in cols:
            headers.append(col.get_text(strip=True).lower())

        # Check if table headers look like product data
        if not any(k in " ".join(headers) for k in ["product", "item", "model", "price", "sku", "qty", "description"]):
            continue

        # Process data rows
        for row in rows[1:]:
            cells = row.find_all(["td", "th"])
            if len(cells) < len(headers):
                continue

            product_dict: dict[str, Any] = {
                "name": None,
                "model": None,
                "sku": None,
                "price": None,
                "currency": None,
                "quantity": None,
                "moq": None,
                "lead_time": None,
                "description": None,
                "dynamic_attributes": []
            }

            # Sort keys by length descending to match longer specific keys (e.g. 'unit price') before short keys (e.g. 'unit')
            sorted_spec_keys = sorted(STANDARD_SPEC_KEYS.items(), key=lambda x: len(x[0]), reverse=True)

            for idx, header_text in enumerate(headers):
                cell_val = cells[idx].get_text(strip=True)
                if not cell_val:
                    continue

                mapped = False
                for std_key, field_name in sorted_spec_keys:
                    if std_key in header_text:
                        if field_name == "price":
                            amount, curr = extract_currency_and_amount(cell_val)
                            product_dict["price"] = amount
                            if curr:
                                product_dict["currency"] = curr
                        elif field_name == "quantity":
                            amount, _ = extract_currency_and_amount(cell_val)
                            product_dict["quantity"] = amount
                        else:
                            product_dict[field_name] = cell_val
                        mapped = True
                        break

                if not mapped:
                    product_dict["dynamic_attributes"].append({
                        "attribute_name": header_text.title(),
                        "attribute_value": cell_val,
                        "unit": None
                    })

            # If product has at least name or model or price or SKU
            if product_dict["name"] or product_dict["model"] or product_dict["sku"] or product_dict["price"]:
                if not product_dict["name"]:
                    product_dict["name"] = product_dict["model"] or product_dict["sku"] or "Extracted Product"
                products.append(product_dict)

    return products


def parse_key_value_pairs(body_text: str) -> dict[str, Any]:
    """
    Parses key-value formatted text lines (e.g., 'Model: ABC-100', 'Price: $50.00').
    """
    data: dict[str, Any] = {
        "name": None,
        "model": None,
        "sku": None,
        "price": None,
        "currency": None,
        "quantity": None,
        "moq": None,
        "lead_time": None,
        "payment_terms": None,
        "incoterms": None,
        "warranty": None,
        "dynamic_attributes": []
    }

    lines = (body_text or "").splitlines()
    for line in lines:
        if ":" in line:
            parts = line.split(":", 1)
            key = parts[0].strip().lower()
            val = parts[1].strip()

            if not val:
                continue

            mapped = False
            for std_key, field_name in STANDARD_SPEC_KEYS.items():
                if key == std_key or std_key in key:
                    if field_name == "price":
                        amt, curr = extract_currency_and_amount(val)
                        data["price"] = amt
                        if curr:
                            data["currency"] = curr
                    elif field_name == "quantity":
                        amt, _ = extract_currency_and_amount(val)
                        data["quantity"] = amt
                    else:
                        data[field_name] = val
                    mapped = True
                    break

            if not mapped and len(key) < 40 and len(val) < 200:
                data["dynamic_attributes"].append({
                    "attribute_name": key.title(),
                    "attribute_value": val,
                    "unit": None
                })

    return data


def extract_products_from_email(body_text: str, body_html: str = "") -> list[dict[str, Any]]:
    """
    Complete product extraction from email body.
    Extracts multi-products from HTML tables or key-value structures.
    """
    products = []

    # Strategy 1: HTML tables
    if body_html:
        products = parse_html_tables(body_html)

    # Strategy 2: Key-value parsing if no tables found or single product email
    if not products and body_text:
        kv_product = parse_key_value_pairs(body_text)
        if kv_product["name"] or kv_product["model"] or kv_product["sku"] or kv_product["price"] or kv_product["dynamic_attributes"]:
            if not kv_product["name"]:
                kv_product["name"] = kv_product["model"] or kv_product["sku"] or "Extracted Product"
            products.append(kv_product)

    # Strategy 3: Fallback regex search for quotation/price patterns if still empty
    if not products and body_text:
        price_match = re.search(r"(\$|€|£|¥|USD|EUR)\s?([\d,]+(\.\d{2})?)", body_text)
        model_match = re.search(r"\b(Model|Item|SKU|Part\s*#?)\s*[:=]?\s*([A-Za-z0-9\-_]+)", body_text, re.IGNORECASE)

        if price_match or model_match:
            price_val, currency_val = extract_currency_and_amount(price_match.group(0)) if price_match else (None, None)
            model_val = model_match.group(2) if model_match else None

            products.append({
                "name": model_val or "Supplier Quoted Item",
                "model": model_val,
                "sku": None,
                "price": price_val,
                "currency": currency_val,
                "quantity": None,
                "moq": None,
                "lead_time": None,
                "dynamic_attributes": []
            })

    return products
