"""Project configuration helpers.

This module is designed to make local development and Streamlit Cloud deployments
behave the same way:

- Locally: reads OPENAI_API_KEY from a `.env` file at the project root.
- Streamlit Cloud: reads OPENAI_API_KEY from `st.secrets`.

In both cases, values are copied into `os.environ` so the rest of the app can
keep using `os.getenv(...)`.
"""

from __future__ import annotations

from pathlib import Path
import os


def project_root() -> Path:
    # app/ lives one level below the project root.
    return Path(__file__).resolve().parents[1]


def load_env() -> None:
    """Load configuration into environment variables.

    Priority (highest to lowest):
      1) Existing os.environ
      2) Streamlit secrets (if running on Streamlit)
      3) .env file at project root (local dev)
    """

    # 3) Local .env
    try:
        from dotenv import load_dotenv

        load_dotenv(project_root() / ".env", override=False)
    except Exception:
        pass

    # 2) Streamlit Cloud secrets
    try:
        import streamlit as st

        # st.secrets can contain nested sections; we only propagate flat key/value pairs.
        for k, v in dict(st.secrets).items():
            if isinstance(v, (str, int, float, bool)):
                os.environ.setdefault(str(k), str(v))
    except Exception:
        # Streamlit may not be installed in some contexts, ignore.
        pass


def get_openai_api_key() -> str | None:
    load_env()
    return os.getenv("OPENAI_API_KEY")
