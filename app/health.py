from __future__ import annotations
from typing import Dict, List
from .datastore import load_user, save_user


def add_weight(username: str, date_iso: str, weight: float) -> None:
    data = load_user(username)
    data.setdefault("weights", []).append({"date": date_iso, "weight": float(weight)})
    save_user(username, data)


def list_weights(username: str) -> List[Dict]:
    data = load_user(username)
    return data.get("weights", [])
