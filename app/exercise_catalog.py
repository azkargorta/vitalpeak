"""Catálogo de ejercicios base: grupos musculares y alternativas.

Usa `data/base_exercises.txt` como fuente de verdad de nombres.
Los grupos por defecto permiten proponer 3 sustitutos coherentes.
"""

from __future__ import annotations

from pathlib import Path
from typing import Dict, List, Optional, Sequence, Set

DATA_DIR = Path("data")
BASE_FILE = DATA_DIR / "base_exercises.txt"

# Grupo por nombre exacto (debe coincidir con base_exercises.txt)
DEFAULT_GROUPS: Dict[str, str] = {
    # Tríceps / brazo
    "Extensión de triceps acostado con barra": "Brazo",
    "Fondos de triceps en barras paralelas": "Brazo",
    "Fondos de triceps en máquina": "Brazo",
    "Jalón de triceps en polea alta": "Brazo",
    "Jalón de triceps en polea alta con cuerda": "Brazo",
    "Press de banco con barra y agarre estrecho": "Brazo",
    "Extensiones de triceps acostado con mancuernas": "Brazo",
    "Extensiones de triceps de pie, tras nuca, con polea": "Brazo",
    "Extensiones de triceps inclinado de pies": "Brazo",
    "Extensiones de triceps, tras nuca, en polea con cuerda": "Brazo",
    # Pecho
    "Apertura de pecho sentado": "Pecho",
    "Cruce parado en polea alta con manija": "Pecho",
    "Fondo de pecho en barra paralela": "Pecho",
    "Press con barra en banco horizontal": "Pecho",
    "Press con barra en banco inclinado": "Pecho",
    "Press de banca con maquina Smith": "Pecho",
    "Press de banco con mancuernas, 30º de inclinación": "Pecho",
    "Press de pecho en banco de maquina de fuerza de martillo": "Pecho",
    "Press inclinado en máquina Smith": "Pecho",
    "Press inclinado de pecho en máquina": "Pecho",
    "Press de pecho con mancuernas en banco horizontal": "Pecho",
    # Espalda
    "Dominadas en barra fija con agarre ancho": "Espalda",
    "Encogimiento de hombros con mancuernas": "Espalda",
    "Jalón al frente en máquina martillo": "Espalda",
    "Jalón vertical con polea alta y agarre cerrado": "Espalda",
    "Remo a un brazo en máquina sentado": "Espalda",
    "Remo a dos manos con mancuernas en banco inclinado": "Espalda",
    "Remo con polea de agarre cerrado": "Espalda",
    "Remo de un brazo con mancuerna": "Espalda",
    "Remo en máquina Smith con agarre prono": "Espalda",
    "Remo inclinado con barra T agarre ancho": "Espalda",
    # Hombro
    "Elevaciones laterales con mancuernas de pies": "Hombro",
    "Elevación lateral de un brazo con polea baja": "Hombro",
    "Elevación lateral en máquina": "Hombro",
    "Press con mancuernas sentado": "Hombro",
    "Press de hombro en máquina": "Hombro",
    "Press de hombro en máquina Smith": "Hombro",
    "Vuelo posterior sentado en máquina": "Hombro",
    # Pierna
    "Curl de pierna parado con polea": "Pierna",
    "Curl de piernas en pronación": "Pierna",
    "Curls de pierna sentado": "Pierna",
    "Elevaciones de pantorrilla en máquina": "Pierna",
    "Elevación de pantorrilla sentado": "Pierna",
    "Entrenamiento de aductores": "Pierna",
    "Estocada con paso adelante con pesos": "Pierna",
    "Extensiones de piernas sentado": "Pierna",
    "Peso muerto con barra": "Pierna",
    "Peso muerto de sumo": "Pierna",
    "Prensa de piernas en posición ancha": "Pierna",
    "Sentadilla de Hack con postura amplia": "Pierna",
    "Sentadillas en máquina Smith": "Pierna",
    "Sentadillas con barra con las piernas separadas": "Pierna",
    # Bíceps / brazo
    "Curl alterno de biceps con mancuerna": "Brazo",
    "Curl con giro con mancuernas": "Brazo",
    "Curl de biceps con máquina": "Brazo",
    "Curl de biceps estilo martillo con mancuernas": "Brazo",
    "Curl del predicador de un brazo con mancuernas": "Brazo",
    "Curl predicador con barra Z": "Brazo",
    "Curl parado a una mano con polea": "Brazo",
}

# Sub-patrón para alternativas más afinadas (mismo movimiento)
_SUBPATTERN: Dict[str, List[str]] = {
    "press_pecho_plano": ["press", "banco horizontal", "banca", "pecho"],
    "press_pecho_inclinado": ["inclinad"],
    "apertura_pecho": ["apertura", "cruce"],
    "fondos": ["fondo"],
    "jalon": ["jalón", "jalon", "dominad"],
    "remo": ["remo"],
    "elevacion_lateral": ["elevacion lateral", "elevación lateral", "elevaciones laterales"],
    "press_hombro": ["press de hombro", "press con mancuernas sentado"],
    "sentadilla": ["sentadilla", "sentadillas", "hack", "prensa"],
    "peso_muerto": ["peso muerto"],
    "curl_femoral": ["curl de pierna", "curls de pierna"],
    "extension_cuadriceps": ["extensiones de piernas"],
    "pantorrilla": ["pantorrilla"],
    "curl_biceps": ["curl", "biceps", "bíceps", "predicador", "martillo"],
    "triceps": ["triceps", "tríceps", "agarre estrecho"],
}


def load_base_exercises() -> List[str]:
    if not BASE_FILE.exists():
        return list(DEFAULT_GROUPS.keys())
    out: List[str] = []
    for line in BASE_FILE.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if line and not line.startswith("#"):
            out.append(line)
    return out


def infer_grupo(name: str) -> str:
    if name in DEFAULT_GROUPS:
        return DEFAULT_GROUPS[name]
    n = (name or "").lower()
    if any(k in n for k in ("pecho", "press de banco", "press con barra en banco", "apertura", "cruce", "banca")):
        if "hombro" in n or "militar" in n:
            return "Hombro"
        if "estrecho" in n or "triceps" in n or "tríceps" in n:
            return "Brazo"
        return "Pecho"
    if any(k in n for k in ("remo", "jalón", "jalon", "dominad", "encogimiento", "espalda")):
        return "Espalda"
    if any(k in n for k in ("hombro", "lateral", "vuelo posterior", "deltoid")):
        return "Hombro"
    if any(k in n for k in ("sentadilla", "prensa", "peso muerto", "pierna", "femoral", "pantorrilla", "estocada", "aductor", "hack")):
        return "Pierna"
    if any(k in n for k in ("curl", "biceps", "bíceps", "triceps", "tríceps", "predicador")):
        return "Brazo"
    if any(k in n for k in ("plancha", "crunch", "core", "abdominal")):
        return "Core"
    return "Otro"


def get_grupo(name: str, username: Optional[str] = None) -> str:
    """Prioriza meta del usuario; si no, catálogo por defecto."""
    if username:
        try:
            from .exercises import get_exercise_meta

            meta = get_exercise_meta(username, name)
            g = (meta or {}).get("grupo")
            if g and g != "Otro":
                return str(g)
        except Exception:
            pass
    return infer_grupo(name)


def exercises_in_group(
    grupo: str,
    *,
    username: Optional[str] = None,
    pool: Optional[Sequence[str]] = None,
) -> List[str]:
    names = list(pool) if pool is not None else load_base_exercises()
    if username:
        try:
            from .exercises import list_all_exercises

            names = list_all_exercises(username)
        except Exception:
            pass
    return [n for n in names if get_grupo(n, username) == grupo]


def _score_similarity(a: str, b: str) -> int:
    """Heurística simple: más puntos si comparten subpatrón / tokens."""
    al, bl = a.lower(), b.lower()
    score = 0
    for keys in _SUBPATTERN.values():
        a_hit = any(k in al for k in keys)
        b_hit = any(k in bl for k in keys)
        if a_hit and b_hit:
            score += 3
    for tok in ("press", "remo", "curl", "jalón", "jalon", "sentadilla", "mancuerna", "máquina", "maquina", "polea", "barra"):
        if tok in al and tok in bl:
            score += 1
    return score


def suggest_alternatives(
    exercise: str,
    *,
    n: int = 3,
    username: Optional[str] = None,
    exclude: Optional[Set[str]] = None,
    pool: Optional[Sequence[str]] = None,
) -> List[str]:
    """Devuelve hasta `n` alternativas del mismo grupo muscular, priorizando similitud."""
    exclude = set(exclude or set())
    exclude.add(exercise)
    grupo = get_grupo(exercise, username)
    candidates = [c for c in exercises_in_group(grupo, username=username, pool=pool) if c not in exclude]
    if not candidates:
        # Fallback: cualquier otro del catálogo
        base = list(pool) if pool is not None else load_base_exercises()
        candidates = [c for c in base if c not in exclude]
    ranked = sorted(candidates, key=lambda c: (-_score_similarity(exercise, c), c.lower()))
    return ranked[: max(0, n)]
