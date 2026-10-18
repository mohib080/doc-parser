"""
Generate high quality sample invoice PDF and PNG files for testing and instant demo.
"""
import os
from PIL import Image, ImageDraw, ImageFont

def generate_sample_invoice(output_pdf_path: str, output_png_path: str):
    # A4 proportion: 800 x 1130
    width, height = 800, 1130
    image = Image.new("RGB", (width, height), color=(255, 255, 255))
    draw = ImageDraw.Draw(image)

    # Use default font or basic styling
    try:
        title_font = ImageFont.truetype("arial.ttf", 28)
        header_font = ImageFont.truetype("arial.ttf", 16)
        body_font = ImageFont.truetype("arial.ttf", 14)
        bold_font = ImageFont.truetype("arialbd.ttf", 15)
        small_font = ImageFont.truetype("arial.ttf", 12)
    except Exception:
        title_font = header_font = body_font = bold_font = small_font = ImageFont.load_default()

    # Brand Header Bar (Indigo accent)
    draw.rectangle([(0, 0), (width, 8)], fill=(79, 70, 229))

    # Merchant Info
    draw.text((50, 40), "ACME CLOUD SOLUTIONS INC.", fill=(17, 24, 39), font=title_font)
    draw.text((50, 75), "100 Innovation Way, Suite 400", fill=(107, 114, 128), font=body_font)
    draw.text((50, 95), "San Francisco, CA 94105", fill=(107, 114, 128), font=body_font)
    draw.text((50, 115), "billing@acmecloud.io | (555) 019-2834", fill=(107, 114, 128), font=body_font)

    # Invoice Badge & Details
    draw.text((550, 40), "INVOICE", fill=(79, 70, 229), font=title_font)
    draw.text((550, 80), "Invoice #: INV-2026-8941", fill=(31, 41, 55), font=bold_font)
    draw.text((550, 105), "Date: 2026-10-18", fill=(75, 85, 99), font=body_font)
    draw.text((550, 130), "Due Date: 2026-11-18", fill=(75, 85, 99), font=body_font)

    # Horizontal divider
    draw.line([(50, 170), (750, 170)], fill=(229, 231, 235), width=2)

    # Billed To
    draw.text((50, 190), "BILLED TO:", fill=(107, 114, 128), font=small_font)
    draw.text((50, 210), "Vertex Labs Technologies", fill=(17, 24, 39), font=bold_font)
    draw.text((50, 230), "Attn: Engineering Operations", fill=(75, 85, 99), font=body_font)
    draw.text((50, 250), "742 Evergreen Terrace, Austin, TX", fill=(75, 85, 99), font=body_font)

    # Table Header Box
    table_top = 300
    draw.rectangle([(50, table_top), (750, table_top + 36)], fill=(243, 244, 246))
    draw.text((65, table_top + 10), "DESCRIPTION", fill=(55, 65, 81), font=bold_font)
    draw.text((450, table_top + 10), "QTY", fill=(55, 65, 81), font=bold_font)
    draw.text((530, table_top + 10), "UNIT PRICE", fill=(55, 65, 81), font=bold_font)
    draw.text((660, table_top + 10), "TOTAL", fill=(55, 65, 81), font=bold_font)

    # Table Rows
    items = [
        ("Enterprise Kubernetes Cluster (Oct)", "1", "$1,450.00", "$1,450.00"),
        ("Dedicated GPU Inference Instance (A100)", "2", "$650.00", "$1,300.00"),
        ("Object Storage Bucket (10TB Egress)", "1", "$180.00", "$180.00"),
        ("Managed PostgreSQL High Availability", "1", "$320.00", "$320.00"),
        ("24/7 Priority SLA Technical Support", "1", "$250.00", "$250.00")
    ]

    current_y = table_top + 50
    for idx, (desc, qty, unit_p, tot_p) in enumerate(items):
        bg = (255, 255, 255) if idx % 2 == 0 else (249, 250, 251)
        draw.rectangle([(50, current_y - 8), (750, current_y + 30)], fill=bg)
        draw.text((65, current_y), desc, fill=(31, 41, 55), font=body_font)
        draw.text((460, current_y), qty, fill=(31, 41, 55), font=body_font)
        draw.text((530, current_y), unit_p, fill=(31, 41, 55), font=body_font)
        draw.text((660, current_y), tot_p, fill=(31, 41, 55), font=body_font)
        draw.line([(50, current_y + 30), (750, current_y + 30)], fill=(243, 244, 246), width=1)
        current_y += 42

    # Totals Section
    current_y += 30
    draw.line([(450, current_y), (750, current_y)], fill=(209, 213, 219), width=1)
    
    current_y += 15
    draw.text((450, current_y), "Subtotal:", fill=(107, 114, 128), font=body_font)
    draw.text((660, current_y), "$3,500.00", fill=(31, 41, 55), font=body_font)

    current_y += 28
    draw.text((450, current_y), "Estimated Tax (8.25%):", fill=(107, 114, 128), font=body_font)
    draw.text((660, current_y), "$288.75", fill=(31, 41, 55), font=body_font)

    current_y += 32
    draw.rectangle([(440, current_y - 6), (750, current_y + 36)], fill=(238, 242, 255))
    draw.text((450, current_y + 4), "GRAND TOTAL:", fill=(67, 56, 202), font=bold_font)
    draw.text((640, current_y + 4), "$3,788.75", fill=(67, 56, 202), font=bold_font)

    # Footer Notes
    draw.line([(50, 1020), (750, 1020)], fill=(229, 231, 235), width=1)
    draw.text((50, 1035), "Payment Terms: Net 30 days. Please include invoice number on wire transfer.", fill=(107, 114, 128), font=small_font)
    draw.text((50, 1055), "Thank you for partnering with Acme Cloud Solutions!", fill=(156, 163, 175), font=small_font)

    # Save PNG
    image.save(output_png_path, "PNG")

    # Save PDF
    rgb_img = image.convert("RGB")
    rgb_img.save(output_pdf_path, "PDF", resolution=100.0)

    print(f"Generated sample invoice PDF: {output_pdf_path}")
    print(f"Generated sample invoice PNG: {output_png_path}")

if __name__ == "__main__":
    out_dir = os.path.join(os.path.dirname(__file__), "app", "static")
    os.makedirs(out_dir, exist_ok=True)
    pdf_p = os.path.join(out_dir, "sample_invoice.pdf")
    png_p = os.path.join(out_dir, "sample_invoice.png")
    generate_sample_invoice(pdf_p, png_p)
