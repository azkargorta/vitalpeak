"""UI de plantillas — compacta, días bien separados, poco texto."""

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

_DAY_COLORS = ["#3AA899", "#4A7C9B", "#C47A4A", "#6B8F71", "#8B6BAE", "#B85C6E"]


def render_templates_page(*, embedded: bool = True) -> None:
    st.markdown(
        """
<style>
.vp-tpl-card {
  background: #fff;
  border: 1px solid rgba(20,40,48,0.10);
  border-radius: 12px;
  padding: 0.85rem 1rem;
  margin-bottom: 0.65rem;
  box-shadow: 0 4px 14px rgba(20,40,48,0.04);
  cursor: default;
}
.vp-tpl-card h4 {
  margin: 0 0 0.25rem 0 !important;
  font-family: 'Barlow Condensed', sans-serif !important;
  text-transform: uppercase;
  letter-spacing: 0.03em;
  font-size: 1.15rem !important;
}
.vp-tpl-meta {
  font-size: 0.78rem;
  color: #6A7F88;
  margin: 0;
}
.vp-day-card {
  background: #fff;
  border: 1px solid rgba(20,40,48,0.10);
  border-radius: 14px;
  padding: 1rem 1.1rem 0.85rem;
  margin: 0 0 1.15rem 0;
  box-shadow: 0 6px 20px rgba(20,40,48,0.05);
  border-left: 5px solid #3AA899;
}
.vp-day-card .vp-day-title {
  font-family: 'Barlow Condensed', sans-serif;
  text-transform: uppercase;
  letter-spacing: 0.04em;
  font-size: 1.35rem;
  font-weight: 700;
  color: #142830;
  margin: 0 0 0.15rem 0;
}
.vp-day-card .vp-day-focus {
  font-size: 0.8rem;
  color: #6A7F88;
  margin: 0 0 0.75rem 0;
}
.vp-ex-row {
  display: flex;
  justify-content: space-between;
  gap: 0.5rem;
  padding: 0.4rem 0;
  border-bottom: 1px solid rgba(20,40,48,0.06);
  font-size: 0.92rem;
}
.vp-ex-row:last-child { border-bottom: none; }
.vp-ex-sets {
  color: #3AA899;
  font-weight: 700;
  white-space: nowrap;
}
</style>
        """,
        unsafe_allow_html=True,
    )

    if embedded:
        st.markdown("## Plantillas")
    else:
        st.title("Plantillas")

    user = st.session_state.get("user")
    pool = list_all_exercises(user) if user else load_base_exercises()

    def _ensure_editor(tpl: dict) -> None:
        st.session_state["tpl_editor"] = tpl
        st.session_state["tpl_editor_id"] = tpl.get("id")
        st.session_state["tpl_day_tab"] = 0

    def _editor():
        return st.session_state.get("tpl_editor")

    # Filtros compactos
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

    # Selector visual en rejilla (botones)
    st.caption(f"{len(templates)} planes disponibles")
    cols = st.columns(2)
    for i, t in enumerate(templates):
        with cols[i % 2]:
            label = f"{t['name']}"
            sub = f"{t['days_per_week']} días · {t['duration_min']} min · {t['goal']}"
            if st.button(
                f"{label}\n{sub}",
                key=f"pick_tpl_{t['id']}",
                use_container_width=True,
                type="primary" if st.session_state.get("tpl_editor_id") == t["id"] else "secondary",
            ):
                _ensure_editor(instantiate_template(t["id"]))
                st.rerun()

    plan = _editor()
    if not plan:
        st.info("Pulsa un plan para cargarlo y personalizarlo.")
        return

    st.markdown("---")
    top1, top2 = st.columns([3, 1])
    with top1:
        st.markdown(f"### {plan.get('name')}")
        st.caption(
            f"{plan.get('level')} · {plan.get('goal')} · "
            f"{plan.get('days_per_week')} días · {plan.get('duration_min')} min"
        )
    with top2:
        if st.button("Quitar del editor", use_container_width=True):
            st.session_state.pop("tpl_editor", None)
            st.session_state.pop("tpl_editor_id", None)
            st.rerun()

    # PDF del plan completo (todos los días)
    try:
        from app.pdf_export import plan_days_to_pdf_bytes

        pdf_bytes = plan_days_to_pdf_bytes(plan)
        safe = "".join(c if c.isalnum() or c in " -_" else "_" for c in str(plan.get("name") or "plan")).strip()
        st.download_button(
            "Descargar PDF completo",
            data=pdf_bytes,
            file_name=f"VitalPeak_{safe}.pdf",
            mime="application/pdf",
            use_container_width=True,
            key="tpl_pdf_dl",
        )
    except Exception:
        pass

    days = plan.get("days") or []
    day_labels = [f"Día {i+1}: {d.get('name', '')}" for i, d in enumerate(days)]
    if "tpl_day_tab" not in st.session_state:
        st.session_state["tpl_day_tab"] = 0
    # Tabs visuales por día = separación clara
    tabs = st.tabs(day_labels if day_labels else ["Día"])

    for d_idx, (tab, day) in enumerate(zip(tabs, days)):
        color = _DAY_COLORS[d_idx % len(_DAY_COLORS)]
        with tab:
            st.markdown(
                f"""
                <div class="vp-day-card" style="border-left-color:{color}">
                  <div class="vp-day-title">{day.get('name', '')}</div>
                  <div class="vp-day-focus">{day.get('focus', '')}</div>
                </div>
                """,
                unsafe_allow_html=True,
            )

            new_name = st.text_input(
                "Nombre",
                value=day.get("name", ""),
                key=f"day_name_{d_idx}",
                label_visibility="collapsed",
            )
            day["name"] = new_name or day.get("name", "")

            items = day.get("items") or []
            remove_idx = None

            for i_idx, it in enumerate(items):
                ex = it.get("exercise", "")
                grupo = get_grupo(ex, user)

                c1, c2, c3, c4, c5 = st.columns([2.8, 0.75, 0.75, 0.9, 1.0])
                with c1:
                    st.markdown(f"**{ex}**")
                    st.caption(grupo)
                    if user:
                        meta = get_exercise_meta(user, ex)
                        from app.exercises import resolve_exercise_image_path

                        img = resolve_exercise_image_path(meta.get("imagen"))
                        if img:
                            try:
                                st.image(str(img), width=120)
                            except Exception:
                                pass
                with c2:
                    it["sets"] = st.number_input(
                        "Ser.",
                        1,
                        10,
                        int(it.get("sets") or 3),
                        key=f"sets_{d_idx}_{i_idx}",
                    )
                with c3:
                    it["reps"] = st.number_input(
                        "Rep.",
                        1,
                        50,
                        int(it.get("reps") or 10),
                        key=f"reps_{d_idx}_{i_idx}",
                    )
                with c4:
                    it["rest_sec"] = st.number_input(
                        "Desc.(s)",
                        0,
                        600,
                        int(it.get("rest_sec") or 90),
                        step=15,
                        key=f"rest_{d_idx}_{i_idx}",
                    )
                with c5:
                    if st.button("Quitar", key=f"del_{d_idx}_{i_idx}"):
                        remove_idx = i_idx

                alts = suggest_alternatives(
                    ex,
                    n=3,
                    username=user,
                    exclude={x.get("exercise") for x in items if x.get("exercise")},
                    pool=pool,
                )
                with st.expander("Cambiar ejercicio", expanded=False):
                    if alts:
                        pick = st.radio(
                            "3 alternativas",
                            alts,
                            key=f"alt_{d_idx}_{i_idx}",
                            horizontal=False,
                        )
                        if st.button("Usar alternativa", key=f"use_alt_{d_idx}_{i_idx}"):
                            it["exercise"] = pick
                            st.rerun()
                    same_group = [n for n in pool if get_grupo(n, user) == grupo]
                    other = st.selectbox(
                        "O elige de la lista",
                        same_group or list(pool),
                        key=f"pick_{d_idx}_{i_idx}",
                    )
                    if st.button("Aplicar de lista", key=f"apply_{d_idx}_{i_idx}"):
                        it["exercise"] = other
                        st.rerun()

            if remove_idx is not None:
                items.pop(remove_idx)
                day["items"] = items
                st.rerun()

            ac1, ac2, ac3, ac4, ac5 = st.columns([2.2, 0.7, 0.7, 0.8, 1])
            with ac1:
                add_ex = st.selectbox("Añadir", pool, key=f"add_ex_{d_idx}", label_visibility="collapsed")
            with ac2:
                add_sets = st.number_input("S", 1, 10, 3, key=f"add_sets_{d_idx}", label_visibility="collapsed")
            with ac3:
                add_reps = st.number_input("R", 1, 50, 10, key=f"add_reps_{d_idx}", label_visibility="collapsed")
            with ac4:
                add_rest = st.number_input("D", 0, 600, 90, step=15, key=f"add_rest_{d_idx}", label_visibility="collapsed")
            with ac5:
                if st.button("＋ Añadir", key=f"add_btn_{d_idx}", use_container_width=True):
                    items.append(
                        {
                            "exercise": add_ex,
                            "sets": int(add_sets),
                            "reps": int(add_reps),
                            "weight": 0.0,
                            "rest_sec": int(add_rest),
                            "notes": "",
                        }
                    )
                    day["items"] = items
                    st.rerun()

    st.session_state["tpl_editor"] = plan

    st.markdown("---")
    prefix = st.text_input("Nombre al guardar", value=plan.get("name", "Plantilla"), key="tpl_save_prefix")
    s1, s2 = st.columns(2)
    with s1:
        save_days = st.button("Guardar cada día", type="primary", use_container_width=True)
    with s2:
        save_one = st.button("Guardar plan completo", use_container_width=True)
    st.caption(
        "Plan completo: se guarda junto pero mantiene los días por separado "
        "para asignarlos en el calendario."
    )

    if save_days or save_one:
        if not user:
            st.error("Inicia sesión para guardar.")
            return
        existing = {r.get("name") for r in list_routines(user)}
        try:
            if save_one:
                days_payload = []
                for day in plan.get("days") or []:
                    items = day_to_routine_items(day)
                    if not items:
                        continue
                    days_payload.append(
                        {
                            "name": day.get("name") or "Día",
                            "focus": day.get("focus") or "",
                            "items": items,
                        }
                    )
                name = (prefix or plan.get("name") or "Plantilla").strip()
                base, n = name, 2
                while name in existing:
                    name = f"{base} ({n})"
                    n += 1
                if not days_payload:
                    st.warning("No hay ejercicios para guardar.")
                else:
                    add_routine(user, name, [], days=days_payload)
                    st.success(
                        f"Guardado el plan **{name}** con {len(days_payload)} días. "
                        "En Planificar puedes asignar cada día al calendario."
                    )
            else:
                saved = 0
                for day in plan.get("days") or []:
                    day_name = f"{prefix} — {day.get('name')}".strip(" —")
                    base, n = day_name, 2
                    while day_name in existing:
                        day_name = f"{base} ({n})"
                        n += 1
                    items = day_to_routine_items(day)
                    if not items:
                        continue
                    add_routine(user, day_name, items)
                    existing.add(day_name)
                    saved += 1
                st.success(f"Guardadas {saved} rutinas. Ve a Planificar.")
        except Exception as e:
            st.error(str(e))
