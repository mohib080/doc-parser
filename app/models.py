"""
SQLAlchemy models for Document and LineItem tables.
Supports dynamic column/row JSON storage alongside standard relational fields.
"""
import json
from datetime import datetime
from sqlalchemy import Column, Integer, String, Float, DateTime, ForeignKey, Text
from sqlalchemy.orm import relationship
from .database import Base


class Document(Base):
    __tablename__ = "documents"

    id = Column(Integer, primary_key=True, index=True)
    filename = Column(String(255), nullable=False)
    file_path = Column(String(500), nullable=False)
    content_type = Column(String(100), nullable=False)
    file_hash = Column(String(64), index=True, nullable=True)  # SHA-256 hex digest for caching

    # Document type & headers
    doc_type = Column(String(50), nullable=True, default="invoice")
    merchant = Column(String(255), nullable=True, default="Unknown Merchant")
    invoice_date = Column(String(50), nullable=True)
    invoice_no = Column(String(100), nullable=True)
    inspector = Column(String(255), nullable=True)

    # Dynamic table structure stored as JSON
    columns_json = Column(Text, nullable=True)
    rows_json = Column(Text, nullable=True)

    # Financial / summary totals
    grand_total = Column(Float, nullable=True, default=0.0)
    currency = Column(String(20), nullable=True, default="$")
    tax = Column(Float, nullable=True, default=0.0)
    notes = Column(Text, nullable=True)
    raw_text = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    # One-to-many relationship with line items
    line_items = relationship(
        "LineItem",
        back_populates="document",
        cascade="all, delete-orphan",
        order_by="LineItem.id"
    )

    def to_dict(self):
        try:
            cols = json.loads(self.columns_json) if self.columns_json else []
        except Exception:
            cols = []
        try:
            rows = json.loads(self.rows_json) if self.rows_json else []
        except Exception:
            rows = []

        return {
            "id": self.id,
            "filename": self.filename,
            "file_path": self.file_path,
            "content_type": self.content_type,
            "file_hash": self.file_hash,
            "doc_type": self.doc_type or "invoice",
            "merchant": self.merchant,
            "title": self.merchant,
            "date": self.invoice_date,
            "invoice_no": self.invoice_no,
            "reference_no": self.invoice_no,
            "inspector": self.inspector,
            "columns": cols,
            "rows": rows,
            "grand_total": self.grand_total,
            "currency": self.currency,
            "tax": self.tax,
            "notes": self.notes,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "line_items": [item.to_dict() for item in self.line_items],
        }


class LineItem(Base):
    __tablename__ = "line_items"

    id = Column(Integer, primary_key=True, index=True)
    document_id = Column(Integer, ForeignKey("documents.id", ondelete="CASCADE"), nullable=False)
    description = Column(String(500), nullable=False)
    quantity = Column(Float, nullable=False, default=1.0)
    unit_price = Column(Float, nullable=False, default=0.0)
    total_price = Column(Float, nullable=False, default=0.0)

    document = relationship("Document", back_populates="line_items")

    def to_dict(self):
        return {
            "id": self.id,
            "document_id": self.document_id,
            "description": self.description,
            "quantity": self.quantity,
            "unit_price": self.unit_price,
            "total_price": self.total_price,
        }
