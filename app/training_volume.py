"""Motor base de volumen semanal para VitalPeak.

Calcula una prescripción inicial de series por músculo a partir de objetivo,
nivel, días disponibles y prioridades. Es deliberadamente conservador: el
volumen debe poder ajustarse después según rendimiento, recuperación y
preferencias del usuario.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, Iterable, List, Mapping, Sequence

MUSCLES = (
    "Pecho",
    "Espalda",
    "Cuádriceps",
    "Isquios",
    "Glúteos",
    "Deltoide lateral",
    "Deltoide posterior",
    "Bíceps",
    "Tríceps",
    "Gemelos",
    "Core",
)

# Objetivo intermedio de partida. No son máximos ni mínimos fisiológicos,
# sino un punto inicial práctico para el generador.
GOAL_BASE: Dict[str, Dict[str, int]] = {
    "hipertrofia": {
        "Pecho": 12, "Espalda": 14, "Cuádriceps": 12, "Isquios": 10,
        "Glúteos": 11, "Deltoide lateral": 10, "Deltoide posterior": 6,
        "Bíceps": 9, "Tríceps": 9, "Gemelos": 8, "Core": 6,
    },
    "fuerza": {
        "Pecho": 10, "Espalda": 10, "Cuádriceps": 10, "Isquios": 8,
        "Glúteos": 8, "Deltoide lateral": 5, "Deltoide posterior": 5,
        "Bíceps": 5, "Tríceps": 6, "Gemelos": 5, "Core": 6,
    },
    "perdida_grasa": {
        "Pecho": 9, "Espalda": 11, "Cuádriceps": 9, "Isquios": 8,
        "Glúteos": 9, "Deltoide lateral": 7, "Deltoide posterior": 5,
        "Bíceps": 6, "Tríceps": 6, "Gemelos": 5, "Core": 6,
    },
    "recomposicion": {
        "Pecho": 11, "Espalda": 13, "Cuádriceps": 11, "Isquios": 9,
        "Glúteos": 10, "Deltoide lateral": 9, "Deltoide posterior": 6,
        "Bíceps": 8, "Tríceps": 8, "Gemelos": 6, "Core": 6,
    },
    "resistencia": {
        "Pecho": 6, "Espalda": 8, "Cuádriceps": 8, "Isquios": 7,
        "Glúteos": 7, "Deltoide lateral": 5, "Deltoide posterior": 4,
        "Bíceps": 4, "Tríceps": 4, "Gemelos": 6, "Core": 6,
    },
    "potencia": {
        "Pecho": 7, "Espalda": 8, "Cuádriceps": 8, "Isquios": 7,
        "Glúteos": 8, "Deltoide lateral": 4, "Deltoide posterior": 4,
        "Bíceps": 4, "Tríceps": 4, "Gemelos": 5, "Core": 6,
    },
    "fitness_general": {
        "Pecho": 8, "Espalda": 9, "Cuádriceps": 8, "Isquios": 7,
        "Glúteos": 8, "Deltoide lateral": 6, "Deltoide posterior": 5,
        "Bíceps": 5, "Tríceps": 5, "Gemelos": 5, "Core": 6,
    },
}

GOAL_ALIASES = {
    "ganar músculo": "hipertrofia",
    "ganar musculo": "hipertrofia",
    "músculo": "hipertrofia",
    "musculo": "hipertrofia",
    "hypertrophy": "hipertrofia",
    "ganar fuerza": "fuerza",
    "strength": "fuerza",
    "perder grasa": "perdida_grasa",
    "pérdida de grasa": "perdida_grasa",
    "perdida de grasa": "perdida_grasa",
    "fat loss": "perdida_grasa",
    "recomposición": "recomposicion",
    "recomposicion corporal": "recomposicion",
    "mejorar resistencia": "resistencia",
    "endurance": "resistencia",
    "rendimiento": "potencia",
    "rendimiento / potencia": "potencia",
    "power": "potencia",
    "estar en forma": "fitness_general",
    "general": "fitness_general",
}

LEVEL_FACTOR = {
    "principiante": 0.70,
    "beginner": 0.70,
    "intermedio": 1.00,
    "intermediate": 1.00,
    "avanzado": 1.15,
    "advanced": 1.15,
}

# Con pocos días reducimos ligeramente el total para que las sesiones no se
# conviertan en maratones. La frecuencia no se trata como un estímulo mágico:
# sirve sobre todo para repartir el volumen de forma viable.
DAY_FACTOR = {2: 0.90, 3: 0.95, 4: 1.00, 5: 1.00, 6: 1.00}

# Límites de seguridad/practicidad del motor inicial.
MUSCLE_LIMITS: Dict[str, tuple[int, int]] = {
    "Pecho": (4, 18), "Espalda": (5, 20), "Cuádriceps": (5, 18),
    "Isquios": (4, 16), "Glúteos": (4, 18), "Deltoide lateral": (3, 16),
    "Deltoide posterior": (2, 12), "Bíceps": (3, 14), "Tríceps": (3, 14),
    "Gemelos": (3, 14), "Core": (3, 12),
}


def _norm(value: str) -> str:
    return " ".join(str(value or "").strip().lower().replace("_", " ").split())


def normalize_goal(goal: str) -> str:
    g = _norm(goal)
    if g in GOAL_BASE:
        return g
    return GOAL_ALIASES.get(g, "fitness_general")


def normalize_level(level: str) -> str:
    lvl = _norm(level)
    if lvl in ("principiante", "beginner"):
        return "principiante"
    if lvl in ("avanzado", "advanced"):
        return "avanzado"
    return "intermedio"


def _clamp(muscle: str, value: float) -> int:
    low, high = MUSCLE_LIMITS[muscle]
    return max(low, min(high, int(round(value))))


def weekly_volume(
    goal: str,
    level: str,
    days: int,
    priority_muscles: Iterable[str] | None = None,
) -> Dict[str, int]:
    """Devuelve series objetivo semanales por músculo.

    Una prioridad aumenta ~20 % el punto de partida, siempre dentro de límites.
    """
    goal_key = normalize_goal(goal)
    level_key = normalize_level(level)
    days = max(2, min(6, int(days or 3)))
    factor = LEVEL_FACTOR[level_key] * DAY_FACTOR[days]
    priorities = {_norm(x) for x in (priority_muscles or [])}

    out: Dict[str, int] = {}
    for muscle, base in GOAL_BASE[goal_key].items():
        value = base * factor
        if _norm(muscle) in priorities:
            value *= 1.20
        out[muscle] = _clamp(muscle, value)
    return out


def recommended_exposures(days: int, muscle: str, weekly_sets: int) -> int:
    """Frecuencia práctica para repartir series, no requisito fisiológico."""
    days = max(2, min(6, int(days or 3)))
    if weekly_sets <= 5:
        return 1 if days <= 3 else 2
    if days == 2:
        return 2
    if days in (3, 4):
        return 2
    return 3 if weekly_sets >= 12 else 2


def distribute_sets(total_sets: int, exposures: int) -> List[int]:
    """Reparte series de forma lo más uniforme posible entre exposiciones."""
    exposures = max(1, int(exposures))
    total_sets = max(0, int(total_sets))
    q, r = divmod(total_sets, exposures)
    return [q + (1 if i < r else 0) for i in range(exposures)]


def build_volume_plan(
    goal: str,
    level: str,
    days: int,
    priority_muscles: Sequence[str] | None = None,
) -> Dict[str, object]:
    weekly = weekly_volume(goal, level, days, priority_muscles)
    distribution: Dict[str, Dict[str, object]] = {}
    for muscle, sets in weekly.items():
        exposures = recommended_exposures(days, muscle, sets)
        distribution[muscle] = {
            "weekly_sets": sets,
            "exposures": exposures,
            "sets_per_exposure": distribute_sets(sets, exposures),
        }
    return {
        "goal": normalize_goal(goal),
        "level": normalize_level(level),
        "days": max(2, min(6, int(days or 3))),
        "priority_muscles": list(priority_muscles or []),
        "muscles": distribution,
    }


def public_volume_config() -> Dict[str, object]:
    """Configuración exportable a la PWA para el futuro generador móvil."""
    return {
        "muscles": list(MUSCLES),
        "goals": GOAL_BASE,
        "level_factors": {"principiante": 0.70, "intermedio": 1.00, "avanzado": 1.15},
        "day_factors": DAY_FACTOR,
        "limits": {m: list(v) for m, v in MUSCLE_LIMITS.items()},
        "priority_factor": 1.20,
    }
