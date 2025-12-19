from __future__ import annotations

import os
from typing import Any, Optional
from collections.abc import Mapping

try:
    import streamlit as st
except Exception:  # pragma: no cover
    st = None  # type: ignore

from supabase import create_client


def _get_secret(key: str, default: Optional[str] = None) -> Optional[str]:
    """Read from Streamlit secrets first (supporting nested TOML), then env vars.

    Streamlit Cloud secrets often end up either as top-level keys:
        SUPABASE_URL = "..."
    or nested tables:
        [supabase]
        url = "..."
        service_role_key = "..."

    This helper tries both, plus common aliases.
    """

    # --- Streamlit secrets
    if st is not None:
        try:
            secrets = st.secrets

            # 1) direct lookup (case-tolerant)
            for k in (key, key.upper(), key.lower()):
                if k in secrets:
                    v = secrets[k]
                    return str(v).strip() if v is not None else None

            # 2) nested lookup: [supabase] / [openai] patterns
            def _lookup_in_table(tbl: Mapping[str, Any], want: str) -> Optional[str]:
                # try exact key and simplified key (strip SUPABASE_ prefix)
                candidates = [want, want.lower(), want.upper()]
                simplified = want
                if simplified.upper().startswith("SUPABASE_"):
                    simplified = simplified.split("SUPABASE_", 1)[1]
                candidates += [simplified, simplified.lower(), simplified.upper()]

                # common aliases for service role key
                if want.upper() == "SUPABASE_SERVICE_ROLE_KEY":
                    candidates += [
                        "SERVICE_ROLE_KEY",
                        "service_role_key",
                        "SERVICE_KEY",
                        "service_key",
                        "KEY",
                        "key",
                    ]
                if want.upper() == "SUPABASE_URL":
                    candidates += ["url", "URL"]
                if want.upper() == "SUPABASE_BUCKET":
                    candidates += ["bucket", "BUCKET"]

                for c in candidates:
                    if c in tbl:
                        v = tbl[c]
                        return str(v).strip() if v is not None else None
                return None

            for section in ("supabase", "SUPABASE"):
                if section in secrets and isinstance(secrets[section], Mapping):
                    v = _lookup_in_table(secrets[section], key)
                    if v:
                        return v

            # 3) generic scan: sometimes people put everything under [secrets]
            for sect_name, sect_val in secrets.items():
                if isinstance(sect_val, Mapping):
                    v = _lookup_in_table(sect_val, key)
                    if v:
                        return v

        except Exception:
            pass

    # --- environment variables (local/dev)
    return (os.getenv(key) or default)


def get_supabase_client():
    url = _get_secret("SUPABASE_URL")
    # Accept common aliases: people often name this differently in secrets.
    key = (
        _get_secret("SUPABASE_SERVICE_ROLE_KEY")
        or _get_secret("SUPABASE_SERVICE_KEY")
        or _get_secret("SUPABASE_SERVICE_ROLE")
        or _get_secret("SUPABASE_KEY")
        or _get_secret("SUPABASE_ANON_KEY")
    )
    if not url or not key:
        return None
    return create_client(str(url).strip(), str(key).strip())


def supabase_config_status() -> dict[str, Any]:
    """Return a safe, non-sensitive view of whether Supabase config is present."""
    url = _get_secret("SUPABASE_URL")
    key = (
        _get_secret("SUPABASE_SERVICE_ROLE_KEY")
        or _get_secret("SUPABASE_SERVICE_KEY")
        or _get_secret("SUPABASE_KEY")
        or _get_secret("SUPABASE_ANON_KEY")
    )
    bucket = _get_secret("SUPABASE_BUCKET")
    keys_present: list[str] = []
    if st is not None:
        try:
            keys_present = sorted([str(k) for k in st.secrets.keys()])
        except Exception:
            keys_present = []
    return {
        "has_url": bool(url and str(url).strip()),
        "has_key": bool(key and str(key).strip()),
        "has_bucket": bool(bucket and str(bucket).strip()),
        "secrets_keys": keys_present,
    }


def get_supabase_bucket(default: str = "posture") -> str:
    return _get_secret("SUPABASE_BUCKET", default) or default


def storage_upload_bytes(
    sb,
    bucket: str,
    path: str,
    data: bytes,
    content_type: str,
    upsert: bool = True,
) -> None:
    """Upload bytes to Supabase Storage."""
    file_opts = {"content-type": content_type, "x-upsert": "true" if upsert else "false"}
    sb.storage.from_(bucket).upload(path, data, file_opts)


def storage_remove(sb, bucket: str, paths: list[str]) -> None:
    if not paths:
        return
    sb.storage.from_(bucket).remove(paths)


def storage_signed_url(sb, bucket: str, path: str, expires_sec: int = 3600) -> str:
    res = sb.storage.from_(bucket).create_signed_url(path, expires_sec)
    # supabase-py returns dict like {'signedURL': '...'}
    return (res or {}).get("signedURL", "")


def db_insert(sb, table: str, row: dict[str, Any]) -> dict[str, Any]:
    return sb.table(table).insert(row).execute().data  # type: ignore


def db_select(sb, table: str, **filters) -> list[dict[str, Any]]:
    q = sb.table(table).select("*")
    for k, v in filters.items():
        q = q.eq(k, v)
    return q.execute().data  # type: ignore


def db_delete(sb, table: str, **filters) -> None:
    q = sb.table(table).delete()
    for k, v in filters.items():
        q = q.eq(k, v)
    q.execute()
