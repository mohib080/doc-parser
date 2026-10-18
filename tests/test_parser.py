"""
Unit tests for invoice parsing schemas and heuristic/LLM extraction.
"""
import pytest
from app.schemas import InvoiceData, LineItemSchema
from app.parser import heuristic_invoice_parser, DocumentParser


def test_line_item_schema():
    item = LineItemSchema(
        description="Cloud Computing Server",
        quantity=2.0,
        unit_price=50.0,
        total_price=100.0
    )
    assert item.description == "Cloud Computing Server"
    assert item.quantity == 2.0
    assert item.unit_price == 50.0
    assert item.total_price == 100.0


def test_invoice_data_schema():
    data = InvoiceData(
        merchant="Acme Corp",
        date="2026-10-18",
        invoice_no="INV-9999",
        line_items=[
            LineItemSchema(
                description="Consulting",
                quantity=5.0,
                unit_price=100.0,
                total_price=500.0
            )
        ],
        grand_total=500.0,
        currency="$",
        tax=45.0
    )
    assert data.merchant == "Acme Corp"
    assert len(data.line_items) == 1
    assert data.grand_total == 500.0
    assert data.tax == 45.0


def test_heuristic_parser_with_sample_text():
    sample_text = """
    Nexus Digital Technologies Ltd
    123 Tech Boulevard, Innovation City
    Invoice #: INV-2026-4412
    Date: 2026-10-15
    Due Date: 2026-11-15

    DESCRIPTION QTY UNIT PRICE TOTAL
    Frontend Architecture Review 10 150.00 1500.00
    Backend API Integration 15 120.00 1800.00
    Database Optimization 5 200.00 1000.00

    Subtotal: $4300.00
    Tax: $344.00
    Grand Total: $4644.00
    """
    parsed = heuristic_invoice_parser(sample_text)
    assert "Nexus Digital Technologies" in parsed.merchant
    assert parsed.invoice_no == "INV-2026-4412"
    assert parsed.date == "2026-10-15"
    assert parsed.grand_total == 4644.0
    assert parsed.tax == 344.0
    assert len(parsed.line_items) >= 1


def test_parser_fallback_on_unstructured():
    unstructured_text = "Some random text without clear table"
    parsed = heuristic_invoice_parser(unstructured_text, filename="receipt_test.pdf")
    assert parsed.merchant is not None
    assert len(parsed.line_items) >= 1
    assert parsed.grand_total > 0
