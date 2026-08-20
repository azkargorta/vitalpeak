"""UI de plantillas de rutinas (editable + 3 alternativas)."""

from __future__ import annotations

import streamlit as st

from app.exercise_catalog import get_grupo, load_base_exercises, suggest_alternatives
from app.exercises import get_exercise_meta, list_all_exercises
from app.routine_templates import (
    TEMPLATE_CATEGORIES,
    day_to_routine_items,
    instantiate_template,
    list_templates,
)
from app.routines import add_routine, list_routines
from app.ui_theme import section_label


def render_templates_page(*, embedded: bool = True) -> None:
    if embedded:
        st.markdown("## Plantillas")
    else:
        st.title("Plantillas de rutinas")

    st.caption(
        "Elige un plan listo, ajústalo y guárdalo. "
        "Al sustituir un ejercicio te ofrecemos 3 opciones del mismo grupo."
    )

    user = st.session_state.get("user")
    if not user:
        st.warning("Inicia sesión para guardar rutinas en tu cuenta. Puedes explorar igual.")
    else:
        st.caption(f"Sesión: {user}")

    pool = list_all_exercises(user) if user else load_base_exercises()

    def _ensure_editor(tpl: dict) -> None:
        st.session_state["tpl_editor"] = tpl
        st.session_state["tpl_editor_id"] = tpl.get("id")

    def _editor():
        return st.session_state.get("tpl_editor")

    section_label("Explorar")
    fc1, fc2, fc3 = st.columns(3)
    with fc1:
        cat = st.selectbox("Categoría", ["Todas"] + TEMPLATE_CATEGORIES, key="tpl_cat")
    with fc2:
        level = st.selectbox(
            "Nivel", ["Todos", "principiante", "intermedio", "avanzado"], key="tpl_level"
        )
    with fc3:
        goal = st.selectbox(
            "Objetivo", ["Todos", "hipertrofia", "fuerza", "mixto"], key="tpl_goal"
        )

    templates = list_templates(
        category=None if cat == "Todas" else cat,
        level=None if level == "Todos" else level,
        goal=None if goal == "Todos" else goal,
    )

    if not templates:
        st.info("No hay plantillas con esos filtros.")
        return

    labels = {
        t["id"]: f"{t['name']} · {t['days_per_week']}d · {t['level']} · {t['goal']}"
        for t in templates
    }
    sel_id = st.selectbox(
        "Elige plantilla",
        options=list(labels.keys()),
        format_func=lambda i: labels[i],
        key="tpl_select",
    )
    selected = next(t for t in templates if t["id"] == sel_id)

    st.markdown(f"### {selected['name']}")
    st.write(selected.get("description") or "")
    m1, m2, m3, m4 = st.columns(4)
    m1.metric("Días/semana", selected.get("days_per_week"))
    m2.metric("Duración", f"{selected.get('duration_min')} min")
    m3.metric("Nivel", selected.get("level"))
    m4.metric("Objetivo", selected.get("goal"))

    with st.expander("Vista previa", expanded=False):
        for day in selected.get("days") or []:
            st.markdown(f"**{day.get('name')}** — _{day.get('focus', '')}_")
            for it in day.get("items") or []:
                st.write(f"- {it['exercise']} · {it['sets']}×{it['reps']}")

    c_load, c_reset = st.columns(2)
    with c_load:
        if st.button("Cargar en editor", type="primary", use_container_width=True):
            _ensure_editor(instantiate_template(sel_id))
            st.rerun()
    with c_reset:
        if st.button("Vaciar editor", use_container_width=True):
            st.session_state.pop("tpl_editor", None)
            st.session_state.pop("tpl_editor_id", None)
            st.rerun()

    st.markdown("---")
    plan = _editor()
    if not plan:
        st.info("Selecciona una plantilla y pulsa **Cargar en editor**.")
        return

    section_label("Personalizar")
    st.subheader(f"Editor: {plan.get('name')}")
    st.caption("Series, reps y sustitución con alternativas del mismo grupo muscular.")

    for d_idx, day in enumerate(plan.get("days") or []):
        with st.expander(f"{day.get('name')} — {day.get('focus', '')}", expanded=True):
            new_name = st.text_input(
                "Nombre del día", value=day.get("name", ""), key=f"day_name_{d_idx}"
            )
            day["name"] = new_name

            items = day.get("items") or []
            remove_idx = None

            for i_idx, it in enumerate(items):
                ex = it.get("exercise", "")
                grupo = get_grupo(ex, user)
                st.markdown(f"**{i_idx + 1}. {ex}**")
                st.caption(f"Grupo: {grupo}")

                if user:
                    meta = get_exercise_meta(user, ex)
                    if meta.get("imagen"):
                        try:
                            st.image(meta["imagen"], width=180)
                        except Exception:
                            pass

                r1, r2, r3, r4 = st.columns([1, 1, 2.2, 0.8])
                with r1:
                    it["sets"] = st.number_input(
                        "Series",
                        min_value=1,
                        max_value=10,
                        value=int(it.get("sets") or 3),
                        key=f"sets_{d_idx}_{i_idx}",
                    )
                with r2:
                    it["reps"] = st.number_input(
                        "Reps",
                        min_value=1,
                        max_value=50,
                        value=int(it.get("reps") or 10),
                        key=f"reps_{d_idx}_{i_idx}",
                    )
                with r3:
                    alts = suggest_alternatives(
                        ex,
                        n=3,
                        username=user,
                        exclude={x.get("exercise") for x in items if x.get("exercise")},
                        pool=pool,
                    )
                    swap_choice = st.selectbox(
                        "3 alternativas",
                        options=alts if alts else ["(sin alternativas)"],
                        key=f"swap_{d_idx}_{i_idx}",
                        disabled=not alts,
                    )
                    if alts and st.button("Sustituir", key=f"swap_btn_{d_idx}_{i_idx}"):
                        it["exercise"] = swap_choice
                        st.rerun()
                with r4:
                    if st.button("Quitar", key=f"del_{d_idx}_{i_idx}"):
                        remove_idx = i_idx

                with st.expander("Elegir otro de la lista", expanded=False):
                    same_group = [n for n in pool if get_grupo(n, user) == grupo]
                    mode = st.radio(
                        "Mostrar",
                        ["Mismo grupo", "Toda la lista"],
                        horizontal=True,
                        key=f"mode_{d_idx}_{i_idx}",
                    )
                    options = same_group if mode == "Mismo grupo" else list(pool)
                    if ex in options:
                        idx0 = options.index(ex)
                    else:
                        idx0 = 0
                        options = [ex] + options
                    picked = st.selectbox(
                        "Ejercicio", options, index=idx0, key=f"pick_{d_idx}_{i_idx}"
                    )
                    if st.button("Aplicar", key=f"apply_{d_idx}_{i_idx}"):
                        it["exercise"] = picked
                        st.rerun()

                if alts:
                    st.caption("Recomendadas: " + " · ".join(alts))
                st.markdown("---")

            if remove_idx is not None:
                items.pop(remove_idx)
                day["items"] = items
                st.rerun()

            st.markdown("**Añadir ejercicio**")
            a1, a2, a3, a4 = st.columns([2, 1, 1, 1])
            with a1:
                add_ex = st.selectbox("Ejercicio", pool, key=f"add_ex_{d_idx}")
            with a2:
                add_sets = st.number_input("Series", 1, 10, 3, key=f"add_sets_{d_idx}")
            with a3:
                add_reps = st.number_input("Reps", 1, 50, 10, key=f"add_reps_{d_idx}")
            with a4:
                if st.button("Añadir", key=f"add_btn_{d_idx}", use_container_width=True):
                    items.append(
                        {
                            "exercise": add_ex,
                            "sets": int(add_sets),
                            "reps": int(add_reps),
                            "weight": 0.0,
                            "notes": "",
                        }
                    )
                    day["items"] = items
                    st.rerun()

    st.session_state["tpl_editor"] = plan

    st.markdown("---")
    section_label("Guardar")
    st.subheader("Guardar en mis rutinas")
    prefix = st.text_input(
        "Prefijo del nombre (opcional)",
        value=plan.get("name", "Plantilla"),
        key="tpl_save_prefix",
    )

    col_s1, col_s2 = st.columns(2)
    with col_s1:
        save_days = st.button(
            "Guardar cada día como rutina", type="primary", use_container_width=True
        )
    with col_s2:
        save_one = st.button("Guardar todo en una rutina", use_container_width=True)

    if save_days or save_one:
        if not user:
            st.error("Necesitas iniciar sesión para guardar.")
            return
        existing = {r.get("name") for r in list_routines(user)}
        try:
            if save_one:
                all_items = []
                for day in plan.get("days") or []:
                    all_items.extend(day_to_routine_items(day))
                name = (prefix or plan.get("name") or "Plantilla").strip()
                base = name
                n = 2
                while name in existing:
                    name = f"{base} ({n})"
                    n += 1
                add_routine(user, name, all_items)
                st.success(f"Guardada rutina **{name}** con {len(all_items)} ejercicios.")
            else:
                saved = 0
                for day in plan.get("days") or []:
                    day_name = f"{prefix} — {day.get('name')}".strip(" —")
                    base = day_name
                    n = 2
                    while day_name in existing:
                        day_name = f"{base} ({n})"
                        n += 1
                    items = day_to_routine_items(day)
                    if not items:
                        continue
                    add_routine(user, day_name, items)
                    existing.add(day_name)
                    saved += 1
                st.success(f"Se guardaron **{saved}** rutina(s). Véalas en Planificar rutinas.")
        except Exception as e:
            st.error(str(e))
