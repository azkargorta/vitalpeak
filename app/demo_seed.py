
from __future__ import annotations

import os
import random
import datetime as _dt
from typing import Dict, List, Any

from .datastore import (
    register_user,
    load_user,
    save_user,
    set_password,
    set_account_email,
    set_recovery_email,
)


def _iso(d: _dt.date) -> str:
    return d.isoformat()


def _maybe_add_routine(rutinas: List[Dict[str, Any]], name: str, items: List[Dict[str, Any]]) -> None:
    if any(r.get("name") == name for r in rutinas):
        return
    rutinas.append({"name": name, "items": items})


def _conf(key: str, default: str = "") -> str:
    # Prioridad: Streamlit Secrets > ENV
    try:
        import streamlit as st  # type: ignore
        if hasattr(st, "secrets") and key in st.secrets:
            return str(st.secrets.get(key, default))
    except Exception:
        pass
    return os.getenv(key, default)



def maybe_seed_admin() -> None:
    """
    Crea (si no existe) un usuario DEMO 'admin' con datos suficientes para probar la app.

    Por seguridad, puedes desactivar el seed poniendo:
      - variable de entorno: VITALPEAK_SEED=0
    """
    if _conf("VITALPEAK_SEED", "1").strip() in ("0", "false", "False", "no", "NO"):
        return

    # Credenciales por defecto (DEMO). Se pueden sobreescribir por Secrets/ENV.
    username = _conf("VITALPEAK_ADMIN_USER", "admin").strip() or "admin"
    email = _conf("VITALPEAK_ADMIN_EMAIL", "gg@gg.com").strip() or "gg@gg.com"
    password = _conf("VITALPEAK_ADMIN_PASSWORD", "admin")

    # 1) Crear usuario si no existe
    register_user(username, password, email=email)

    # 2) Forzar credenciales/Emails del usuario demo (lo pidió el proyecto)
    #    Nota: si lo quieres desactivar, pon VITALPEAK_SEED=0.
    set_password(username, password)
    set_account_email(username, email)
    set_recovery_email(username, email)

    data = load_user(username) or {}

    # 3) Completar datos básicos sin pisar si ya existen (pero ya hemos forzado emails arriba)
    data.setdefault("email", email)
    data.setdefault("recovery_email", email)

    profile = data.get("profile") or {}
    if not profile:
        profile = {
            "first_name": "Admin",
            "last_name": "Vitalpeak",
            "birthdate": "1990-01-01",
            "gender": "Prefiero no decir",
            "notes": "Usuario DEMO para pruebas internas.",
        }
    data["profile"] = profile

    # 4) Peso (últimos ~60 días)
    weights = data.get("weights") or []
    if not weights:
        today = _dt.date.today()
        days = 60
        base = 82.0
        # tendencia suave + pequeñas variaciones (para que la gráfica se vea real)
        for i in range(days):
            d = today - _dt.timedelta(days=(days - 1 - i))
            trend = -0.04 * i  # -2.4 kg en 60 días aprox
            noise = random.uniform(-0.2, 0.2)
            w = base + trend + noise
            weights.append({"date": _iso(d), "weight": round(w, 1)})
        data["weights"] = weights

    # 5) Ejercicios custom + meta (para probar gestor)
    customs = data.get("custom_exercises") or []
    meta = data.get("exercise_meta") or {}

    def add_custom(name: str, grupo: str):
        if name not in customs:
            customs.append(name)
        meta.setdefault(name, {"grupo": grupo, "imagen": None})

    add_custom("Plancha (isométrico)", "Core")
    add_custom("Hip thrust con barra", "Pierna")
    add_custom("Curl martillo con mancuernas", "Brazo")

    data["custom_exercises"] = customs
    data["exercise_meta"] = meta

    # 6) Rutinas DEMO (4 bloques típicos)
    rutinas = data.get("rutinas") or []
    if not rutinas:
        _maybe_add_routine(
            rutinas,
            "Full Body (DEMO)",
            [
                {"exercise": "Sentadilla de Hack con postura amplia", "sets": 4, "reps": 8, "weight": 60.0},
                {"exercise": "Press con barra en banco horizontal", "sets": 4, "reps": 8, "weight": 50.0},
                {"exercise": "Remo de un brazo con mancuerna", "sets": 3, "reps": 10, "weight": 22.5},
                {"exercise": "Peso muerto con barra", "sets": 3, "reps": 6, "weight": 70.0},
                {"exercise": "Plancha (isométrico)", "sets": 3, "reps": 45, "weight": 0.0},
            ],
        )
        _maybe_add_routine(
            rutinas,
            "Push (DEMO)",
            [
                {"exercise": "Press con barra en banco inclinado", "sets": 4, "reps": 10, "weight": 45.0},
                {"exercise": "Apertura de pecho sentado", "sets": 3, "reps": 12, "weight": 35.0},
                {"exercise": "Press de hombro en máquina", "sets": 3, "reps": 10, "weight": 30.0},
                {"exercise": "Jalón de triceps en polea alta con cuerda", "sets": 3, "reps": 12, "weight": 25.0},
            ],
        )
        _maybe_add_routine(
            rutinas,
            "Pull (DEMO)",
            [
                {"exercise": "Remo inclinado con barra T agarre ancho", "sets": 4, "reps": 8, "weight": 40.0},
                {"exercise": "Remo con polea de agarre cerrado", "sets": 3, "reps": 10, "weight": 45.0},
                {"exercise": "Curl martillo con mancuernas", "sets": 3, "reps": 12, "weight": 12.5},
            ],
        )
        _maybe_add_routine(
            rutinas,
            "Legs (DEMO)",
            [
                {"exercise": "Prensa de piernas en posición ancha", "sets": 4, "reps": 12, "weight": 120.0},
                {"exercise": "Extensiones de piernas sentado", "sets": 3, "reps": 12, "weight": 40.0},
                {"exercise": "Curls de pierna sentado", "sets": 3, "reps": 12, "weight": 30.0},
                {"exercise": "Hip thrust con barra", "sets": 4, "reps": 10, "weight": 70.0},
            ],
        )
        data["rutinas"] = rutinas

    # 7) Planificador de rutinas (últimos 60 días + próximos 14)
    plan = dict(data.get("routine_plan", {}) or {})
    if not plan and data.get("rutinas"):
        routine_names = [r["name"] for r in data["rutinas"]]
        name_map = {
            "Push (DEMO)": "Push (DEMO)",
            "Pull (DEMO)": "Pull (DEMO)",
            "Legs (DEMO)": "Legs (DEMO)",
            "Full Body (DEMO)": "Full Body (DEMO)",
        }
        today = _dt.date.today()
        # patrón: L Push, M Pull, X descanso, J Legs, V Full Body, S descanso/extra, D descanso
        for offset in range(-60, 15):
            d = today + _dt.timedelta(days=offset)
            wd = d.weekday()  # 0=L
            if wd == 0:
                plan[_iso(d)] = name_map["Push (DEMO)"]
            elif wd == 1:
                plan[_iso(d)] = name_map["Pull (DEMO)"]
            elif wd == 3:
                plan[_iso(d)] = name_map["Legs (DEMO)"]
            elif wd == 4:
                plan[_iso(d)] = name_map["Full Body (DEMO)"]
            elif wd == 5:
                # sábado: si quieres probar un 5º día, alterna Push/Pull
                plan[_iso(d)] = routine_names[(offset % len(routine_names))]
            # miércoles (2) y domingo (6): libre por defecto
        data["routine_plan"] = plan

    # 8) Entrenamientos (últimos ~60 días) con sobrecarga progresiva suave
    entrenos = data.get("entrenamientos") or []
    if not entrenos:
        today = _dt.date.today()

        # ejercicios por rutina (coherente con lo que hay en rutinas)
        push_ex = [
            ("Press con barra en banco inclinado", 45.0),
            ("Apertura de pecho sentado", 35.0),
            ("Press de hombro en máquina", 30.0),
            ("Jalón de triceps en polea alta con cuerda", 25.0),
        ]
        pull_ex = [
            ("Remo inclinado con barra T agarre ancho", 40.0),
            ("Remo con polea de agarre cerrado", 45.0),
            ("Curl martillo con mancuernas", 12.5),
        ]
        legs_ex = [
            ("Prensa de piernas en posición ancha", 120.0),
            ("Extensiones de piernas sentado", 40.0),
            ("Curls de pierna sentado", 30.0),
            ("Hip thrust con barra", 70.0),
        ]
        full_ex = [
            ("Sentadilla de Hack con postura amplia", 60.0),
            ("Press con barra en banco horizontal", 50.0),
            ("Remo de un brazo con mancuerna", 22.5),
            ("Peso muerto con barra", 70.0),
            ("Plancha (isométrico)", 0.0),
        ]

        def _session_rows(d: _dt.date, ex_list: list[tuple[str, float]], *, reps_base: int, inc: float, session_idx: int):
            d_iso = _iso(d)
            rows = []
            for ex, base_w in ex_list:
                # progresión: +inc cada 2 sesiones aprox
                prog = (session_idx // 2) * inc
                w = max(0.0, base_w + prog)
                sets = 3 if ex != "Plancha (isométrico)" else 2
                for setn in range(1, sets + 1):
                    reps = reps_base - (setn - 1)
                    if ex == "Plancha (isométrico)":
                        reps = 45 + (session_idx % 3) * 5
                    rows.append({"date": d_iso, "exercise": ex, "set": setn, "reps": int(reps), "weight": float(round(w, 1))})
            return rows

        # Generar sesiones solo en días con plan asignado (L/M/J/V y algunos S)
        session_idx = 0
        for offset in range(60, -1, -1):
            d = today - _dt.timedelta(days=offset)
            rt = (data.get("routine_plan") or {}).get(_iso(d))
            if not rt:
                continue
            if "Push" in rt:
                entrenos.extend(_session_rows(d, push_ex, reps_base=12, inc=1.0, session_idx=session_idx))
            elif "Pull" in rt:
                entrenos.extend(_session_rows(d, pull_ex, reps_base=12, inc=1.0, session_idx=session_idx))
            elif "Legs" in rt:
                entrenos.extend(_session_rows(d, legs_ex, reps_base=12, inc=2.5, session_idx=session_idx))
            else:
                entrenos.extend(_session_rows(d, full_ex, reps_base=10, inc=2.5, session_idx=session_idx))
            session_idx += 1
        data["entrenamientos"] = entrenos

    # 9) Campos extra que usa la app (si no existen)
    data.setdefault("routine_plan", data.get("routine_plan", {}))
    data.setdefault("custom_exercises", data.get("custom_exercises", []))
    data.setdefault("exercise_meta", data.get("exercise_meta", {}))
    data.setdefault("rutinas", data.get("rutinas", []))
    data.setdefault("entrenamientos", data.get("entrenamientos", []))
    data.setdefault("weights", data.get("weights", []))
    data.setdefault("profile", data.get("profile", {}))
    data.setdefault("role", "admin")

    # 10) Objetivos DEMO (para probar la pantalla de Objetivos)
    data.setdefault(
        "objetivos",
        {
            "dias_semana": 4,
            "peso_objetivo": 78.0,
            "ejercicios": {
                "Press con barra en banco horizontal": {"peso": 70.0, "reps": 8},
                "Prensa de piernas en posición ancha": {"peso": 160.0, "reps": 12},
                "Peso muerto con barra": {"peso": 100.0, "reps": 5},
            },
        },
    )

    save_user(username, data)
