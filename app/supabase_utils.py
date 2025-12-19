from __future__ import annotations

import os
from typing import Any, Optional

try:
    import streamlit as st
except Exception:  # pragma: no cover
    st = None  # type: ignore

from supabase import create_client


def _get_secret(key: str, default: Optional[str] = None) -> Optional[str]:
    """Read from Streamlit secrets first, then env vars."""
    if st is not None:
        try:
            if key in st.secrets:
                return str(st.secrets[key])
        except Exception:
            pass
    return os.getenv(key, default)


def get_supabase_client():
    url = _get_secret("SUPABASE_URL")
    key = _get_secret("SUPABASE_SERVICE_ROLE_KEY")
    if not url or not key:
        return None
    return create_client(url, key)


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
