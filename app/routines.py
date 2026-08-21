from __future__ import annotations

from typing import Any, Dict, List, Optional

from .datastore import load_user, save_user
from .training import add_training_set


def list_routines(username: str) -> List[Dict]:
    data = load_user(username)
    return data.get("rutinas", [])


def add_routine(
    username: str,
    name: str,
    items: List[Dict],
    *,
    days: Optional[List[Dict[str, Any]]] = None,
) -> None:
    data = load_user(username)
    routines = data.get("rutinas", [])
    if any(r.get("name") == name for r in routines):
        raise ValueError("Ya existe una rutina con ese nombre")
    entry: Dict[str, Any] = {"name": name, "items": list(items or [])}
    if days:
        entry["kind"] = "program"
        entry["days"] = days
        if not entry["items"]:
            flat: List[Dict] = []
            for d in days:
                flat.extend(list(d.get("items") or []))
            entry["items"] = flat
    routines.append(entry)
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
    data_plan = dict(data.get("routine_plan", {}))
    for k, v in list(data_plan.items()):
        if v == old:
            data_plan[k] = new
    data["routine_plan"] = data_plan
    save_user(username, data)


def is_program(routine: Dict[str, Any]) -> bool:
    return bool(routine.get("kind") == "program" and routine.get("days"))


def program_sessions(routine: Dict[str, Any]) -> List[Dict[str, Any]]:
    """Sesiones asignables: name (para calendario), session_label, items, focus."""
    if is_program(routine):
        out = []
        for d in routine.get("days") or []:
            label = str(d.get("name") or "Día")
            out.append(
                {
                    "name": f"{routine['name']} — {label}",
                    "session_label": label,
                    "focus": d.get("focus") or "",
                    "items": list(d.get("items") or []),
                }
            )
        return out
    return [
        {
            "name": str(routine.get("name") or "Rutina"),
            "session_label": str(routine.get("name") or "Rutina"),
            "focus": "",
            "items": list(routine.get("items") or []),
        }
    ]


def materialize_program_days(username: str, routine: Dict[str, Any]) -> List[str]:
    """Asegura rutinas hijas por día (para el calendario / Entrenar). Devuelve nombres."""
    sessions = program_sessions(routine)
    if not is_program(routine):
        return [sessions[0]["name"]] if sessions else []

    existing = {r.get("name") for r in list_routines(username)}
    names: List[str] = []
    for s in sessions:
        names.append(s["name"])
        if s["name"] not in existing:
            add_routine(username, s["name"], s["items"])
            existing.add(s["name"])
    return names


def find_routine(username: str, name: str) -> Optional[Dict[str, Any]]:
    return next((r for r in list_routines(username) if r.get("name") == name), None)


def apply_routine(username: str, routine_name: str, date_iso: str) -> int:
    data = load_user(username)
    routine = next((r for r in data.get("rutinas", []) if r.get("name") == routine_name), None)
    if not routine:
        return 0
    # Si es un plan completo sin materializar, no aplicar todo mezclado
    items = routine.get("items", [])
    if is_program(routine) and routine.get("days"):
        # Preferir no usar el plan crudo en un solo día
        items = routine.get("items", [])
    count = 0
    for item in items:
        ex = item.get("exercise")
        sets = int(item.get("sets", 1))
        reps = int(item.get("reps", 10))
        weight = float(item.get("weight", 0.0))
        for s in range(1, sets + 1):
            add_training_set(username, date_iso, ex, s, reps, weight)
            count += 1
    return count
