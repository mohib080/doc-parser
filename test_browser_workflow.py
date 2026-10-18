"""
Automated Browser UI Workflow Test using Playwright.
Navigates to http://127.0.0.1:8000, performs upload, verifies populated data table and side-by-side preview,
and monitors browser console logs for any errors.
"""
import os
import sys
import time
from playwright.sync_api import sync_playwright

BASE_URL = "http://127.0.0.1:8000"
STATIC_DIR = os.path.join(os.path.dirname(__file__), "app", "static")

def run_browser_verification():
    print(f"[*] Launching browser verification against {BASE_URL}...")
    console_errors = []
    console_messages = []

    with sync_playwright() as p:
        # Launch browser (uses installed chromium or msedge)
        browser = None
        try:
            browser = p.chromium.launch(headless=True)
        except Exception:
            # Fallback to system installed Edge if chromium driver isn't downloaded yet
            browser = p.chromium.launch(headless=True, channel="msedge")

        context = browser.new_context(viewport={"width": 1400, "height": 900})
        page = context.new_page()

        # Listen to console messages and page errors
        page.on("console", lambda msg: (
            console_errors.append(f"[{msg.type.upper()}] {msg.text}")
            if msg.type in ["error"] else console_messages.append(f"[{msg.type}] {msg.text}")
        ))
        page.on("pageerror", lambda err: console_errors.append(f"[UNHANDLED EXCEPTION] {err}"))

        # 1. Navigate to page
        print(f"[*] Navigating to {BASE_URL}...")
        page.goto(BASE_URL, wait_until="networkidle")
        assert "DocuParse AI" in page.title(), f"Unexpected title: {page.title()}"
        print("[OK] Page loaded successfully. Title: " + page.title())

        # 2. Test 1: Upload sample PDF file via file input
        sample_pdf_path = os.path.join(STATIC_DIR, "sample_invoice.pdf")
        assert os.path.exists(sample_pdf_path), "sample_invoice.pdf missing"

        print(f"[*] Uploading sample PDF ({sample_pdf_path})...")
        file_input = page.locator("#file-input")
        file_input.set_input_files(sample_pdf_path)

        # Wait for workspace section to be displayed
        page.wait_for_selector("#workspace-section:not(.hidden)", timeout=15000)
        print("[OK] Workspace side-by-side section visible!")

        # 3. Verify populated invoice fields in the UI
        vendor_text = page.locator("#val-merchant").inner_text().strip()
        inv_no_text = page.locator("#val-invoice-no").inner_text().strip()
        date_text = page.locator("#val-date").inner_text().strip()
        grand_total_text = page.locator("#val-grand-total").inner_text().strip()
        line_items_count_text = page.locator("#line-items-count").inner_text().strip()
        rows = page.locator("#line-items-tbody tr")
        row_count = rows.count()

        print("\n--- EXTRACTED UI DATA TABLE ---")
        print(f"Vendor / Merchant : {vendor_text}")
        print(f"Invoice Number    : {inv_no_text}")
        print(f"Invoice Date      : {date_text}")
        print(f"Grand Total       : {grand_total_text}")
        print(f"Line Items Count  : {line_items_count_text} (Table Rows: {row_count})")
        for i in range(row_count):
            row_text = " | ".join(rows.nth(i).locator("td").all_inner_texts())
            print(f"  Row {i+1}: {row_text}")
        print("-------------------------------\n")

        # Assertions on parsed fields
        assert "Acme" in vendor_text, f"Vendor mismatch: {vendor_text}"
        assert "INV-" in inv_no_text, f"Invoice number mismatch: {inv_no_text}"
        assert "2026" in date_text, f"Date mismatch: {date_text}"
        assert "3788.75" in grand_total_text, f"Grand total mismatch: {grand_total_text}"
        assert row_count >= 1, f"Expected table rows, got {row_count}"
        print("[OK] Parsed invoice details verified successfully in UI data table.")

        # 4. Verify preview container
        preview_container = page.locator("#preview-container")
        assert preview_container.is_visible()
        print("[OK] Document preview container verified.")

        # 5. Take screenshot of the UI
        screenshot_path = os.path.join(os.path.dirname(__file__), "ui_verification_screenshot.png")
        page.screenshot(path=screenshot_path, full_page=True)
        print(f"[OK] Full UI screenshot saved: {screenshot_path}")

        # 6. Check console errors
        print("\n[*] Checking browser console logs...")
        if console_errors:
            print(f"[!] Warning: {len(console_errors)} console errors detected:")
            for err in console_errors:
                print(f"    {err}")
            # Raise assertion if critical JavaScript errors
            assert not any("UNHANDLED" in e for e in console_errors), "Unhandled JS exception occurred!"
        else:
            print("[OK] Zero browser console errors. Clean browser runtime!")

        browser.close()
        print("\nALL BROWSER WORKFLOW CHECKS PASSED CLEANLY!")

if __name__ == "__main__":
    run_browser_verification()
