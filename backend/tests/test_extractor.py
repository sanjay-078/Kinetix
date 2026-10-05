import pytest
from app.services.extractor import extract_products_from_email, parse_html_tables, parse_key_value_pairs

def test_extract_html_table_multi_products():
    html = """
    <table border="1">
      <tr><th>Product Name</th><th>Model</th><th>Unit Price</th><th>MOQ</th></tr>
      <tr><td>Stepper Motor</td><td>ST-420</td><td>$14.50</td><td>100 pcs</td></tr>
      <tr><td>Servo Motor</td><td>SV-500</td><td>$85.00</td><td>20 pcs</td></tr>
    </table>
    """
    products = parse_html_tables(html)
    assert len(products) == 2
    assert products[0]["model"] == "ST-420"
    assert products[0]["price"] == 14.50
    assert products[0]["currency"] == "USD"
    assert products[1]["model"] == "SV-500"
    assert products[1]["price"] == 85.00

def test_extract_key_value_pairs_and_dynamic_attributes():
    text = """
    Model: NEMA-17
    Product: Micro Stepper Motor
    Price: $12.00
    MOQ: 50 pcs
    Holding Torque: 0.45 Nm
    Voltage: 24V
    GSM: 180
    """
    data = parse_key_value_pairs(text)
    assert data["model"] == "NEMA-17"
    assert data["price"] == 12.00
    
    dyn_names = [a["attribute_name"] for a in data["dynamic_attributes"]]
    assert "Holding Torque" in dyn_names
    assert "Voltage" in dyn_names or "Gsm" in dyn_names

def test_no_guessing_missing_values():
    text = "Model: XYZ-100\nPrice: $10.00"
    data = parse_key_value_pairs(text)
    assert data["model"] == "XYZ-100"
    assert data["lead_time"] is None
    assert data["incoterms"] is None
