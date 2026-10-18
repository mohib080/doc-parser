"""
Integration and API tests for the parsing endpoint, SQLite database persistence, and CSV export.
Covers both Invoices and Dynamic Tables (Stock Audit Sheets).
"""
import os
import io
import pytest
from fastapi.testclient import TestClient
from PIL import Image

from app.main import app
from app.database import Base, engine, SessionLocal
from app.models import Document, LineItem

client = TestClient(app)


@pytest.fixture(autouse=True)
def setup_and_teardown(monkeypatch):
    Base.metadata.create_all(bind=engine)
    monkeypatch.setenv("GEMINI_API_KEY", "")
    yield


def create_dummy_png_bytes():
    img = Image.new("RGB", (300, 300), color=(255, 255, 255))
    buf = io.BytesIO()
    img.save(buf, format="PNG")
    return buf.getvalue()


def test_root_serves_html():
    response = client.get("/")
    assert response.status_code == 200
    assert "DocuParse AI" in response.text


def test_parse_endpoint_with_sample_invoice_pdf():
    sample_pdf_path = os.path.join(os.path.dirname(__file__), "..", "app", "static", "sample_invoice.pdf")
    assert os.path.exists(sample_pdf_path), "Sample PDF should exist"

    with open(sample_pdf_path, "rb") as f:
        file_bytes = f.read()

    response = client.post(
        "/api/parse",
        files={"file": ("sample_invoice.pdf", file_bytes, "application/pdf")}
    )

    assert response.status_code == 201, f"Failed: {response.text}"
    data = response.json()
    assert data["success"] is True
    assert "document" in data
    doc = data["document"]
    assert doc["id"] is not None
    assert doc["filename"] == "sample_invoice.pdf"
    assert doc["doc_type"] == "invoice"
    assert len(doc["columns"]) > 0
    assert len(doc["rows"]) > 0
    assert len(doc["line_items"]) > 0

    # Verify directly in SQLite database
    db = SessionLocal()
    try:
        db_doc = db.query(Document).filter(Document.id == doc["id"]).first()
        assert db_doc is not None
        assert db_doc.filename == "sample_invoice.pdf"
        assert len(db_doc.line_items) == len(doc["line_items"])

        for item in db_doc.line_items:
            assert item.document_id == db_doc.id
            assert item.description
            assert item.total_price >= 0
    finally:
        db.close()


def test_parse_endpoint_with_stock_audit_pdf():
    audit_pdf_path = os.path.join(os.path.dirname(__file__), "..", "app", "static", "sample_stock_audit.pdf")
    assert os.path.exists(audit_pdf_path), "Stock audit PDF should exist"

    with open(audit_pdf_path, "rb") as f:
        file_bytes = f.read()

    response = client.post(
        "/api/parse",
        files={"file": ("sample_stock_audit.pdf", file_bytes, "application/pdf")}
    )

    assert response.status_code == 201, f"Failed: {response.text}"
    data = response.json()
    assert data["success"] is True
    doc = data["document"]
    assert doc["doc_type"] == "stock_audit"
    assert any("code" in c.lower() for c in doc["columns"])
    assert any("bin" in c.lower() for c in doc["columns"])
    assert any("count" in c.lower() for c in doc["columns"])
    assert len(doc["rows"]) >= 5

    # Test dynamic CSV export matching stock audit columns
    csv_resp = client.get(f"/api/documents/{doc['id']}/export-csv")
    assert csv_resp.status_code == 200
    assert "text/csv" in csv_resp.headers["content-type"]
    csv_text = csv_resp.text
    assert "stock_audit" in csv_text
    assert "W-104" in csv_text
    assert "Hydraulic Flange Seal" in csv_text


def test_parse_endpoint_with_image():
    png_bytes = create_dummy_png_bytes()
    response = client.post(
        "/api/parse",
        files={"file": ("receipt_scan.png", png_bytes, "image/png")}
    )
    assert response.status_code == 201
    data = response.json()
    assert data["success"] is True
    assert data["document"]["filename"] == "receipt_scan.png"


def test_parse_invalid_file_extension():
    response = client.post(
        "/api/parse",
        files={"file": ("malicious_script.exe", b"binary content", "application/octet-stream")}
    )
    assert response.status_code == 400
    assert "Unsupported file type" in response.json()["detail"]


def test_parse_empty_file():
    response = client.post(
        "/api/parse",
        files={"file": ("empty.pdf", b"", "application/pdf")}
    )
    assert response.status_code == 400
    assert "empty" in response.json()["detail"].lower()


def test_get_documents_and_detail():
    response = client.get("/api/documents")
    assert response.status_code == 200
    docs = response.json()
    assert isinstance(docs, list)
    assert len(docs) > 0

    doc_id = docs[0]["id"]
    detail_resp = client.get(f"/api/documents/{doc_id}")
    assert detail_resp.status_code == 200
    assert detail_resp.json()["id"] == doc_id


def test_export_csv():
    list_resp = client.get("/api/documents")
    docs = list_resp.json()
    assert len(docs) > 0
    doc_id = docs[0]["id"]

    response = client.get(f"/api/documents/{doc_id}/export-csv")
    assert response.status_code == 200
    assert "text/csv" in response.headers["content-type"]
    csv_content = response.text
    assert "Document ID" in csv_content


def test_delete_document():
    png_bytes = create_dummy_png_bytes()
    upload_resp = client.post(
        "/api/parse",
        files={"file": ("to_delete.png", png_bytes, "image/png")}
    )
    assert upload_resp.status_code == 201, f"Failed: {upload_resp.text}"
    doc_id = upload_resp.json()["document"]["id"]

    delete_resp = client.delete(f"/api/documents/{doc_id}")
    assert delete_resp.status_code == 200

    get_resp = client.get(f"/api/documents/{doc_id}")
    assert get_resp.status_code == 404


def test_parse_handwritten_user_image(monkeypatch):
    """Verify live Gemini Vision extracts 12 rows (B101 M6 bolts through P901 Paint brushes)."""
    user_img_path = os.path.join(os.path.dirname(__file__), "..", "app", "uploads", "58f833abda8a4121b2560080d04f206b_handwritten exce.jpg")
    if not os.path.exists(user_img_path):
        pytest.skip("User image not found")

    from dotenv import dotenv_values
    env_vals = dotenv_values()
    real_key = env_vals.get("GEMINI_API_KEY") or os.getenv("GEMINI_API_KEY")
    if not real_key:
        pytest.skip("No GEMINI_API_KEY found for live vision test")
    monkeypatch.setenv("GEMINI_API_KEY", real_key)

    with open(user_img_path, "rb") as f:
        file_bytes = f.read()

    response = client.post(
        "/api/parse",
        files={"file": ("handwritten exce.jpg", file_bytes, "image/jpeg")}
    )
    if response.status_code == 500 and "RESOURCE_EXHAUSTED" in response.text:
        pytest.skip("Gemini free tier quota limit reached (429 RESOURCE_EXHAUSTED)")

    assert response.status_code == 201, f"Failed: {response.text}"
    data = response.json()
    doc = data["document"]
    rows = doc.get("rows", [])
    assert len(rows) == 12, f"Expected 12 rows, got {len(rows)}"

    first_row_text = " ".join(str(v) for v in rows[0].values())
    last_row_text = " ".join(str(v) for v in rows[-1].values())

    assert "B101" in first_row_text
    assert "M6 bolts" in first_row_text
    assert "P901" in last_row_text
    assert "Paint brushes" in last_row_text
