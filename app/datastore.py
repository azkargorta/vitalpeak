from __future__ import annotations
import json, os, time, secrets, base64, hashlib, hmac
from pathlib import Path
from typing import Dict, Any, Optional

BASE_DIR = Path(".")
USERS_DIR = BASE_DIR / "usuarios_data"
RESET_DIR = USERS_DIR  # store reset tokens alongside user files

def ensure_base_dirs() -> None:
    USERS_DIR.mkdir(parents=True, exist_ok=True)

def user_json_path(username: str) -> Path:
    return USERS_DIR / f"{username}.json"

def _reset_token_path(username: str) -> Path:
    return RESET_DIR / f"{username}.reset.json"

def load_user(username: str) -> Optional[Dict[str, Any]]:
    ensure_base_dirs()
    p = user_json_path(username)
    if not p.exists():
        # fallback: lowercased (por si el registro lo guardó en minúsculas)
        pl = user_json_path(username.lower())
        if pl.exists():
            try:
                return json.loads(pl.read_text(encoding="utf-8"))
            except Exception:
                return None
        return None
    try:
        return json.loads(p.read_text(encoding="utf-8"))
    except Exception:
        return None

def save_user(username: str, data: Dict[str, Any]) -> None:
    ensure_base_dirs()
    p = user_json_path(username)
    p.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")

def ensure_user(username: str) -> Dict[str, Any]:
    ensure_base_dirs()
    p = user_json_path(username)
    if not p.exists():
        data = {
            "password": "",
            "email": None,
            "recovery_email": None,
            "entrenamientos": [],
            "rutinas": [],
            "custom_exercises": [],
            "exercise_meta": {},
            "weights": [],
        }
        save_user(username, data)
        return data
    d = load_user(username) or {}
    return d

def _pbkdf2_hash(password: str, *, iterations: int = 310_000) -> str:
    salt = secrets.token_bytes(16)
    dk = hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), salt, iterations)
    return "pbkdf2$sha256${it}${salt}${hash}".format(
        it=iterations,
        salt=base64.b64encode(salt).decode("ascii"),
        hash=base64.b64encode(dk).decode("ascii"),
    )

def _pbkdf2_verify(password: str, encoded: str) -> bool:
    try:
        scheme, algo, it_s, salt_b64, hash_b64 = encoded.split("$", 4)
        if scheme != "pbkdf2" or algo != "sha256":
            return False
        iterations = int(it_s)
        salt = base64.b64decode(salt_b64.encode("ascii"))
        expected = base64.b64decode(hash_b64.encode("ascii"))
        dk = hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), salt, iterations)
        # constant time compare
        return hmac.compare_digest(dk, expected)
    except Exception:
        return False

def _looks_pbkdf2(s: str) -> bool:
    return isinstance(s, str) and s.startswith("pbkdf2$")

def _looks_sha256_hex(s: str) -> bool:
    if not isinstance(s, str) or len(s) != 64: return False
    try:
        int(s, 16)
        return True
    except Exception:
        return False

def _sha256_hex(password: str) -> str:
    return hashlib.sha256(password.encode("utf-8")).hexdigest()

def set_password(username: str, new_password: str) -> None:
    d = ensure_user(username)
    d["password"] = _pbkdf2_hash(new_password)
    save_user(username, d)

def authenticate(username: str, password: str) -> bool:
    d = load_user(username)
    if not d: 
        return False
    stored = d.get("password", "")
    # Soportar formatos antiguos: texto plano o sha256 hex
    if _looks_pbkdf2(stored):
        return _pbkdf2_verify(password, stored)
    if _looks_sha256_hex(stored):
        return _sha256_hex(password) == stored
    # texto plano (compatibilidad)
    return stored == password

def register_user(username: str, password: str, email: Optional[str]=None) -> bool:
    ensure_base_dirs()
    p = user_json_path(username)
    if p.exists():
        return False
    data = {
        "password": _pbkdf2_hash(password),
        "email": email,
        "recovery_email": email,
        "entrenamientos": [],
        "rutinas": [],
        "custom_exercises": [],
        "exercise_meta": {},
        "weights": [],
    }
    save_user(username, data)
    return True

def set_account_email(username: str, email: str) -> None:
    d = ensure_user(username)
    d["email"] = email
    d.setdefault("recovery_email", email)
    save_user(username, d)

def create_password_reset(username: str, *, ttl_seconds: int = 3600) -> dict | None:
    # Crea un token de reinicio y lo persiste
    if not load_user(username):
        return None
    token = secrets.token_urlsafe(24)
    payload = {"token": token, "expires_at": int(time.time()) + ttl_seconds}
    _reset_token_path(username).write_text(json.dumps(payload), encoding="utf-8")
    return payload

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
