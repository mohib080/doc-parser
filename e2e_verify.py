"""
End-to-End Verification Script for Document Parser
"""
import os
import sys
import time
import httpx
import sqlite3

BASE_URL = "http://127.0.0.1:8000"

def run_e2e_checks():
    print(f"[*] Checking connection to {BASE_URL}...")
    with httpx.Client(base_url=BASE_URL, timeout=10) as client:
        # 1. Check frontend
        resp = client.get("/")
        assert resp.status_code == 200, f"Frontend failed with {resp.status_code}"
        assert "DocuParse AI" in resp.text
        print("[OK] Frontend HTML served successfully.")

        # 2. Check Static Assets
        resp = client.get("/static/app.js")
        assert resp.status_code == 200
        print("[OK] Frontend app.js loaded successfully.")

        # 3. Test /api/parse with PDF
        pdf_path = os.path.join(os.path.dirname(__file__), "app", "static", "sample_invoice.pdf")
        with open(pdf_path, "rb") as f:
            pdf_bytes = f.read()

        resp = client.post(
            "/api/parse",
            files={"file": ("acme_sample.pdf", pdf_bytes, "application/pdf")}
        )
        assert resp.status_code == 201, f"Parse failed: {resp.text}"
        data = resp.json()
        doc_id = data["document"]["id"]
        print(f"[OK] Document parsed via /api/parse. ID: {doc_id}")
        print(f"    Merchant: {data['document']['merchant']}")
        print(f"    Invoice #: {data['document']['invoice_no']}")
        print(f"    Grand Total: {data['document']['currency']}{data['document']['grand_total']}")
        print(f"    Line Items Count: {len(data['document']['line_items'])}")

        # 4. Check SQLite Storage
        conn = sqlite3.connect("doc_parser.db")
        cursor = conn.cursor()
        cursor.execute("SELECT id, filename, merchant, grand_total FROM documents WHERE id = ?", (doc_id,))
        row = cursor.fetchone()
        assert row is not None, "Document not found in SQLite"
        print(f"[OK] SQLite documents table verified: ID={row[0]}, File={row[1]}, Total={row[3]}")

        cursor.execute("SELECT id, description, quantity, total_price FROM line_items WHERE document_id = ?", (doc_id,))
        items = cursor.fetchall()
        assert len(items) > 0, "No line items found in SQLite"
        print(f"[OK] SQLite line_items table verified ({len(items)} items saved linked to document_id={doc_id}):")
        for item in items:
            print(f"      - Item #{item[0]}: {item[1]} (Qty: {item[2]}, Total: {item[3]})")
        conn.close()

        # 5. Check CSV Export
        csv_resp = client.get(f"/api/documents/{doc_id}/export-csv")
        assert csv_resp.status_code == 200
        assert "text/csv" in csv_resp.headers["content-type"]
        assert "Document ID" in csv_resp.text
        assert "Item ID,Description,Quantity,Unit Price,Total Price" in csv_resp.text
        print(f"[OK] CSV Export verified. Sample content:\n{csv_resp.text[:250]}...")

        # 6. Check File Serving for Preview
        file_preview_path = data["document"]["file_path"]
        preview_resp = client.get(file_preview_path)
        assert preview_resp.status_code == 200
        assert len(preview_resp.content) == len(pdf_bytes)
        print(f"[OK] Document preview file serving verified ({file_preview_path}).")

    print("\nALL END-TO-END TESTS PASSED SUCCESSFULLY!")

if __name__ == "__main__":
    run_e2e_checks()
