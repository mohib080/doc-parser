# DocuParse AI - Full-Stack Document Parser Prototype

A full-stack, LLM-powered Document & Invoice Parser prototype built with **FastAPI**, **SQLite**, and a responsive **HTML5 / Tailwind CSS** single-page frontend.

---

## 🌟 Features

- **Document Ingestion**: Upload invoices as **PDF** or **Images** (`.pdf`, `.png`, `.jpg`, `.jpeg`, `.webp`).
- **Structured LLM Parsing**: Uses Pydantic structured schemas (`InvoiceData`, `LineItemSchema`) with Google Gemini multimodal structured output (`gemini-1.5-flash`), backed by a deterministic heuristic/regex engine for offline or mock scenarios.
- **Relational Storage**: Persists records into SQLite across two linked tables:
  - `documents`: Stores document metadata (merchant, invoice number, date, grand total, currency, tax, raw text, file path).
  - `line_items`: Stores individual items with foreign key link (`document_id`), item descriptions, quantities, unit prices, and line totals.
- **Side-by-Side Visual Workspace**:
  - **Left**: Interactive PDF / Image previewer.
  - **Right**: Extracted structured metadata cards and dynamic line items data table.
- **One-Click Export**: Download structured invoice data and line items directly to a formatted **CSV** file.
- **Quick Test Sample**: Built-in 1-click "Load Sample Invoice" button to test the parsing pipeline immediately.
- **Comprehensive Test Suite**: Automated unit and API integration tests with `pytest` and `httpx`.

---

## 📐 Architecture & Database Schema

### Database Schema (SQLite)

```sql
CREATE TABLE documents (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    filename VARCHAR(255) NOT NULL,
    file_path VARCHAR(500) NOT NULL,
    content_type VARCHAR(100) NOT NULL,
    merchant VARCHAR(255) DEFAULT 'Unknown Merchant',
    invoice_date VARCHAR(50),
    invoice_no VARCHAR(100),
    grand_total FLOAT DEFAULT 0.0,
    currency VARCHAR(20) DEFAULT '$',
    tax FLOAT DEFAULT 0.0,
    raw_text TEXT,
    created_at DATETIME
);

CREATE TABLE line_items (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    document_id INTEGER NOT NULL REFERENCES documents(id) ON DELETE CASCADE,
    description VARCHAR(500) NOT NULL,
    quantity FLOAT DEFAULT 1.0,
    unit_price FLOAT DEFAULT 0.0,
    total_price FLOAT DEFAULT 0.0
);
```

### LLM Structured Output Schema (`schemas.py`)

```python
class LineItemSchema(BaseModel):
    description: str = Field(..., description="Description or product/service name")
    quantity: float = Field(default=1.0, description="Quantity or unit count")
    unit_price: float = Field(default=0.0, description="Price per individual unit")
    total_price: float = Field(default=0.0, description="Total amount for this line item")

class InvoiceData(BaseModel):
    merchant: str = Field(..., description="Merchant or vendor name")
    date: Optional[str] = Field(None, description="Invoice date")
    invoice_no: Optional[str] = Field(None, description="Invoice reference number")
    line_items: List[LineItemSchema] = Field(default_factory=list)
    grand_total: Optional[float] = Field(None, description="Grand total due")
    currency: Optional[str] = Field("$", description="Currency symbol")
    tax: Optional[float] = Field(None, description="Tax or VAT amount")
```

---

## 🚀 API Endpoints

| Method | Endpoint | Description |
|---|---|---|
| `POST` | `/api/parse` | Accepts multipart `file`, runs LLM extraction, saves to DB, returns structured record |
| `GET` | `/api/documents` | Lists all parsed documents from SQLite |
| `GET` | `/api/documents/{id}` | Retrieves a single document and its line items |
| `DELETE` | `/api/documents/{id}` | Deletes a document and its associated file & line items |
| `GET` | `/api/documents/{id}/export-csv` | Streams a formatted CSV export of document line items |
| `GET` | `/api/files/{filename}` | Serves uploaded PDF/image for side-by-side preview |
| `GET` | `/` | Serves the interactive Tailwind single-page app |

---

## 🧪 Running Tests

Run the complete test suite:
```powershell
.\venv\Scripts\pytest -v
```

Run live end-to-end verification:
```powershell
.\venv\Scripts\python e2e_verify.py
```

---

## 💻 Running the Server

Start the FastAPI application:
```powershell
.\venv\Scripts\uvicorn app.main:app --host 127.0.0.1 --port 8000 --reload
```
Open **[http://127.0.0.1:8000](http://127.0.0.1:8000)** in your browser.
Interactive OpenAPI docs are available at **[http://127.0.0.1:8000/docs](http://127.0.0.1:8000/docs)**.
