"""
Integration and API tests for the parsing endpoint, SQLite database persistence, and CSV export.
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
def setup_and_teardown():
    # Setup test DB tables
    Base.metadata.create_all(bind=engine)
    yield
    # We can keep or cleanup if needed


def create_dummy_png_bytes():
    img = Image.new("RGB", (300, 300), color=(255, 255, 255))
    buf = io.BytesIO()
    img.save(buf, format="PNG")
    return buf.getvalue()


def test_root_serves_html():
    response = client.get("/")
    assert response.status_code == 200
    assert "DocuParse AI" in response.text


def test_parse_endpoint_with_sample_pdf():
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
    assert len(doc["line_items"]) > 0

    # Verify directly in SQLite database
    db = SessionLocal()
    try:
        db_doc = db.query(Document).filter(Document.id == doc["id"]).first()
        assert db_doc is not None
        assert db_doc.filename == "sample_invoice.pdf"
        assert len(db_doc.line_items) == len(doc["line_items"])

        # Check line item foreign key
        for item in db_doc.line_items:
            assert item.document_id == db_doc.id
            assert item.description
            assert item.total_price >= 0
    finally:
        db.close()


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
    # Fetch all documents
    response = client.get("/api/documents")
    assert response.status_code == 200
    docs = response.json()
    assert isinstance(docs, list)
    assert len(docs) > 0

    doc_id = docs[0]["id"]
    # Fetch single document
    detail_resp = client.get(f"/api/documents/{doc_id}")
    assert detail_resp.status_code == 200
    assert detail_resp.json()["id"] == doc_id


def test_export_csv():
    # First ensure at least one document exists
    list_resp = client.get("/api/documents")
    docs = list_resp.json()
    assert len(docs) > 0
    doc_id = docs[0]["id"]

    response = client.get(f"/api/documents/{doc_id}/export-csv")
    assert response.status_code == 200
    assert "text/csv" in response.headers["content-type"]
    csv_content = response.text
    assert "Document ID" in csv_content
    assert "Item ID,Description,Quantity,Unit Price,Total Price" in csv_content


def test_delete_document():
    # Create a quick document to delete
    png_bytes = create_dummy_png_bytes()
    upload_resp = client.post(
        "/api/parse",
        files={"file": ("to_delete.png", png_bytes, "image/png")}
    )
    doc_id = upload_resp.json()["document"]["id"]

    delete_resp = client.delete(f"/api/documents/{doc_id}")
    assert delete_resp.status_code == 200

    # Ensure it no longer exists
    get_resp = client.get(f"/api/documents/{doc_id}")
    assert get_resp.status_code == 404
