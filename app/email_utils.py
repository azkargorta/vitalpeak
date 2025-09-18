
from __future__ import annotations
import os, smtplib
from email.message import EmailMessage
from typing import Optional, Tuple

def send_email(to_email: str, subject: str, html: str, text: Optional[str] = None) -> Tuple[bool, str]:
    host = os.getenv("SMTP_HOST")
    port = int(os.getenv("SMTP_PORT", "587"))
    user = os.getenv("SMTP_USER")
    password = os.getenv("SMTP_PASS")
    sender = os.getenv("SMTP_FROM", user or "no-reply@example.com")

    if not host or not user or not password:
        return False, "SMTP no configurado (SMTP_HOST/SMTP_PORT/SMTP_USER/SMTP_PASS)."

    msg = EmailMessage()
    msg["Subject"] = subject
    msg["From"] = sender
    msg["To"] = to_email
    if text:
        msg.set_content(text)
    msg.add_alternative(html, subtype="html")

    try:
        with smtplib.SMTP(host, port) as server:
            server.starttls()
            server.login(user, password)
            server.send_message(msg)
            return True, "Email enviado"
    except Exception as e:
        return False, f"Fallo enviando email: {e}"
