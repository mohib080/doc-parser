"""
Database connection and session handling.
"""
import os
from typing import Optional
import hashlib
from sqlalchemy import create_engine, text, inspect
from sqlalchemy.orm import declarative_base, sessionmaker, Session, joinedload

DATABASE_URL = os.environ.get("DATABASE_URL", "sqlite:///./doc_parser.db")

# connect_args={"check_same_thread": False} is required for SQLite in FastAPI
connect_args = {"check_same_thread": False} if DATABASE_URL.startswith("sqlite") else {}

engine = create_engine(DATABASE_URL, connect_args=connect_args)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()


def init_db():
    """Create tables and ensure file_hash column & index exist with automatic backfill."""
    Base.metadata.create_all(bind=engine)
    try:
        with engine.connect() as conn:
            # Check existing columns in documents table
            res = conn.execute(text("PRAGMA table_info(documents);"))
            columns = [row[1] for row in res.fetchall()]
            if columns and "file_hash" not in columns:
                conn.execute(text("ALTER TABLE documents ADD COLUMN file_hash VARCHAR(64);"))
                conn.execute(text("CREATE INDEX IF NOT EXISTS ix_documents_file_hash ON documents (file_hash);"))
                conn.commit()

        # Backfill hash for existing records if their file exists on disk
        from .models import Document
        with SessionLocal() as session:
            unhashed_docs = session.query(Document).filter(
                (Document.file_hash == None) | (Document.file_hash == "")
            ).all()
            for d in unhashed_docs:
                if d.file_path and os.path.exists(d.file_path):
                    try:
                        with open(d.file_path, "rb") as f:
                            d.file_hash = hashlib.sha256(f.read()).hexdigest()
                    except Exception:
                        pass
            session.commit()
    except Exception as e:
        # Table might not exist yet or non-sqlite DB
        pass


def get_document_by_hash(file_hash: str, db: Optional[Session] = None):
    """
    Lookup an existing document and its line items by SHA-256 hash.
    Returns the Document instance or None.
    """
    if not file_hash:
        return None

    from .models import Document
    if db is not None:
        return (
            db.query(Document)
            .options(joinedload(Document.line_items))
            .filter(Document.file_hash == file_hash)
            .order_by(Document.id.desc())
            .first()
        )

    with SessionLocal() as session:
        doc = (
            session.query(Document)
            .options(joinedload(Document.line_items))
            .filter(Document.file_hash == file_hash)
            .order_by(Document.id.desc())
            .first()
        )
        if doc:
            session.expunge_all()
        return doc


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

