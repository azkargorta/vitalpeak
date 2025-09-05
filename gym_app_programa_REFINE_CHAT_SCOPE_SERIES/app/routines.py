from __future__ import annotations
from typing import Dict, List
from .datastore import load_user, save_user
from .training import add_training_set


def list_routines(username: str) -> List[Dict]:
    data = load_user(username)
    return data.get("rutinas", [])


def add_routine(username: str, name: str, items: List[Dict]) -> None:
    data = load_user(username)
    routines = data.get("rutinas", [])
    if any(r.get("name") == name for r in routines):
        raise ValueError("Ya existe una rutina con ese nombre")
    routines.append({"name": name, "items": items})
    data["rutinas"] = routines
    save_user(username, data)


def delete_routine(username: str, name: str) -> None:
    data = load_user(username)
    routines = [r for r in data.get("rutinas", []) if r.get("name") != name]
    data["rutinas"] = routines
    save_user(username, data)


def rename_routine(username: str, old: str, new: str) -> None:
    data = load_user(username)
    for r in data.get("rutinas", []):
        if r.get("name") == old:
            r["name"] = new
            break
    save_user(username, data)


def apply_routine(username: str, routine_name: str, date_iso: str) -> int:
    data = load_user(username)
    routine = next((r for r in data.get("rutinas", []) if r.get("name") == routine_name), None)
    if not routine:
        return 0
    count = 0
    for item in routine.get("items", []):
        ex = item.get("exercise")
        sets = int(item.get("sets", 1))
        reps = int(item.get("reps", 10))
        weight = float(item.get("weight", 0.0))
        for s in range(1, sets + 1):
            add_training_set(username, date_iso, ex, s, reps, weight)
            count += 1
    return count
