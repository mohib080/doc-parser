"""
Generate sample documents for testing:
1. Standard Invoice (PDF + PNG)
2. Warehouse Stock Audit & Inventory Sheet with handwritten-style marks (PDF + PNG)
"""
import os
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas
from reportlab.lib import colors
from PIL import Image, ImageDraw, ImageFont

def generate_invoice_pdf(pdf_path: str):
    c = canvas.Canvas(pdf_path, pagesize=letter)
    width, height = letter # 612 x 792

    # Brand accent bar
    c.setFillColor(colors.HexColor("#4F46E5"))
    c.rect(0, height - 8, width, 8, fill=1, stroke=0)

    # Merchant details
    c.setFillColor(colors.HexColor("#111827"))
    c.setFont("Helvetica-Bold", 18)
    c.drawString(50, height - 45, "Acme Cloud Solutions Inc.")

    c.setFillColor(colors.HexColor("#6B7280"))
    c.setFont("Helvetica", 9)
    c.drawString(50, height - 62, "100 Innovation Way, Suite 400, San Francisco, CA 94105")
    c.drawString(50, height - 76, "billing@acmecloud.io | (555) 019-2834")

    # Invoice metadata
    c.setFillColor(colors.HexColor("#4F46E5"))
    c.setFont("Helvetica-Bold", 18)
    c.drawString(420, height - 45, "INVOICE")

    c.setFillColor(colors.HexColor("#1F2937"))
    c.setFont("Helvetica-Bold", 10)
    c.drawString(420, height - 65, "Invoice #: INV-2026-8941")

    c.setFillColor(colors.HexColor("#4B5563"))
    c.setFont("Helvetica", 9)
    c.drawString(420, height - 80, "Date: 2026-10-18")
    c.drawString(420, height - 94, "Due Date: 2026-11-18")

    # Divider
    c.setStrokeColor(colors.HexColor("#E5E7EB"))
    c.setLineWidth(1)
    c.line(50, height - 110, 562, height - 110)

    # Table Header
    table_top = height - 160
    c.setFillColor(colors.HexColor("#F3F4F6"))
    c.rect(50, table_top - 5, 512, 22, fill=1, stroke=0)

    c.setFillColor(colors.HexColor("#374151"))
    c.setFont("Helvetica-Bold", 9)
    c.drawString(60, table_top + 2, "DESCRIPTION")
    c.drawRightString(360, table_top + 2, "QUANTITY")
    c.drawRightString(460, table_top + 2, "UNIT PRICE")
    c.drawRightString(550, table_top + 2, "TOTAL")

    items = [
        ("Enterprise Kubernetes Cluster (Oct)", "1", "$1450.00", "$1450.00"),
        ("Dedicated GPU Inference Instance (A100)", "2", "$650.00", "$1300.00"),
        ("Object Storage Bucket (10TB Egress)", "1", "$180.00", "$180.00"),
        ("Managed PostgreSQL High Availability", "1", "$320.00", "$320.00"),
        ("24/7 Priority SLA Technical Support", "1", "$250.00", "$250.00"),
    ]

    curr_y = table_top - 25
    c.setFont("Helvetica", 9)
    for desc, qty, unit_p, tot_p in items:
        c.setFillColor(colors.HexColor("#1F2937"))
        c.drawString(60, curr_y, desc)
        c.drawRightString(360, curr_y, qty)
        c.drawRightString(460, curr_y, unit_p)
        c.drawRightString(550, curr_y, tot_p)

        c.setStrokeColor(colors.HexColor("#F3F4F6"))
        c.line(50, curr_y - 8, 562, curr_y - 8)
        curr_y -= 26

    # Totals
    curr_y -= 15
    c.setStrokeColor(colors.HexColor("#D1D5DB"))
    c.line(340, curr_y + 12, 562, curr_y + 12)

    c.setFillColor(colors.HexColor("#6B7280"))
    c.setFont("Helvetica", 9)
    c.drawString(350, curr_y, "Subtotal:")
    c.drawRightString(550, curr_y, "$3500.00")

    curr_y -= 18
    c.drawString(350, curr_y, "Estimated Tax (8.25%):")
    c.drawRightString(550, curr_y, "$288.75")

    curr_y -= 24
    c.setFillColor(colors.HexColor("#EEF2FF"))
    c.rect(340, curr_y - 6, 222, 26, fill=1, stroke=0)

    c.setFillColor(colors.HexColor("#4338CA"))
    c.setFont("Helvetica-Bold", 10)
    c.drawString(350, curr_y + 2, "GRAND TOTAL:")
    c.drawRightString(550, curr_y + 2, "$3788.75")

    c.save()
    print(f"[OK] Generated Invoice PDF: {pdf_path}")


def generate_stock_audit_pdf(pdf_path: str):
    """Generate Warehouse Stock Audit Sheet PDF with custom columns and handwritten style notes."""
    c = canvas.Canvas(pdf_path, pagesize=letter)
    width, height = letter # 612 x 792

    # Brand Header Bar (Emerald accent for Inventory/Audit)
    c.setFillColor(colors.HexColor("#059669"))
    c.rect(0, height - 10, width, 10, fill=1, stroke=0)

    # Header title
    c.setFillColor(colors.HexColor("#065F46"))
    c.setFont("Helvetica-Bold", 16)
    c.drawString(50, height - 45, "CENTRAL WAREHOUSE - INVENTORY STOCK AUDIT SHEET")

    c.setFillColor(colors.HexColor("#4B5563"))
    c.setFont("Helvetica", 9)
    c.drawString(50, height - 62, "Facility: Main Distribution Hub 04 | Aisle: Bay 4 & 5 | Cycle: Q4 Full Physical Audit")

    # Audit Info Box
    c.setFillColor(colors.HexColor("#F0FDF4"))
    c.setStrokeColor(colors.HexColor("#BBF7D0"))
    c.rect(50, height - 110, 512, 38, fill=1, stroke=1)

    c.setFillColor(colors.HexColor("#1F2937"))
    c.setFont("Helvetica-Bold", 9)
    c.drawString(60, height - 88, "Audit Date: 2026-10-18")
    c.drawString(200, height - 88, "Sheet #: AUDIT-2026-089")
    c.drawString(360, height - 88, "Checked By: Alex Vance (QC Lead)")

    c.setFont("Helvetica", 8)
    c.setFillColor(colors.HexColor("#4B5563"))
    c.drawString(60, height - 102, "Standard operating procedure: Count all open boxes. Note any damaged seals or discrepancies.")

    # Table Header Box
    table_top = height - 145
    c.setFillColor(colors.HexColor("#E2E8F0"))
    c.rect(50, table_top - 5, 512, 22, fill=1, stroke=0)

    headers = [
        ("CODE", 55),
        ("ITEM DESCRIPTION", 110),
        ("BIN", 265),
        ("BOOK", 320),
        ("COUNT", 365),
        ("DIFF", 415),
        ("NOTES / REMARKS", 455),
        ("CHK", 545)
    ]
    c.setFillColor(colors.HexColor("#1E293B"))
    c.setFont("Helvetica-Bold", 8)
    for title, x in headers:
        c.drawString(x, table_top + 2, title)

    # Rows with realistic stock audit records
    audit_rows = [
        ("W-104", "Hydraulic Flange Seal 40mm", "Bin A-12", "150", "148", "-2", "Damaged in shelf", "AV"),
        ("W-209", "Stainless Steel Hex Bolts M8", "Bin A-15", "500", "500", "0", "Verified sealed box", "AV"),
        ("W-312", "Brushless DC Motor 24V", "Bin B-03", "45", "42", "-3", "Short shipment suspected", "AV"),
        ("W-450", "Silicone Thermal Paste 50g", "Bin B-08", "80", "85", "+5", "Extra from return bin", "AV"),
        ("W-518", "Linear Optical Encoder 100mm", "Bin C-01", "25", "25", "0", "Calibrated & counted", "AV"),
        ("W-621", "Polyurethane Timing Belt 2M", "Bin C-04", "120", "119", "-1", "Worn teeth discarded", "AV")
    ]

    curr_y = table_top - 24
    c.setFont("Helvetica", 8)
    for idx, (code, desc, bin_loc, book, count, diff, note, chk) in enumerate(audit_rows):
        # Alternate zebra striping
        if idx % 2 == 1:
            c.setFillColor(colors.HexColor("#F8FAFC"))
            c.rect(50, curr_y - 6, 512, 18, fill=1, stroke=0)

        c.setFillColor(colors.HexColor("#0F172A"))
        c.drawString(55, curr_y, code)
        c.drawString(110, curr_y, desc)
        c.drawString(265, curr_y, bin_loc)
        c.drawRightString(345, curr_y, book)
        c.drawRightString(395, curr_y, count)

        # Highlight negative variance in red, positive in green
        if diff.startswith("-"):
            c.setFillColor(colors.HexColor("#DC2626"))
        elif diff.startswith("+"):
            c.setFillColor(colors.HexColor("#16A34A"))
        else:
            c.setFillColor(colors.HexColor("#64748B"))
        c.drawRightString(435, curr_y, diff)

        # Handwritten style note font representation
        c.setFillColor(colors.HexColor("#1E293B"))
        c.setFont("Helvetica-Oblique", 8)
        c.drawString(455, curr_y, note)
        c.setFont("Helvetica-Bold", 8)
        c.drawString(545, curr_y, chk)
        c.setFont("Helvetica", 8)

        # Line separator
        c.setStrokeColor(colors.HexColor("#E2E8F0"))
        c.line(50, curr_y - 7, 562, curr_y - 7)
        curr_y -= 22

    # Bottom notes / handwritten supervisor remarks section
    curr_y -= 20
    c.setFillColor(colors.HexColor("#FFFBEB"))
    c.setStrokeColor(colors.HexColor("#FDE68A"))
    c.rect(50, curr_y - 45, 512, 55, fill=1, stroke=1)

    c.setFillColor(colors.HexColor("#92400E"))
    c.setFont("Helvetica-Bold", 8)
    c.drawString(60, curr_y - 2, "SUPERVISOR AUDIT SIGN-OFF & HANDWRITTEN REMARKS:")
    c.setFont("Helvetica-Oblique", 8)
    c.setFillColor(colors.HexColor("#78350F"))
    c.drawString(60, curr_y - 16, "Alex Vance: Follow-up required with receiving dock regarding W-312 motor variance (-3 units).")
    c.drawString(60, curr_y - 28, "W-450 return bin discrepancy resolved and updated in inventory ERP. Re-audit bay 4 next Monday.")
    c.drawString(60, curr_y - 40, "Auditor Signature: Alex Vance  |  Warehouse Manager Approval: Approved & Logged")

    c.save()
    print(f"[OK] Generated Stock Audit PDF: {pdf_path}")


def generate_png_images(static_dir: str):
    """Generate high resolution PNGs for both invoice and stock audit."""
    # 1. Invoice PNG
    invoice_png = os.path.join(static_dir, "sample_invoice.png")
    img_inv = Image.new("RGB", (850, 1100), color=(255, 255, 255))
    d_inv = ImageDraw.Draw(img_inv)
    d_inv.rectangle([(0, 0), (850, 10)], fill=(79, 70, 229))
    d_inv.text((50, 40), "Acme Cloud Solutions Inc.", fill=(17, 24, 39))
    d_inv.text((600, 40), "INVOICE: INV-2026-8941", fill=(79, 70, 229))
    d_inv.text((50, 80), "Date: 2026-10-18 | Grand Total: $3,788.75", fill=(75, 85, 99))
    img_inv.save(invoice_png, "PNG")

    # 2. Stock Audit PNG
    audit_png = os.path.join(static_dir, "sample_stock_audit.png")
    img_aud = Image.new("RGB", (900, 1100), color=(255, 255, 255))
    d_aud = ImageDraw.Draw(img_aud)
    d_aud.rectangle([(0, 0), (900, 12)], fill=(5, 150, 105))
    d_aud.text((50, 40), "CENTRAL WAREHOUSE - INVENTORY STOCK AUDIT SHEET", fill=(6, 95, 70))
    d_aud.text((50, 70), "Audit Date: 2026-10-18 | Sheet #: AUDIT-2026-089 | Checked By: Alex Vance", fill=(75, 85, 99))
    d_aud.line([(50, 105), (850, 105)], fill=(209, 213, 219), width=2)

    # Draw table headers
    d_aud.rectangle([(50, 120), (850, 155)], fill=(226, 232, 240))
    d_aud.text((60, 130), "CODE        ITEM DESCRIPTION               BIN        BOOK    COUNT    DIFF    NOTES", fill=(15, 23, 42))

    rows = [
        "W-104       Hydraulic Flange Seal 40mm    Bin A-12   150     148      -2      Damaged in shelf",
        "W-209       Stainless Steel Bolts M8      Bin A-15   500     500       0      Sealed box OK",
        "W-312       Brushless DC Motor 24V        Bin B-03   45      42       -3      Short shipment",
        "W-450       Silicone Thermal Paste 50g    Bin B-08   80      85       +5      Extra from return",
        "W-518       Linear Optical Encoder        Bin C-01   25      25        0      Calibrated & count"
    ]
    curr_y = 175
    for r in rows:
        d_aud.text((60, curr_y), r, fill=(30, 41, 59))
        d_aud.line([(50, curr_y + 25), (850, curr_y + 25)], fill=(241, 245, 249), width=1)
        curr_y += 38

    d_aud.rectangle([(50, 950), (850, 1020)], fill=(254, 243, 199))
    d_aud.text((65, 965), "SUPERVISOR SIGN-OFF: Alex Vance | Re-audit bay 4 next Monday.", fill=(146, 64, 14))

    img_aud.save(audit_png, "PNG")
    print(f"[OK] Generated Stock Audit PNG: {audit_png}")


if __name__ == "__main__":
    out_dir = os.path.join(os.path.dirname(__file__), "app", "static")
    os.makedirs(out_dir, exist_ok=True)
    generate_invoice_pdf(os.path.join(out_dir, "sample_invoice.pdf"))
    generate_stock_audit_pdf(os.path.join(out_dir, "sample_stock_audit.pdf"))
    generate_png_images(out_dir)
