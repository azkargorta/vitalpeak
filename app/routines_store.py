import os, json
from typing import List, Dict, Any, Optional
from sqlalchemy import create_engine, Column, Integer, String, Text, DateTime, func
from sqlalchemy.orm import sessionmaker, declarative_base

DB_URL = os.getenv("DATABASE_URL") or "sqlite:///routines.db"
engine = create_engine(DB_URL, pool_pre_ping=True)
SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False)
Base = declarative_base()

class RoutinePlan(Base):
    __tablename__ = "routine_plans"
    id = Column(Integer, primary_key=True)
    title = Column(String(200), nullable=False)
    weeks = Column(Integer, default=4)
    plan_json = Column(Text, nullable=False)
    schedule_json = Column(Text, nullable=False)
    created_at = Column(DateTime, server_default=func.now())

def init_db():
    Base.metadata.create_all(bind=engine)

def save_plan(title: str, weeks: int, plan: Dict[str, Any], schedule: List[Dict[str, Any]]) -> int:
    init_db()
    db = SessionLocal()
    try:
        item = RoutinePlan(
            title=title.strip(),
            weeks=int(weeks),
            plan_json=json.dumps(plan, ensure_ascii=False),
            schedule_json=json.dumps(schedule, ensure_ascii=False)
        )
        db.add(item)
        db.commit()
        db.refresh(item)
        return item.id
    finally:
        db.close()

def list_plans(limit: int = 50) -> List[Dict[str, Any]]:
    init_db()
    db = SessionLocal()
    try:
        rows = db.query(RoutinePlan).order_by(RoutinePlan.id.desc()).limit(limit).all()
        return [{
            "id": r.id,
            "title": r.title,
            "weeks": r.weeks,
            "created_at": r.created_at.isoformat() if r.created_at else None
        } for r in rows]
    finally:
        db.close()

def get_plan(plan_id: int) -> Optional[Dict[str, Any]]:
    init_db()
    db = SessionLocal()
    try:
        r = db.query(RoutinePlan).filter(RoutinePlan.id==plan_id).first()
        if not r:
            return None
        return {
            "id": r.id,
            "title": r.title,
            "weeks": r.weeks,
            "plan": json.loads(r.plan_json),
            "schedule": json.loads(r.schedule_json),
            "created_at": r.created_at.isoformat() if r.created_at else None
        }
    finally:
        db.close()

def delete_plan(plan_id: int) -> bool:
    init_db()
    db = SessionLocal()
    try:
        r = db.query(RoutinePlan).filter(RoutinePlan.id==plan_id).first()
        if not r:
            return False
        db.delete(r)
        db.commit()
        return True
    finally:
        db.close()

