"""
Generate high quality sample invoice PDF (with native text layer) and PNG.
"""
import os
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas
from reportlab.lib import colors
from PIL import Image, ImageDraw, ImageFont

def generate_pdf_with_reportlab(pdf_path: str):
    c = canvas.Canvas(pdf_path, pagesize=letter)
    width, height = letter # 612 x 792

    # Top brand bar
    c.setFillColor(colors.HexColor("#4F46E5"))
    c.rect(0, height - 8, width, 8, fill=1, stroke=0)

    # Merchant details
    c.setFillColor(colors.HexColor("#111827"))
    c.setFont("Helvetica-Bold", 20)
    c.drawString(50, height - 50, "Acme Cloud Solutions Inc.")

    c.setFillColor(colors.HexColor("#6B7280"))
    c.setFont("Helvetica", 9)
    c.drawString(50, height - 68, "100 Innovation Way, Suite 400, San Francisco, CA 94105")
    c.drawString(50, height - 82, "billing@acmecloud.io | (555) 019-2834")

    # Invoice details
    c.setFillColor(colors.HexColor("#4F46E5"))
    c.setFont("Helvetica-Bold", 20)
    c.drawString(420, height - 50, "INVOICE")

    c.setFillColor(colors.HexColor("#1F2937"))
    c.setFont("Helvetica-Bold", 10)
    c.drawString(420, height - 72, "Invoice #: INV-2026-8941")

    c.setFillColor(colors.HexColor("#4B5563"))
    c.setFont("Helvetica", 9)
    c.drawString(420, height - 88, "Date: 2026-10-18")
    c.drawString(420, height - 102, "Due Date: 2026-11-18")

    # Divider
    c.setStrokeColor(colors.HexColor("#E5E7EB"))
    c.setLineWidth(1)
    c.line(50, height - 120, 562, height - 120)

    # Billed to
    c.setFillColor(colors.HexColor("#6B7280"))
    c.setFont("Helvetica-Bold", 8)
    c.drawString(50, height - 140, "BILLED TO:")
    c.setFillColor(colors.HexColor("#111827"))
    c.setFont("Helvetica-Bold", 10)
    c.drawString(50, height - 155, "Vertex Labs Technologies")
    c.setFillColor(colors.HexColor("#4B5563"))
    c.setFont("Helvetica", 9)
    c.drawString(50, height - 170, "Attn: Engineering Operations")
    c.drawString(50, height - 184, "742 Evergreen Terrace, Austin, TX")

    # Table Header
    table_top = height - 220
    c.setFillColor(colors.HexColor("#F3F4F6"))
    c.rect(50, table_top - 5, 512, 22, fill=1, stroke=0)

    c.setFillColor(colors.HexColor("#374151"))
    c.setFont("Helvetica-Bold", 9)
    c.drawString(60, table_top + 2, "DESCRIPTION")
    c.drawRightString(360, table_top + 2, "QTY")
    c.drawRightString(460, table_top + 2, "UNIT PRICE")
    c.drawRightString(550, table_top + 2, "TOTAL")

    # Line items
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

    # Footer
    c.setStrokeColor(colors.HexColor("#E5E7EB"))
    c.line(50, 70, 562, 70)
    c.setFillColor(colors.HexColor("#9CA3AF"))
    c.setFont("Helvetica", 8)
    c.drawString(50, 52, "Payment Terms: Net 30 days. Please include invoice number on wire transfer.")
    c.drawString(50, 38, "Thank you for partnering with Acme Cloud Solutions!")

    c.save()
    print(f"[OK] Generated PDF with native text: {pdf_path}")

def generate_png_image(png_path: str):
    width, height = 800, 1100
    image = Image.new("RGB", (width, height), color=(255, 255, 255))
    draw = ImageDraw.Draw(image)

    try:
        title_font = ImageFont.truetype("arial.ttf", 26)
        header_font = ImageFont.truetype("arial.ttf", 16)
        body_font = ImageFont.truetype("arial.ttf", 14)
        bold_font = ImageFont.truetype("arialbd.ttf", 14)
        small_font = ImageFont.truetype("arial.ttf", 12)
    except Exception:
        title_font = header_font = body_font = bold_font = small_font = ImageFont.load_default()

    draw.rectangle([(0, 0), (width, 8)], fill=(79, 70, 229))
    draw.text((50, 40), "Acme Cloud Solutions Inc.", fill=(17, 24, 39), font=title_font)
    draw.text((50, 75), "100 Innovation Way, Suite 400, San Francisco, CA 94105", fill=(107, 114, 128), font=body_font)
    draw.text((50, 95), "billing@acmecloud.io | (555) 019-2834", fill=(107, 114, 128), font=body_font)

    draw.text((550, 40), "INVOICE", fill=(79, 70, 229), font=title_font)
    draw.text((550, 80), "Invoice #: INV-2026-8941", fill=(31, 41, 55), font=bold_font)
    draw.text((550, 105), "Date: 2026-10-18", fill=(75, 85, 99), font=body_font)

    draw.line([(50, 140), (750, 140)], fill=(229, 231, 235), width=2)
    draw.text((50, 160), "BILLED TO: Vertex Labs Technologies", fill=(17, 24, 39), font=bold_font)

    table_top = 220
    draw.rectangle([(50, table_top), (750, table_top + 36)], fill=(243, 244, 246))
    draw.text((65, table_top + 10), "DESCRIPTION", fill=(55, 65, 81), font=bold_font)
    draw.text((450, table_top + 10), "QTY", fill=(55, 65, 81), font=bold_font)
    draw.text((530, table_top + 10), "UNIT PRICE", fill=(55, 65, 81), font=bold_font)
    draw.text((660, table_top + 10), "TOTAL", fill=(55, 65, 81), font=bold_font)

    items = [
        ("Enterprise Kubernetes Cluster (Oct)", "1", "$1450.00", "$1450.00"),
        ("Dedicated GPU Inference Instance (A100)", "2", "$650.00", "$1300.00"),
        ("Object Storage Bucket (10TB Egress)", "1", "$180.00", "$180.00"),
        ("Managed PostgreSQL High Availability", "1", "$320.00", "$320.00"),
        ("24/7 Priority SLA Technical Support", "1", "$250.00", "$250.00")
    ]

    curr_y = table_top + 50
    for desc, qty, unit_p, tot_p in items:
        draw.text((65, curr_y), desc, fill=(31, 41, 55), font=body_font)
        draw.text((460, curr_y), qty, fill=(31, 41, 55), font=body_font)
        draw.text((530, curr_y), unit_p, fill=(31, 41, 55), font=body_font)
        draw.text((660, curr_y), tot_p, fill=(31, 41, 55), font=body_font)
        draw.line([(50, curr_y + 30), (750, curr_y + 30)], fill=(243, 244, 246), width=1)
        curr_y += 42

    curr_y += 30
    draw.text((450, curr_y), "Subtotal: $3500.00", fill=(107, 114, 128), font=body_font)
    curr_y += 25
    draw.text((450, curr_y), "Estimated Tax: $288.75", fill=(107, 114, 128), font=body_font)
    curr_y += 30
    draw.rectangle([(440, curr_y - 6), (750, curr_y + 36)], fill=(238, 242, 255))
    draw.text((450, curr_y + 4), "GRAND TOTAL: $3788.75", fill=(67, 56, 202), font=bold_font)

    image.save(png_path, "PNG")
    print(f"[OK] Generated PNG image: {png_path}")

if __name__ == "__main__":
    out_dir = os.path.join(os.path.dirname(__file__), "app", "static")
    os.makedirs(out_dir, exist_ok=True)
    pdf_p = os.path.join(out_dir, "sample_invoice.pdf")
    png_p = os.path.join(out_dir, "sample_invoice.png")
    generate_pdf_with_reportlab(pdf_p)
    generate_png_image(png_p)
