"""
Pydantic schemas for LLM structured output and API endpoints.
Supports both standard Invoice mode and dynamic custom tables (Stock Audits, Inventory, Sheets).
"""
import json
from datetime import datetime
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field, ConfigDict


# -------------------------------------------------------------
# Structured LLM Output Schemas
# -------------------------------------------------------------
class LineItemSchema(BaseModel):
    description: str = Field(..., description="Description or product/service/item name")
    quantity: float = Field(default=1.0, description="Quantity or unit count")
    unit_price: float = Field(default=0.0, description="Price per individual unit")
    total_price: float = Field(default=0.0, description="Total amount or variance value for this item")


class ParsedDocumentData(BaseModel):
    """
    Flexible schema that handles both financial Invoices and general
    handwritten/printed tables (Stock Audits, Inventory Sheets, Inspection Logs).
    """
    doc_type: str = Field(
        default="invoice",
        description="Type of document: 'invoice', 'receipt', 'stock_audit', 'inventory', 'table', or 'form'"
    )
    title: str = Field(
        default="Unknown Document",
        description="Document title, merchant/vendor name, or audit sheet header"
    )
    date: Optional[str] = Field(
        None,
        description="Document date, invoice date, or audit date (e.g. YYYY-MM-DD or readable date)"
    )
    reference_no: Optional[str] = Field(
        None,
        description="Invoice number, audit ID, sheet number, or tracking reference"
    )
    inspector: Optional[str] = Field(
        None,
        description="Auditor, inspector, checked by, or technician name/initials if present"
    )
    columns: List[str] = Field(
        default_factory=list,
        description=(
            "List of dynamic table column headers extracted from the document. "
            "For invoices: ['Description', 'Quantity', 'Unit Price', 'Total']. "
            "For stock audits: ['Code', 'Item Description', 'Bin', 'Book Qty', 'Physical Count', 'Variance', 'Notes', 'Checked By']. "
            "For generic tables: exact header titles found."
        )
    )
    rows: List[Dict[str, str]] = Field(
        default_factory=list,
        description=(
            "Extracted table rows. Each row maps column header name -> cell text/value. "
            "Must preserve every column and capture handwriting accurately."
        )
    )
    grand_total: Optional[float] = Field(
        None,
        description="Grand total amount due / balance if invoice or financial document"
    )
    currency: Optional[str] = Field(
        "$",
        description="Currency symbol or code (e.g. $, USD, EUR) if financial"
    )
    tax: Optional[float] = Field(
        None,
        description="Tax or VAT amount if invoice"
    )
    notes: Optional[str] = Field(
        None,
        description="Follow-up notes, audit remarks, payment terms, or handwriting observations"
    )

    # Legacy invoice compatibility properties
    @property
    def merchant(self) -> str:
        return self.title

    @property
    def invoice_no(self) -> Optional[str]:
        return self.reference_no

    @property
    def line_items(self) -> List[LineItemSchema]:
        """Convert rows into LineItemSchema objects for backward compatibility."""
        items = []
        for r in self.rows:
            # Try to identify description
            desc = (
                r.get("Description") or r.get("Item Description") or r.get("Item") or
                r.get("Product") or r.get("Code") or next(iter(r.values()), "Item")
            )
            # Try to identify quantity
            qty_val = (
                r.get("Quantity") or r.get("Qty") or r.get("Count") or
                r.get("Physical Count") or r.get("Book Qty") or "1"
            )
            try:
                qty = float(str(qty_val).replace(",", "").replace("$", ""))
            except (ValueError, TypeError):
                qty = 1.0

            # Try to identify unit price
            up_val = r.get("Unit Price") or r.get("Price") or r.get("Rate") or "0"
            try:
                up = float(str(up_val).replace(",", "").replace("$", ""))
            except (ValueError, TypeError):
                up = 0.0

            # Try to identify total price or variance
            tot_val = (
                r.get("Total") or r.get("Total Price") or r.get("Amount") or
                r.get("Variance") or r.get("Diff") or "0"
            )
            try:
                tot = float(str(tot_val).replace(",", "").replace("$", "").replace("+", ""))
            except (ValueError, TypeError):
                tot = qty * up

            items.append(LineItemSchema(
                description=str(desc),
                quantity=qty,
                unit_price=up,
                total_price=tot
            ))
        return items


# Backward compatibility alias
InvoiceData = ParsedDocumentData


# -------------------------------------------------------------
# API Response Schemas
# -------------------------------------------------------------
class LineItemResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    document_id: int
    description: str
    quantity: float
    unit_price: float
    total_price: float


class DocumentResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    filename: str
    file_path: str
    content_type: str
    doc_type: Optional[str] = "invoice"
    merchant: Optional[str]
    title: Optional[str] = None
    date: Optional[str]
    invoice_no: Optional[str]
    reference_no: Optional[str] = None
    inspector: Optional[str] = None
    columns: List[str] = Field(default_factory=list)
    rows: List[Dict[str, Any]] = Field(default_factory=list)
    grand_total: Optional[float]
    currency: Optional[str]
    tax: Optional[float]
    notes: Optional[str] = None
    created_at: Optional[datetime]
    line_items: List[LineItemResponse]


class ParseResponse(BaseModel):
    success: bool
    message: str
    document: DocumentResponse
    parsed_data: ParsedDocumentData
