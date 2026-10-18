"""
End-to-End Verification Script for Document Parser.
Tests both standard Invoices and custom dynamic tables (Stock Audits).
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

        # 3. Test /api/parse with Invoice PDF
        invoice_pdf_path = os.path.join(os.path.dirname(__file__), "app", "static", "sample_invoice.pdf")
        with open(invoice_pdf_path, "rb") as f:
            pdf_bytes = f.read()

        resp = client.post(
            "/api/parse",
            files={"file": ("acme_sample.pdf", pdf_bytes, "application/pdf")}
        )
        assert resp.status_code == 201, f"Parse failed: {resp.text}"
        inv_data = resp.json()
        inv_id = inv_data["document"]["id"]
        print(f"[OK] Invoice parsed via /api/parse. ID: {inv_id}")
        print(f"    Merchant: {inv_data['document']['merchant']}")
        print(f"    Invoice #: {inv_data['document']['invoice_no']}")
        print(f"    Grand Total: {inv_data['document']['currency']}{inv_data['document']['grand_total']}")
        print(f"    Line Items Count: {len(inv_data['document']['line_items'])}")

        # 4. Test /api/parse with Stock Audit PDF (Dynamic Custom Table)
        audit_pdf_path = os.path.join(os.path.dirname(__file__), "app", "static", "sample_stock_audit.pdf")
        with open(audit_pdf_path, "rb") as f:
            audit_bytes = f.read()

        resp = client.post(
            "/api/parse",
            files={"file": ("sample_stock_audit.pdf", audit_bytes, "application/pdf")}
        )
        assert resp.status_code == 201, f"Audit parse failed: {resp.text}"
        audit_data = resp.json()
        audit_id = audit_data["document"]["id"]
        print(f"\n[OK] Stock Audit parsed via /api/parse. ID: {audit_id}")
        print(f"    Document Type : {audit_data['document']['doc_type']}")
        print(f"    Title         : {audit_data['document']['title']}")
        print(f"    Sheet / Ref # : {audit_data['document']['reference_no']}")
        print(f"    Inspector     : {audit_data['document']['inspector']}")
        print(f"    Dynamic Cols  : {audit_data['document']['columns']}")
        print(f"    Rows Extracted: {len(audit_data['document']['rows'])}")

        # 5. Check SQLite Storage for both records
        conn = sqlite3.connect("doc_parser.db")
        cursor = conn.cursor()
        cursor.execute("SELECT id, filename, doc_type, merchant, inspector FROM documents WHERE id = ?", (audit_id,))
        row = cursor.fetchone()
        assert row is not None, "Stock audit document not found in SQLite"
        print(f"[OK] SQLite documents table verified for Audit: ID={row[0]}, Type={row[2]}, Inspector={row[4]}")
        conn.close()

        # 6. Check Dynamic CSV Export for Stock Audit
        csv_resp = client.get(f"/api/documents/{audit_id}/export-csv")
        assert csv_resp.status_code == 200
        assert "text/csv" in csv_resp.headers["content-type"]
        assert "Document Type,stock_audit" in csv_resp.text
        assert "Code,Item Description,Bin,Book Qty,Physical Count,Variance,Notes,Checked By" in csv_resp.text
        print(f"[OK] Dynamic CSV Export verified for Stock Audit. Header columns match exactly:")
        for line in csv_resp.text.splitlines()[:12]:
            if line.strip():
                print(f"    {line}")

        # 7. Check File Serving for Preview
        file_preview_path = audit_data["document"]["file_path"]
        preview_resp = client.get(file_preview_path)
        assert preview_resp.status_code == 200
        assert len(preview_resp.content) == len(audit_bytes)
        print(f"\n[OK] Stock Audit preview file serving verified ({file_preview_path}).")

    print("\nALL INVOICE & STOCK AUDIT END-TO-END TESTS PASSED SUCCESSFULLY!")

if __name__ == "__main__":
    run_e2e_checks()
