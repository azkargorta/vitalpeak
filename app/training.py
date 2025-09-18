from __future__ import annotations
from typing import Dict, List, Optional, Tuple
from .datastore import load_user, save_user
import streamlit as st


def add_training_set(username: str, date_iso: str, exercise: str, set_index: int, reps: int, weight: float) -> None:
    data = load_user(username)
    row = {
        "date": date_iso,
        "exercise": exercise,
        "set": int(set_index),
        "reps": int(reps),
        "weight": float(weight),
    }
    data.setdefault("entrenamientos", []).append(row)
    save_user(username, data)


def list_training(username: str) -> List[Dict]:
    data = load_user(username)
    return data.get("entrenamientos", [])


def last_values_for_exercise(username: str, exercise: str) -> Optional[Tuple[int, float]]:
    data = load_user(username)
    entries = [e for e in data.get("entrenamientos", []) if e.get("exercise") == exercise]
    if not entries:
        return None
    last = sorted(entries, key=lambda x: (x.get("date",""), x.get("set",0)))[-1]
    return int(last.get("reps", 0)), float(last.get("weight", 0.0))
