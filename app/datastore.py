from __future__ import annotations
import json, os, time, secrets, base64, hashlib, hmac
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, Any, Optional

BASE_DIR = Path(".")
USERS_DIR = BASE_DIR / "usuarios_data"
RESET_DIR = USERS_DIR

TABLE_USERS = "user_accounts"
TABLE_RESETS = "password_resets"


def _sb():
    """Cliente Supabase o None si no hay secrets / paquete."""
    try:
        from app.supabase_utils import get_supabase_client

        return get_supabase_client()
    except Exception:
        return None


def using_cloud_db() -> bool:
    return _sb() is not None


def ensure_base_dirs() -> None:
    USERS_DIR.mkdir(parents=True, exist_ok=True)

def user_json_path(username: str) -> Path:
    return USERS_DIR / f"{username}.json"

def _reset_token_path(username: str) -> Path:
    return RESET_DIR / f"{username}.reset.json"


def _empty_user(*, password: str = "", email: Optional[str] = None) -> Dict[str, Any]:
    return {
        "password": password,
        "email": email,
        "recovery_email": email,
        "profile": {},
        "entrenamientos": [],
        "rutinas": [],
        "custom_exercises": [],
        "exercise_meta": {},
        "weights": [],
        "objetivos": {"dias_semana": 3, "peso_objetivo": None, "ejercicios": {}},
    }


def _load_user_sb(sb, username: str) -> Optional[Dict[str, Any]]:
    try:
        res = sb.table(TABLE_USERS).select("data").eq("username", username).limit(1).execute()
        rows = res.data or []
        if not rows:
            res = (
                sb.table(TABLE_USERS)
                .select("data")
                .eq("username_norm", username.lower())
                .limit(1)
                .execute()
            )
            rows = res.data or []
        if not rows:
            return None
        data = rows[0].get("data")
        return dict(data) if isinstance(data, dict) else None
    except Exception:
        return None


def _canonical_username(sb, username: str) -> str:
    res = sb.table(TABLE_USERS).select("username").eq("username", username).limit(1).execute()
    rows = res.data or []
    if rows:
        return str(rows[0]["username"])
    res = (
        sb.table(TABLE_USERS)
        .select("username")
        .eq("username_norm", username.lower())
        .limit(1)
        .execute()
    )
    rows = res.data or []
    if rows:
        return str(rows[0]["username"])
    return username


def _save_user_sb(sb, username: str, data: Dict[str, Any]) -> None:
    key = _canonical_username(sb, username)
    payload = {
        "username": key,
        "username_norm": key.lower(),
        "data": data,
        "updated_at": datetime.now(timezone.utc).isoformat(),
    }
    sb.table(TABLE_USERS).upsert(payload, on_conflict="username").execute()


def load_user(username: str) -> Optional[Dict[str, Any]]:
    sb = _sb()
    if sb is not None:
        return _load_user_sb(sb, username)

    ensure_base_dirs()
    p = user_json_path(username)
    if not p.exists():
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
    """Guarda el documento del usuario (Supabase si hay secrets; si no, JSON local)."""
    sb = _sb()
    if sb is not None:
        _save_user_sb(sb, username, data)
        return

    ensure_base_dirs()
    p = user_json_path(username)
    payload = json.dumps(data, ensure_ascii=False, indent=2)
    tmp = p.with_suffix(p.suffix + f".tmp.{os.getpid()}")
    last_err: Exception | None = None
    for attempt in range(8):
        try:
            tmp.write_text(payload, encoding="utf-8")
            os.replace(tmp, p)
            return
        except PermissionError as e:
            last_err = e
            time.sleep(0.05 * (attempt + 1))
        except OSError as e:
            last_err = e
            time.sleep(0.05 * (attempt + 1))
        finally:
            if tmp.exists():
                try:
                    tmp.unlink()
                except Exception:
                    pass
    # Último intento directo (mensaje más claro si falla)
    try:
        p.write_text(payload, encoding="utf-8")
    except PermissionError as e:
        raise PermissionError(
            f"No se pudo escribir {p}. Cierra otras instancias de Streamlit/OneDrive "
            f"o espera a que sincronice, e inténtalo de nuevo. Detalle: {e}"
        ) from (last_err or e)

def ensure_user(username: str) -> Dict[str, Any]:
    d = load_user(username)
    if d:
        return d
    data = _empty_user()
    save_user(username, data)
    return data

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
    if _looks_pbkdf2(stored):
        return _pbkdf2_verify(password, stored)
    if _looks_sha256_hex(stored):
        return _sha256_hex(password) == stored
    return stored == password

def register_user(username: str, password: str, email: Optional[str]=None) -> bool:
    if load_user(username):
        return False
    data = _empty_user(password=_pbkdf2_hash(password), email=email)
    save_user(username, data)
    return True

def set_account_email(username: str, email: str) -> None:
    d = ensure_user(username)
    d["email"] = email
    d.setdefault("recovery_email", email)
    save_user(username, d)

def set_recovery_email(username: str, email: str) -> None:
    d = ensure_user(username)
    d["recovery_email"] = email
    save_user(username, d)

def get_emails_for_user(username: str) -> dict:
    d = load_user(username) or {}
    return {"email": d.get("email"), "recovery_email": d.get("recovery_email")}


def resolve_login_identifier(identifier: str) -> Optional[str]:
    """Devuelve el username canónico a partir de usuario o email."""
    ident = (identifier or "").strip()
    if not ident:
        return None
    if load_user(ident):
        sb = _sb()
        if sb is not None:
            return _canonical_username(sb, ident)
        return ident

    ident_l = ident.lower()
    sb = _sb()
    if sb is not None:
        try:
            res = sb.table(TABLE_USERS).select("username,data").execute()
            for row in res.data or []:
                data = row.get("data") or {}
                emails = [
                    str(data.get("email") or "").strip().lower(),
                    str(data.get("recovery_email") or "").strip().lower(),
                ]
                if ident_l in emails:
                    return str(row.get("username"))
        except Exception:
            return None
        return None

    ensure_base_dirs()
    for p in USERS_DIR.glob("*.json"):
        if p.name.endswith(".reset.json"):
            continue
        try:
            d = json.loads(p.read_text(encoding="utf-8"))
        except Exception:
            continue
        emails = [
            str(d.get("email") or "").strip().lower(),
            str(d.get("recovery_email") or "").strip().lower(),
        ]
        if ident_l in emails:
            return p.stem
    return None


def set_profile(username: str, profile: dict) -> None:
    d = ensure_user(username)
    d["profile"] = profile or {}
    save_user(username, d)

def create_password_reset(username: str, *, ttl_seconds: int = 3600) -> dict | None:
    if not load_user(username):
        return None
    token = secrets.token_urlsafe(24)
    payload = {"token": token, "expires_at": int(time.time()) + ttl_seconds}
    sb = _sb()
    if sb is not None:
        key = _canonical_username(sb, username)
        sb.table(TABLE_RESETS).upsert(
            {"username": key, "token": token, "expires_at": payload["expires_at"]},
            on_conflict="username",
        ).execute()
        return payload
    _reset_token_path(username).write_text(json.dumps(payload), encoding="utf-8")
    return payload

def get_password_reset(username: str) -> dict | None:
    sb = _sb()
    if sb is not None:
        key = _canonical_username(sb, username)
        res = sb.table(TABLE_RESETS).select("token,expires_at").eq("username", key).limit(1).execute()
        rows = res.data or []
        return rows[0] if rows else None
    p = _reset_token_path(username)
    if not p.exists():
        return None
    try:
        return json.loads(p.read_text(encoding="utf-8"))
    except Exception:
        return None

def clear_password_reset(username: str) -> None:
    sb = _sb()
    if sb is not None:
        key = _canonical_username(sb, username)
        sb.table(TABLE_RESETS).delete().eq("username", key).execute()
        return
    p = _reset_token_path(username)
    if p.exists():
        p.unlink()

def exercise_image_dir(username: str | None = None) -> Path:
    ensure_base_dirs()
    base = BASE_DIR / "exercise_images"
    if username:
        base = base / username
    base.mkdir(parents=True, exist_ok=True)
    return base
