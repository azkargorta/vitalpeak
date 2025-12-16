from __future__ import annotations

from datetime import date, timedelta
from typing import Any, Dict, List, Optional, Tuple

from .datastore import load_user, save_user


DEFAULT_GOALS: Dict[str, Any] = {
    "dias_semana": 3,          # objetivo de entrenos/semana
    "peso_objetivo": None,     # kg
    # { "Press banca": {"peso": 80.0, "reps": 8} }
    "ejercicios": {},
}


def _normalize(goals: Optional[Dict[str, Any]]) -> Dict[str, Any]:
    g = dict(DEFAULT_GOALS)
    if isinstance(goals, dict):
        g.update({k: goals.get(k) for k in DEFAULT_GOALS.keys() if k in goals})
        # ejercicios: siempre dict
        ex = goals.get("ejercicios")
        if isinstance(ex, dict):
            g["ejercicios"] = ex
    if g.get("dias_semana") is None:
        g["dias_semana"] = 0
    try:
        g["dias_semana"] = int(g["dias_semana"])
    except Exception:
        g["dias_semana"] = 0
    if g["dias_semana"] < 0:
        g["dias_semana"] = 0
    if g["dias_semana"] > 7:
        g["dias_semana"] = 7
    # peso objetivo
    po = g.get("peso_objetivo")
    if po in ("", "None"):
        po = None
    try:
        po = None if po is None else float(po)
    except Exception:
        po = None
    g["peso_objetivo"] = po
    # normalizar metas de ejercicio
    cleaned: Dict[str, Dict[str, Any]] = {}
    for name, meta in (g.get("ejercicios") or {}).items():
        if not isinstance(name, str) or not name.strip():
            continue
        if not isinstance(meta, dict):
            continue
        tw = meta.get("peso")
        tr = meta.get("reps")
        try:
            tw = None if tw is None or tw == "" else float(tw)
        except Exception:
            tw = None
        try:
            tr = None if tr is None or tr == "" else int(tr)
        except Exception:
            tr = None
        cleaned[name.strip()] = {"peso": tw, "reps": tr}
    g["ejercicios"] = cleaned
    return g


def get_goals(username: str) -> Dict[str, Any]:
    data = load_user(username) or {}
    return _normalize(data.get("objetivos"))


def save_goals(username: str, goals: Dict[str, Any]) -> None:
    data = load_user(username) or {}
    data["objetivos"] = _normalize(goals)
    save_user(username, data)


def set_weekly_days_goal(username: str, dias_semana: int) -> None:
    g = get_goals(username)
    g["dias_semana"] = max(0, min(7, int(dias_semana)))
    save_goals(username, g)


def set_target_body_weight(username: str, peso_objetivo: Optional[float]) -> None:
    g = get_goals(username)
    g["peso_objetivo"] = None if peso_objetivo is None else float(peso_objetivo)
    save_goals(username, g)


def set_exercise_goal(
    username: str,
    exercise: str,
    *,
    peso_objetivo: Optional[float] = None,
    reps_objetivo: Optional[int] = None,
) -> None:
    name = (exercise or "").strip()
    if not name:
        return
    g = get_goals(username)
    g.setdefault("ejercicios", {})
    g["ejercicios"][name] = {
        "peso": None if peso_objetivo is None else float(peso_objetivo),
        "reps": None if reps_objetivo is None else int(reps_objetivo),
    }
    save_goals(username, g)


def remove_exercise_goal(username: str, exercise: str) -> None:
    name = (exercise or "").strip()
    g = get_goals(username)
    ex = g.get("ejercicios") or {}
    if name in ex:
        del ex[name]
        g["ejercicios"] = ex
        save_goals(username, g)


def rename_exercise_goal(username: str, old: str, new: str) -> None:
    old_n = (old or "").strip()
    new_n = (new or "").strip()
    if not old_n or not new_n or old_n == new_n:
        return
    g = get_goals(username)
    ex = g.get("ejercicios") or {}
    if old_n in ex and new_n not in ex:
        ex[new_n] = ex.pop(old_n)
        g["ejercicios"] = ex
        save_goals(username, g)


def delete_exercise_goal(username: str, exercise: str) -> None:
    remove_exercise_goal(username, exercise)


def week_start_monday(d: date) -> date:
    return d - timedelta(days=d.weekday())


def week_range(d: date) -> Tuple[date, date]:
    start = week_start_monday(d)
    end = start + timedelta(days=6)
    return start, end


def workout_days_in_range(username: str, start: date, end: date) -> int:
    """Cuenta días únicos con al menos 1 serie registrada (entrenamientos) en el rango."""
    data = load_user(username) or {}
    entrenos = data.get("entrenamientos", []) or []
    days = set()
    for e in entrenos:
        ds = e.get("date")
        if not ds:
            continue
        try:
            dd = date.fromisoformat(str(ds)[:10])
        except Exception:
            continue
        if start <= dd <= end:
            days.add(dd)
    return len(days)


def weekly_workout_counts(username: str, weeks_back: int = 8, *, anchor: Optional[date] = None) -> List[Dict[str, Any]]:
    """Devuelve lista (semana_inicio, semana_fin, entrenos) para las últimas N semanas."""
    if anchor is None:
        anchor = date.today()
    this_start = week_start_monday(anchor)
    out: List[Dict[str, Any]] = []
    for i in range(weeks_back - 1, -1, -1):
        ws = this_start - timedelta(days=7 * i)
        we = ws + timedelta(days=6)
        c = workout_days_in_range(username, ws, we)
        out.append({"week_start": ws, "week_end": we, "workouts": c})
    return out
