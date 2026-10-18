"""
Pydantic schemas for LLM structured output and API endpoints.
"""
from datetime import datetime
from typing import List, Optional
from pydantic import BaseModel, Field, ConfigDict


# -------------------------------------------------------------
# Structured LLM Output Schemas
# -------------------------------------------------------------
class LineItemSchema(BaseModel):
    description: str = Field(..., description="Description or product/service name")
    quantity: float = Field(default=1.0, description="Quantity or unit count")
    unit_price: float = Field(default=0.0, description="Price per individual unit")
    total_price: float = Field(default=0.0, description="Total amount for this line item")


class InvoiceData(BaseModel):
    merchant: str = Field(..., description="Merchant, vendor, or seller business name")
    date: Optional[str] = Field(None, description="Invoice or receipt date (e.g. YYYY-MM-DD or readable text)")
    invoice_no: Optional[str] = Field(None, description="Invoice or reference number (e.g. INV-2024-001)")
    line_items: List[LineItemSchema] = Field(
        default_factory=list,
        description="Individual line items extracted from the document"
    )
    grand_total: Optional[float] = Field(None, description="Final grand total / amount due")
    currency: Optional[str] = Field("$", description="Currency symbol or code (e.g. $, USD, EUR)")
    tax: Optional[float] = Field(None, description="Tax or VAT amount if identified")
    notes: Optional[str] = Field(None, description="Any payment notes, terms, or memo")


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
    merchant: Optional[str]
    date: Optional[str]
    invoice_no: Optional[str]
    grand_total: Optional[float]
    currency: Optional[str]
    tax: Optional[float]
    created_at: Optional[datetime]
    line_items: List[LineItemResponse]


class ParseResponse(BaseModel):
    success: bool
    message: str
    document: DocumentResponse
    parsed_data: InvoiceData
