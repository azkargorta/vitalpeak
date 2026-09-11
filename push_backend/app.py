import json
import os
import sqlite3
from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo

from fastapi import FastAPI, Header, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from pywebpush import WebPushException, webpush

DB_PATH = Path(os.getenv("PUSH_DB_PATH", "push_backend/push.db"))
VAPID_PUBLIC_KEY = os.getenv("VAPID_PUBLIC_KEY", "")
VAPID_PRIVATE_KEY = os.getenv("VAPID_PRIVATE_KEY", "")
VAPID_SUBJECT = os.getenv("VAPID_SUBJECT", "mailto:admin@example.com")
CRON_SECRET = os.getenv("CRON_SECRET", "")
ALLOWED_ORIGINS = [x.strip() for x in os.getenv("ALLOWED_ORIGINS", "*").split(",") if x.strip()]

app = FastAPI(title="VitalPeak Push API")
app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS if ALLOWED_ORIGINS != ["*"] else ["*"],
    allow_credentials=False,
    allow_methods=["GET", "POST", "DELETE"],
    allow_headers=["*"],
)


def db():
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS subscriptions (
            endpoint TEXT PRIMARY KEY,
            subscription_json TEXT NOT NULL,
            reminder_time TEXT NOT NULL,
            timezone TEXT NOT NULL,
            training_dates_json TEXT NOT NULL,
            enabled INTEGER NOT NULL DEFAULT 1,
            last_sent_date TEXT,
            updated_at TEXT NOT NULL
        )
        """
    )
    return conn


class SubscribePayload(BaseModel):
    subscription: dict
    reminder_time: str = Field(pattern=r"^\d{2}:\d{2}$")
    timezone: str
    training_dates: list[str] = []
    enabled: bool = True


class UnsubscribePayload(BaseModel):
    endpoint: str


@app.get("/health")
def health():
    return {"ok": True}


@app.get("/api/push/public-key")
def public_key():
    if not VAPID_PUBLIC_KEY:
        raise HTTPException(503, "VAPID public key not configured")
    return {"publicKey": VAPID_PUBLIC_KEY}


@app.post("/api/push/subscribe")
def subscribe(payload: SubscribePayload):
    endpoint = payload.subscription.get("endpoint")
    if not endpoint:
        raise HTTPException(400, "Missing subscription endpoint")
    conn = db()
    conn.execute(
        """
        INSERT INTO subscriptions (
            endpoint, subscription_json, reminder_time, timezone,
            training_dates_json, enabled, updated_at
        ) VALUES (?, ?, ?, ?, ?, ?, ?)
        ON CONFLICT(endpoint) DO UPDATE SET
            subscription_json=excluded.subscription_json,
            reminder_time=excluded.reminder_time,
            timezone=excluded.timezone,
            training_dates_json=excluded.training_dates_json,
            enabled=excluded.enabled,
            updated_at=excluded.updated_at
        """,
        (
            endpoint,
            json.dumps(payload.subscription),
            payload.reminder_time,
            payload.timezone,
            json.dumps(payload.training_dates),
            1 if payload.enabled else 0,
            datetime.utcnow().isoformat(),
        ),
    )
    conn.commit()
    conn.close()
    return {"ok": True}


@app.delete("/api/push/unsubscribe")
def unsubscribe(payload: UnsubscribePayload):
    conn = db()
    conn.execute("DELETE FROM subscriptions WHERE endpoint=?", (payload.endpoint,))
    conn.commit()
    conn.close()
    return {"ok": True}


def due_now(row):
    try:
        tz = ZoneInfo(row["timezone"])
    except Exception:
        tz = ZoneInfo("UTC")
    now = datetime.now(tz)
    today = now.date().isoformat()
    if not row["enabled"] or row["last_sent_date"] == today:
        return False, today
    try:
        training_dates = set(json.loads(row["training_dates_json"] or "[]"))
    except Exception:
        training_dates = set()
    if today not in training_dates:
        return False, today
    try:
        hh, mm = [int(x) for x in row["reminder_time"].split(":", 1)]
    except Exception:
        return False, today
    return (now.hour, now.minute) >= (hh, mm), today


def send_push(subscription):
    if not VAPID_PRIVATE_KEY:
        raise RuntimeError("VAPID_PRIVATE_KEY is not configured")
    payload = json.dumps(
        {
            "title": "Hoy tienes entrenamiento",
            "body": "Tienes un entrenamiento programado en VitalPeak. ¡A por ello!",
            "url": "./",
            "tag": "vitalpeak-training",
        }
    )
    webpush(
        subscription_info=subscription,
        data=payload,
        vapid_private_key=VAPID_PRIVATE_KEY,
        vapid_claims={"sub": VAPID_SUBJECT},
    )


@app.post("/api/push/send-due")
def send_due(x_cron_secret: str | None = Header(default=None)):
    if CRON_SECRET and x_cron_secret != CRON_SECRET:
        raise HTTPException(401, "Invalid cron secret")
    conn = db()
    rows = conn.execute("SELECT * FROM subscriptions").fetchall()
    sent = 0
    removed = 0
    errors = 0
    for row in rows:
        is_due, today = due_now(row)
        if not is_due:
            continue
        try:
            subscription = json.loads(row["subscription_json"])
            send_push(subscription)
            conn.execute(
                "UPDATE subscriptions SET last_sent_date=? WHERE endpoint=?",
                (today, row["endpoint"]),
            )
            sent += 1
        except WebPushException as exc:
            status = getattr(getattr(exc, "response", None), "status_code", None)
            if status in (404, 410):
                conn.execute("DELETE FROM subscriptions WHERE endpoint=?", (row["endpoint"],))
                removed += 1
            else:
                errors += 1
        except Exception:
            errors += 1
    conn.commit()
    conn.close()
    return {"ok": True, "sent": sent, "removed": removed, "errors": errors}
