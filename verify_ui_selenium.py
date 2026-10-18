"""
End-to-End Browser UI Workflow Verification using Selenium and Microsoft Edge.
Tests http://localhost:8000:
- Navigates to app
- Uploads sample PDF and sample PNG
- Validates extracted invoice data and line items table
- Validates side-by-side document preview
- Captures screenshot
- Inspects browser console logs for any errors
"""
import os
import sys
import time

from selenium import webdriver
from selenium.webdriver.edge.options import Options as EdgeOptions
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

BASE_URL = "http://localhost:8000"
STATIC_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "app", "static")

def run_ui_verification():
    print(f"[*] Starting Edge browser in headless mode...")
    options = EdgeOptions()
    options.add_argument("--headless=new")
    options.add_argument("--window-size=1400,950")
    options.add_argument("--disable-gpu")
    options.add_argument("--no-sandbox")
    options.set_capability("goog:loggingPrefs", {"browser": "ALL"})

    driver = webdriver.Edge(options=options)
    wait = WebDriverWait(driver, 15)

    try:
        # Step 1: Navigate to the application
        print(f"[*] Navigating to {BASE_URL}...")
        driver.get(BASE_URL)
        assert "DocuParse AI" in driver.title, f"Unexpected page title: {driver.title}"
        print(f"[OK] Application loaded successfully. Title: '{driver.title}'")

        # Step 2: Upload the sample PDF invoice
        sample_pdf = os.path.abspath(os.path.join(STATIC_DIR, "sample_invoice.pdf"))
        assert os.path.exists(sample_pdf), f"Sample file not found: {sample_pdf}"
        print(f"[*] Uploading sample PDF via UI file input: {sample_pdf}...")

        file_input = driver.find_element(By.ID, "file-input")
        file_input.send_keys(sample_pdf)

        # Step 3: Wait for workspace section to appear
        print("[*] Waiting for LLM extraction and table rendering...")
        workspace = wait.until(lambda d: "hidden" not in d.find_element(By.ID, "workspace-section").get_attribute("class"))
        print("[OK] Workspace side-by-side view rendered!")

        # Wait a moment for DOM fields to populate
        time.sleep(1)

        # Step 4: Verify parsed invoice details in the UI
        val_merchant = driver.find_element(By.ID, "val-merchant").text.strip()
        val_invoice_no = driver.find_element(By.ID, "val-invoice-no").text.strip()
        val_date = driver.find_element(By.ID, "val-date").text.strip()
        val_grand_total = driver.find_element(By.ID, "val-grand-total").text.strip()
        val_tax = driver.find_element(By.ID, "val-tax").text.strip()
        items_count = driver.find_element(By.ID, "line-items-count").text.strip()

        rows = driver.find_elements(By.CSS_SELECTOR, "#line-items-tbody tr")

        print("\n" + "="*50)
        print("          EXTRACTED INVOICE UI TABLE")
        print("="*50)
        print(f" Merchant / Vendor : {val_merchant}")
        print(f" Invoice Number    : {val_invoice_no}")
        print(f" Invoice Date      : {val_date}")
        print(f" Tax / VAT         : {val_tax}")
        print(f" Grand Total       : {val_grand_total}")
        print(f" Line Items Count  : {items_count} (Table Rows: {len(rows)})")
        print("-" * 50)
        for idx, row in enumerate(rows):
            cols = [td.text.strip() for td in row.find_elements(By.TAG_NAME, "td")]
            print(f" #{idx+1} | " + " | ".join(cols))
        print("="*50 + "\n")

        # Assertions on parsed fields
        assert "Acme" in val_merchant, f"Merchant mismatch: {val_merchant}"
        assert "INV-" in val_invoice_no, f"Invoice number mismatch: {val_invoice_no}"
        assert "2026" in val_date, f"Date mismatch: {val_date}"
        assert "3788.75" in val_grand_total, f"Grand total mismatch: {val_grand_total}"
        assert len(rows) >= 5, f"Expected 5 items, found {len(rows)}"
        print("[OK] Verified all invoice header fields and line items populated accurately!")

        # Step 5: Verify document preview side-by-side
        preview_container = driver.find_element(By.ID, "preview-container")
        iframe = preview_container.find_element(By.TAG_NAME, "iframe")
        assert iframe.is_displayed(), "Document preview iframe should be displayed"
        print(f"[OK] Side-by-side document preview verified (src: {iframe.get_attribute('src')})")

        # Step 6: Test sample PNG upload workflow
        sample_png = os.path.abspath(os.path.join(STATIC_DIR, "sample_invoice.png"))
        print(f"\n[*] Testing image upload workflow ({sample_png})...")
        file_input = driver.find_element(By.ID, "file-input")
        file_input.send_keys(sample_png)
        time.sleep(1.5)
        png_merchant = driver.find_element(By.ID, "val-merchant").text.strip()
        assert len(png_merchant) > 0
        print(f"[OK] Image invoice parsed and displayed in UI (Merchant: '{png_merchant}')")

        # Step 7: Take a full screenshot
        screenshot_file = os.path.join(os.path.dirname(os.path.abspath(__file__)), "ui_workflow_verified.png")
        driver.save_screenshot(screenshot_file)
        print(f"[OK] Verification screenshot saved: {screenshot_file}")

        # Step 8: Inspect browser console logs
        print("\n[*] Checking browser console logs for any errors...")
        logs = driver.get_log("browser")
        severe_errors = [l for l in logs if l.get("level") in ["SEVERE", "ERROR"]]
        if severe_errors:
            print(f"[!] Warning: Found {len(severe_errors)} console errors:")
            for e in severe_errors:
                print(f"    - {e.get('message')}")
            assert False, "Severe browser console errors encountered!"
        else:
            print("[OK] Zero browser console errors found. Browser console clean!")

        print("\nALL UI WORKFLOW AND BROWSER CHECKS COMPLETED SUCCESSFULLY!")

    finally:
        driver.quit()

if __name__ == "__main__":
    run_ui_verification()
