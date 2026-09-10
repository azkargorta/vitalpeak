"""Selector inteligente de ejercicios para VitalPeak.

Usa los metadatos del catálogo para elegir ejercicios coherentes con músculo,
objetivo, nivel y material disponible, penalizando redundancias dentro de la
misma sesión. No genera todavía la rutina completa: es una capa reutilizable
por los futuros generadores web/móvil.
"""

from __future__ import annotations

import json
import unicodedata
from collections import Counter
from pathlib import Path
from typing import Dict, Iterable, List, Mapping, Sequence

ROOT = Path(__file__).resolve().parents[1]
METADATA_FILE = ROOT / "data" / "exercise_metadata.json"


def _norm(value: str) -> str:
    text = unicodedata.normalize("NFKD", str(value or ""))
    text = "".join(ch for ch in text if not unicodedata.combining(ch))
    return " ".join(text.lower().replace("_", " ").strip().split())


# Los nombres del motor de volumen son deliberadamente simples. Los metadatos
# pueden ser más anatómicos; estos alias permiten casar ambos mundos.
MUSCLE_ALIASES: Dict[str, tuple[str, ...]] = {
    "Pecho": ("pectoral", "pecho"),
    "Espalda": ("espalda", "dorsal", "trapecio", "romboides"),
    "Cuádriceps": ("cuadriceps",),
    "Isquios": ("isquios", "isquiosurales", "femoral"),
    "Glúteos": ("gluteos", "gluteo mayor", "gluteo medio", "gluteo menor"),
    "Deltoide lateral": ("deltoide lateral",),
    "Deltoide posterior": ("deltoide posterior",),
    "Bíceps": ("biceps", "braquial"),
    "Tríceps": ("triceps",),
    "Gemelos": ("gemelos", "gastrocnemio", "soleo", "pantorrilla"),
    "Core": ("core", "recto abdominal", "oblicuos", "abdominal"),
}

GOAL_ALIASES = {
    "ganar musculo": "hipertrofia",
    "musculo": "hipertrofia",
    "hypertrophy": "hipertrofia",
    "ganar fuerza": "fuerza",
    "strength": "fuerza",
    "perder grasa": "perdida_grasa",
    "perdida de grasa": "perdida_grasa",
    "fat loss": "perdida_grasa",
    "recomposicion corporal": "recomposicion",
    "recomposición": "recomposicion",
    "mejorar resistencia": "resistencia",
    "endurance": "resistencia",
    "rendimiento": "potencia",
    "rendimiento / potencia": "potencia",
    "power": "potencia",
    "estar en forma": "fitness_general",
    "salud general": "fitness_general",
    "general": "fitness_general",
}

LEVEL_ORDER = {"beginner": 0, "principiante": 0, "intermediate": 1, "intermedio": 1, "advanced": 2, "avanzado": 2}
FATIGUE_ORDER = {"low": 0, "medium": 1, "high": 2}


def normalize_goal(goal: str) -> str:
    g = _norm(goal)
    canonical = {"hipertrofia", "fuerza", "perdida grasa", "recomposicion", "resistencia", "potencia", "fitness general"}
    if g in canonical:
        return g.replace(" ", "_")
    return GOAL_ALIASES.get(g, "fitness_general")


def normalize_level(level: str) -> str:
    lvl = _norm(level)
    if lvl in ("beginner", "principiante"):
        return "beginner"
    if lvl in ("advanced", "avanzado"):
        return "advanced"
    return "intermediate"


def load_metadata() -> Dict[str, dict]:
    try:
        raw = json.loads(METADATA_FILE.read_text(encoding="utf-8"))
        return raw if isinstance(raw, dict) else {}
    except (OSError, json.JSONDecodeError):
        return {}


def _muscle_match(meta_muscle: str, target: str) -> bool:
    value = _norm(meta_muscle)
    aliases = MUSCLE_ALIASES.get(target, (_norm(target),))
    return any(alias in value or value in alias for alias in aliases)


def _equipment_allowed(meta: Mapping[str, object], available_equipment: Iterable[str] | None) -> bool:
    if not available_equipment:
        return True
    allowed = {_norm(x) for x in available_equipment if str(x).strip()}
    if not allowed or allowed & {"gimnasio completo", "full gym", "todo", "all"}:
        return True
    equipment = _norm(str(meta.get("equipment", "")))
    # Peso corporal no requiere equipamiento específico.
    if equipment == "peso corporal":
        return True
    synonyms = {
        "barra z": {"barra z", "barra"},
        "barra": {"barra"},
        "mancuernas": {"mancuernas", "mancuerna"},
        "maquina": {"maquina", "maquinas"},
        "polea": {"polea", "poleas"},
        "smith": {"smith", "maquina smith", "maquinas"},
        "barra paralela": {"barra paralela", "paralelas", "peso corporal"},
        "rueda abdominal": {"rueda abdominal", "ab wheel"},
        "kettlebell": {"kettlebell", "pesa rusa"},
        "trineo": {"trineo", "sled"},
        "cuerda": {"cuerda", "battle ropes"},
    }
    acceptable = synonyms.get(equipment, {equipment})
    return bool(acceptable & allowed)


def score_exercise(
    name: str,
    meta: Mapping[str, object],
    target_muscle: str,
    goal: str,
    level: str,
    *,
    selected_patterns: Mapping[str, int] | None = None,
    selected_names: Iterable[str] | None = None,
) -> tuple[float, List[str]]:
    """Puntúa un ejercicio. Cuanto mayor, más adecuado para esta elección."""
    selected_patterns = selected_patterns or {}
    selected_names_norm = {_norm(x) for x in (selected_names or [])}
    reasons: List[str] = []
    score = 0.0

    primary = str(meta.get("primary_muscle", ""))
    secondary = [str(x) for x in (meta.get("secondary_muscles") or [])]
    if _muscle_match(primary, target_muscle):
        score += 12
        reasons.append("músculo principal")
    elif any(_muscle_match(x, target_muscle) for x in secondary):
        score += 4
        reasons.append("músculo secundario")
    else:
        return -999.0, ["no trabaja el músculo objetivo de forma relevante"]

    goal_key = normalize_goal(goal)
    goals = {normalize_goal(str(x)) for x in (meta.get("goals") or [])}
    if goal_key in goals:
        score += 4
        reasons.append("encaja con el objetivo")
    elif goal_key in {"recomposicion", "perdida_grasa"} and "hipertrofia" in goals:
        score += 2.5
        reasons.append("útil para conservar/ganar masa muscular")
    elif goal_key == "fitness_general" and ("fitness_general" in goals or "hipertrofia" in goals):
        score += 2

    user_level = LEVEL_ORDER[normalize_level(level)]
    ex_level = LEVEL_ORDER.get(_norm(str(meta.get("difficulty", "intermediate"))), 1)
    if ex_level > user_level:
        score -= 8 * (ex_level - user_level)
        reasons.append("penalizado por dificultad")
    elif ex_level == user_level:
        score += 1.5

    ex_type = _norm(str(meta.get("exercise_type", "")))
    equipment = _norm(str(meta.get("equipment", "")))
    fatigue = _norm(str(meta.get("fatigue", "medium")))

    if goal_key == "fuerza":
        if ex_type == "compuesto":
            score += 4
            reasons.append("compuesto para fuerza")
        if equipment in {"barra", "barra z"}:
            score += 2
        if FATIGUE_ORDER.get(fatigue, 1) == 2:
            score += 1
    elif goal_key in {"hipertrofia", "recomposicion", "perdida_grasa"}:
        if equipment in {"maquina", "polea", "mancuernas", "maquina smith"}:
            score += 2
            reasons.append("estable y fácil de progresar")
        if fatigue == "low":
            score += 1.5
        elif fatigue == "high":
            score -= 0.5
    elif goal_key == "potencia":
        if ex_type in {"potencia", "explosivo", "acondicionamiento"}:
            score += 6
            reasons.append("específico de potencia")
        if fatigue == "high":
            score -= 1
    elif goal_key == "resistencia":
        if ex_type in {"acondicionamiento", "potencia"}:
            score += 3
        if fatigue == "low":
            score += 1

    pattern = str(meta.get("movement_pattern", ""))
    pattern_count = int(selected_patterns.get(pattern, 0)) if pattern else 0
    if pattern_count:
        score -= 4.0 * pattern_count
        reasons.append("penalización por patrón repetido")

    if _norm(name) in selected_names_norm:
        score -= 100

    # Pequeña bonificación a unilateral si aún no hay mucha redundancia: aporta
    # variedad y puede ayudar a repartir trabajo sin duplicar exactamente gestos.
    if _norm(str(meta.get("laterality", ""))) == "unilateral" and pattern_count == 0:
        score += 0.5

    return score, reasons


def rank_exercises(
    target_muscle: str,
    goal: str,
    level: str,
    *,
    available_equipment: Iterable[str] | None = None,
    selected_names: Iterable[str] | None = None,
    selected_patterns: Mapping[str, int] | None = None,
    metadata: Mapping[str, Mapping[str, object]] | None = None,
) -> List[dict]:
    """Devuelve todos los candidatos válidos ordenados de mejor a peor."""
    catalog = metadata or load_metadata()
    ranked: List[dict] = []
    for name, meta in catalog.items():
        if not isinstance(meta, Mapping) or not _equipment_allowed(meta, available_equipment):
            continue
        score, reasons = score_exercise(
            name, meta, target_muscle, goal, level,
            selected_patterns=selected_patterns,
            selected_names=selected_names,
        )
        if score <= -900:
            continue
        ranked.append({"name": name, "score": round(score, 2), "reasons": reasons, "metadata": dict(meta)})
    ranked.sort(key=lambda x: (-x["score"], _norm(x["name"])))
    return ranked


def select_exercises(
    target_muscle: str,
    count: int,
    goal: str,
    level: str,
    *,
    available_equipment: Iterable[str] | None = None,
    already_selected: Sequence[str] | None = None,
    metadata: Mapping[str, Mapping[str, object]] | None = None,
) -> List[dict]:
    """Elige varios ejercicios actualizando la penalización de redundancia."""
    catalog = metadata or load_metadata()
    chosen: List[dict] = []
    names = list(already_selected or [])
    pattern_counts: Counter[str] = Counter()
    for name in names:
        meta = catalog.get(name) or {}
        pattern = str(meta.get("movement_pattern", ""))
        if pattern:
            pattern_counts[pattern] += 1

    for _ in range(max(0, int(count))):
        ranked = rank_exercises(
            target_muscle, goal, level,
            available_equipment=available_equipment,
            selected_names=names,
            selected_patterns=pattern_counts,
            metadata=catalog,
        )
        if not ranked:
            break
        best = ranked[0]
        chosen.append(best)
        names.append(best["name"])
        pattern = str(best["metadata"].get("movement_pattern", ""))
        if pattern:
            pattern_counts[pattern] += 1
    return chosen


def select_session_exercises(
    muscle_slots: Mapping[str, int],
    goal: str,
    level: str,
    *,
    available_equipment: Iterable[str] | None = None,
) -> List[dict]:
    """Selecciona una sesión completa evitando duplicados y exceso de patrones.

    `muscle_slots` indica cuántos ejercicios se desean para cada músculo, por
    ejemplo {"Pecho": 2, "Espalda": 2, "Tríceps": 1}.
    """
    catalog = load_metadata()
    selected: List[dict] = []
    selected_names: List[str] = []
    pattern_counts: Counter[str] = Counter()

    for muscle, count in muscle_slots.items():
        for _ in range(max(0, int(count))):
            ranked = rank_exercises(
                muscle, goal, level,
                available_equipment=available_equipment,
                selected_names=selected_names,
                selected_patterns=pattern_counts,
                metadata=catalog,
            )
            if not ranked:
                break
            best = ranked[0]
            best["target_muscle"] = muscle
            selected.append(best)
            selected_names.append(best["name"])
            pattern = str(best["metadata"].get("movement_pattern", ""))
            if pattern:
                pattern_counts[pattern] += 1

    # Orden práctico: compuestos y ejercicios de mayor fatiga antes; aislamiento
    # y core después. La futura capa de rutina podrá modificarlo por prioridades.
    type_order = {"potencia": 0, "explosivo": 0, "compuesto": 1, "aislamiento": 2, "core": 3, "acondicionamiento": 4}
    fatigue_order = {"high": 0, "medium": 1, "low": 2}
    selected.sort(key=lambda x: (
        type_order.get(_norm(str(x["metadata"].get("exercise_type", ""))), 2),
        fatigue_order.get(_norm(str(x["metadata"].get("fatigue", "medium"))), 1),
        -x["score"],
    ))
    return selected


def public_selector_config() -> Dict[str, object]:
    """Parámetros que puede usar la PWA cuando se active el generador móvil."""
    return {
        "muscle_aliases": {k: list(v) for k, v in MUSCLE_ALIASES.items()},
        "scoring": {
            "primary_muscle": 12,
            "secondary_muscle": 4,
            "goal_match": 4,
            "repeated_pattern_penalty": 4,
            "duplicate_exercise_penalty": 100,
            "beginner_advanced_penalty_per_level": 8,
        },
        "principles": [
            "priorizar músculo objetivo",
            "respetar material disponible",
            "adaptar dificultad al nivel",
            "penalizar patrones repetidos",
            "favorecer compuestos en fuerza",
            "favorecer estabilidad y progresión en hipertrofia",
            "priorizar movimientos explosivos en potencia",
        ],
    }
