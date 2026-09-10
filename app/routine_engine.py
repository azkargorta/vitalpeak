"""Motor unificado de generación de rutinas para VitalPeak.

Combina elección automática del split, volumen semanal y selector inteligente
de ejercicios. Genera una propuesta estructurada y determinista a partir de:
objetivo, nivel, días, duración de sesión, equipamiento y prioridades.
"""

from __future__ import annotations

from collections import defaultdict
from typing import Dict, Iterable, List, Mapping, Sequence

from .exercise_selector import select_session_exercises
from .training_volume import build_volume_plan, normalize_goal, normalize_level

UPPER = ["Pecho", "Espalda", "Deltoide lateral", "Deltoide posterior", "Bíceps", "Tríceps"]
LOWER = ["Cuádriceps", "Isquios", "Glúteos", "Gemelos", "Core"]
PUSH = ["Pecho", "Deltoide lateral", "Tríceps"]
PULL = ["Espalda", "Deltoide posterior", "Bíceps"]
LEGS = ["Cuádriceps", "Isquios", "Glúteos", "Gemelos", "Core"]

SPLIT_RULES = {
    2: "Full Body",
    3: "Full Body",
    4: "Upper / Lower",
    5: "Upper / Lower + PPL",
    6: "PPL x2",
}


def choose_split(goal: str, level: str, days: int) -> str:
    """Elige un split sensato priorizando frecuencia y reparto del volumen."""
    days = max(2, min(6, int(days or 3)))
    goal_key = normalize_goal(goal)
    level_key = normalize_level(level)

    if days == 2:
        return "Full Body"
    if days == 3:
        # Para fuerza e iniciación, full body mantiene mejor frecuencia de básicos.
        if goal_key in {"fuerza", "fitness_general"} or level_key == "principiante":
            return "Full Body"
        return "PPL"
    if days == 4:
        return "Upper / Lower"
    if days == 5:
        return "Upper / Lower + PPL"
    return "PPL x2"


def split_days(split: str) -> List[dict]:
    if split == "Full Body":
        return [
            {"name": "Full Body A", "muscles": UPPER + LOWER},
            {"name": "Full Body B", "muscles": UPPER + LOWER},
            {"name": "Full Body C", "muscles": UPPER + LOWER},
        ]
    if split == "Upper / Lower":
        return [
            {"name": "Upper A", "muscles": UPPER},
            {"name": "Lower A", "muscles": LOWER},
            {"name": "Upper B", "muscles": UPPER},
            {"name": "Lower B", "muscles": LOWER},
        ]
    if split == "PPL":
        return [
            {"name": "Push", "muscles": PUSH},
            {"name": "Pull", "muscles": PULL},
            {"name": "Legs", "muscles": LEGS},
        ]
    if split == "Upper / Lower + PPL":
        return [
            {"name": "Upper", "muscles": UPPER},
            {"name": "Lower", "muscles": LOWER},
            {"name": "Push", "muscles": PUSH},
            {"name": "Pull", "muscles": PULL},
            {"name": "Legs", "muscles": LEGS},
        ]
    return [
        {"name": "Push A", "muscles": PUSH},
        {"name": "Pull A", "muscles": PULL},
        {"name": "Legs A", "muscles": LEGS},
        {"name": "Push B", "muscles": PUSH},
        {"name": "Pull B", "muscles": PULL},
        {"name": "Legs B", "muscles": LEGS},
    ]


def _session_exercise_cap(minutes: int) -> int:
    minutes = max(30, min(120, int(minutes or 60)))
    if minutes <= 40:
        return 5
    if minutes <= 60:
        return 7
    if minutes <= 80:
        return 8
    return 9


def _prescription(goal: str, exercise_type: str, fatigue: str) -> dict:
    goal = normalize_goal(goal)
    compound = str(exercise_type).lower() == "compuesto"
    high_fatigue = str(fatigue).lower() == "high"

    if goal == "fuerza":
        return {"reps": "3-6" if compound else "6-10", "rir": 2, "rest_sec": 180 if compound else 120}
    if goal == "potencia":
        return {"reps": "3-5" if compound else "5-8", "rir": 3, "rest_sec": 150}
    if goal == "resistencia":
        return {"reps": "12-20", "rir": 2, "rest_sec": 60}
    if goal in {"hipertrofia", "recomposicion", "perdida_grasa"}:
        return {"reps": "6-10" if compound else "10-15", "rir": 2, "rest_sec": 150 if high_fatigue else (120 if compound else 75)}
    return {"reps": "8-12", "rir": 2, "rest_sec": 90}


def _assign_muscle_sets(volume_plan: Mapping[str, object], days: List[dict]) -> List[dict]:
    """Reparte las series semanales del motor entre los días que trabajan cada músculo."""
    muscle_data = volume_plan.get("muscles", {}) if isinstance(volume_plan, Mapping) else {}
    assigned = [{"name": d["name"], "muscles": list(d["muscles"]), "sets": {}} for d in days]

    for muscle, info in muscle_data.items():
        eligible = [i for i, day in enumerate(days) if muscle in day["muscles"]]
        if not eligible:
            continue
        weekly_sets = int((info or {}).get("weekly_sets", 0))
        q, r = divmod(weekly_sets, len(eligible))
        for pos, day_index in enumerate(eligible):
            assigned[day_index]["sets"][muscle] = q + (1 if pos < r else 0)
    return assigned


def _slots_from_sets(muscle_sets: Mapping[str, int], exercise_cap: int) -> Dict[str, int]:
    """Convierte series objetivo en número de ejercicios por músculo para la sesión."""
    slots: Dict[str, int] = {}
    for muscle, sets in muscle_sets.items():
        sets = int(sets or 0)
        if sets <= 0:
            continue
        # 1 ejercicio hasta 4 series; 2 cuando el músculo necesita 5+ en esa sesión.
        slots[muscle] = 2 if sets >= 5 else 1

    while sum(slots.values()) > exercise_cap:
        reducible = sorted(
            (m for m, n in slots.items() if n > 1),
            key=lambda m: muscle_sets.get(m, 0),
        )
        if reducible:
            slots[reducible[0]] -= 1
            continue
        smallest = min(slots, key=lambda m: muscle_sets.get(m, 0))
        del slots[smallest]
    return slots


def _allocate_exercise_sets(selected: List[dict], muscle_sets: Mapping[str, int]) -> List[dict]:
    by_muscle: Dict[str, List[dict]] = defaultdict(list)
    for item in selected:
        by_muscle[item.get("target_muscle", "")].append(item)

    result: List[dict] = []
    for muscle, exercises in by_muscle.items():
        total = max(len(exercises) * 2, int(muscle_sets.get(muscle, 0)))
        q, r = divmod(total, len(exercises))
        for i, item in enumerate(exercises):
            sets = max(2, min(5, q + (1 if i < r else 0)))
            meta = item.get("metadata") or {}
            prescription = _prescription("fitness_general", str(meta.get("exercise_type", "")), str(meta.get("fatigue", "")))
            result.append({
                "exercise": item["name"],
                "target_muscle": muscle,
                "sets": sets,
                "score": item.get("score"),
                "metadata": meta,
                "prescription": prescription,
            })
    return result


def generate_routine(
    goal: str,
    level: str,
    days: int,
    *,
    session_minutes: int = 60,
    available_equipment: Iterable[str] | None = None,
    priority_muscles: Sequence[str] | None = None,
) -> Dict[str, object]:
    """Genera una rutina completa usando volumen + split + selector."""
    days = max(2, min(6, int(days or 3)))
    split = choose_split(goal, level, days)
    day_defs = split_days(split)[:days]
    volume = build_volume_plan(goal, level, days, priority_muscles)
    assigned = _assign_muscle_sets(volume, day_defs)
    cap = _session_exercise_cap(session_minutes)
    generated_days: List[dict] = []

    for day in assigned:
        slots = _slots_from_sets(day["sets"], cap)
        selected = select_session_exercises(
            slots,
            goal,
            level,
            available_equipment=available_equipment,
        )
        items = _allocate_exercise_sets(selected, day["sets"])
        # Aplicar prescripción del objetivo real.
        for item in items:
            meta = item.get("metadata") or {}
            item["prescription"] = _prescription(
                goal,
                str(meta.get("exercise_type", "")),
                str(meta.get("fatigue", "")),
            )
        generated_days.append({
            "name": day["name"],
            "target_sets": day["sets"],
            "exercises": items,
        })

    return {
        "goal": normalize_goal(goal),
        "level": normalize_level(level),
        "days": days,
        "session_minutes": int(session_minutes or 60),
        "split": split,
        "priority_muscles": list(priority_muscles or []),
        "volume_plan": volume,
        "sessions": generated_days,
    }


def public_routine_engine_config() -> Dict[str, object]:
    return {
        "split_rules": {str(k): v for k, v in SPLIT_RULES.items()},
        "supported_splits": ["Full Body", "PPL", "Upper / Lower", "Upper / Lower + PPL", "PPL x2"],
        "session_caps": {"40": 5, "60": 7, "80": 8, "120": 9},
        "prescription": {
            "fuerza": {"compound_reps": "3-6", "isolation_reps": "6-10", "rir": 2},
            "hipertrofia": {"compound_reps": "6-10", "isolation_reps": "10-15", "rir": 2},
            "recomposicion": {"compound_reps": "6-10", "isolation_reps": "10-15", "rir": 2},
            "perdida_grasa": {"compound_reps": "6-10", "isolation_reps": "10-15", "rir": 2},
            "resistencia": {"reps": "12-20", "rir": 2},
            "potencia": {"reps": "3-5", "rir": 3},
            "fitness_general": {"reps": "8-12", "rir": 2},
        },
    }
