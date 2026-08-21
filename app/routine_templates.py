"""Plantillas de entrenamiento predefinidas (sin IA).

Todas las entradas usan nombres exactos de `data/base_exercises.txt`.
Cubre splits × niveles × objetivos con sentido.
"""

from __future__ import annotations

from copy import deepcopy
from typing import Any, Dict, List, Optional


def _item(exercise: str, sets: int, reps: int, *, notes: str = "", rest_sec: int = 90) -> Dict[str, Any]:
    return {
        "exercise": exercise,
        "sets": int(sets),
        "reps": int(reps),
        "weight": 0.0,
        "rest_sec": int(rest_sec),
        "notes": notes,
    }


def _day(name: str, focus: str, items: List[Dict[str, Any]]) -> Dict[str, Any]:
    return {"name": name, "focus": focus, "items": items}


def _scale(items: List[Dict[str, Any]], *, sets_delta: int = 0, reps: Optional[int] = None) -> List[Dict[str, Any]]:
    out = []
    for it in items:
        s = max(2, int(it["sets"]) + sets_delta)
        r = int(reps if reps is not None else it["reps"])
        out.append(_item(it["exercise"], s, r, notes=it.get("notes") or ""))
    return out


TEMPLATE_CATEGORIES = [
    "Split semanal",
    "Full body",
    "Por grupo muscular",
    "Empuje / Tirón",
    "Fuerza",
    "Bro split",
]


# ---------- Bloques de día reutilizables ----------
def day_push_a(level: str = "intermedio") -> Dict[str, Any]:
    base = [
        _item("Press con barra en banco horizontal", 4, 8),
        _item("Press de banco con mancuernas, 30º de inclinación", 3, 10),
        _item("Cruce parado en polea alta con manija", 3, 12),
        _item("Press de hombro en máquina", 3, 10),
        _item("Elevaciones laterales con mancuernas de pies", 3, 15),
        _item("Jalón de triceps en polea alta con cuerda", 3, 12),
    ]
    if level == "principiante":
        items = _scale(base[:5], sets_delta=-1, reps=10)
    elif level == "avanzado":
        items = _scale(base, sets_delta=0) + [_item("Fondos de triceps en máquina", 3, 10)]
    else:
        items = base
    return _day("Push A — Empuje", "Pecho, hombro, tríceps", items)


def day_push_b(level: str = "intermedio") -> Dict[str, Any]:
    base = [
        _item("Press con barra en banco inclinado", 4, 8),
        _item("Press de pecho en banco de maquina de fuerza de martillo", 3, 10),
        _item("Apertura de pecho sentado", 3, 12),
        _item("Press de hombro en máquina Smith", 3, 10),
        _item("Elevación lateral en máquina", 3, 15),
        _item("Press de banco con barra y agarre estrecho", 3, 10),
        _item("Extensiones de triceps, tras nuca, en polea con cuerda", 3, 12),
    ]
    if level == "principiante":
        items = _scale(base[:5], sets_delta=-1, reps=10)
    else:
        items = base if level != "avanzado" else base
    return _day("Push B — Empuje", "Pecho inclinado y hombro", items)


def day_pull_a(level: str = "intermedio") -> Dict[str, Any]:
    base = [
        _item("Dominadas en barra fija con agarre ancho", 4, 8),
        _item("Remo inclinado con barra T agarre ancho", 4, 10),
        _item("Jalón vertical con polea alta y agarre cerrado", 3, 10),
        _item("Remo con polea de agarre cerrado", 3, 12),
        _item("Encogimiento de hombros con mancuernas", 3, 12),
        _item("Curl predicador con barra Z", 3, 10),
        _item("Curl parado a una mano con polea", 3, 12),
    ]
    if level == "principiante":
        items = [
            _item("Jalón vertical con polea alta y agarre cerrado", 3, 10),
            _item("Remo con polea de agarre cerrado", 3, 10),
            _item("Remo de un brazo con mancuerna", 3, 10),
            _item("Vuelo posterior sentado en máquina", 2, 12),
            _item("Curl de biceps con máquina", 2, 12),
        ]
    else:
        items = base
    return _day("Pull A — Tirón", "Espalda y bíceps", items)


def day_pull_b(level: str = "intermedio") -> Dict[str, Any]:
    base = [
        _item("Jalón al frente en máquina martillo", 4, 10),
        _item("Remo de un brazo con mancuerna", 4, 10),
        _item("Remo a dos manos con mancuernas en banco inclinado", 3, 12),
        _item("Remo a un brazo en máquina sentado", 3, 12),
        _item("Vuelo posterior sentado en máquina", 3, 15),
        _item("Curl alterno de biceps con mancuerna", 3, 12),
        _item("Curl de biceps estilo martillo con mancuernas", 3, 12),
    ]
    if level == "principiante":
        items = _scale(base[:5], sets_delta=-1, reps=10)
    else:
        items = base
    return _day("Pull B — Tirón", "Remo y bíceps", items)


def day_legs_a(level: str = "intermedio") -> Dict[str, Any]:
    base = [
        _item("Sentadillas con barra con las piernas separadas", 4, 8),
        _item("Prensa de piernas en posición ancha", 4, 10),
        _item("Extensiones de piernas sentado", 3, 12),
        _item("Curls de pierna sentado", 3, 12),
        _item("Estocada con paso adelante con pesos", 3, 10),
        _item("Elevaciones de pantorrilla en máquina", 4, 12),
    ]
    if level == "principiante":
        items = [
            _item("Sentadillas en máquina Smith", 3, 10),
            _item("Prensa de piernas en posición ancha", 3, 12),
            _item("Extensiones de piernas sentado", 2, 12),
            _item("Curls de pierna sentado", 2, 12),
            _item("Elevaciones de pantorrilla en máquina", 3, 12),
        ]
    elif level == "avanzado":
        items = base + [_item("Entrenamiento de aductores", 3, 12)]
    else:
        items = base
    return _day("Legs A — Cuádriceps", "Pierna (cuádriceps)", items)


def day_legs_b(level: str = "intermedio") -> Dict[str, Any]:
    base = [
        _item("Peso muerto con barra", 4, 6),
        _item("Sentadilla de Hack con postura amplia", 3, 10),
        _item("Curl de piernas en pronación", 3, 12),
        _item("Peso muerto de sumo", 3, 8),
        _item("Entrenamiento de aductores", 3, 12),
        _item("Elevación de pantorrilla sentado", 4, 12),
    ]
    if level == "principiante":
        items = [
            _item("Peso muerto de sumo", 3, 8),
            _item("Sentadillas en máquina Smith", 3, 10),
            _item("Curl de piernas en pronación", 2, 12),
            _item("Estocada con paso adelante con pesos", 2, 10),
            _item("Elevación de pantorrilla sentado", 3, 12),
        ]
    else:
        items = base
    return _day("Legs B — Bisagra", "Isquios y cadena posterior", items)


def day_upper_a(level: str = "intermedio") -> Dict[str, Any]:
    base = [
        _item("Press con barra en banco horizontal", 4, 8),
        _item("Remo con polea de agarre cerrado", 4, 10),
        _item("Press de banco con mancuernas, 30º de inclinación", 3, 10),
        _item("Jalón vertical con polea alta y agarre cerrado", 3, 10),
        _item("Elevaciones laterales con mancuernas de pies", 3, 12),
        _item("Curl alterno de biceps con mancuerna", 3, 12),
        _item("Jalón de triceps en polea alta con cuerda", 3, 12),
    ]
    if level == "principiante":
        items = _scale(base[:5], sets_delta=-1, reps=10)
    elif level == "avanzado":
        items = base + [_item("Vuelo posterior sentado en máquina", 3, 12)]
    else:
        items = base
    return _day("Upper A", "Pecho, espalda, hombro", items)


def day_upper_b(level: str = "intermedio") -> Dict[str, Any]:
    base = [
        _item("Press con barra en banco inclinado", 4, 8),
        _item("Remo de un brazo con mancuerna", 4, 10),
        _item("Press de pecho con mancuernas en banco horizontal", 3, 10),
        _item("Dominadas en barra fija con agarre ancho", 3, 8),
        _item("Press con mancuernas sentado", 3, 10),
        _item("Vuelo posterior sentado en máquina", 3, 12),
        _item("Curl de biceps estilo martillo con mancuernas", 3, 12),
        _item("Extensión de triceps acostado con barra", 3, 10),
    ]
    if level == "principiante":
        items = [
            _item("Press inclinado de pecho en máquina", 3, 10),
            _item("Remo con polea de agarre cerrado", 3, 10),
            _item("Press de hombro en máquina", 3, 10),
            _item("Elevaciones laterales con mancuernas de pies", 2, 12),
            _item("Curl de biceps con máquina", 2, 12),
            _item("Jalón de triceps en polea alta", 2, 12),
        ]
    else:
        items = base
    return _day("Upper B", "Variación superior", items)


def day_fb_a() -> Dict[str, Any]:
    return _day(
        "Full Body A",
        "Sentadilla + press + remo",
        [
            _item("Sentadillas en máquina Smith", 3, 10),
            _item("Press con barra en banco horizontal", 3, 10),
            _item("Remo con polea de agarre cerrado", 3, 10),
            _item("Press de hombro en máquina", 3, 10),
            _item("Curl alterno de biceps con mancuerna", 2, 12),
            _item("Jalón de triceps en polea alta", 2, 12),
        ],
    )


def day_fb_b() -> Dict[str, Any]:
    return _day(
        "Full Body B",
        "Peso muerto + jalón + inclinado",
        [
            _item("Peso muerto con barra", 3, 8),
            _item("Jalón vertical con polea alta y agarre cerrado", 3, 10),
            _item("Press de banco con mancuernas, 30º de inclinación", 3, 10),
            _item("Elevaciones laterales con mancuernas de pies", 3, 12),
            _item("Estocada con paso adelante con pesos", 3, 10),
            _item("Extensiones de triceps acostado con mancuernas", 2, 12),
        ],
    )


def day_fb_c() -> Dict[str, Any]:
    return _day(
        "Full Body C",
        "Prensa + remo + pecho máquina",
        [
            _item("Prensa de piernas en posición ancha", 3, 12),
            _item("Remo de un brazo con mancuerna", 3, 10),
            _item("Press inclinado de pecho en máquina", 3, 10),
            _item("Press con mancuernas sentado", 3, 10),
            _item("Curl de biceps estilo martillo con mancuernas", 2, 12),
            _item("Elevaciones de pantorrilla en máquina", 3, 12),
        ],
    )


def day_pecho() -> Dict[str, Any]:
    return _day(
        "Pecho",
        "Pecho",
        [
            _item("Press con barra en banco horizontal", 4, 8),
            _item("Press con barra en banco inclinado", 4, 8),
            _item("Press de pecho con mancuernas en banco horizontal", 3, 10),
            _item("Apertura de pecho sentado", 3, 12),
            _item("Cruce parado en polea alta con manija", 3, 12),
            _item("Fondo de pecho en barra paralela", 3, 8),
        ],
    )


def day_espalda() -> Dict[str, Any]:
    return _day(
        "Espalda",
        "Espalda",
        [
            _item("Dominadas en barra fija con agarre ancho", 4, 8),
            _item("Remo inclinado con barra T agarre ancho", 4, 10),
            _item("Jalón vertical con polea alta y agarre cerrado", 3, 10),
            _item("Remo de un brazo con mancuerna", 3, 10),
            _item("Remo con polea de agarre cerrado", 3, 12),
            _item("Encogimiento de hombros con mancuernas", 3, 12),
        ],
    )


def day_pierna() -> Dict[str, Any]:
    return _day(
        "Pierna",
        "Pierna",
        [
            _item("Sentadillas con barra con las piernas separadas", 4, 8),
            _item("Prensa de piernas en posición ancha", 4, 10),
            _item("Peso muerto de sumo", 3, 8),
            _item("Extensiones de piernas sentado", 3, 12),
            _item("Curls de pierna sentado", 3, 12),
            _item("Entrenamiento de aductores", 3, 12),
            _item("Elevaciones de pantorrilla en máquina", 4, 12),
        ],
    )


def day_hombro() -> Dict[str, Any]:
    return _day(
        "Hombro",
        "Hombro",
        [
            _item("Press con mancuernas sentado", 4, 8),
            _item("Press de hombro en máquina Smith", 3, 10),
            _item("Elevaciones laterales con mancuernas de pies", 4, 12),
            _item("Elevación lateral de un brazo con polea baja", 3, 12),
            _item("Elevación lateral en máquina", 3, 15),
            _item("Vuelo posterior sentado en máquina", 3, 12),
        ],
    )


def day_brazos() -> Dict[str, Any]:
    return _day(
        "Brazos",
        "Bíceps y tríceps",
        [
            _item("Curl predicador con barra Z", 3, 10),
            _item("Curl alterno de biceps con mancuerna", 3, 12),
            _item("Curl de biceps estilo martillo con mancuernas", 3, 12),
            _item("Extensión de triceps acostado con barra", 3, 10),
            _item("Jalón de triceps en polea alta con cuerda", 3, 12),
            _item("Fondos de triceps en barras paralelas", 3, 8),
        ],
    )


def _tpl(
    tid: str,
    name: str,
    category: str,
    level: str,
    goal: str,
    days_per_week: int,
    duration_min: int,
    description: str,
    days: List[Dict[str, Any]],
) -> Dict[str, Any]:
    return {
        "id": tid,
        "name": name,
        "category": category,
        "level": level,
        "goal": goal,
        "days_per_week": days_per_week,
        "duration_min": duration_min,
        "description": description,
        "days": days,
    }


def _build_templates() -> List[Dict[str, Any]]:
    t: List[Dict[str, Any]] = []

    # —— Full body ——
    for level, goal, dur, desc in [
        ("principiante", "mixto", 45, "Tres sesiones completas, ideal para empezar."),
        ("principiante", "hipertrofia", 50, "Full body con más volumen de aislamiento."),
        ("intermedio", "hipertrofia", 55, "Full body 3 días con buen volumen."),
        ("intermedio", "mixto", 50, "Equilibrio fuerza e hipertrofia en cuerpo completo."),
        ("avanzado", "hipertrofia", 60, "Full body denso; alta densidad de trabajo."),
    ]:
        days = [day_fb_a(), day_fb_b(), day_fb_c()]
        if level == "avanzado":
            days = [
                _day(d["name"], d["focus"], _scale(d["items"], sets_delta=1))
                for d in days
            ]
        t.append(
            _tpl(
                f"fb_3d_{level}_{goal}",
                f"Full Body 3 días · {level}",
                "Full body",
                level,
                goal,
                3,
                dur,
                desc,
                days,
            )
        )

    # —— Upper / Lower ——
    for level, goal, dur in [
        ("principiante", "hipertrofia", 50),
        ("principiante", "mixto", 45),
        ("intermedio", "hipertrofia", 60),
        ("intermedio", "mixto", 55),
        ("avanzado", "hipertrofia", 65),
        ("avanzado", "fuerza", 60),
    ]:
        days = [
            day_upper_a(level),
            day_legs_a(level),
            day_upper_b(level),
            day_legs_b(level),
        ]
        if goal == "fuerza":
            days = [
                _day(
                    days[0]["name"],
                    days[0]["focus"],
                    _scale(days[0]["items"][:5], reps=5) + days[0]["items"][5:],
                ),
                _day(
                    days[1]["name"],
                    days[1]["focus"],
                    _scale(days[1]["items"][:3], reps=5) + days[1]["items"][3:],
                ),
                days[2],
                days[3],
            ]
        t.append(
            _tpl(
                f"ul_4d_{level}_{goal}",
                f"Upper / Lower 4 días · {level}",
                "Split semanal",
                level,
                goal,
                4,
                dur,
                f"Dos upper + dos lower. Nivel {level}, objetivo {goal}.",
                days,
            )
        )

    # —— PPL 3 días ——
    for level, goal, dur in [
        ("principiante", "hipertrofia", 50),
        ("principiante", "mixto", 45),
        ("intermedio", "hipertrofia", 60),
        ("intermedio", "mixto", 55),
        ("avanzado", "hipertrofia", 65),
    ]:
        t.append(
            _tpl(
                f"ppl_3d_{level}_{goal}",
                f"PPL 3 días · {level}",
                "Split semanal",
                level,
                goal,
                3,
                dur,
                f"Push / Pull / Legs una vez por semana. {level}, {goal}.",
                [day_push_a(level), day_pull_a(level), day_legs_a(level)],
            )
        )

    # —— PPL 6 días ——
    for level, goal, dur in [
        ("intermedio", "hipertrofia", 55),
        ("avanzado", "hipertrofia", 60),
        ("avanzado", "mixto", 55),
    ]:
        t.append(
            _tpl(
                f"ppl_6d_{level}_{goal}",
                f"PPL 6 días · {level}",
                "Split semanal",
                level,
                goal,
                6,
                dur,
                f"PPL dos veces/semana. Alto volumen — {level}.",
                [
                    day_push_a(level),
                    day_pull_a(level),
                    day_legs_a(level),
                    day_push_b(level),
                    day_pull_b(level),
                    day_legs_b(level),
                ],
            )
        )

    # —— Bro split 5 días ——
    for level in ("intermedio", "avanzado"):
        t.append(
            _tpl(
                f"bro_5d_{level}_hipertrofia",
                f"Bro split 5 días · {level}",
                "Bro split",
                level,
                "hipertrofia",
                5,
                50 if level == "intermedio" else 55,
                "Un grupo muscular por día: pecho, espalda, pierna, hombro, brazos.",
                [day_pecho(), day_espalda(), day_pierna(), day_hombro(), day_brazos()],
            )
        )

    # —— Por grupo ——
    for name, builder, focus in [
        ("Solo pecho", day_pecho, "pecho"),
        ("Solo espalda", day_espalda, "espalda"),
        ("Solo pierna", day_pierna, "pierna"),
        ("Solo hombro", day_hombro, "hombro"),
        ("Solo brazos", day_brazos, "brazos"),
    ]:
        for level in ("principiante", "intermedio", "avanzado"):
            d = builder()
            items = d["items"]
            if level == "principiante":
                items = _scale(items[:5], sets_delta=-1, reps=10)
            elif level == "avanzado":
                items = _scale(items, sets_delta=1)
            t.append(
                _tpl(
                    f"solo_{focus}_{level}",
                    f"{name} · {level}",
                    "Por grupo muscular",
                    level,
                    "hipertrofia",
                    1,
                    40 if level == "principiante" else 50,
                    f"Sesión enfocada en {focus}.",
                    [_day(d["name"], d["focus"], items)],
                )
            )

    # —— Empuje / Tirón ——
    for level in ("principiante", "intermedio", "avanzado"):
        t.append(
            _tpl(
                f"push_day_{level}",
                f"Día de empuje · {level}",
                "Empuje / Tirón",
                level,
                "hipertrofia",
                1,
                45 if level == "principiante" else 55,
                "Pecho + hombro + tríceps.",
                [day_push_a(level)],
            )
        )
        t.append(
            _tpl(
                f"pull_day_{level}",
                f"Día de tirón · {level}",
                "Empuje / Tirón",
                level,
                "hipertrofia",
                1,
                45 if level == "principiante" else 55,
                "Espalda + bíceps + posterior.",
                [day_pull_a(level)],
            )
        )

    # —— Fuerza ——
    fuerza_days = [
        _day(
            "Fuerza A — Press",
            "Press banca",
            [
                _item("Press con barra en banco horizontal", 5, 5),
                _item("Press con barra en banco inclinado", 4, 6),
                _item("Remo con polea de agarre cerrado", 4, 8),
                _item("Press de banco con barra y agarre estrecho", 3, 6),
                _item("Elevaciones laterales con mancuernas de pies", 3, 12),
            ],
        ),
        _day(
            "Fuerza B — Sentadilla",
            "Sentadilla",
            [
                _item("Sentadillas con barra con las piernas separadas", 5, 5),
                _item("Prensa de piernas en posición ancha", 4, 8),
                _item("Curls de pierna sentado", 3, 10),
                _item("Estocada con paso adelante con pesos", 3, 8),
                _item("Elevaciones de pantorrilla en máquina", 4, 10),
            ],
        ),
        _day(
            "Fuerza C — Peso muerto",
            "Peso muerto",
            [
                _item("Peso muerto con barra", 5, 5),
                _item("Remo inclinado con barra T agarre ancho", 4, 6),
                _item("Dominadas en barra fija con agarre ancho", 4, 6),
                _item("Press con mancuernas sentado", 3, 8),
                _item("Curl predicador con barra Z", 3, 8),
            ],
        ),
    ]
    for level, dur in [("principiante", 50), ("intermedio", 55), ("avanzado", 65)]:
        days = fuerza_days
        if level == "principiante":
            days = [
                _day(d["name"], d["focus"], _scale(d["items"], sets_delta=-1, reps=6))
                for d in fuerza_days
            ]
        elif level == "avanzado":
            days = [
                _day(d["name"], d["focus"], _scale(d["items"], sets_delta=1))
                for d in fuerza_days
            ]
        t.append(
            _tpl(
                f"fuerza_3d_{level}",
                f"Fuerza básicos 3 días · {level}",
                "Fuerza",
                level,
                "fuerza",
                3,
                dur,
                "Compuestos con pocas reps y más series de calidad.",
                days,
            )
        )

    return t


TEMPLATES: List[Dict[str, Any]] = _build_templates()


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
                "rest_sec": int(it.get("rest_sec") or 90),
            }
        )
    return items
