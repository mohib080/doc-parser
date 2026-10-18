"""
SQLAlchemy models for Document and LineItem tables.
"""
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
    merchant = Column(String(255), nullable=True, default="Unknown Merchant")
    invoice_date = Column(String(50), nullable=True)
    invoice_no = Column(String(100), nullable=True)
    grand_total = Column(Float, nullable=True, default=0.0)
    currency = Column(String(20), nullable=True, default="$")
    tax = Column(Float, nullable=True, default=0.0)
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
        return {
            "id": self.id,
            "filename": self.filename,
            "file_path": self.file_path,
            "content_type": self.content_type,
            "merchant": self.merchant,
            "date": self.invoice_date,
            "invoice_no": self.invoice_no,
            "grand_total": self.grand_total,
            "currency": self.currency,
            "tax": self.tax,
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
