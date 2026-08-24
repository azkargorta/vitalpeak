"""Página Hoy: qué toca hoy, lista del entreno y vista de la semana."""

from __future__ import annotations

import datetime as _dt
from datetime import date
from typing import Any, Dict, List, Optional

import streamlit as st

from app.datastore import load_user
from app.routines import list_routines
from app.ui_theme import render_brand_hero, section_label


def _goto(page: str) -> None:
    st.session_state["nav_page"] = page
    st.rerun()


def _item_line(it: Dict[str, Any], idx: int) -> str:
    name = (it.get("exercise") or it.get("nombre") or "—").strip()
    sets = it.get("sets") or it.get("series") or "—"
    reps = it.get("reps") or it.get("repeticiones") or "—"
    weight = it.get("weight") if it.get("weight") is not None else it.get("peso")
    rest = it.get("rest_sec") or it.get("descanso") or ""
    parts = [f"**{idx}. {name}**", f"{sets}×{reps}"]
    if weight not in (None, "", 0, 0.0):
        parts.append(f"{weight} kg")
    if rest not in (None, ""):
        parts.append(f"descanso {rest}")
    return " · ".join(parts)


def _start_train(username: str, first_ex: Optional[str] = None) -> None:
    from app.train_session_ui import SESSION_KEY, get_or_start_session

    sess = get_or_start_session(username, date.today())
    if sess and sess.get("items") and first_ex:
        for i, it in enumerate(sess["items"]):
            if it["exercise"] == first_ex:
                sess["ex_idx"] = i
                sess["set_num"] = 1
                sess["draft_reps"] = it["reps"]
                sess["draft_weight"] = it["weight"]
                sess["phase"] = "logging"
                break
        st.session_state[SESSION_KEY] = sess
    _goto("Entrenar")


def render_today_page(username: str) -> None:
    data_u = load_user(username) or {}
    plan = dict(data_u.get("routine_plan") or {})
    routines = list_routines(username) or []
    routines_by_name = {r.get("name"): r for r in routines}
    today = date.today()
    today_iso = today.isoformat()
    rt_name = plan.get(today_iso)
    routine = routines_by_name.get(rt_name) if rt_name else None
    items: List[Dict[str, Any]] = list((routine or {}).get("items") or []) if routine else []

    weekday_es = [
        "Lunes",
        "Martes",
        "Miércoles",
        "Jueves",
        "Viernes",
        "Sábado",
        "Domingo",
    ]
    months_es = [
        "",
        "enero",
        "febrero",
        "marzo",
        "abril",
        "mayo",
        "junio",
        "julio",
        "agosto",
        "septiembre",
        "octubre",
        "noviembre",
        "diciembre",
    ]
    kicker = f"{weekday_es[today.weekday()]} {today.day} de {months_es[today.month]}"

    if rt_name and items:
        panel_title = rt_name
        panel_body = f"{len(items)} ejercicios · listo para entrenar"
        lead = "Tu sesión de hoy."
    elif rt_name:
        panel_title = rt_name
        panel_body = "La rutina está vacía o ya no existe. Revísala en Planificar."
        lead = "Hay un plan asignado, pero falta contenido."
    else:
        panel_title = "Día libre"
        panel_body = "No hay rutina para hoy. Puedes planificar la semana o empezar una plantilla."
        lead = "Sin sesión asignada."

    render_brand_hero(
        title="VitalPeak",
        kicker=kicker,
        lead=lead,
        panel_title=panel_title,
        panel_body=panel_body,
    )

    # —— Sesión de hoy ——
    section_label("Sesión de hoy")
    st.markdown('<div class="vp-today">', unsafe_allow_html=True)

    if rt_name and items:
        st.markdown(f"### {rt_name}")
        for i, it in enumerate(items, start=1):
            st.markdown(_item_line(it, i))

        cta1, cta2 = st.columns([2, 1])
        with cta1:
            if st.button("Empezar entrenamiento", type="primary", use_container_width=True, key="hoy_start"):
                first = (items[0].get("exercise") or items[0].get("nombre") or "").strip() or None
                _start_train(username, first)
        with cta2:
            if st.button("Planificar", use_container_width=True, key="hoy_plan"):
                st.session_state["rutinas_tab"] = "Planificar"
                _goto("Rutinas")

        first_ex = (items[0].get("exercise") or items[0].get("nombre") or "").strip()
        if first_ex:
            with st.expander(f"Movimiento · {first_ex}", expanded=False):
                from app.exercises_ui import render_movement_preview

                render_movement_preview(first_ex, key="hoy_mov", show_steps=False)

    elif rt_name:
        st.markdown(f"### {rt_name}")
        st.caption("Sin ejercicios. Edita la plantilla o asigna otra rutina.")
        if st.button("Ir a planificar", type="primary", use_container_width=True, key="hoy_fix_plan"):
            st.session_state["rutinas_tab"] = "Planificar"
            _goto("Rutinas")
    else:
        st.markdown("### Nada asignado")
        st.caption("Elige una plantilla o asigna una rutina al día de hoy.")
        b1, b2 = st.columns(2)
        with b1:
            if st.button("Ver plantillas", type="primary", use_container_width=True, key="hoy_tpl"):
                st.session_state["rutinas_tab"] = "Plantillas"
                _goto("Rutinas")
        with b2:
            if st.button("Planificar semana", use_container_width=True, key="hoy_plan_empty"):
                st.session_state["rutinas_tab"] = "Planificar"
                _goto("Rutinas")

    st.markdown("</div>", unsafe_allow_html=True)

    # —— Semana (lista: usable en teléfono / WebView) ——
    section_label("Esta semana")
    monday = today - _dt.timedelta(days=today.weekday())
    week_dates = [monday + _dt.timedelta(days=i) for i in range(7)]
    abbr = ["Lun", "Mar", "Mié", "Jue", "Vie", "Sáb", "Dom"]

    rows_html: List[str] = ['<div class="vp-week-list">']
    for i, d in enumerate(week_dates):
        rt = plan.get(d.isoformat()) or ""
        is_today = d.isoformat() == today_iso
        label = rt if rt else "Libre"
        if len(label) > 28:
            label = label[:26] + "…"
        cls = "vp-week-row vp-week-row--today" if is_today else "vp-week-row"
        rows_html.append(
            f'<div class="{cls}">'
            f'<div class="vp-week-abbr">{abbr[i]}</div>'
            f'<div class="vp-week-num">{d.day}</div>'
            f'<div class="vp-week-rt">{label}</div>'
            f"</div>"
        )
    rows_html.append("</div>")
    st.markdown("\n".join(rows_html), unsafe_allow_html=True)

    planned_n = sum(1 for d in week_dates if plan.get(d.isoformat()))
    st.caption(f"{planned_n} de 7 días con rutina · {len(routines)} plantillas guardadas")
