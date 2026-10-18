"""
FastAPI application for Document Parser prototype.
Supports both standard Invoices and dynamic custom tables (Stock Audits, Inventory Sheets).
"""
import os
import uuid
import csv
import io
import json
from typing import List, Optional
from datetime import datetime

from fastapi import FastAPI, UploadFile, File, Depends, HTTPException, Header, status
from fastapi.responses import JSONResponse, StreamingResponse, FileResponse
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from dotenv import load_dotenv

# Load .env file automatically
load_dotenv()

from .database import engine, Base, get_db
from .models import Document, LineItem
from .schemas import DocumentResponse, ParseResponse, ParsedDocumentData
from .parser import DocumentParser

# Ensure DB tables exist
Base.metadata.create_all(bind=engine)

# Directory configurations
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
UPLOAD_DIR = os.path.join(BASE_DIR, "uploads")
STATIC_DIR = os.path.join(BASE_DIR, "static")
os.makedirs(UPLOAD_DIR, exist_ok=True)
os.makedirs(STATIC_DIR, exist_ok=True)

app = FastAPI(
    title="DocuParse AI - Intelligent Document & Table Parser",
    description="Multimodal LLM Document & Vision Extraction (Gemini 2.5 Flash)",
    version="2.0.0"
)

# CORS Middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.post("/api/parse", response_model=ParseResponse, status_code=status.HTTP_201_CREATED)
async def parse_document(
    file: UploadFile = File(...),
    x_gemini_api_key: Optional[str] = Header(None, alias="X-Gemini-Api-Key"),
    db: Session = Depends(get_db)
):
    """
    Accepts a PDF or Image (handwritten/printed Invoice or Stock Audit Sheet),
    extracts structured data using Gemini 2.5 Flash Vision API,
    persists into SQLite, and returns the parsed record with dynamic columns & rows.
    """
    if not file.filename:
        raise HTTPException(status_code=400, detail="No file uploaded")

    allowed_extensions = {".pdf", ".png", ".jpg", ".jpeg", ".webp"}
    ext = os.path.splitext(file.filename)[1].lower()
    if ext not in allowed_extensions:
        raise HTTPException(
            status_code=400,
            detail=f"Unsupported file type '{ext}'. Allowed types: {', '.join(allowed_extensions)}"
        )

    file_bytes = await file.read()
    if len(file_bytes) == 0:
        raise HTTPException(status_code=400, detail="Uploaded file is empty")

    # Generate unique storage filename
    unique_name = f"{uuid.uuid4().hex}_{file.filename}"
    saved_path = os.path.join(UPLOAD_DIR, unique_name)
    with open(saved_path, "wb") as f:
        f.write(file_bytes)

    # API key preference: Header > .env/environment
    api_key = x_gemini_api_key or os.environ.get("GEMINI_API_KEY")
    parser = DocumentParser(api_key=api_key)
    try:
        parsed_data, raw_text = parser.parse(file_bytes, file.filename, file.content_type or "application/octet-stream")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

    # Save to SQLite database: 'documents' table
    doc_record = Document(
        filename=file.filename,
        file_path=saved_path,
        content_type=file.content_type or "application/octet-stream",
        doc_type=parsed_data.doc_type,
        merchant=parsed_data.title,
        invoice_date=parsed_data.date,
        invoice_no=parsed_data.reference_no,
        inspector=parsed_data.inspector,
        columns_json=json.dumps(parsed_data.columns),
        rows_json=json.dumps(parsed_data.rows),
        grand_total=parsed_data.grand_total or 0.0,
        currency=parsed_data.currency or "$",
        tax=parsed_data.tax or 0.0,
        notes=parsed_data.notes,
        raw_text=raw_text,
        created_at=datetime.utcnow()
    )
    db.add(doc_record)
    db.flush()  # populate doc_record.id

    # Save to SQLite database: 'line_items' table (backward compatible relational link)
    for item in parsed_data.line_items:
        line_item_record = LineItem(
            document_id=doc_record.id,
            description=item.description,
            quantity=item.quantity,
            unit_price=item.unit_price,
            total_price=item.total_price
        )
        db.add(line_item_record)

    db.commit()
    db.refresh(doc_record)

    doc_dict = doc_record.to_dict()
    doc_dict["file_path"] = f"/api/files/{unique_name}"

    return {
        "success": True,
        "message": f"Successfully parsed {parsed_data.doc_type} document '{file.filename}'",
        "document": doc_dict,
        "parsed_data": parsed_data
    }


@app.get("/api/documents", response_model=List[DocumentResponse])
def get_documents(db: Session = Depends(get_db)):
    """Retrieve list of all parsed documents with dynamic columns, rows, and line items."""
    docs = db.query(Document).order_by(Document.id.desc()).all()
    results = []
    for d in docs:
        d_dict = d.to_dict()
        file_basename = os.path.basename(d.file_path)
        d_dict["file_path"] = f"/api/files/{file_basename}"
        results.append(d_dict)
    return results


@app.get("/api/documents/{document_id}", response_model=DocumentResponse)
def get_document(document_id: int, db: Session = Depends(get_db)):
    """Retrieve a single document by ID."""
    d = db.query(Document).filter(Document.id == document_id).first()
    if not d:
        raise HTTPException(status_code=404, detail="Document not found")
    d_dict = d.to_dict()
    file_basename = os.path.basename(d.file_path)
    d_dict["file_path"] = f"/api/files/{file_basename}"
    return d_dict


@app.delete("/api/documents/{document_id}")
def delete_document(document_id: int, db: Session = Depends(get_db)):
    """Delete a document and its line items."""
    d = db.query(Document).filter(Document.id == document_id).first()
    if not d:
        raise HTTPException(status_code=404, detail="Document not found")
    try:
        if os.path.exists(d.file_path):
            os.remove(d.file_path)
    except Exception:
        pass
    db.delete(d)
    db.commit()
    return {"success": True, "message": f"Document {document_id} deleted"}


@app.get("/api/documents/{document_id}/export-csv")
def export_csv(document_id: int, db: Session = Depends(get_db)):
    """
    Export document data to CSV matching the exact dynamic table columns.
    For Invoices: Description, Quantity, Unit Price, Total Price.
    For Stock Audits / Custom Tables: Code, Item Description, Bin, Book Qty, Physical Count, Variance, Notes, Checked By.
    """
    d = db.query(Document).filter(Document.id == document_id).first()
    if not d:
        raise HTTPException(status_code=404, detail="Document not found")

    output = io.StringIO()
    writer = csv.writer(output)

    # Document Header Section
    writer.writerow(["Document ID", d.id])
    writer.writerow(["Filename", d.filename])
    writer.writerow(["Document Type", d.doc_type or "invoice"])
    writer.writerow(["Title / Vendor", d.merchant])
    writer.writerow(["Date", d.invoice_date])
    writer.writerow(["Reference / Invoice #", d.invoice_no])
    if d.inspector:
        writer.writerow(["Inspector / Checked By", d.inspector])
    if d.grand_total and d.grand_total > 0:
        writer.writerow(["Currency", d.currency or "$"])
        writer.writerow(["Grand Total", d.grand_total])
        writer.writerow(["Tax", d.tax or 0.0])
    if d.notes:
        writer.writerow(["Notes", d.notes])
    writer.writerow([])

    # Parse columns and rows
    try:
        columns = json.loads(d.columns_json) if d.columns_json else []
    except Exception:
        columns = []
    try:
        rows = json.loads(d.rows_json) if d.rows_json else []
    except Exception:
        rows = []

    # Write Dynamic Table Columns
    if columns and rows:
        writer.writerow(columns)
        for r in rows:
            writer.writerow([r.get(c, "") for c in columns])
    else:
        # Fallback to standard line_items if columns_json not present
        writer.writerow(["Item ID", "Description", "Quantity", "Unit Price", "Total Price"])
        for item in d.line_items:
            writer.writerow([
                item.id,
                item.description,
                item.quantity,
                item.unit_price,
                item.total_price
            ])

    output.seek(0)
    clean_title = (d.merchant or "document").replace(" ", "_").replace("/", "_")
    filename = f"{d.doc_type or 'doc'}_{d.invoice_no or d.id}_{clean_title}.csv"

    return StreamingResponse(
        iter([output.getvalue()]),
        media_type="text/csv",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'}
    )


@app.get("/api/files/{filename}")
def serve_file(filename: str):
    """Serve uploaded document file for preview in frontend."""
    file_path = os.path.join(UPLOAD_DIR, filename)
    if not os.path.exists(file_path):
        raise HTTPException(status_code=404, detail="File not found")

    ext = os.path.splitext(filename)[1].lower()
    media_types = {
        ".pdf": "application/pdf",
        ".png": "image/png",
        ".jpg": "image/jpeg",
        ".jpeg": "image/jpeg",
        ".webp": "image/webp",
    }
    media_type = media_types.get(ext, "application/octet-stream")
    return FileResponse(file_path, media_type=media_type)


@app.get("/favicon.ico")
def favicon():
    """Return empty 204 for favicon requests."""
    from fastapi import Response
    return Response(status_code=204)


# Mount static assets
app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")


@app.get("/")
def read_root():
    """Serve the single-page frontend."""
    index_file = os.path.join(STATIC_DIR, "index.html")
    if os.path.exists(index_file):
        return FileResponse(index_file, media_type="text/html")
    return {"message": "DocuParse AI Prototype is running. Open /docs for Swagger API."}
