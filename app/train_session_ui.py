"""Sesión de entrenamiento guiada: rutina del día, series y descanso."""

from __future__ import annotations

import re
import time
from datetime import date, timedelta
from typing import Any, Dict, List, Optional

import streamlit as st

from app.datastore import load_user
from app.exercises_ui import render_movement_preview
from app.routines import find_routine, list_routines
from app.training import add_training_set, last_values_for_exercise


SESSION_KEY = "vp_train_session"


def parse_rest_seconds(value: Any, default: int = 90) -> int:
    """Convierte '90s', '60-90s', '2m', '2-3m' o int → segundos (usa el mínimo del rango)."""
    if value is None or value == "":
        return default
    if isinstance(value, (int, float)):
        return max(0, int(value))
    s = str(value).strip().lower().replace(" ", "")
    m = re.match(r"(\d+)\s*-\s*(\d+)\s*s", s)
    if m:
        return max(0, int(m.group(1)))
    m = re.match(r"(\d+)\s*s", s)
    if m:
        return max(0, int(m.group(1)))
    m = re.match(r"(\d+)\s*-\s*(\d+)\s*m", s)
    if m:
        return max(0, int(m.group(1)) * 60)
    m = re.match(r"(\d+)\s*m", s)
    if m:
        return max(0, int(m.group(1)) * 60)
    m = re.search(r"(\d+)", s)
    if m:
        n = int(m.group(1))
        return n if n >= 30 else n * 60  # "90" → 90s; "2" → 2m heurística floja
    return default


def _normalize_items(raw_items: List[Dict[str, Any]], username: str) -> List[Dict[str, Any]]:
    out: List[Dict[str, Any]] = []
    for it in raw_items or []:
        name = (it.get("exercise") or it.get("nombre") or "").strip()
        if not name:
            continue
        sets = int(it.get("sets") or it.get("series") or 3)
        reps = it.get("reps") or it.get("repeticiones") or 10
        try:
            reps_i = int(str(reps).split("-")[0])
        except Exception:
            reps_i = 10
        weight = float(it.get("weight") or it.get("peso") or 0.0)
        last = last_values_for_exercise(username, name)
        if last and weight <= 0:
            reps_i, weight = int(last[0]), float(last[1])
        rest = parse_rest_seconds(
            it.get("rest_sec") or it.get("descanso") or it.get("rest"),
            default=90,
        )
        out.append(
            {
                "exercise": name,
                "sets": max(1, sets),
                "reps": max(1, reps_i),
                "weight": max(0.0, weight),
                "rest_sec": rest,
            }
        )
    return out


def _today_routine_name(username: str, day: date) -> Optional[str]:
    data = load_user(username) or {}
    plan = dict(data.get("routine_plan") or {})
    return plan.get(day.isoformat()) or None


def init_session_from_routine(username: str, day: date, routine_name: str) -> Dict[str, Any]:
    routine = find_routine(username, routine_name)
    items = _normalize_items(list((routine or {}).get("items") or []), username)
    return {
        "date": day.isoformat(),
        "routine_name": routine_name,
        "items": items,
        "ex_idx": 0,
        "set_num": 1,
        "draft_reps": items[0]["reps"] if items else 10,
        "draft_weight": items[0]["weight"] if items else 0.0,
        "phase": "logging" if items else "empty",
        "rest_ends_at": None,
        "show_next_dialog": False,
        "logged": [],
    }


def get_or_start_session(username: str, day: date) -> Optional[Dict[str, Any]]:
    sess = st.session_state.get(SESSION_KEY)
    if sess and sess.get("date") == day.isoformat() and sess.get("items"):
        return sess
    rt = _today_routine_name(username, day)
    if not rt:
        return None
    sess = init_session_from_routine(username, day, rt)
    st.session_state[SESSION_KEY] = sess
    return sess


def _current_item(sess: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    items = sess.get("items") or []
    ix = int(sess.get("ex_idx") or 0)
    if 0 <= ix < len(items):
        return items[ix]
    return None


def _next_item(sess: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    items = sess.get("items") or []
    ix = int(sess.get("ex_idx") or 0) + 1
    if 0 <= ix < len(items):
        return items[ix]
    return None


def _start_rest(sess: Dict[str, Any], seconds: int) -> None:
    if seconds <= 0:
        sess["rest_ends_at"] = None
        return
    sess["rest_ends_at"] = time.time() + seconds


def _skip_rest(sess: Dict[str, Any]) -> None:
    sess["rest_ends_at"] = None


def _advance_after_set(sess: Dict[str, Any]) -> None:
    """Tras guardar una serie: más series del mismo ejercicio o diálogo de siguiente."""
    item = _current_item(sess)
    if not item:
        sess["phase"] = "done"
        sess["show_next_dialog"] = False
        return
    planned = int(item["sets"])
    set_num = int(sess.get("set_num") or 1)
    if set_num < planned:
        sess["set_num"] = set_num + 1
        sess["phase"] = "logging"
        sess["show_next_dialog"] = False
        return
    # Completó las series planificadas (o una extra) → diálogo en la misma página
    sess["phase"] = "logging"
    sess["show_next_dialog"] = True


def _go_next_exercise(sess: Dict[str, Any]) -> None:
    nxt = _next_item(sess)
    sess["show_next_dialog"] = False
    if not nxt:
        sess["phase"] = "done"
        return
    sess["ex_idx"] = int(sess["ex_idx"]) + 1
    sess["set_num"] = 1
    sess["draft_reps"] = int(nxt["reps"])
    sess["draft_weight"] = float(nxt["weight"])
    sess["phase"] = "logging"
    sess["rest_ends_at"] = None


def _prepare_extra_set(sess: Dict[str, Any]) -> None:
    item = _current_item(sess)
    if not item:
        return
    planned = int(item.get("sets") or 1)
    last_logged = 0
    for row in sess.get("logged") or []:
        if row["exercise"] == item["exercise"]:
            last_logged = max(last_logged, int(row["set"]))
    sess["set_num"] = max(planned, last_logged) + 1
    sess["phase"] = "logging"
    sess["show_next_dialog"] = False


@st.dialog("Ejercicio completado")
def _next_step_dialog(sess: Dict[str, Any]) -> None:
    item = _current_item(sess)
    nxt = _next_item(sess)
    name = (item or {}).get("exercise") or "este ejercicio"
    st.markdown(f"Has terminado las series de **{name}**.")
    if nxt:
        st.markdown(f"**Siguiente ejercicio:** {nxt['exercise']}")
        st.caption(f"{nxt['sets']} series · {nxt['reps']} reps")
    else:
        st.caption("Era el último ejercicio de la rutina.")

    c1, c2 = st.columns(2)
    with c1:
        if st.button("Añadir otra serie", use_container_width=True, key="dlg_extra_set"):
            _prepare_extra_set(sess)
            st.rerun()
    with c2:
        label = "Continuar" if nxt else "Terminar sesión"
        if st.button(label, type="primary", use_container_width=True, key="dlg_continue"):
            if nxt:
                _go_next_exercise(sess)
            else:
                sess["show_next_dialog"] = False
                sess["phase"] = "done"
            st.rerun()


def _render_rest_timer(sess: Dict[str, Any]) -> None:
    ends = sess.get("rest_ends_at")
    if not ends:
        return
    remaining = int(ends - time.time())
    if remaining <= 0:
        sess["rest_ends_at"] = None
        st.success("Descanso terminado.")
        return

    st.info(f"Descanso: **{remaining // 60}:{remaining % 60:02d}**")
    c1, c2 = st.columns(2)
    with c1:
        if st.button("Omitir descanso", use_container_width=True, key="skip_rest"):
            _skip_rest(sess)
            st.rerun()
    with c2:
        st.caption("La cuenta sigue al actualizar.")

    @st.fragment(run_every=timedelta(seconds=1))
    def _tick():
        left = int(ends - time.time())
        if left <= 0:
            sess["rest_ends_at"] = None
            st.success("¡Listo! Siguiente serie.")
            return
        st.metric("Tiempo restante", f"{left // 60}:{left % 60:02d}")

    _tick()


def _render_progress(sess: Dict[str, Any]) -> None:
    items = sess.get("items") or []
    ix = int(sess.get("ex_idx") or 0)
    item = _current_item(sess)
    st.caption(
        f"**{sess.get('routine_name')}** · {sess.get('date')} · "
        f"Ejercicio {min(ix + 1, len(items))}/{len(items)}"
    )
    if item:
        planned = int(item["sets"])
        set_num = int(sess.get("set_num") or 1)
        st.progress(min(1.0, ix / max(len(items), 1)))
        st.markdown(
            f"### {item['exercise']}\n"
            f"Serie **{set_num}**"
            + (f" de **{planned}**" if sess.get("phase") == "logging" and set_num <= planned else "")
        )


def _render_logging(username: str, sess: Dict[str, Any]) -> None:
    item = _current_item(sess)
    if not item:
        sess["phase"] = "done"
        st.rerun()
        return

    next_ex = (_next_item(sess) or {}).get("exercise")
    col_log, col_mov = st.columns([1.1, 1], gap="large")

    with col_log:
        if sess.get("rest_ends_at"):
            _render_rest_timer(sess)

        sk = f"{int(sess.get('ex_idx') or 0)}_{int(sess.get('set_num') or 1)}"
        with st.form("session_set_form", clear_on_submit=False):
            c1, c2, c3 = st.columns(3)
            with c1:
                set_num = st.number_input(
                    "Serie #",
                    min_value=1,
                    step=1,
                    value=int(sess.get("set_num") or 1),
                    key=f"sess_set_num_{sk}",
                )
            with c2:
                reps = st.number_input(
                    "Repeticiones",
                    min_value=1,
                    step=1,
                    value=int(sess.get("draft_reps") or item["reps"]),
                    key=f"sess_reps_{sk}",
                )
            with c3:
                weight = st.number_input(
                    "Peso (kg)",
                    min_value=0.0,
                    step=0.5,
                    value=float(sess.get("draft_weight") or item["weight"]),
                    key=f"sess_weight_{sk}",
                )
            rest_sec = st.number_input(
                "Descanso tras esta serie (s)",
                min_value=0,
                step=15,
                value=int(item.get("rest_sec") or 90),
                key=f"sess_rest_sec_{sk}",
                help="0 = sin temporizador. Puedes omitirlo después.",
            )
            submitted = st.form_submit_button("Guardar serie", type="primary", use_container_width=True)

        if submitted:
            add_training_set(
                username,
                sess["date"],
                item["exercise"],
                int(set_num),
                int(reps),
                float(weight),
            )
            sess["logged"].append(
                {
                    "exercise": item["exercise"],
                    "set": int(set_num),
                    "reps": int(reps),
                    "weight": float(weight),
                }
            )
            # Autorelleno siguiente serie con los mismos valores
            sess["draft_reps"] = int(reps)
            sess["draft_weight"] = float(weight)
            sess["set_num"] = int(set_num)  # _advance usará esto
            item["rest_sec"] = int(rest_sec)
            _start_rest(sess, int(rest_sec))
            _advance_after_set(sess)
            # Si avanzamos set_num dentro del mismo ejercicio, draft ya está
            if sess.get("phase") == "logging" and sess.get("set_num") == int(set_num):
                # edge: planned was current; advance bumped set_num
                pass
            st.success(f"Serie {set_num} guardada · {reps} reps @ {weight} kg")
            st.rerun()

        # Series ya hechas de este ejercicio hoy en la sesión
        done = [x for x in sess.get("logged") or [] if x["exercise"] == item["exercise"]]
        if done:
            st.caption("En esta sesión:")
            for row in done:
                st.write(f"- Serie {row['set']}: {row['reps']} × {row['weight']} kg")

    with col_mov:
        render_movement_preview(
            item["exercise"],
            key="sess_mov",
            next_exercise=next_ex,
        )


def _render_between(sess: Dict[str, Any]) -> None:
    """Compat: ya no se usa pantalla aparte; el diálogo cubre este caso."""
    sess["show_next_dialog"] = True
    sess["phase"] = "logging"
    st.rerun()


def _render_done(sess: Dict[str, Any]) -> None:
    st.balloons()
    st.success("Sesión completada. ¡Buen trabajo!")
    st.caption(f"Series registradas: {len(sess.get('logged') or [])}")
    if st.button("Empezar de nuevo esta rutina", use_container_width=True):
        st.session_state.pop(SESSION_KEY, None)
        st.rerun()


def _render_picker(username: str, day: date) -> None:
    st.info("No hay rutina asignada para este día en el calendario.")
    routines = list_routines(username)
    if not routines:
        st.warning("Crea una rutina en Plantillas o asígnala en Planificar.")
        return
    names = [r["name"] for r in routines]
    pick = st.selectbox("Elegir rutina para hoy", names, key="train_pick_routine")
    if st.button("Empezar esta rutina", type="primary", use_container_width=True):
        st.session_state[SESSION_KEY] = init_session_from_routine(username, day, pick)
        st.rerun()


def render_train_page(username: str) -> None:
    st.title("Entrenar")
    day = st.date_input("Fecha", value=date.today(), key="train_session_date")
    sess = st.session_state.get(SESSION_KEY)
    if sess and sess.get("date") != day.isoformat():
        st.session_state.pop(SESSION_KEY, None)
        sess = None

    sess = get_or_start_session(username, day)
    if not sess or not sess.get("items"):
        _render_picker(username, day)
        return

    top = st.columns([3, 1])
    with top[1]:
        if st.button("Reiniciar sesión", use_container_width=True, key="reset_sess"):
            st.session_state.pop(SESSION_KEY, None)
            st.rerun()

    _render_progress(sess)

    if sess.get("show_next_dialog") and sess.get("phase") != "done":
        _next_step_dialog(sess)

    phase = sess.get("phase") or "logging"
    if phase == "done":
        _render_done(sess)
    elif phase in ("logging", "between_exercises"):
        _render_logging(username, sess)
    else:
        _render_picker(username, day)
