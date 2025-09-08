# app/pdf_store.py
from typing import List, Optional, Dict
import os
from sqlalchemy import create_engine, Column, Integer, String, LargeBinary, DateTime, func
from sqlalchemy.orm import declarative_base, sessionmaker

DB_URL = os.getenv("DATABASE_URL") or "sqlite:///routines.db"
engine = create_engine(DB_URL, pool_pre_ping=True)
SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False)
Base = declarative_base()

class PDFDoc(Base):
    __tablename__ = "pdf_docs"
    id = Column(Integer, primary_key=True)
    user = Column(String(100), nullable=False)
    title = Column(String(255), nullable=False)
    size = Column(Integer, nullable=False)
    content = Column(LargeBinary, nullable=False)
    created_at = Column(DateTime, server_default=func.now())

def init_db():
    Base.metadata.create_all(bind=engine)

def save_pdf(user: str, title: str, content: bytes) -> int:
    init_db()
    db = SessionLocal()
    try:
        row = PDFDoc(user=user or "default", title=title.strip() or "Plan", size=len(content), content=content)
        db.add(row)
        db.commit()
        db.refresh(row)
        return row.id
    finally:
        db.close()

def list_pdfs(user: Optional[str] = None, limit: int = 200) -> List[Dict]:
    init_db()
    db = SessionLocal()
    try:
        q = db.query(PDFDoc).order_by(PDFDoc.id.desc())
        if user:
            q = q.filter(PDFDoc.user == user)
        rows = q.limit(limit).all()
        return [{
            "id": r.id,
            "user": r.user,
            "title": r.title,
            "size": r.size,
            "created_at": r.created_at.isoformat() if r.created_at else None
        } for r in rows]
    finally:
        db.close()

def get_pdf_content(doc_id: int) -> Optional[bytes]:
    init_db()
    db = SessionLocal()
    try:
        r = db.query(PDFDoc).filter(PDFDoc.id == doc_id).first()
        return r.content if r else None
    finally:
        db.close()

def delete_pdf(doc_id: int) -> bool:
    init_db()
    db = SessionLocal()
    try:
        r = db.query(PDFDoc).filter(PDFDoc.id == doc_id).first()
        if not r:
            return False
        db.delete(r)
        db.commit()
        return True
    finally:
        db.close()

def update_title(doc_id: int, new_title: str) -> bool:
    init_db()
    db = SessionLocal()
    try:
        r = db.query(PDFDoc).filter(PDFDoc.id == doc_id).first()
        if not r:
            return False
        r.title = new_title.strip() or r.title
        db.commit()
        return True
    finally:
        db.close()
