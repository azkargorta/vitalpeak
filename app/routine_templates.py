"""Plantillas de entrenamiento predefinidas (sin IA).

Todas las entradas usan nombres exactos de `data/base_exercises.txt`.
"""

from __future__ import annotations

from copy import deepcopy
from typing import Any, Dict, List, Optional


def _item(exercise: str, sets: int, reps: int, *, notes: str = "") -> Dict[str, Any]:
    return {
        "exercise": exercise,
        "sets": int(sets),
        "reps": int(reps),
        "weight": 0.0,
        "notes": notes,
    }


# Categorías pensadas como app pro
TEMPLATE_CATEGORIES = [
    "Split semanal",
    "Full body",
    "Por grupo muscular",
    "Empuje / Tirón",
    "Fuerza",
]


TEMPLATES: List[Dict[str, Any]] = [
    # ---------- Split semanal ----------
    {
        "id": "ul_4d",
        "name": "Upper / Lower (4 días)",
        "category": "Split semanal",
        "level": "intermedio",
        "goal": "hipertrofia",
        "days_per_week": 4,
        "duration_min": 60,
        "description": "Clásico 4 días: dos de tren superior y dos de tren inferior. Ideal para progresar con buen recuperación.",
        "days": [
            {
                "name": "Upper A — Empuje + Tirón",
                "focus": "Pecho, espalda, hombro",
                "items": [
                    _item("Press con barra en banco horizontal", 4, 8),
                    _item("Remo con polea de agarre cerrado", 4, 10),
                    _item("Press de banco con mancuernas, 30º de inclinación", 3, 10),
                    _item("Jalón vertical con polea alta y agarre cerrado", 3, 10),
                    _item("Elevaciones laterales con mancuernas de pies", 3, 12),
                    _item("Curl alterno de biceps con mancuerna", 3, 12),
                    _item("Jalón de triceps en polea alta con cuerda", 3, 12),
                ],
            },
            {
                "name": "Lower A — Cuádriceps",
                "focus": "Pierna (cuádriceps dominante)",
                "items": [
                    _item("Sentadillas con barra con las piernas separadas", 4, 8),
                    _item("Prensa de piernas en posición ancha", 4, 10),
                    _item("Extensiones de piernas sentado", 3, 12),
                    _item("Curls de pierna sentado", 3, 12),
                    _item("Estocada con paso adelante con pesos", 3, 10),
                    _item("Elevaciones de pantorrilla en máquina", 4, 12),
                ],
            },
            {
                "name": "Upper B — Variación",
                "focus": "Pecho inclinado, remo, hombro",
                "items": [
                    _item("Press con barra en banco inclinado", 4, 8),
                    _item("Remo de un brazo con mancuerna", 4, 10),
                    _item("Press de pecho con mancuernas en banco horizontal", 3, 10),
                    _item("Dominadas en barra fija con agarre ancho", 3, 8),
                    _item("Press con mancuernas sentado", 3, 10),
                    _item("Vuelo posterior sentado en máquina", 3, 12),
                    _item("Curl de biceps estilo martillo con mancuernas", 3, 12),
                    _item("Extensión de triceps acostado con barra", 3, 10),
                ],
            },
            {
                "name": "Lower B — Bisagra / isquios",
                "focus": "Peso muerto y cadena posterior",
                "items": [
                    _item("Peso muerto con barra", 4, 6),
                    _item("Sentadilla de Hack con postura amplia", 3, 10),
                    _item("Curl de piernas en pronación", 3, 12),
                    _item("Peso muerto de sumo", 3, 8),
                    _item("Entrenamiento de aductores", 3, 12),
                    _item("Elevación de pantorrilla sentado", 4, 12),
                ],
            },
        ],
    },
    {
        "id": "ppl_6d",
        "name": "Push / Pull / Legs (6 días)",
        "category": "Split semanal",
        "level": "avanzado",
        "goal": "hipertrofia",
        "days_per_week": 6,
        "duration_min": 55,
        "description": "PPL dos veces por semana. Alto volumen; requiere buena recuperación.",
        "days": [
            {
                "name": "Push A",
                "focus": "Pecho, hombro, tríceps",
                "items": [
                    _item("Press con barra en banco horizontal", 4, 8),
                    _item("Press de banco con mancuernas, 30º de inclinación", 3, 10),
                    _item("Cruce parado en polea alta con manija", 3, 12),
                    _item("Press de hombro en máquina", 3, 10),
                    _item("Elevaciones laterales con mancuernas de pies", 3, 15),
                    _item("Jalón de triceps en polea alta", 3, 12),
                    _item("Fondos de triceps en máquina", 3, 10),
                ],
            },
            {
                "name": "Pull A",
                "focus": "Espalda y bíceps",
                "items": [
                    _item("Dominadas en barra fija con agarre ancho", 4, 8),
                    _item("Remo inclinado con barra T agarre ancho", 4, 10),
                    _item("Jalón vertical con polea alta y agarre cerrado", 3, 10),
                    _item("Remo con polea de agarre cerrado", 3, 12),
                    _item("Encogimiento de hombros con mancuernas", 3, 12),
                    _item("Curl predicador con barra Z", 3, 10),
                    _item("Curl parado a una mano con polea", 3, 12),
                ],
            },
            {
                "name": "Legs A",
                "focus": "Cuádriceps y pantorrillas",
                "items": [
                    _item("Sentadillas en máquina Smith", 4, 8),
                    _item("Prensa de piernas en posición ancha", 4, 10),
                    _item("Extensiones de piernas sentado", 3, 12),
                    _item("Curls de pierna sentado", 3, 12),
                    _item("Estocada con paso adelante con pesos", 3, 10),
                    _item("Elevaciones de pantorrilla en máquina", 4, 15),
                ],
            },
            {
                "name": "Push B",
                "focus": "Pecho inclinado y hombro",
                "items": [
                    _item("Press con barra en banco inclinado", 4, 8),
                    _item("Press de pecho en banco de maquina de fuerza de martillo", 3, 10),
                    _item("Apertura de pecho sentado", 3, 12),
                    _item("Press de hombro en máquina Smith", 3, 10),
                    _item("Elevación lateral en máquina", 3, 15),
                    _item("Press de banco con barra y agarre estrecho", 3, 10),
                    _item("Extensiones de triceps, tras nuca, en polea con cuerda", 3, 12),
                ],
            },
            {
                "name": "Pull B",
                "focus": "Remo y bíceps",
                "items": [
                    _item("Jalón al frente en máquina martillo", 4, 10),
                    _item("Remo de un brazo con mancuerna", 4, 10),
                    _item("Remo a dos manos con mancuernas en banco inclinado", 3, 12),
                    _item("Remo a un brazo en máquina sentado", 3, 12),
                    _item("Vuelo posterior sentado en máquina", 3, 15),
                    _item("Curl alterno de biceps con mancuerna", 3, 12),
                    _item("Curl de biceps estilo martillo con mancuernas", 3, 12),
                ],
            },
            {
                "name": "Legs B",
                "focus": "Bisagra y glúteo/isquios",
                "items": [
                    _item("Peso muerto de sumo", 4, 6),
                    _item("Sentadilla de Hack con postura amplia", 3, 10),
                    _item("Curl de piernas en pronación", 3, 12),
                    _item("Curl de pierna parado con polea", 3, 12),
                    _item("Entrenamiento de aductores", 3, 15),
                    _item("Elevación de pantorrilla sentado", 4, 15),
                ],
            },
        ],
    },
    {
        "id": "ppl_3d",
        "name": "Push / Pull / Legs (3 días)",
        "category": "Split semanal",
        "level": "intermedio",
        "goal": "hipertrofia",
        "days_per_week": 3,
        "duration_min": 60,
        "description": "Una pasada semanal de empuje, tirón y pierna. Perfecto si entrenas 3 días.",
        "days": [
            {
                "name": "Push — Empuje",
                "focus": "Pecho, hombro, tríceps",
                "items": [
                    _item("Press con barra en banco horizontal", 4, 8),
                    _item("Press inclinado de pecho en máquina", 3, 10),
                    _item("Press con mancuernas sentado", 3, 10),
                    _item("Elevaciones laterales con mancuernas de pies", 3, 12),
                    _item("Fondo de pecho en barra paralela", 3, 8),
                    _item("Jalón de triceps en polea alta con cuerda", 3, 12),
                ],
            },
            {
                "name": "Pull — Tirón",
                "focus": "Espalda y bíceps",
                "items": [
                    _item("Jalón vertical con polea alta y agarre cerrado", 4, 10),
                    _item("Remo con polea de agarre cerrado", 4, 10),
                    _item("Remo de un brazo con mancuerna", 3, 10),
                    _item("Vuelo posterior sentado en máquina", 3, 12),
                    _item("Curl de biceps con máquina", 3, 12),
                    _item("Curl con giro con mancuernas", 3, 12),
                ],
            },
            {
                "name": "Legs — Pierna",
                "focus": "Cuádriceps, isquios, pantorrilla",
                "items": [
                    _item("Sentadillas con barra con las piernas separadas", 4, 8),
                    _item("Peso muerto con barra", 3, 8),
                    _item("Prensa de piernas en posición ancha", 3, 12),
                    _item("Extensiones de piernas sentado", 3, 12),
                    _item("Curls de pierna sentado", 3, 12),
                    _item("Elevaciones de pantorrilla en máquina", 4, 12),
                ],
            },
        ],
    },
    # ---------- Full body ----------
    {
        "id": "fb_3d",
        "name": "Full Body (3 días)",
        "category": "Full body",
        "level": "principiante",
        "goal": "mixto",
        "days_per_week": 3,
        "duration_min": 50,
        "description": "Tres sesiones de cuerpo completo con patrones básicos. Ideal para empezar o volver a entrenar.",
        "days": [
            {
                "name": "Full Body A",
                "focus": "Sentadilla + press + remo",
                "items": [
                    _item("Sentadillas en máquina Smith", 3, 10),
                    _item("Press con barra en banco horizontal", 3, 10),
                    _item("Remo con polea de agarre cerrado", 3, 10),
                    _item("Press de hombro en máquina", 3, 10),
                    _item("Curl alterno de biceps con mancuerna", 2, 12),
                    _item("Jalón de triceps en polea alta", 2, 12),
                ],
            },
            {
                "name": "Full Body B",
                "focus": "Peso muerto + jalón + press inclinado",
                "items": [
                    _item("Peso muerto con barra", 3, 8),
                    _item("Jalón vertical con polea alta y agarre cerrado", 3, 10),
                    _item("Press de banco con mancuernas, 30º de inclinación", 3, 10),
                    _item("Elevaciones laterales con mancuernas de pies", 3, 12),
                    _item("Estocada con paso adelante con pesos", 3, 10),
                    _item("Extensiones de triceps acostado con mancuernas", 2, 12),
                ],
            },
            {
                "name": "Full Body C",
                "focus": "Prensa + remo unilateral + pecho máquina",
                "items": [
                    _item("Prensa de piernas en posición ancha", 3, 12),
                    _item("Remo de un brazo con mancuerna", 3, 10),
                    _item("Press inclinado de pecho en máquina", 3, 10),
                    _item("Press con mancuernas sentado", 3, 10),
                    _item("Curl de biceps estilo martillo con mancuernas", 2, 12),
                    _item("Elevaciones de pantorrilla en máquina", 3, 12),
                ],
            },
        ],
    },
    # ---------- Por grupo muscular ----------
    {
        "id": "solo_pecho",
        "name": "Solo pecho",
        "category": "Por grupo muscular",
        "level": "intermedio",
        "goal": "hipertrofia",
        "days_per_week": 1,
        "duration_min": 45,
        "description": "Sesión enfocada en pecho: plano, inclinado, aislamiento y fondos.",
        "days": [
            {
                "name": "Pecho",
                "focus": "Pecho",
                "items": [
                    _item("Press con barra en banco horizontal", 4, 8),
                    _item("Press con barra en banco inclinado", 4, 8),
                    _item("Press de pecho con mancuernas en banco horizontal", 3, 10),
                    _item("Apertura de pecho sentado", 3, 12),
                    _item("Cruce parado en polea alta con manija", 3, 12),
                    _item("Fondo de pecho en barra paralela", 3, 8),
                ],
            },
        ],
    },
    {
        "id": "solo_espalda",
        "name": "Solo espalda",
        "category": "Por grupo muscular",
        "level": "intermedio",
        "goal": "hipertrofia",
        "days_per_week": 1,
        "duration_min": 45,
        "description": "Tirón vertical, horizontal y trabajo de trapecio.",
        "days": [
            {
                "name": "Espalda",
                "focus": "Espalda",
                "items": [
                    _item("Dominadas en barra fija con agarre ancho", 4, 8),
                    _item("Remo inclinado con barra T agarre ancho", 4, 10),
                    _item("Jalón vertical con polea alta y agarre cerrado", 3, 10),
                    _item("Remo de un brazo con mancuerna", 3, 10),
                    _item("Remo con polea de agarre cerrado", 3, 12),
                    _item("Encogimiento de hombros con mancuernas", 3, 12),
                ],
            },
        ],
    },
    {
        "id": "solo_pierna",
        "name": "Solo pierna",
        "category": "Por grupo muscular",
        "level": "intermedio",
        "goal": "hipertrofia",
        "days_per_week": 1,
        "duration_min": 55,
        "description": "Cuádriceps, isquios, aductores y pantorrillas.",
        "days": [
            {
                "name": "Pierna",
                "focus": "Pierna",
                "items": [
                    _item("Sentadillas con barra con las piernas separadas", 4, 8),
                    _item("Prensa de piernas en posición ancha", 4, 10),
                    _item("Peso muerto de sumo", 3, 8),
                    _item("Extensiones de piernas sentado", 3, 12),
                    _item("Curls de pierna sentado", 3, 12),
                    _item("Entrenamiento de aductores", 3, 12),
                    _item("Elevaciones de pantorrilla en máquina", 4, 12),
                ],
            },
        ],
    },
    {
        "id": "solo_hombro",
        "name": "Solo hombro",
        "category": "Por grupo muscular",
        "level": "intermedio",
        "goal": "hipertrofia",
        "days_per_week": 1,
        "duration_min": 40,
        "description": "Press + laterales + deltoides posterior.",
        "days": [
            {
                "name": "Hombro",
                "focus": "Hombro",
                "items": [
                    _item("Press con mancuernas sentado", 4, 8),
                    _item("Press de hombro en máquina Smith", 3, 10),
                    _item("Elevaciones laterales con mancuernas de pies", 4, 12),
                    _item("Elevación lateral de un brazo con polea baja", 3, 12),
                    _item("Elevación lateral en máquina", 3, 15),
                    _item("Vuelo posterior sentado en máquina", 3, 12),
                ],
            },
        ],
    },
    {
        "id": "solo_brazos",
        "name": "Solo brazos",
        "category": "Por grupo muscular",
        "level": "intermedio",
        "goal": "hipertrofia",
        "days_per_week": 1,
        "duration_min": 40,
        "description": "Bíceps y tríceps con variedad de ángulos.",
        "days": [
            {
                "name": "Brazos",
                "focus": "Brazo",
                "items": [
                    _item("Curl predicador con barra Z", 3, 10),
                    _item("Curl alterno de biceps con mancuerna", 3, 12),
                    _item("Curl de biceps estilo martillo con mancuernas", 3, 12),
                    _item("Extensión de triceps acostado con barra", 3, 10),
                    _item("Jalón de triceps en polea alta con cuerda", 3, 12),
                    _item("Fondos de triceps en barras paralelas", 3, 8),
                ],
            },
        ],
    },
    # ---------- Empuje / Tirón ----------
    {
        "id": "push_day",
        "name": "Día de empuje",
        "category": "Empuje / Tirón",
        "level": "intermedio",
        "goal": "hipertrofia",
        "days_per_week": 1,
        "duration_min": 50,
        "description": "Pecho + hombro + tríceps en una sola sesión.",
        "days": [
            {
                "name": "Empuje",
                "focus": "Pecho / Hombro / Tríceps",
                "items": [
                    _item("Press con barra en banco horizontal", 4, 8),
                    _item("Press inclinado en máquina Smith", 3, 10),
                    _item("Apertura de pecho sentado", 3, 12),
                    _item("Press de hombro en máquina", 3, 10),
                    _item("Elevaciones laterales con mancuernas de pies", 3, 12),
                    _item("Press de banco con barra y agarre estrecho", 3, 10),
                    _item("Extensiones de triceps de pie, tras nuca, con polea", 3, 12),
                ],
            },
        ],
    },
    {
        "id": "pull_day",
        "name": "Día de tirón",
        "category": "Empuje / Tirón",
        "level": "intermedio",
        "goal": "hipertrofia",
        "days_per_week": 1,
        "duration_min": 50,
        "description": "Espalda + bíceps + deltoides posterior.",
        "days": [
            {
                "name": "Tirón",
                "focus": "Espalda / Bíceps",
                "items": [
                    _item("Dominadas en barra fija con agarre ancho", 4, 8),
                    _item("Remo en máquina Smith con agarre prono", 4, 10),
                    _item("Jalón al frente en máquina martillo", 3, 10),
                    _item("Remo a un brazo en máquina sentado", 3, 12),
                    _item("Vuelo posterior sentado en máquina", 3, 12),
                    _item("Curl del predicador de un brazo con mancuernas", 3, 12),
                    _item("Curl parado a una mano con polea", 3, 12),
                ],
            },
        ],
    },
    # ---------- Fuerza ----------
    {
        "id": "fuerza_3d",
        "name": "Fuerza — básicos (3 días)",
        "category": "Fuerza",
        "level": "intermedio",
        "goal": "fuerza",
        "days_per_week": 3,
        "duration_min": 55,
        "description": "Enfoque en compuestos con menos reps y más series de calidad.",
        "days": [
            {
                "name": "Fuerza A — Press",
                "focus": "Press banca y accesorios",
                "items": [
                    _item("Press con barra en banco horizontal", 5, 5),
                    _item("Press con barra en banco inclinado", 4, 6),
                    _item("Remo con polea de agarre cerrado", 4, 8),
                    _item("Press de banco con barra y agarre estrecho", 3, 6),
                    _item("Elevaciones laterales con mancuernas de pies", 3, 12),
                ],
            },
            {
                "name": "Fuerza B — Sentadilla",
                "focus": "Sentadilla y pierna",
                "items": [
                    _item("Sentadillas con barra con las piernas separadas", 5, 5),
                    _item("Prensa de piernas en posición ancha", 4, 8),
                    _item("Curls de pierna sentado", 3, 10),
                    _item("Estocada con paso adelante con pesos", 3, 8),
                    _item("Elevaciones de pantorrilla en máquina", 4, 10),
                ],
            },
            {
                "name": "Fuerza C — Peso muerto",
                "focus": "Peso muerto y tirón",
                "items": [
                    _item("Peso muerto con barra", 5, 5),
                    _item("Remo inclinado con barra T agarre ancho", 4, 6),
                    _item("Dominadas en barra fija con agarre ancho", 4, 6),
                    _item("Press con mancuernas sentado", 3, 8),
                    _item("Curl predicador con barra Z", 3, 8),
                ],
            },
        ],
    },
]


def list_templates(
    *,
    category: Optional[str] = None,
    level: Optional[str] = None,
    goal: Optional[str] = None,
) -> List[Dict[str, Any]]:
    out = TEMPLATES
    if category:
        out = [t for t in out if t.get("category") == category]
    if level:
        out = [t for t in out if t.get("level") == level]
    if goal:
        out = [t for t in out if t.get("goal") == goal]
    return out


def get_template(template_id: str) -> Optional[Dict[str, Any]]:
    for t in TEMPLATES:
        if t.get("id") == template_id:
            return deepcopy(t)
    return None


def instantiate_template(template_id: str) -> Optional[Dict[str, Any]]:
    """Copia editable de la plantilla (para el editor de sesión)."""
    return get_template(template_id)


def day_to_routine_items(day: Dict[str, Any]) -> List[Dict[str, Any]]:
    items = []
    for it in day.get("items") or []:
        items.append(
            {
                "exercise": it.get("exercise"),
                "sets": int(it.get("sets") or 3),
                "reps": int(it.get("reps") or 10),
                "weight": float(it.get("weight") or 0.0),
            }
        )
    return items
