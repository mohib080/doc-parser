# DocuParse AI 🔍

> **A production-ready, full-stack AI document parser** that reads invoices, handwritten tables, and stock audit sheets using Google Gemini 2.5 Flash Vision — with automatic SHA-256 caching to stay safely within API quota limits.

[![Python](https://img.shields.io/badge/Python-3.11+-blue)](https://python.org)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.115+-green)](https://fastapi.tiangolo.com)
[![Gemini](https://img.shields.io/badge/Gemini-2.5%20Flash-orange)](https://ai.google.dev)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow)](LICENSE)

## 🎥 Project Demo

[![Watch DocuParse AI Demo](https://img.youtube.com/vi/VhDpAYD8aCo/0.jpg)](https://youtu.be/VhDpAYD8aCo)

[▶ Watch the demo on YouTube](https://youtu.be/VhDpAYD8aCo)

Visit : [DocuParse](https://doc-parser-zis5.onrender.com)

---


---

## Table of Contents

- [What It Does](#what-it-does)
- [Tech Stack](#tech-stack)
- [Project Structure](#project-structure)
- [Quick Start](#quick-start)
- [Configuration](#configuration)
- [How It Works](#how-it-works)
- [API Reference](#api-reference)
- [Database Schema](#database-schema)
- [Frontend](#frontend)
- [Running Tests](#running-tests)
- [File Hash Caching](#file-hash-caching)
- [Fallback Mode](#fallback-mode)
- [Development Notes](#development-notes)

---

## What It Does

DocuParse AI accepts an uploaded **PDF or image** (including **handwritten** documents) and extracts structured data from it automatically. It supports two document modes out of the box:

| Mode | Document Type | Extracted Fields |
|------|--------------|-----------------|
| **Invoice** | Printed/scanned financial invoices | Merchant, Date, Invoice #, Line Items (Qty, Price, Total), Grand Total, Tax, Currency |
| **Stock Audit** | Handwritten/printed inventory or audit sheets | Code, Item Description, Bin, Book Qty, Physical Count, Variance, Notes, Checked By |

The frontend shows a **side-by-side preview** of the document next to the extracted data table. All records are saved to SQLite and can be **exported as CSV** with one click.

---

## Tech Stack

| Layer | Technology |
|-------|-----------|
| **Backend API** | FastAPI (Python 3.11+) |
| **AI / Vision** | Google Gemini 2.5 Flash (`google-genai` SDK) |
| **Database** | SQLite via SQLAlchemy ORM |
| **Frontend** | Single-page HTML5 + Tailwind CSS v4 CDN |
| **PDF Parsing** | pypdf (text extraction from machine-readable PDFs) |
| **Testing** | pytest + FastAPI TestClient |

---

## Project Structure

```
doc-parser/
│
├── app/
│   ├── __init__.py
│   ├── main.py          # FastAPI app, all API routes
│   ├── parser.py        # DocumentParser class — Gemini Vision + heuristic fallback
│   ├── database.py      # SQLAlchemy engine, session, init_db(), get_document_by_hash()
│   ├── models.py        # SQLAlchemy ORM models (Document, LineItem)
│   ├── schemas.py       # Pydantic schemas (ParsedDocumentData, DocumentResponse, etc.)
│   ├── uploads/         # Uploaded files are stored here (auto-created)
│   └── static/
│       ├── index.html   # Full single-page frontend
│       ├── app.js       # Frontend logic (upload, render table, CSV export)
│       ├── sample_invoice.pdf
│       ├── sample_invoice.png
│       ├── sample_stock_audit.pdf
│       └── sample_stock_audit.png
│
├── tests/
│   ├── __init__.py
│   ├── test_api.py      # Integration tests for all endpoints
│   └── test_parser.py   # Unit tests for parsing schemas and heuristics
│
├── .env                 # Your local secrets (not committed to git)
├── .env.example         # Template — copy this to .env to get started
├── requirements.txt     # Python dependencies
├── e2e_verify.py        # Full end-to-end smoke test script
├── generate_sample.py   # Script to regenerate sample PDF files
└── doc_parser.db        # SQLite database (auto-created on first run)
```

---

## Quick Start

### Prerequisites

- Python 3.11+
- A Gemini API key from [Google AI Studio](https://aistudio.google.com/app/apikey) *(free tier works)*

### 1. Clone the repo

```bash
git clone https://github.com/mohib080/doc-parser.git
cd doc-parser
```

### 2. Create a virtual environment and install dependencies

```bash
# Windows
python -m venv venv
.\venv\Scripts\activate
pip install -r requirements.txt

# macOS / Linux
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

### 3. Configure your API key

```bash
# Copy the example file
cp .env.example .env
```

Open `.env` and paste your Gemini API key:

```env
GEMINI_API_KEY=AIzaSy...yourkey...
DATABASE_URL=sqlite:///./doc_parser.db
```

> **No key?** The app still works without one — it falls back to a regex/heuristic parser that can read machine-readable PDFs. Handwritten documents require the Gemini API key.

### 4. Start the server

```bash
# Windows
.\venv\Scripts\uvicorn app.main:app --host 127.0.0.1 --port 8000 --reload

# macOS / Linux
uvicorn app.main:app --host 127.0.0.1 --port 8000 --reload
```

Open **http://127.0.0.1:8000** in your browser. That's it.

Interactive API docs are available at **http://127.0.0.1:8000/docs**.

---

## Configuration

All configuration is done through the `.env` file. Copy `.env.example` to `.env` and edit it:

| Variable | Default | Description |
|----------|---------|-------------|
| `GEMINI_API_KEY` | *(empty)* | Google Gemini API key. When blank, heuristic fallback mode is used. |
| `DATABASE_URL` | `sqlite:///./doc_parser.db` | SQLAlchemy connection string. Change to a PostgreSQL URL for production. |

### Custom API Key (per session)

In the UI, clicking the **"Custom API Key"** button in the top-right lets you provide a session-specific Gemini key. This overrides the `.env` key for that browser session without modifying any files. Useful for testing with a different account.

---

## How It Works

### Parsing Pipeline

```
Upload File (PDF / Image)
        │
        ▼
Compute SHA-256 Hash
        │
        ├──► Hash already in DB? ──► YES ──► Return cached document instantly
        │                                     (no API call, no quota usage)
        │
        ▼ NO
Save file to app/uploads/
        │
        ▼
GEMINI_API_KEY set?
        │
        ├──► YES ──► Send file bytes + prompt to Gemini 2.5 Flash Vision
        │             Parse JSON response → ParsedDocumentData
        │
        └──► NO  ──► Offline heuristic engine
                      Extract text from PDF (pypdf)
                      Regex-based field detection

        ▼
Save Document + file_hash + LineItems to SQLite
        │
        ▼
Return structured JSON response to frontend
```

### Document Type Detection

The parser automatically detects document type based on content:

- Files/content containing keywords like `audit`, `stock`, `inventory`, `count`, or `sheet` → `stock_audit` mode
- Everything else defaults to `invoice` mode

The frontend **dynamically adapts** its table headers and CSV export to match whatever columns were extracted — it doesn't hardcode any field names.

---

## API Reference

All endpoints return JSON unless specified otherwise.

### `POST /api/parse`

Upload a document to extract structured data.

**Request**: `multipart/form-data`

| Field | Type | Description |
|-------|------|-------------|
| `file` | File | PDF, PNG, JPG, JPEG, or WEBP. Max size limited by server. |

**Headers** (optional):

| Header | Description |
|--------|-------------|
| `X-Gemini-Api-Key` | Override the server's API key for this request only |

**Response** `201 Created`:

```json
{
  "success": true,
  "cached": false,
  "message": "Successfully parsed invoice document 'invoice.pdf'",
  "document": {
    "id": 42,
    "filename": "invoice.pdf",
    "file_hash": "a3f9b2c1...",
    "doc_type": "invoice",
    "merchant": "Acme Corp",
    "date": "2026-10-18",
    "invoice_no": "INV-2026-8941",
    "grand_total": 3788.75,
    "currency": "$",
    "tax": 288.75,
    "columns": ["Description", "Quantity", "Unit Price", "Total"],
    "rows": [{ "Description": "Cloud Server", "Quantity": "2", "Unit Price": "800.00", "Total": "1600.00" }],
    "line_items": [...],
    "created_at": "2026-10-18T17:09:00"
  }
}
```

When `"cached": true`, the response is returned instantly without calling Gemini — same document was uploaded before.

---

### `GET /api/documents`

Returns a list of all parsed documents (newest first).

**Response** `200 OK`: Array of document objects.

---

### `GET /api/documents/{id}`

Returns a single document with all line items and dynamic rows.

**Response** `200 OK` or `404 Not Found`.

---

### `DELETE /api/documents/{id}`

Deletes a document record, its line items, and the uploaded file from disk.

**Response** `200 OK`:
```json
{ "success": true, "message": "Document 42 deleted successfully" }
```

---

### `GET /api/documents/{id}/export-csv`

Streams a CSV file download with headers matching the document's dynamic columns.

**Response**: `text/csv` download with dynamic headers.

---

### `GET /api/files/{filename}`

Serves the original uploaded file (used for the side-by-side preview panel).

---

## Database Schema

### `documents` table

| Column | Type | Description |
|--------|------|-------------|
| `id` | INTEGER PK | Auto-increment primary key |
| `filename` | VARCHAR(255) | Original uploaded filename |
| `file_path` | VARCHAR(500) | Absolute path to stored file |
| `content_type` | VARCHAR(100) | MIME type (e.g. `application/pdf`) |
| `file_hash` | VARCHAR(64) | SHA-256 hex digest for cache lookup |
| `doc_type` | VARCHAR(50) | `invoice`, `stock_audit`, `receipt`, etc. |
| `merchant` | VARCHAR(255) | Vendor / company name |
| `invoice_date` | VARCHAR(50) | Document date string |
| `invoice_no` | VARCHAR(100) | Invoice or reference number |
| `inspector` | VARCHAR(255) | Auditor or checker name |
| `columns_json` | TEXT | JSON array of dynamic column headers |
| `rows_json` | TEXT | JSON array of row dicts |
| `grand_total` | FLOAT | Total amount |
| `currency` | VARCHAR(20) | Currency symbol |
| `tax` | FLOAT | Tax amount |
| `notes` | TEXT | Remarks or follow-up notes |
| `raw_text` | TEXT | Raw text extracted from PDF |
| `created_at` | DATETIME | Timestamp of upload |

### `line_items` table

| Column | Type | Description |
|--------|------|-------------|
| `id` | INTEGER PK | Auto-increment primary key |
| `document_id` | INTEGER FK | References `documents.id` (CASCADE DELETE) |
| `description` | VARCHAR(500) | Item/service description |
| `quantity` | FLOAT | Quantity |
| `unit_price` | FLOAT | Price per unit |
| `total_price` | FLOAT | Line total |

> The `file_hash` column is automatically added via migration if upgrading from an older version of the database. Existing files on disk are backfilled on first startup.

---

## Frontend

The entire frontend is a single HTML file served at `/`. No build step required.

### Key Features

- **Drag & Drop** upload zone — drag any PDF or image directly onto the page
- **Side-by-side workspace**: document preview panel (left) + extracted data panel (right)
- **Dynamic table headers**: column names adapt automatically to whatever the AI extracted
- **Sample files**: built-in "Sample Invoice" and "Sample Stock Audit" buttons to test instantly
- **Document History**: sidebar showing all previously parsed documents with one-click reload
- **CSV Export**: exports with the exact dynamic columns from the current document
- **Custom API Key button**: override the Gemini key for the current session without touching `.env`

---

## Running Tests

Run the full test suite (unit + integration):

```bash
.\venv\Scripts\pytest -v tests/
```

Run the end-to-end live verification script (requires a running server):

```bash
.\venv\Scripts\python e2e_verify.py
```

### Test Coverage

| Test | Description |
|------|-------------|
| `test_root_serves_html` | Frontend HTML is served correctly |
| `test_parse_endpoint_with_sample_invoice_pdf` | Invoice PDF parses and saves to DB |
| `test_parse_endpoint_with_stock_audit_pdf` | Stock audit PDF parses with correct columns |
| `test_parse_endpoint_with_image` | Image upload parses successfully |
| `test_parse_invalid_file_extension` | `.exe` upload returns 400 |
| `test_parse_empty_file` | Empty file returns 400 |
| `test_get_documents_and_detail` | Document list and detail endpoints work |
| `test_export_csv` | CSV export returns valid CSV |
| `test_delete_document` | Delete removes record and returns 404 after |
| `test_file_hash_caching_avoids_llm_call` | **Cache hit returns same document ID without Gemini call** |
| `test_parse_handwritten_user_image` | Live Gemini extraction (skipped if quota exceeded or no key) |

> **Note**: Tests run with `GEMINI_API_KEY` blanked via `monkeypatch.setenv` so they never consume real API quota. The live handwritten image test (`test_parse_handwritten_user_image`) is the only exception — it reads the key from `.env` and skips gracefully if quota is exhausted.

---

## File Hash Caching

Every uploaded file is SHA-256 hashed **before** any API call is made. The hash is checked against the `documents.file_hash` column in SQLite:

- **Cache HIT**: The same file was parsed before → returns the cached document and line items **instantly**, with `"cached": true` in the response. Zero Gemini API calls. Zero quota usage.
- **Cache MISS**: New file → runs through the full Gemini Vision pipeline and saves the hash alongside the result.

This protects against quota exhaustion when testing repeatedly with the same files, and speeds up re-uploads significantly.

---

## Fallback Mode

When `GEMINI_API_KEY` is not set (or blank), the parser automatically uses an **offline heuristic engine**:

- For **machine-readable PDFs**: extracts raw text via `pypdf` then uses regex patterns to detect merchant names, invoice numbers, dates, line item tables, and totals.
- For **images without an API key**: generates a minimal placeholder document (not useful for real data — set the API key for image/handwriting support).

The fallback engine is production-safe for printed PDFs with clear formatting. It is not suitable for handwritten documents.

---

## Development Notes

### Adding a New Document Type

1. In `app/parser.py`, extend the keyword list in `DocumentParser.parse()` to detect the new type.
2. Update the Gemini prompt in `parse_with_gemini()` to instruct the model on expected column names.
3. The frontend will automatically adapt to whatever `columns` and `rows` the API returns — no frontend changes needed.

### Switching to PostgreSQL

Change `DATABASE_URL` in `.env`:

```env
DATABASE_URL=postgresql://user:password@localhost:5432/docparser
```

Install the PostgreSQL driver:

```bash
pip install psycopg2-binary
```

The SQLAlchemy models are database-agnostic. Note: the `file_hash` column migration uses `PRAGMA table_info` which is SQLite-specific — review `init_db()` in `database.py` if migrating.

### Rate Limits

The free tier of the Gemini API allows **20 requests per day** for `gemini-2.5-flash`. The SHA-256 file-hash cache is specifically designed to protect against hitting this limit during development. For production, upgrade to a paid tier or implement a request queue.

---

## License

MIT License — see [LICENSE](LICENSE) for details.
