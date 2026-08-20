"""Planificador de rutinas — UI limpia y centrada en el calendario."""

from __future__ import annotations

import calendar as _cal
import datetime as _dt
from collections import Counter, defaultdict
from io import BytesIO

import pandas as pd
import streamlit as st

from app.datastore import load_user, save_user
from app.exercises import list_all_exercises
from app.routines import add_routine, delete_routine, list_routines, rename_routine


def _get_plan(u: str) -> dict:
    data = load_user(u) or {}
    return dict(data.get("routine_plan", {}))


def _set_plan(u: str, d_iso: str, routine_name: str | None) -> None:
    data = load_user(u) or {}
    plan = dict(data.get("routine_plan", {}))
    if routine_name:
        plan[d_iso] = routine_name
    elif d_iso in plan:
        del plan[d_iso]
    data["routine_plan"] = plan
    save_user(u, data)


_ROUTINE_PALETTE = [
    "#B8E8E0",  # teal
    "#BFD4F5",  # blue
    "#F5C9A8",  # peach
    "#C8E6A8",  # green
    "#D4C2F0",  # lilac
    "#F5B8C8",  # pink
    "#FFE08A",  # yellow
    "#A8D8F0",  # sky
    "#E8C4A0",  # sand
    "#B8F0C8",  # mint
    "#F0B8A8",  # coral
    "#C8C8F0",  # periwinkle
]


def _colors_for_names(names: list[str]) -> dict[str, str]:
    """Asigna un color distinto a cada rutina (sin colisiones por hash)."""
    unique = sorted({n for n in names if n})
    n = len(_ROUTINE_PALETTE)
    return {name: _ROUTINE_PALETTE[i % n] for i, name in enumerate(unique)}


_MONTH_ES = [
    "", "Enero", "Febrero", "Marzo", "Abril", "Mayo", "Junio",
    "Julio", "Agosto", "Septiembre", "Octubre", "Noviembre", "Diciembre",
]


def _month_label(year: int, month: int) -> str:
    return f"{_MONTH_ES[month]} {year}"


def _months_with_plan(plan: dict) -> list[tuple[int, int]]:
    """Meses (año, mes) que tienen al menos una rutina asignada."""
    seen: set[tuple[int, int]] = set()
    for iso, name in plan.items():
        if not name:
            continue
        try:
            d = _dt.date.fromisoformat(iso)
        except ValueError:
            continue
        seen.add((d.year, d.month))
    return sorted(seen, reverse=True)


def _copy_weekday_pattern(
    user: str,
    src_year: int,
    src_month: int,
    dst_year: int,
    dst_month: int,
    *,
    wipe: bool,
) -> int:
    """Copia el patrón por día de la semana del mes origen al destino. Devuelve nº de días."""
    plan_current = _get_plan(user)
    freq: dict = defaultdict(Counter)
    days_src = _cal.monthrange(src_year, src_month)[1]
    for d in range(1, days_src + 1):
        dd = _dt.date(src_year, src_month, d)
        val = plan_current.get(dd.isoformat())
        if val:
            freq[dd.weekday()][val] += 1
    weekday_map = {wd: counter.most_common(1)[0][0] for wd, counter in freq.items() if counter}
    if not weekday_map:
        return 0
    days_dst = _cal.monthrange(dst_year, dst_month)[1]
    if wipe:
        for d in range(1, days_dst + 1):
            _set_plan(user, _dt.date(dst_year, dst_month, d).isoformat(), None)
    applied = 0
    for d in range(1, days_dst + 1):
        dd = _dt.date(dst_year, dst_month, d)
        if dd.weekday() in weekday_map:
            _set_plan(user, dd.isoformat(), weekday_map[dd.weekday()])
            applied += 1
    return applied


def _render_month_calendar(plan: dict, year: int, month: int) -> None:
    cal = _cal.Calendar(firstweekday=0)
    weeks = cal.monthdayscalendar(year, month)
    weekdays = ["Lun", "Mar", "Mié", "Jue", "Vie", "Sáb", "Dom"]

    month_names: list[str] = []
    for week in weeks:
        for day in week:
            if day == 0:
                continue
            n = plan.get(_dt.date(year, month, day).isoformat(), "")
            if n:
                month_names.append(n)
    colors = _colors_for_names(month_names)
    assigned = sorted(colors.keys())

    html = """
    <style>
    .vp-cal { width:100%; border-collapse:separate; border-spacing:6px; table-layout:fixed; }
    .vp-cal th {
      font-family: Manrope, sans-serif; font-size:0.72rem; font-weight:700;
      letter-spacing:0.06em; text-transform:uppercase; color:#6A7F88;
      padding:0.35rem; text-align:center;
    }
    .vp-cal td {
      background:#fff; border:1px solid rgba(20,40,48,0.08); border-radius:10px;
      vertical-align:top; height:72px; padding:8px;
    }
    .vp-cal .dnum { font-weight:700; font-size:0.85rem; color:#142830; }
    .vp-cal .tag {
      display:block; margin-top:6px; padding:4px 6px; border-radius:6px;
      font-size:0.7rem; font-weight:600; line-height:1.25; word-break:break-word;
    }
    .vp-cal .libre { opacity:0.45; font-weight:500; background:#F3F6F4; }
    </style>
    <table class="vp-cal"><thead><tr>
    """
    html += "".join(f"<th>{d}</th>" for d in weekdays) + "</tr></thead><tbody>"
    for week in weeks:
        html += "<tr>"
        for day in week:
            if day == 0:
                html += "<td style='background:transparent;border:none'></td>"
                continue
            d = _dt.date(year, month, day)
            name = plan.get(d.isoformat(), "")
            tag = (
                f'<span class="tag" style="background:{colors[name]}">{name}</span>'
                if name
                else '<span class="tag libre">Libre</span>'
            )
            html += f'<td><div class="dnum">{day}</div>{tag}</td>'
        html += "</tr>"
    html += "</tbody></table>"
    if assigned:
        chips = " ".join(
            f'<span class="tag" style="display:inline-block;margin:2px 4px;background:{colors[n]}">{n}</span>'
            for n in assigned
        )
        html += f'<div style="margin-top:8px">{chips}</div>'
    st.markdown(html, unsafe_allow_html=True)


def render_planner_page(user: str) -> None:
    routines = list_routines(user)
    routine_names = [r["name"] for r in routines] if routines else []
    plan = _get_plan(user)
    today = _dt.date.today()
    today_iso = today.isoformat()
    today_rt = plan.get(today_iso)

    # —— Hoy ——
    if today_rt:
        st.info(f"**Hoy:** {today_rt}")
    else:
        st.caption("Hoy no tienes rutina asignada.")

    if not routine_names:
        st.warning("Aún no tienes rutinas. Ve a **Plantillas**, elige un plan y guárdalo.")
        return

    # —— Calendario ——
    st.markdown("#### Calendario")
    if "planner_month" not in st.session_state:
        st.session_state["planner_month"] = today.replace(day=1)

    nav1, nav2, nav3 = st.columns([1, 2, 1])
    with nav1:
        if st.button("← Mes", use_container_width=True, key="planner_prev_m"):
            base = st.session_state["planner_month"]
            if base.month == 1:
                st.session_state["planner_month"] = base.replace(year=base.year - 1, month=12)
            else:
                st.session_state["planner_month"] = base.replace(month=base.month - 1)
            st.rerun()
    with nav2:
        ym = st.session_state["planner_month"]
        st.markdown(
            f"<div style='text-align:center;font-family:Barlow Condensed,sans-serif;"
            f"font-size:1.4rem;font-weight:700;text-transform:uppercase;padding-top:0.35rem'>"
            f"{ym.strftime('%B %Y')}</div>",
            unsafe_allow_html=True,
        )
    with nav3:
        if st.button("Mes →", use_container_width=True, key="planner_next_m"):
            base = st.session_state["planner_month"]
            if base.month == 12:
                st.session_state["planner_month"] = base.replace(year=base.year + 1, month=1)
            else:
                st.session_state["planner_month"] = base.replace(month=base.month + 1)
            st.rerun()

    ym = st.session_state["planner_month"]
    _render_month_calendar(plan, ym.year, ym.month)

    # —— Copiar de otro mes (destino = mes visible) ——
    with st.expander(f"Copiar entrenos a {_month_label(ym.year, ym.month)}", expanded=False):
        st.caption("Replica el patrón semanal (lun/mar/…) de otro mes en el que estás viendo.")
        months_avail = _months_with_plan(plan)
        months_avail = [(y, m) for y, m in months_avail if (y, m) != (ym.year, ym.month)]
        if not months_avail:
            st.info("No hay otros meses con entrenos guardados. Asigna rutinas en un mes y vuelve aquí.")
        else:
            labels = [_month_label(y, m) for y, m in months_avail]
            pick = st.selectbox("Copiar desde", labels, key="planner_copy_src")
            src_y, src_m = months_avail[labels.index(pick)]
            wipe = st.checkbox(
                f"Vaciar antes {_month_label(ym.year, ym.month)}",
                value=False,
                key="planner_copy_wipe",
            )
            if st.button("Copiar al mes actual", type="primary", use_container_width=True, key="planner_copy_go"):
                n = _copy_weekday_pattern(
                    user, src_y, src_m, ym.year, ym.month, wipe=wipe
                )
                if n == 0:
                    st.warning("El mes origen no tiene asignaciones útiles.")
                else:
                    st.success(f"Copiados {n} días desde {pick}.")
                    st.rerun()

    st.markdown("---")

    # —— Asignar (único flujo principal) ——
    st.markdown("#### Asignar")
    a1, a2, a3 = st.columns([1.2, 1.6, 1.2])
    with a1:
        sel_date = st.date_input("Día", value=today, key="planner_day")
    with a2:
        sel_rt = st.selectbox("Rutina", routine_names, key="planner_rt")
    with a3:
        st.write("")
        st.write("")
        b1, b2 = st.columns(2)
        with b1:
            if st.button("Asignar", type="primary", use_container_width=True, key="planner_assign"):
                _set_plan(user, sel_date.isoformat(), sel_rt)
                st.success("Listo")
                st.rerun()
        with b2:
            if st.button("Quitar", use_container_width=True, key="planner_clear"):
                _set_plan(user, sel_date.isoformat(), None)
                st.rerun()

    # Preview del día elegido
    prev = plan.get(sel_date.isoformat())
    if prev:
        r = next((rr for rr in routines if rr["name"] == prev), None)
        with st.expander(f"Detalle · {prev}", expanded=False):
            if r:
                st.dataframe(pd.DataFrame(r.get("items", [])), use_container_width=True, hide_index=True)
            else:
                st.caption("La rutina ya no existe.")

    # —— Repetir en el mes (secundario) ——
    with st.expander("Repetir un día de la semana en todo el mes", expanded=False):
        weekday_names = ["Lunes", "Martes", "Miércoles", "Jueves", "Viernes", "Sábado", "Domingo"]
        w1, w2 = st.columns(2)
        with w1:
            wd = st.selectbox(
                "Día de la semana",
                list(range(7)),
                format_func=lambda i: weekday_names[i],
                key="planner_wd",
            )
        with w2:
            wr = st.selectbox("Rutina", routine_names, key="planner_wd_rt")
        if st.button("Aplicar a todo el mes", use_container_width=True, key="planner_wd_apply"):
            count = 0
            days_in = _cal.monthrange(ym.year, ym.month)[1]
            for d in range(1, days_in + 1):
                dd = _dt.date(ym.year, ym.month, d)
                if dd.weekday() == wd:
                    _set_plan(user, dd.isoformat(), wr)
                    count += 1
            st.success(f"Asignado a {count} días.")
            st.rerun()

    # —— Mis rutinas ——
    with st.expander(f"Mis rutinas ({len(routines)})", expanded=False):
        sel = st.selectbox("Ver", routine_names, key="planner_registry")
        r = next(rr for rr in routines if rr["name"] == sel)
        st.dataframe(pd.DataFrame(r.get("items", [])), use_container_width=True, hide_index=True)
        c1, c2 = st.columns(2)
        with c1:
            new_name = st.text_input("Renombrar", value=sel, key="planner_rename")
            if st.button("Guardar nombre", use_container_width=True) and new_name and new_name != sel:
                try:
                    rename_routine(user, sel, new_name)
                    st.rerun()
                except Exception as e:
                    st.error(str(e))
        with c2:
            st.write("")
            st.write("")
            if st.button("Eliminar rutina", use_container_width=True, key="planner_del_rt"):
                delete_routine(user, sel)
                st.rerun()

        st.markdown("**Crear rutina manual**")
        exercises = list_all_exercises(user)
        with st.form("planner_create_rt"):
            rt_name = st.text_input("Nombre")
            df_items = st.data_editor(
                pd.DataFrame([{"exercise": exercises[0] if exercises else "", "sets": 3, "reps": 10, "weight": 0.0}]),
                num_rows="dynamic",
                use_container_width=True,
                column_config={
                    "exercise": st.column_config.SelectboxColumn("Ejercicio", options=exercises, required=True),
                    "sets": st.column_config.NumberColumn("Series", min_value=1, max_value=20, step=1),
                    "reps": st.column_config.NumberColumn("Reps", min_value=1, max_value=100, step=1),
                    "weight": st.column_config.NumberColumn("Peso", min_value=0.0, step=0.5),
                },
                hide_index=True,
            )
            if st.form_submit_button("Crear", type="primary"):
                rows = []
                for _, row in df_items.dropna(subset=["exercise"]).iterrows():
                    ex = str(row.get("exercise") or "").strip()
                    if not ex:
                        continue
                    rows.append(
                        {
                            "exercise": ex,
                            "sets": int(row.get("sets") or 1),
                            "reps": int(row.get("reps") or 10),
                            "weight": float(row.get("weight") or 0.0),
                        }
                    )
                if not rt_name or not rows:
                    st.warning("Nombre y al menos un ejercicio.")
                else:
                    try:
                        add_routine(user, rt_name, rows)
                        st.success("Creada.")
                        st.rerun()
                    except Exception as e:
                        st.error(str(e))

    # —— Más opciones ——
    with st.expander("Más opciones", expanded=False):
        st.caption("Exportar PDF")
        try:
            from reportlab.lib import colors
            from reportlab.lib.pagesizes import A4
            from reportlab.lib.styles import getSampleStyleSheet
            from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle
        except Exception:
            st.caption("Instala reportlab para exportar PDF.")
            return

        export_sel = st.selectbox("Rutina", routine_names, key="pdf_rt")
        if st.button("Generar PDF", use_container_width=True):
            r = next(rr for rr in routines if rr["name"] == export_sel)
            buf = BytesIO()
            doc = SimpleDocTemplate(buf, pagesize=A4, leftMargin=36, rightMargin=36, topMargin=36, bottomMargin=36)
            styles = getSampleStyleSheet()
            story = [Paragraph(f"Rutina — {export_sel}", styles["Title"]), Spacer(1, 12)]
            data = [["Ejercicio", "Series", "Reps", "Peso"]]
            for it in r.get("items", []):
                data.append(
                    [
                        str(it.get("exercise", "")),
                        str(it.get("sets", "")),
                        str(it.get("reps", "")),
                        str(it.get("weight", "")),
                    ]
                )
            table = Table(data, repeatRows=1)
            table.setStyle(
                TableStyle(
                    [
                        ("BACKGROUND", (0, 0), (-1, 0), colors.lightgrey),
                        ("GRID", (0, 0), (-1, -1), 0.5, colors.grey),
                        ("FONTSIZE", (0, 0), (-1, -1), 10),
                    ]
                )
            )
            story.append(table)
            doc.build(story)
            st.download_button(
                "Descargar PDF",
                data=buf.getvalue(),
                file_name=f"rutina_{export_sel}.pdf",
                mime="application/pdf",
                use_container_width=True,
            )
