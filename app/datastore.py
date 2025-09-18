from __future__ import annotations
import json
from pathlib import Path
from typing import Dict

BASE_DIR = Path(".")
USERS_DIR = BASE_DIR / "usuarios_data"


def ensure_base_dirs() -> None:
    USERS_DIR.mkdir(parents=True, exist_ok=True)


def user_json_path(username: str) -> Path:
    return USERS_DIR / f"{username}.json"


def ensure_user(username: str) -> Dict:
    ensure_base_dirs()
    path = user_json_path(username)
    if not path.exists():
        data = {
            "password": "",
            "entrenamientos": [],
            "rutinas": [],
            "custom_exercises": [],
            "exercise_meta": {},
            "weights": [],
        }
        path.write_text(json.dumps(data, indent=2, ensure_ascii=False), encoding="utf-8")
        return json.loads(path.read_text(encoding="utf-8"))


def load_user(username: str) -> Dict:
    ensure_base_dirs()
    path = user_json_path(username)
    if not path.exists():
        raise FileNotFoundError(f"User {username} does not exist.")
        return json.loads(path.read_text(encoding="utf-8"))


def save_user(username: str, data: Dict) -> None:
    ensure_base_dirs()
    path = user_json_path(username)
    path.write_text(json.dumps(data, indent=2, ensure_ascii=False), encoding="utf-8")


def register_user(username: str, password: str) -> bool:
    ensure_base_dirs()
    path = user_json_path(username)
    if path.exists():
        return False
    data = ensure_user(username)
    data["password"] = password  # NOTE: plaintext; cambia a hash si lo publicas
    save_user(username, data)
    return True


def authenticate(username: str, password: str) -> bool:
    try:
        data = load_user(username)
    except FileNotFoundError:
        return False
        return data.get("password", "") == password


def exercise_image_dir(username: str) -> Path:
    d = USERS_DIR / username / "exercise_images"
    d.mkdir(parents=True, exist_ok=True)
    return d


# === Auth/Profile/Reset extensions ===
from typing import Dict
import json
from pathlib import Path
import streamlit as st

def load_user(username: str) -> Dict:
    p = user_json_path(username)
    if not p.exists():
        raise FileNotFoundError(username)
        return json.loads(p.read_text(encoding="utf-8"))

def save_user(username: str, data: Dict) -> None:
    ensure_base_dirs()
    p = user_json_path(username)
    p.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")

def register_user(username: str, password: str, email: str | None = None) -> bool:
    ensure_base_dirs()
    p = user_json_path(username)
    if p.exists():
        return False
    data = {"username": username, "password": password}
    if email:
        data["email"] = email
        data["recovery_email"] = email
    save_user(username, data)
    return True

def set_password(username: str, new_password: str) -> None:
    data = load_user(username)
    data["password"] = new_password
    save_user(username, data)

def set_account_email(username: str, new_email: str) -> None:
    data = load_user(username)
    data["email"] = new_email
    save_user(username, data)

def set_recovery_email(username: str, new_email: str) -> None:
    data = load_user(username)
    data["recovery_email"] = new_email
    save_user(username, data)

def get_emails_for_user(username: str):
    try:
        data = load_user(username)
        return data.get("email"), data.get("recovery_email") or data.get("email")
    except FileNotFoundError:
        return None, None

def set_profile(username: str, profile: dict) -> None:
    data = load_user(username)
    data["profile"] = profile
    save_user(username, data)

def _reset_token_path(username: str) -> Path:
    return USERS_DIR / f"{username}.reset.json"

def create_password_reset(username: str, token: str, ttl_seconds: int = 3600) -> dict:
    pl = {"token": token, "expires_at": int(__import__("time").time()) + ttl_seconds}
    _reset_token_path(username).write_text(json.dumps(pl, ensure_ascii=False, indent=2), encoding="utf-8")
    return pl

def get_password_reset(username: str) -> dict | None:
    p = _reset_token_path(username)
    if not p.exists():
        return None
    try:
        return json.loads(p.read_text(encoding="utf-8"))
    except Exception:
        return None

def clear_password_reset(username: str) -> None:
    p = _reset_token_path(username)
    if p.exists():
        p.unlink()