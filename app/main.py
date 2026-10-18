"""
FastAPI application for Document Parser prototype.
"""
import os
import uuid
import csv
import io
from typing import List, Optional
from datetime import datetime

from fastapi import FastAPI, UploadFile, File, Depends, HTTPException, Header, status
from fastapi.responses import JSONResponse, StreamingResponse, FileResponse
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session

from .database import engine, Base, get_db
from .models import Document, LineItem
from .schemas import DocumentResponse, ParseResponse, InvoiceData
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
    title="Document Parser API",
    description="LLM-Powered Document and Invoice Parser Prototype",
    version="1.0.0"
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
    Accepts a PDF or Image invoice document, extracts structured data using an LLM schema,
    persists the document and line items into SQLite, and returns the parsed record.
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

    # Parse with DocumentParser (LLM or intelligent fallback)
    api_key = x_gemini_api_key or os.environ.get("GEMINI_API_KEY")
    parser = DocumentParser(api_key=api_key)
    parsed_data, raw_text = parser.parse(file_bytes, file.filename, file.content_type or "application/octet-stream")

    # Save to SQLite database: 'documents' table
    doc_record = Document(
        filename=file.filename,
        file_path=saved_path,
        content_type=file.content_type or "application/octet-stream",
        merchant=parsed_data.merchant,
        invoice_date=parsed_data.date,
        invoice_no=parsed_data.invoice_no,
        grand_total=parsed_data.grand_total or 0.0,
        currency=parsed_data.currency or "$",
        tax=parsed_data.tax or 0.0,
        raw_text=raw_text,
        created_at=datetime.utcnow()
    )
    db.add(doc_record)
    db.flush()  # populate doc_record.id

    # Save to SQLite database: 'line_items' table
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

    return {
        "success": True,
        "message": f"Successfully parsed document {file.filename}",
        "document": {
            "id": doc_record.id,
            "filename": doc_record.filename,
            "file_path": f"/api/files/{unique_name}",
            "content_type": doc_record.content_type,
            "merchant": doc_record.merchant,
            "date": doc_record.invoice_date,
            "invoice_no": doc_record.invoice_no,
            "grand_total": doc_record.grand_total,
            "currency": doc_record.currency,
            "tax": doc_record.tax,
            "created_at": doc_record.created_at,
            "line_items": [i.to_dict() for i in doc_record.line_items]
        },
        "parsed_data": parsed_data
    }


@app.get("/api/documents", response_model=List[DocumentResponse])
def get_documents(db: Session = Depends(get_db)):
    """Retrieve list of all parsed documents with line items."""
    docs = db.query(Document).order_by(Document.id.desc()).all()
    results = []
    for d in docs:
        file_basename = os.path.basename(d.file_path)
        results.append({
            "id": d.id,
            "filename": d.filename,
            "file_path": f"/api/files/{file_basename}",
            "content_type": d.content_type,
            "merchant": d.merchant,
            "date": d.invoice_date,
            "invoice_no": d.invoice_no,
            "grand_total": d.grand_total,
            "currency": d.currency,
            "tax": d.tax,
            "created_at": d.created_at,
            "line_items": [i.to_dict() for i in d.line_items]
        })
    return results


@app.get("/api/documents/{document_id}", response_model=DocumentResponse)
def get_document(document_id: int, db: Session = Depends(get_db)):
    """Retrieve a single document by ID."""
    d = db.query(Document).filter(Document.id == document_id).first()
    if not d:
        raise HTTPException(status_code=404, detail="Document not found")
    file_basename = os.path.basename(d.file_path)
    return {
        "id": d.id,
        "filename": d.filename,
        "file_path": f"/api/files/{file_basename}",
        "content_type": d.content_type,
        "merchant": d.merchant,
        "date": d.invoice_date,
        "invoice_no": d.invoice_no,
        "grand_total": d.grand_total,
        "currency": d.currency,
        "tax": d.tax,
        "created_at": d.created_at,
        "line_items": [i.to_dict() for i in d.line_items]
    }


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
    """Export document line items to a CSV file."""
    d = db.query(Document).filter(Document.id == document_id).first()
    if not d:
        raise HTTPException(status_code=404, detail="Document not found")

    output = io.StringIO()
    writer = csv.writer(output)
    # Write metadata header
    writer.writerow(["Document ID", d.id])
    writer.writerow(["Filename", d.filename])
    writer.writerow(["Merchant", d.merchant])
    writer.writerow(["Invoice Number", d.invoice_no])
    writer.writerow(["Invoice Date", d.invoice_date])
    writer.writerow(["Currency", d.currency])
    writer.writerow(["Grand Total", d.grand_total])
    writer.writerow(["Tax", d.tax])
    writer.writerow([])
    # Write line items table
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
    filename = f"invoice_{d.invoice_no or d.id}_{d.merchant or 'export'}.csv".replace(" ", "_")
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
    
    # Determine media type
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


# Mount static assets
app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")


@app.get("/favicon.ico")
def favicon():
    """Return empty 204 for favicon requests."""
    from fastapi import Response
    return Response(status_code=204)


@app.get("/")
def read_root():
    """Serve the single-page frontend."""
    index_file = os.path.join(STATIC_DIR, "index.html")
    if os.path.exists(index_file):
        return FileResponse(index_file, media_type="text/html")
    return {"message": "Document Parser Prototype is running. Open /docs for Swagger API."}
