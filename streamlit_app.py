import matplotlib.pyplot as plt
from datetime import date
from pathlib import Path

import pandas as pd
import streamlit as st

from app.datastore import (
    ensure_base_dirs, register_user, authenticate, load_user, save_user,
)
from app.exercises import (
    list_all_exercises, add_custom_exercise, remove_custom_exercise, rename_custom_exercise,
    save_exercise_meta, get_exercise_meta, GRUPOS, store_exercise_image,
)
from app.training import (
    add_training_set, list_training, last_values_for_exercise,
)
from app.health import (
    add_weight, list_weights,
)
from app.routines import (
    list_routines, add_routine, delete_routine, rename_routine, apply_routine
)

st.set_page_config(page_title="Gym App Web", page_icon="🏋️", layout="wide")
ensure_base_dirs()

def require_auth():
    if "user" not in st.session_state or not st.session_state["user"]:
        st.warning("Inicia sesión para continuar.")
        st.stop()

def logout():
    st.session_state.clear()
    st.rerun()

with st.sidebar:
    if "user" in st.session_state and st.session_state["user"]:
        st.success(f"Conectado como **{st.session_state['user']}**")
        if st.button("Cerrar sesión", use_container_width=True):
            logout()
    st.markdown("---")
    page = st.radio(
        "Secciones",
        [
            "🔐 Login / Registro",
            "🏠 Inicio",
            "🏋️ Añadir entrenamiento",
            "📚 Gestor de ejercicios",
            "📈 Tabla de entrenamientos",
            "🩺 Salud (Peso)",
            "📘 Rutinas",
        ],
        index=0 if "user" not in st.session_state else 1,
    )

if page == "🔐 Login / Registro":
    st.title("Acceso")
    col1, col2 = st.columns(2)
    with col1:
        st.subheader("Iniciar sesión")
        u = st.text_input("Usuario", key="login_user")
        p = st.text_input("Contraseña", type="password", key="login_pass")
        if st.button("Entrar"):
            if authenticate(u, p):
                st.session_state["user"] = u
                st.success("¡Bienvenido!")
                st.rerun()
            else:
                st.error("Usuario/contraseña incorrectos.")
    with col2:
        st.subheader("Crear cuenta")
        u2 = st.text_input("Nuevo usuario", key="reg_user")
        p2 = st.text_input("Nueva contraseña", type="password", key="reg_pass")
        if st.button("Registrarme"):
            if not u2 or not p2:
                st.warning("Completa usuario y contraseña.")
            else:
                created = register_user(u2, p2)
                if created:
                    st.success("Usuario creado. Ahora inicia sesión.")
                else:
                    st.error("Ese usuario ya existe.")

elif page == "🏠 Inicio":
    require_auth()
    st.title("Inicio")
    st.write("Usa la barra lateral para navegar. Datos persistidos en `usuarios_data/<usuario>.json`.")


elif page == "🏋️ Añadir entrenamiento":
    require_auth()
    st.title("Añadir entrenamiento")
    user = st.session_state["user"]
    d = st.date_input("Fecha", value=date.today())
    exercises = list_all_exercises(user)
    ex = st.selectbox("Ejercicio", options=exercises)
    suggestion = last_values_for_exercise(user, ex)

    with st.form("add_set_form", clear_on_submit=False):
        colA, colB, colC = st.columns(3)
        with colA:
            set_idx = st.number_input("Serie #", min_value=1, step=1, value=1)
        with colB:
            reps = st.number_input("Repeticiones", min_value=1, step=1, value=int(suggestion[0]) if suggestion else 10)
        with colC:
            weight = st.number_input("Peso (kg)", min_value=0.0, step=0.5, value=float(suggestion[1]) if suggestion else 0.0)
        if suggestion:
            st.caption(f"Sugerencia última serie de **{ex}**: {suggestion[0]} reps @ {suggestion[1]} kg")
        submit_add = st.form_submit_button("Añadir serie")
    if submit_add:
        add_training_set(user, d.isoformat(), ex, int(set_idx), int(reps), float(weight))
        st.success("Serie guardada.")

    st.markdown("---")
    st.subheader("Importar rutina y rellenar pesos")
    # Editor de entrenamiento desde rutina (nuevo)
    import pandas as _pd

    routines = list_routines(user)
    if routines:
        names = [r["name"] for r in routines]
        col1, col2 = st.columns([3,1])
        sel_r = col1.selectbox("Rutina", names, key="train_sel_routine")
        if col2.button("Importar rutina", use_container_width=True):
            r = next(r for r in routines if r["name"] == sel_r)
            rows = []
            for it in r.get("items", []):
                ex_name = it.get("exercise")
                sets = int(it.get("sets", 1))
                reps = int(it.get("reps", 10))
                for s in range(1, sets+1):
                    rows.append({"ejercicio": ex_name, "serie": s, "reps": reps, "peso": 0.0})
            st.session_state['routine_rows'] = rows
            st.success(f"Rutina '{sel_r}' importada para el {d.isoformat()}.")
            st.rerun()

        if 'routine_rows' in st.session_state and st.session_state['routine_rows']:
            with st.form("routine_editor_form", clear_on_submit=False):
                df = _pd.DataFrame(st.session_state['routine_rows'])
                edited = st.data_editor(
                    df,
                    key="routine_editor_table",
                    num_rows="dynamic",
                    use_container_width=True,
                    column_config={
                        "ejercicio": st.column_config.TextColumn("Ejercicio", disabled=True),
                        "serie": st.column_config.NumberColumn("Serie", min_value=1, step=1),
                        "reps": st.column_config.NumberColumn("Reps", min_value=1, step=1),
                        "peso": st.column_config.NumberColumn("Peso (kg)", min_value=0.0, step=0.5),
                    },
                    hide_index=True
                )

                cA, cB, cC = st.columns(3)
                target = cA.text_input("Ejercicio objetivo", placeholder="ej. press banca")
                add_series = cB.form_submit_button("+ Añadir serie", disabled=not target)
                del_series = cC.form_submit_button("🗑️ Eliminar última serie", disabled=not target)

                # Aplicar acciones de serie
                if add_series:
                    subset = edited[edited["ejercicio"].str.lower() == target.lower()]
                    if subset.empty:
                        st.warning("No encontré ese ejercicio en la tabla.")
                    else:
                        max_s = int(subset["serie"].max())
                        reps_def = int(subset["reps"].iloc[0])
                        new_row = {"ejercicio": target, "serie": max_s+1, "reps": reps_def, "peso": 0.0}
                        edited = _pd.concat([edited, _pd.DataFrame([new_row])], ignore_index=True)

                if del_series:
                    mask = edited["ejercicio"].str.lower() == target.lower()
                    subset = edited[mask]
                    if subset.empty:
                        st.warning("No encontré ese ejercicio en la tabla.")
                    else:
                        max_s = int(subset["serie"].max())
                        drop_idx = edited[(mask) & (edited["serie"] == max_s)].index
                        edited = edited.drop(index=drop_idx)

                # Guardar
                save_edited = st.form_submit_button("💾 Guardar entrenamiento desde rutina")
            # Fuera del form: sincroniza y guarda si procede
            st.session_state['routine_rows'] = edited.to_dict(orient="records")
            if save_edited:
                count = 0
                for row in st.session_state['routine_rows']:
                    try:
                        add_training_set(user, d.isoformat(), row["ejercicio"], int(row["serie"]), int(row["reps"]), float(row.get("peso") or 0.0))
                        count += 1
                    except Exception as e:
                        st.error(f"Error guardando {row}: {e}")
                st.success(f"Se guardaron {count} series en {d.isoformat()}.")
                st.session_state.pop('routine_rows', None)
    else:
        st.info("Primero crea una rutina en la sección 📘 Rutinas.")

elif page == "📚 Gestor de ejercicios":
    require_auth()
    st.title("Gestor de ejercicios")
    user = st.session_state["user"]
    all_ex = list_all_exercises(user)
    st.write(f"Total ejercicios: **{len(all_ex)}**")

    st.subheader("Añadir ejercicio personalizado")
    new_name = st.text_input("Nombre del ejercicio nuevo")
    if st.button("Añadir") and new_name:
        add_custom_exercise(user, new_name)
        st.success(f"Añadido: {new_name}")
        st.rerun()

    st.subheader("Editar meta (grupo, imagen)")
    ex = st.selectbox("Ejercicio", options=all_ex, key="meta_select")
    meta = get_exercise_meta(user, ex)
    grupo = st.selectbox("Grupo muscular", options=GRUPOS, index=GRUPOS.index(meta.get("grupo","Otro")) if meta.get("grupo") in GRUPOS else GRUPOS.index("Otro"))
    img_up = st.file_uploader("Imagen del ejercicio (opcional)", type=["png","jpg","jpeg","webp"])
    img_rel = meta.get("imagen")
    if img_up is not None:
        img_rel = store_exercise_image(user, img_up.name, img_up.getbuffer())
    if st.button("Guardar meta"):
        save_exercise_meta(user, ex, grupo, img_rel)
        st.success("Meta guardada.")
    if img_rel:
        st.image(str(img_rel), caption=f"Imagen {ex}", width=240)

    st.subheader("Renombrar / Eliminar")
    col1, col2 = st.columns(2)
    with col1:
        to_rename = st.selectbox("Ejercicio a renombrar", options=all_ex, key="rename_select")
        new_name2 = st.text_input("Nuevo nombre")
        if st.button("Renombrar"):
            if new_name2:
                rename_custom_exercise(user, to_rename, new_name2)
                st.success("Renombrado.")
                st.rerun()
            else:
                st.warning("Escribe un nuevo nombre.")
    with col2:
        del_name = st.text_input("Nombre exacto a eliminar (personalizado)")
        if st.button("Eliminar"):
            if del_name and del_name not in set(list_all_exercises(user)[:len(list_all_exercises(user))]):
                remove_custom_exercise(user, del_name)
                st.success("Eliminado.")
                st.rerun()
            else:
                st.warning("Solo se pueden eliminar personalizados.")

elif page == "📈 Tabla de entrenamientos":
    require_auth()
    st.title("Tabla de entrenamientos")
    user = st.session_state["user"]
    rows = list_training(user)
    if not rows:
        st.info("Aún no hay registros.")
    else:
        df = pd.DataFrame(rows)
        colf1, colf2, colf3 = st.columns(3)
        with colf1:
            exs = sorted(df["exercise"].unique().tolist())
            sel_ex = st.multiselect("Filtrar ejercicio", exs, default=exs)
        with colf2:
            d_from = st.date_input("Desde", value=pd.to_datetime(df["date"]).min().date())
        with colf3:
            d_to = st.date_input("Hasta", value=pd.to_datetime(df["date"]).max().date())
        mask = (df["exercise"].isin(sel_ex)) & (pd.to_datetime(df["date"]).dt.date.between(d_from, d_to))
        df_filtered = df[mask].sort_values(["date","exercise","set"]).reset_index(drop=True)
        st.dataframe(df_filtered)

        # Exportar Excel consolidado (una hoja por mes/semana o todo)
        modo = st.selectbox("Consolidar en hoja por:", ["mes","semana","todo"], index=0)
        from io import BytesIO
        import pandas as _pd, calendar as _cal, datetime as _dt
        def export_entrenamientos_excel(df_in: _pd.DataFrame, modo: str = "mes") -> bytes:
            out = BytesIO()
            with _pd.ExcelWriter(out, engine="xlsxwriter") as writer:
                if "date" not in df_in.columns:
                    raise ValueError("Falta columna 'date'")
                df_in = df_in.copy()
                df_in["date"] = _pd.to_datetime(df_in["date"])
                if modo == "todo":
                    sheet_name = "Entrenamientos"; row = 0
                    for dt, g in df_in.sort_values("date").groupby(df_in["date"].dt.date):
                        g2 = g.sort_values(["date","exercise","set"])
                        writer.sheets.setdefault(sheet_name, writer.book.add_worksheet(sheet_name))
                        ws = writer.sheets[sheet_name]
                        ws.write(row, 0, f"Fecha: {dt.isoformat()}"); row += 1
                        g2.to_excel(writer, sheet_name=sheet_name, index=False, startrow=row)
                        row += len(g2) + 2
                else:
                    if modo == "mes":
                        df_in["_key"] = df_in["date"].dt.strftime("%Y-%m")
                    else:
                        df_in["_key"] = df_in["date"].dt.strftime("%G-W%V")
                    for key, gkey in df_in.sort_values(["_key","date"]).groupby("_key"):
                        sheet = str(key); row = 0
                        for dt, gday in gkey.groupby(gkey["date"].dt.date):
                            g2 = gday.drop(columns=["_key"]).sort_values(["date","exercise","set"])
                            writer.sheets.setdefault(sheet, writer.book.add_worksheet(sheet))
                            ws = writer.sheets[sheet]
                            ws.write(row, 0, f"Fecha: {dt.isoformat()}"); row += 1
                            g2.to_excel(writer, sheet_name=sheet, index=False, startrow=row)
                            row += len(g2) + 2
            return out.getvalue()

        if st.button("Exportar a Excel (consolidado)", use_container_width=True):
            try:
                xbytes = export_entrenamientos_excel(df_filtered, modo=modo)
                st.download_button("Descargar Excel", data=xbytes, file_name=f"entrenamientos_{modo}.xlsx", mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet", use_container_width=True)
            except Exception as e:
                st.error(str(e))


elif page == "🩺 Salud (Peso)":
    require_auth()
    st.title("Salud — Peso")
    user = st.session_state["user"]
    col1, col2 = st.columns(2)
    with col1:
        st.subheader("Añadir registro")
        with st.form("weight_form", clear_on_submit=False):
            d = st.date_input("Fecha", value=date.today(), key="peso_fecha")
            w = st.number_input("Peso (kg)", min_value=0.0, step=0.1, value=70.0, key="peso_valor")
            guardar = st.form_submit_button("Guardar peso")
        if guardar:
            add_weight(user, d.isoformat(), float(w))
            st.success("Peso guardado.")
    with col2:
        st.subheader("Tabla de pesos")
        rows = list_weights(user)
        if rows:
            df_tab = pd.DataFrame(rows).sort_values("date", ascending=False)
            st.dataframe(df_tab, use_container_width=True, hide_index=True)
        else:
            st.info("Sin registros aún.")
    st.subheader("Gráfico de evolución")
    rows = list_weights(user)
    if rows:
        import matplotlib.dates as mdates
        import datetime as _dt
        df = pd.DataFrame(rows)
        df["date"] = pd.to_datetime(df["date"]).dt.date
        df = df.sort_values("date")

        # Filtro de fechas: por defecto últimos 6 meses (ajustados al rango de datos)
        import datetime as _dt
        data_min = df["date"].min()
        data_max = df["date"].max()
        # Asegurar tipos date
        if hasattr(data_min, "to_pydatetime"): data_min = data_min.to_pydatetime().date()
        if hasattr(data_max, "to_pydatetime"): data_max = data_max.to_pydatetime().date()
        today = _dt.date.today()
        # Fin por defecto no puede superar el último dato
        default_end = data_max if today > data_max else today
        # Inicio por defecto es 180 días antes pero no menor que el primer dato
        candidate_start = default_end - _dt.timedelta(days=180)
        default_start = candidate_start if candidate_start > data_min else data_min
        colf1, colf2 = st.columns(2)
        start_date = colf1.date_input("Desde", value=default_start, min_value=data_min, max_value=data_max)
        end_date = colf2.date_input("Hasta", value=default_end, min_value=data_min, max_value=data_max)
        if start_date > end_date:
            st.warning("El rango de fechas es inválido (Desde > Hasta).")
        mask = (df["date"] >= start_date) & (df["date"] <= end_date)
        df_plot = df[mask]

        if df_plot.empty:
            st.info("No hay datos en el rango seleccionado.")
        # --- Gráfica de peso (bloque limpio, sin TABs) ---
        if not df_plot.empty:
            fig, ax = plt.subplots()
            ax.plot(df_plot["date"], df_plot["weight"], marker="o")
            ax.set_xlabel("Fecha")
            ax.set_ylabel("Peso (kg)")
            ax.set_title("Evolución de peso")

            # Fechas en vertical para que no se solapen
            ax.xaxis.set_major_locator(mdates.AutoDateLocator())
            ax.xaxis.set_major_formatter(mdates.DateFormatter("%d-%m"))
            for label in ax.get_xticklabels():
                label.set_rotation(90)
                label.set_fontsize(8)

            fig.tight_layout()
            st.pyplot(fig, clear_figure=True)
        else:
            st.info("No hay datos de peso para mostrar.")
        
elif page == "📘 Rutinas":
    require_auth()
    st.title("Planificador de rutinas")
    user = st.session_state["user"]

    # ---------- Utilidades de plan ----------
    def _get_plan(u: str):
        data = load_user(u)
        return dict(data.get("routine_plan", {}))

    def _set_plan(u: str, d_iso: str, routine_name: str | None):
        data = load_user(u)
        plan = dict(data.get("routine_plan", {}))
        if routine_name:
            plan[d_iso] = routine_name
        else:
            if d_iso in plan:
                del plan[d_iso]
        data["routine_plan"] = plan
        save_user(u, data)

    routines = list_routines(user)
    routine_names = [r["name"] for r in routines] if routines else []
    plan = _get_plan(user)

    # ---------- RUTINA DE HOY ----------
    with st.expander("RUTINA DE HOY", expanded=False):
        today = date.today()
        today_iso = today.isoformat()
        if plan.get(today_iso):
            rt_name = plan[today_iso]
            st.markdown(f"**{rt_name}**")
            r = next((rr for rr in routines if rr["name"] == rt_name), None)
            if r:
                st.table(pd.DataFrame(r.get("items", [])))
            else:
                st.info("La rutina asignada ya no existe.")
        else:
            st.success("Día libre 🎉")

    # ---------- Planificar por día (asignación puntual) ----------
    with st.expander("Planificar por día (asignación puntual — solo ese día)", expanded=False):
        colA, colB = st.columns(2)
        with colA:
            st.subheader("Asignar rutina por día")
            sel_date = st.date_input("Día a asignar", value=date.today(), key="planner_assign_date")
            if routine_names:
                sel_routine = st.selectbox("Rutina a asignar", routine_names, key="planner_assign_rt")
            else:
                sel_routine = None
                st.info("No tienes rutinas creadas aún.")
            c1, c2 = st.columns(2)
            with c1:
                if st.button("Asignar rutina (solo ese día)", use_container_width=True, disabled=sel_routine is None):
                    _set_plan(user, sel_date.isoformat(), sel_routine)
                    st.success(f"Asignada **{sel_routine}** al {sel_date.isoformat()}.")
                    st.rerun()
            with c2:
                if st.button("Eliminar asignación de ese día", use_container_width=True):
                    _set_plan(user, sel_date.isoformat(), None)
                    st.success(f"Eliminada asignación del {sel_date.isoformat()}.")
                    st.rerun()
        with colB:
            st.subheader("Ver rutina de un día")
            view_date = st.date_input("Ir a día", value=date.today(), key="planner_view_date")
            d_iso = view_date.isoformat()
            rt = plan.get(d_iso)
            if rt:
                st.write(f"**Rutina asignada**: {rt}")
                r = next((rr for rr in routines if rr["name"] == rt), None)
                if r:
                    st.table(pd.DataFrame(r.get("items", [])))
                else:
                    st.info("La rutina asignada ya no existe.")
            else:
                st.info("Día libre")

    # ---------- Asignar/Desasignar por día de semana para todo el mes ----------
    with st.expander("Asignar rutina a un día de la semana para todo el mes", expanded=False):
        import datetime as _dt
        import calendar as _cal
        month_picker = st.date_input("Elegir mes (cualquier día dentro del mes)", value=date.today(), key="month_picker")
        target_year, target_month = month_picker.year, month_picker.month
        weekday_names = ["Lunes", "Martes", "Miércoles", "Jueves", "Viernes", "Sábado", "Domingo"]
        weekday_index = st.selectbox("Día de la semana", options=list(range(7)), format_func=lambda i: weekday_names[i], key="weekday_for_month")
        if routine_names:
            month_routine = st.selectbox("Rutina a asignar", routine_names, key="weekday_month_routine")
        else:
            month_routine = None
            st.info("No tienes rutinas creadas aún. Crea una en el apartado de abajo.")
        def _iter_month_dates(year: int, month: int):
            days_in_month = _cal.monthrange(year, month)[1]
            for d in range(1, days_in_month + 1):
                yield _dt.date(year, month, d)
        colm1, colm2 = st.columns(2)
        with colm1:
            if st.button("Asignar a todo el mes", use_container_width=True, disabled=month_routine is None):
                count = 0
                for d in _iter_month_dates(target_year, target_month):
                    if d.weekday() == weekday_index:
                        _set_plan(user, d.isoformat(), month_routine)
                        count += 1
                st.success(f"Asignada **{month_routine}** a todos los {weekday_names[weekday_index]} de {target_month:02d}/{target_year}. Total días: {count}.")
                st.rerun()
        with colm2:
            if st.button("Desasignar todos ese día de la semana en el mes", use_container_width=True):
                count = 0
                for d in _iter_month_dates(target_year, target_month):
                    if d.weekday() == weekday_index and d.isoformat() in plan:
                        _set_plan(user, d.isoformat(), None)
                        count += 1
                st.success(f"Desasignadas {count} fechas de los {weekday_names[weekday_index]} de {target_month:02d}/{target_year}.")
                st.rerun()

    # ---------- Mini-calendario mensual coloreado ----------
    with st.expander("Mini-calendario mensual (vista rápida)", expanded=False):
        import calendar as _cal
        import datetime as _dt
        cal_month = st.date_input("Elegir mes", value=date.today(), key="mini_cal_month")
        y, m = cal_month.year, cal_month.month
        cal = _cal.Calendar(firstweekday=0)
        weeks = cal.monthdayscalendar(y, m)
        palette = ["#E3F2FD", "#FCE4EC", "#E8F5E9", "#FFF3E0", "#F3E5F5", "#E0F2F1", "#F9FBE7", "#ECEFF1", "#FBE9E7", "#EDE7F6"]
        def color_for(name: str) -> str:
            if not name: return "transparent"
            return palette[abs(hash(name)) % len(palette)]
        weekdays = ["L", "M", "X", "J", "V", "S", "D"]
        html = "<style>.cal td{padding:6px 8px;border:1px solid #ddd;vertical-align:top;width:14%;} .cal th{padding:6px 8px;border:1px solid #ddd;background:#fafafa;} .tag{display:block;margin-top:4px;padding:2px 4px;border-radius:4px;font-size:11px;}</style>"
        html += "<table class='cal' style='border-collapse:collapse;width:100%'>"
        html += "<thead><tr>" + "".join(f"<th>{d}</th>" for d in weekdays) + "</tr></thead><tbody>"
        for week in weeks:
            html += "<tr>"
            for day in week:
                if day == 0:
                    html += "<td></td>"
                else:
                    d = _dt.date(y, m, day)
                    iso = d.isoformat()
                    name = plan.get(iso, "")
                    bg = color_for(name)
                    tag = f"<span class='tag' style='background:{bg}'>{name}</span>" if name else "<span class='tag' style='opacity:0.4'>Libre</span>"
                    html += f"<td><div><strong>{day}</strong></div>{tag}</td>"
            html += "</tr>"
        html += "</tbody></table>"
        assigned_names = set()
        for week in weeks:
            for day in week:
                if day != 0:
                    iso_key = _dt.date(y, m, day).isoformat()
                    val = plan.get(iso_key)
                    if val: assigned_names.add(val)
        if assigned_names:
            html += "<div style='margin-top:8px'><strong>Leyenda:</strong> " + " ".join(f"<span class='tag' style='background:{color_for(n)}'>{n}</span>" for n in sorted(assigned_names)) + "</div>"
        st.markdown(html, unsafe_allow_html=True)

    # ---------- Copiar plan de un mes a otro (por día de la semana) ----------
    with st.expander("Copiar plan de un mes a otro (por día de la semana)", expanded=False):
        import datetime as _dt
        import calendar as _cal
        from collections import Counter, defaultdict
        src_month = st.date_input("Mes origen", value=date.today(), key="copy_src_month")
        dst_month = st.date_input("Mes destino", value=date.today(), key="copy_dst_month")
        wipe = st.checkbox("Borrar asignaciones del mes destino antes de copiar", value=False, key="copy_wipe_dst")
        def _iter_month_dates(y, m):
            days = _cal.monthrange(y, m)[1]
            for d in range(1, days+1):
                yield _dt.date(y, m, d)
        if st.button("Copiar plan (por día de la semana)", use_container_width=True):
            plan_current = _get_plan(user)
            weekday_map = {}
            freq = defaultdict(Counter)
            for d in _iter_month_dates(src_month.year, src_month.month):
                val = plan_current.get(d.isoformat())
                if val: freq[d.weekday()][val] += 1
            for wd, counter in freq.items():
                if counter: weekday_map[wd] = counter.most_common(1)[0][0]
            if not weekday_map:
                st.info("En el mes origen no hay asignaciones para derivar el patrón.")
            else:
                if wipe:
                    for d in _iter_month_dates(dst_month.year, dst_month.month):
                        iso = d.isoformat()
                        if iso in plan_current:
                            _set_plan(user, iso, None)
                    plan_current = _get_plan(user)
                applied = 0
                for d in _iter_month_dates(dst_month.year, dst_month.month):
                    wd = d.weekday()
                    if wd in weekday_map:
                        _set_plan(user, d.isoformat(), weekday_map[wd]); applied += 1
                st.success(f"Copiadas {applied} asignaciones por patrón de día de semana de {src_month.strftime('%Y-%m')} a {dst_month.strftime('%Y-%m')}.")
                st.rerun()

    # ---------- Crear nueva rutina ----------
    with st.expander("Crear nueva rutina", expanded=False):
        exercises = list_all_exercises(user)
        default_rows = [{"exercise": "", "sets": 3, "reps": 10, "weight": 0.0}]
        with st.form("create_routine_form", clear_on_submit=False):
            rt_name = st.text_input("Nombre de la rutina")
            df_items = st.data_editor(
                pd.DataFrame(default_rows),
                num_rows="dynamic",
                use_container_width=True,
                column_config={
                    "exercise": st.column_config.SelectboxColumn("Ejercicio", options=exercises, required=True),
                    "sets": st.column_config.NumberColumn("Series", min_value=1, max_value=20, step=1),
                    "reps": st.column_config.NumberColumn("Reps", min_value=1, max_value=100, step=1),
                    "weight": st.column_config.NumberColumn("Peso (kg)", min_value=0.0, step=0.5),
                },
            )
            save_btn = st.form_submit_button("Guardar rutina")
            if save_btn:
                rows = []
                for _, row in df_items.dropna(subset=["exercise"]).iterrows():
                    ex = str(row.get("exercise") or "").strip()
                    if not ex: continue
                    rows.append({"exercise": ex, "sets": int(row.get("sets") or 1), "reps": int(row.get("reps") or 10), "weight": float(row.get("weight") or 0.0)})
                if not rt_name:
                    st.warning("Ponle un nombre a la rutina.")
                elif not rows:
                    st.warning("Añade al menos un ejercicio.")
                else:
                    try:
                        add_routine(user, rt_name, rows)
                        st.success(f"Rutina **{rt_name}** guardada.")
                        st.rerun()
                    except Exception as e:
                        st.error(str(e))

    # ---------- Registro de rutinas ----------
    with st.expander("Registro de rutinas", expanded=False):
        routines = list_routines(user)
        st.write(f"Total: **{len(routines)}**")
        if routines:
            names = [r["name"] for r in routines]
            sel = st.selectbox("Ver rutina", names, key="registry_view_sel")
            if sel:
                r = next(r for r in routines if r["name"] == sel)
                st.table(pd.DataFrame(r.get("items", [])))
                colx, coly = st.columns([2,1])
                with colx:
                    new_name = st.text_input("Renombrar a:", value=sel, key="registry_rename_to")
                    if st.button("Renombrar", use_container_width=True):
                        if new_name and new_name != sel:
                            try:
                                rename_routine(user, sel, new_name)
                                st.success(f"Renombrada a **{new_name}**."); st.rerun()
                            except Exception as e:
                                st.error(str(e))
                with coly:
                    if st.button("Eliminar rutina", use_container_width=True):
                        delete_routine(user, sel); st.success(f"Eliminada **{sel}**."); st.rerun()
        else:
            st.info("No hay rutinas todavía. Crea una en el formulario de arriba.")

    # ---------- Auto-configurador de rutinas (chat) ----------
    with st.expander("Auto-configurador de rutinas (chat)", expanded=False):
        import re as _re
        import datetime as _dt
        if "autoplan_msgs" not in st.session_state: st.session_state["autoplan_msgs"] = []
        if "autoplan_step" not in st.session_state: st.session_state["autoplan_step"] = 0
        if "autoplan_data" not in st.session_state: st.session_state["autoplan_data"] = {"goal": None, "days": None, "level": None, "equipment": None, "session": None}
        def _say(role, text): st.session_state["autoplan_msgs"].append({"role": role, "text": text})
        if not st.session_state["autoplan_msgs"]:
            _say("assistant", "¡Hola! Soy tu asistente para crear un plan. Empecemos 🤖💪")
            _say("assistant", "1) ¿Cuál es tu objetivo principal? (fuerza / hipertrofia / pérdida de grasa)")
        for m in st.session_state["autoplan_msgs"]:
            with st.chat_message("assistant" if m["role"] == "assistant" else "user"): st.write(m["text"])

        def _parse_goal(text):
            t = text.lower()
            if "fuerza" in t: return "fuerza"
            if "hiper" in t or "masa" in t or "musculo" in t: return "hipertrofia"
            if "defin" in t or "grasa" in t or "peso" in t: return "perdida_grasa"
            return None

        def _parse_days(text):
            # robusto: acepta "4", "4 dias", "cuatro", etc.
            t = str(text).strip().lower()
            palabras = {"uno":1,"dos":2,"tres":3,"cuatro":4,"cinco":5,"seis":6,"siete":7}
            for k,v in palabras.items():
                if k in t: return v
            m = _re.search(r"(\d+)", t)
            if m:
                try:
                    n = int(m.group(1))
                    if 1 <= n <= 7: return n
                except Exception: pass
            return None

        def _parse_level(text):
            t = text.lower()
            if "princi" in t: return "principiante"
            if "inter" in t: return "intermedio"
            if "avan" in t: return "avanzado"
            return None

        def _parse_equip(text):
            t = text.lower()
            if "gim" in t or "gimnasio" in t: return ["gimnasio"]
            opts = []
            if "manc" in t or "pesas" in t or "barra" in t: opts.append("pesas")
            if "maqui" in t: opts.append("maquinas")
            if "casa" in t or "sin" in t: opts.append("casa")
            return opts or None

        def _parse_session(text):
            t = str(text).strip().lower()
            m = _re.search(r"(\d+)", t)
            if m:
                try:
                    n = int(m.group(1))
                    if 20 <= n <= 120: return n
                except Exception: pass
            return None

        user_in = st.chat_input("Escribe tu respuesta...")
        if user_in:
            _say("user", user_in.strip())
            step = st.session_state["autoplan_step"]
            data = st.session_state["autoplan_data"]
            if step == 0:
                g = _parse_goal(user_in)
                if g:
                    data["goal"] = g
                    st.session_state["autoplan_step"] = 1
                    _say("assistant", "2) ¿Cuántos días por semana quieres entrenar? (1-7)")
                else:
                    _say("assistant", "No te entendí del todo. Dime fuerza / hipertrofia / pérdida de grasa.")
            elif step == 1:
                d = _parse_days(user_in)
                if d:
                    data["days"] = d; _say("assistant", f"Perfecto: {d} días/semana.")
                    st.session_state["autoplan_step"] = 2
                    _say("assistant", "3) ¿Tu nivel? (principiante / intermedio / avanzado)")
                else:
                    _say("assistant", "Dime un número entre 1 y 7 😉")
            elif step == 2:
                lv = _parse_level(user_in)
                if lv:
                    data["level"] = lv
                    st.session_state["autoplan_step"] = 3
                    _say("assistant", "4) ¿Qué equipamiento tienes? (gimnasio, pesas, máquinas, casa)")
                else:
                    _say("assistant", "Responde: principiante / intermedio / avanzado.")
            elif step == 3:
                eq = _parse_equip(user_in)
                if eq:
                    data["equipment"] = eq
                    st.session_state["autoplan_step"] = 4
                    _say("assistant", "5) ¿Cuántos minutos quieres entrenar por sesión? (20-120)")
                else:
                    _say("assistant", "Indica algo como: gimnasio / pesas / máquinas / casa (puede ser varias).")
            elif step == 4:
                mins = _parse_session(user_in)
                if mins:
                    data["session"] = mins; _say("assistant", f"Perfecto: {mins} minutos por sesión.")
                    st.session_state["autoplan_step"] = 5
                    _say("assistant", "¡Perfecto! Con esto puedo proponerte un programa. Pulsa **Generar plan** abajo 👇")
                else:
                    _say("assistant", "Pon un número entre 20 y 120.")
            else:
                _say("assistant", "Si quieres cambiar algo, pulsa **Reiniciar chat**.")
            st.rerun()

        with st.expander("Ajustes manuales (opcional)", expanded=False):
            data = st.session_state["autoplan_data"]
            data["goal"] = st.selectbox("Objetivo", ["fuerza", "hipertrofia", "perdida_grasa"], index=(["fuerza","hipertrofia","perdida_grasa"].index(data["goal"]) if data["goal"] else 1))
            data["days"] = st.slider("Días/semana", 1, 7, value=data["days"] or 3)
            data["level"] = st.selectbox("Nivel", ["principiante","intermedio","avanzado"], index=(["principiante","intermedio","avanzado"].index(data["level"]) if data["level"] else 0))
            data["equipment"] = st.multiselect("Equipamiento", ["gimnasio","pesas","maquinas","casa"], default=data["equipment"] or ["gimnasio"])
            data["session"] = st.slider("Minutos por sesión", 20, 120, value=data["session"] or 60)

        colg1, colg2, colg3 = st.columns(3)
        with colg1:
            if st.button("Generar plan", use_container_width=True):
                st.session_state["autoplan_step"] = 5
        with colg2:
            if st.button("Reiniciar chat", use_container_width=True):
                st.session_state["autoplan_msgs"] = []
                st.session_state["autoplan_step"] = 0
                st.session_state["autoplan_data"] = {"goal": None, "days": None, "level": None, "equipment": None, "session": None}
                st.rerun()
        with colg3:
            st.caption("Ajusta valores arriba si el chat no te entendió.")

        # ===== Generación + REFINO interactivo =====
        if st.session_state["autoplan_step"] >= 5:
            all_ex = list_all_exercises(user)
            if not all_ex:
                st.warning("No tienes ejercicios en tu catálogo. Ve a **📚 Ejercicios** y añade tu lista primero."); st.stop()

            days = st.session_state["autoplan_data"]["days"] or 3
            if days == 1: split = ["Full Body A"]
            elif days == 2: split = ["Upper", "Lower"]
            elif days == 3: split = ["Full Body A", "Full Body B", "Full Body C"]
            elif days == 4: split = ["Upper A", "Lower A", "Upper B", "Lower B"]
            elif days == 5: split = ["Push", "Pull", "Legs", "Upper", "Lower"]
            else: split = ["Push A", "Pull A", "Legs A", "Push B", "Pull B", "Legs B"]

            def _rep_range(goal):
                if goal == "fuerza": return (3,5)
                if goal == "perdida_grasa": return (12,15)
                return (8,12)

            def _routine_template(name, picks):
                lo, hi = _rep_range(st.session_state["autoplan_data"]["goal"] or "hipertrofia")
                items = [{"exercise": ex, "sets": 3, "reps": (lo+hi)//2, "weight": 0.0} for ex in picks]
                return {"name": name, "items": items}

            def _pick_exercises(pool, keywords):
                pool_lower = {p.lower(): p for p in pool}
                selected = []
                for kw in keywords:
                    cand = next((pool_lower[k] for k in pool_lower if kw.lower() in k), None)
                    if cand and cand not in selected: selected.append(cand)
                for ex in pool:
                    if len(selected) >= 8: break
                    if ex not in selected: selected.append(ex)
                return selected[:8]

            GROUPS = {
                "pecho": ["pecho","banca","press banca","aperturas","inclinado"],
                "espalda": ["espalda","remo","jalón","dominada","pull"],
                "piernas": ["pierna","piernas","sentadilla","zancada","prensa","gemelo","femoral","cuad","peso muerto"],
                "hombros": ["hombro","hombros","militar","elevaciones laterales","arnold"],
                "brazos": ["bíceps","biceps","tríceps","triceps","curl","extensión"],
                "core": ["core","abdominal","abdomen","plancha","lumbar"],
            }
            def _classify_groups(name: str):
                n = name.lower(); gset=set()
                for g,kws in GROUPS.items():
                    if any(kw in n for kw in kws): gset.add(g)
                return gset
            def _alt_from_pool(orig_ex: str, pool: list[str]):
                target = _classify_groups(orig_ex)
                for ex in pool:
                    if ex == orig_ex: continue
                    if _classify_groups(ex) & target: return ex
                for ex in pool:
                    if ex != orig_ex: return ex
                return orig_ex

            if "autoplan_program" not in st.session_state or not st.session_state["autoplan_program"]:
                routines_built = []
                for name in split:
                    if "Upper" in name or name in ["Push","Pull"]:
                        kws = ["press banca","remo","press militar","domin","jalón","curl","tríceps"]
                    elif "Lower" in name or "Legs" in name:
                        kws = ["sentadilla","peso muerto","zancada","prensa","gemelo","hip thrust"]
                    else:
                        kws = ["sentadilla","press banca","remo","peso muerto","press militar","domin"]
                    picks = _pick_exercises(all_ex, kws)
                    routines_built.append(_routine_template(name, picks))
                st.session_state["autoplan_program"] = routines_built

            program = st.session_state["autoplan_program"]
            st.success("Programa actual:")
            for r in program:
                st.markdown(f"**{r['name']}**"); st.table(pd.DataFrame(r["items"]))

            st.markdown("**Dime cosas como:**  
• *no quiero sentadilla* → alternativa  
• *sustituye jalón por dominadas*  
• *más piernas* / *menos pecho*")

            def _apply_feedback(text: str, program: list[dict]):
                t = text.strip().lower()
                changed = False

                # ---------- SCOPE: 'solo en <rutina>' o 'en <rutina>' ----------
                scope = None
                import re as _sre
                scope_match = _sre.search(r"(?:solo\s+en|en)\s+(?:el\s+d[ií]a\s+)?(.+)$", t)
                if scope_match:
                    scope_name = scope_match.group(1).strip()
                    # elegir rutina cuyo nombre contenga scope_name (case-insensitive)
                    names = [r["name"] for r in program]
                    scope = next((nm for nm in names if scope_name in nm.lower()), None)
                    # quita la clausula '... en <rutina>' del texto para facilitar el resto de parseos
                    t = t[:scope_match.start()].strip()

                def _target_routines():
                    if scope:
                        return [r for r in program if r["name"].lower() == scope]
                    return program

                # ---------- 1) Sustitución explícita: "sustituye X por Y" ----------
                m = _sre.search(r"sustit(uir|uye|uya)\s+(.+?)\s+por\s+(.+)", t)
                if m:
                    old = m.group(2).strip()
                    new = m.group(3).strip()
                    new_real = next((e for e in all_ex if new in e.lower()), None) or _alt_from_pool(old, all_ex)
                    for r in _target_routines():
                        for it in r["items"]:
                            if old in it["exercise"].lower():
                                it["exercise"] = new_real
                                changed = True
                    msg_scope = f" en **{scope}**" if scope else ""
                    return changed, f"Sustituido **{old}** por **{new_real}**{msg_scope}."

                # ---------- 2) 'no quiero X' / 'quitar X' ----------
                m = _sre.search(r"(no quiero|quitar|quita|elimina|eliminar)\s+(.+)", t)
                if m:
                    bad = m.group(2).strip()
                    alt = _alt_from_pool(bad, all_ex)
                    for r in _target_routines():
                        for it in r["items"]:
                            if bad in it["exercise"].lower():
                                it["exercise"] = alt
                                changed = True
                    msg_scope = f" en **{scope}**" if scope else ""
                    return changed, f"Reemplazado **{bad}** por **{alt}**{msg_scope}."

                # ---------- 3) Más/Menos grupo ----------
                m = _sre.search(r"(más|mas|menos)\s+(pecho|espalda|piernas|hombros|brazos|core)", t)
                if m:
                    op = m.group(1); grp = m.group(2)
                    cand = [e for e in all_ex if grp in _classify_groups(e)]
                    if not cand:
                        return False, f"No encontré ejercicios de **{grp}** en tu lista."
                    # cuenta por rutina restringida por scope
                    counts = []
                    targets = _target_routines()
                    for r in targets:
                        c = sum(1 for it in r["items"] if grp in _classify_groups(it["exercise"]))
                        counts.append(c)
                    import pandas as _pd
                    if op.startswith("mas") or op.startswith("más"):
                        idx_rel = int(_pd.Series(counts).idxmin())
                        r = targets[idx_rel]
                        ex = next((e for e in cand if e not in [it["exercise"] for it in r["items"]]), cand[0])
                        r["items"].append({"exercise": ex, "sets": 3, "reps": 10, "weight": 0.0})
                        changed = True
                        return changed, f"Añadido **{ex}** (énfasis **{grp}**) en **{r['name']}**."
                    else:
                        idx_rel = int(_pd.Series(counts).idxmax())
                        r = targets[idx_rel]
                        pos = None
                        for i, it in enumerate(r["items"]):
                            if grp in _classify_groups(it["exercise"]):
                                pos = i; break
                        if pos is not None:
                            removed = r["items"].pop(pos)
                            changed = True
                            return changed, f"Quitado **{removed['exercise']}** (menos **{grp}**) de **{r['name']}**."
                        else:
                            return False, f"No había ejercicios de **{grp}** para quitar."

                # ---------- 4) Ajuste de SERIES / REPS en grupo o ejercicio ----------
                # Ejemplos: "sube a 4 series en pecho", "pon a 6 reps en sentadilla"
                m = _sre.search(r"(sube|baja|pon|ajusta|cambia)\s+a\s+(\d+)\s+(series|reps?|repeticiones)\s+en\s+(pecho|espalda|piernas|hombros|brazos|core)", t)
                if m:
                    val = int(m.group(2))
                    field = m.group(3)
                    grp = m.group(4)
                    # normaliza campo
                    field_key = "sets" if "series" in field else "reps"
                    count_mod = 0
                    for r in _target_routines():
                        for it in r["items"]:
                            if grp in _classify_groups(it["exercise"]):
                                it[field_key] = val
                                count_mod += 1
                    if count_mod == 0:
                        return False, f"No hay ejercicios de **{grp}** para ajustar."
                    msg_scope = f" en **{scope}**" if scope else ""
                    return True, f"Ajustadas **{count_mod}** entradas ({field_key}={val}) para **{grp}**{msg_scope}."

                # Ajuste por ejercicio concreto
                m = _sre.search(r"(sube|baja|pon|ajusta|cambia)\s+a\s+(\d+)\s+(series|reps?|repeticiones)\s+en\s+(.+)", t)
                if m:
                    val = int(m.group(2))
                    field = m.group(3)
                    ex_kw = m.group(4).strip()
                    field_key = "sets" if "series" in field else "reps"
                    count_mod = 0
                    for r in _target_routines():
                        for it in r["items"]:
                            if ex_kw in it["exercise"].lower():
                                it[field_key] = val
                                count_mod += 1
                    if count_mod == 0:
                        return False, f"No encontré **{ex_kw}** para ajustar."
                    msg_scope = f" en **{scope}**" if scope else ""
                    return True, f"Ajustadas **{count_mod}** entradas ({field_key}={val}) para **{ex_kw}**{msg_scope}."

                return False, "No entendí el ajuste. Prueba con *'no quiero sentadilla'*, *'sustituye jalón por dominadas'*, *'más piernas'*, o *'sube a 4 series en pecho'* (puedes añadir *'solo en Lower A'*).

            fb = st.chat_input("Dime qué quieres cambiar…")
            if fb:
                changed,msg = _apply_feedback(fb, program)
                if changed:
                    st.session_state["autoplan_program"] = program; st.success(msg); st.rerun()
                else:
                    st.info(msg)

            # Exportar / Guardar / Asignar del programa actual
            from io import BytesIO
            try:
                from reportlab.lib.pagesizes import A4
                from reportlab.lib import colors
                from reportlab.lib.styles import getSampleStyleSheet
                from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, PageBreak
            except Exception as _e:
                st.error("Falta 'reportlab'. Instálala con: pip install reportlab"); A4=None

            def _build_program_pdf(title: str, routines_list: list) -> bytes:
                buf = BytesIO()
                doc = SimpleDocTemplate(buf, pagesize=A4, leftMargin=36, rightMargin=36, topMargin=36, bottomMargin=36)
                styles = getSampleStyleSheet(); story=[Paragraph(title, styles["Title"]), Spacer(1,12)]
                for idx, r in enumerate(routines_list):
                    story.append(Paragraph(r["name"], styles["Heading2"]))
                    data = [["Ejercicio","Series","Reps","Peso (kg)"]]
                    for it in r["items"]:
                        data.append([it["exercise"], str(it["sets"]), str(it["reps"]), str(it["weight"])])
                    table = Table(data, repeatRows=1)
                    table.setStyle(TableStyle([("BACKGROUND",(0,0),(-1,0),colors.lightgrey),("GRID",(0,0),(-1,-1),0.5,colors.grey),("ALIGN",(1,1),(-1,-1),"CENTER"),("VALIGN",(0,0),(-1,-1),"MIDDLE"),("FONTSIZE",(0,0),(-1,-1),10),("BOTTOMPADDING",(0,0),(-1,0),6),("TOPPADDING",(0,0),(-1,0),6)]))
                    story.append(table)
                    if idx < len(routines_list)-1: story.append(PageBreak())
                doc.build(story); pdf=buf.getvalue(); buf.close(); return pdf

            colp1, colp2, colp3 = st.columns([1,1,2])
            with colp1:
                pdf_bytes = _build_program_pdf("Programa de entrenamiento", program) if A4 else None
                if pdf_bytes:
                    st.download_button("Descargar programa PDF", data=pdf_bytes, file_name="programa_entrenamiento.pdf", mime="application/pdf", use_container_width=True)
            with colp2:
                if st.button("Guardar rutinas en registro", use_container_width=True):
                    existing = [r["name"] for r in list_routines(user)]
                    saved=0
                    for r in program:
                        name=r["name"]; base=name; k=1
                        while name in existing:
                            k+=1; name=f"{base} ({k})"
                        try:
                            add_routine(user, name, r["items"]); existing.append(name); saved+=1
                        except Exception as e:
                            st.warning(f"No se pudo guardar {name}: {e}")
                    st.success(f"Guardadas {saved} rutinas."); st.rerun()
            with colp3:
                st.subheader("Asignar al calendario")
                start = st.date_input("Fecha de inicio", value=date.today(), key="autoplan_start")
                weeks = st.number_input("Semanas", min_value=1, max_value=12, value=4, step=1, key="autoplan_weeks")
                weekdays = ["Lunes","Martes","Miércoles","Jueves","Viernes","Sábado","Domingo"]
                chosen = st.multiselect("Días de entrenamiento", options=list(range(7)), default=list(range(min(len(program), 6))), format_func=lambda i: weekdays[i], key="autoplan_weekdays")
                if st.button("Aplicar al calendario", use_container_width=True, disabled=len(chosen)==0):
                    order=list(range(len(program))); idx=0; count=0
                    for w in range(int(weeks)):
                        for wd in sorted(chosen):
                            d = start + _dt.timedelta(days=(wd - start.weekday()) % 7) + _dt.timedelta(weeks=w)
                            routine = program[order[idx % len(order)]]["name"]
                            _set_plan(user, d.isoformat(), routine); idx+=1; count+=1
                    st.success(f"Asignadas {count} sesiones al calendario."); st.rerun()

    # ---------- Exportar rutina (PDF) ----------
    with st.expander("Exportar rutina (PDF)", expanded=False):
        from io import BytesIO
        try:
            from reportlab.lib.pagesizes import A4
            from reportlab.lib import colors
            from reportlab.lib.styles import getSampleStyleSheet
            from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
        except Exception as _e:
            st.error("Falta la dependencia 'reportlab'. Instálala con: pip install reportlab"); st.stop()

        def _build_pdf(title: str, items: list, fecha: str | None = None) -> bytes:
            buf = BytesIO()
            doc = SimpleDocTemplate(buf, pagesize=A4, leftMargin=36, rightMargin=36, topMargin=36, bottomMargin=36)
            styles = getSampleStyleSheet(); story=[]
            story.append(Paragraph(title, styles["Title"]))
            if fecha: story.append(Paragraph(f"Fecha: {fecha}", styles["Normal"]))
            story.append(Spacer(1, 12))
            data = [["Ejercicio","Series","Reps","Peso (kg)"]]
            for it in items:
                data.append([str(it.get("exercise","")), str(it.get("sets","")), str(it.get("reps","")), str(it.get("weight",""))])
            table = Table(data, repeatRows=1)
            table.setStyle(TableStyle([("BACKGROUND",(0,0),(-1,0),colors.lightgrey),("GRID",(0,0),(-1,-1),0.5,colors.grey),("ALIGN",(1,1),(-1,-1),"CENTER"),("VALIGN",(0,0),(-1,-1),"MIDDLE"),("FONTSIZE",(0,0),(-1,-1),10),("BOTTOMPADDING",(0,0),(-1,0),6),("TOPPADDING",(0,0),(-1,0),6)]))
            story.append(table); doc.build(story); pdf=buf.getvalue(); buf.close(); return pdf

        mode = st.radio("¿Qué quieres exportar?", ["Rutina de hoy", "Elegir rutina"], horizontal=True)
        if mode == "Rutina de hoy":
            today = date.today(); today_iso = today.isoformat()
            rt_name = _get_plan(user).get(today_iso)
            if not rt_name: st.info("Hoy no hay rutina asignada.")
            else:
                r = next((rr for rr in list_routines(user) if rr["name"] == rt_name), None)
                if not r: st.warning("La rutina asignada ya no existe.")
                else:
                    pdf_bytes = _build_pdf(f"Rutina de hoy — {rt_name}", r.get("items", []), fecha=today_iso)
                    st.download_button("Descargar PDF", data=pdf_bytes, file_name=f"rutina_{today_iso}_{rt_name}.pdf", mime="application/pdf", use_container_width=True)
        else:
            routines = list_routines(user)
            if not routines: st.info("No tienes rutinas creadas aún.")
            else:
                names = [r["name"] for r in routines]
                sel = st.selectbox("Rutina a exportar", names, key="export_sel_routine")
                if sel:
                    r = next(rr for rr in routines if rr["name"] == sel)
                    pdf_bytes = _build_pdf(f"Rutina — {sel}", r.get("items", []))
                    st.download_button("Descargar PDF", data=pdf_bytes, file_name=f"rutina_{sel}.pdf", mime="application/pdf", use_container_width=True)
