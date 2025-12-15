
def _asegurar_dias_minimos(datos_usuario: dict):
    dias = datos_usuario.get("dias")
    if not dias or not isinstance(dias, (list, tuple)) or len(dias) == 0:
        # Si el usuario no seleccionó nada, por defecto 3 días
        datos_usuario["dias"] = ["Lunes", "Miércoles", "Viernes"]

import matplotlib.pyplot as plt
from datetime import date
from pathlib import Path

import pandas as pd
import streamlit as st
from dotenv import load_dotenv
import os
load_dotenv()
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
# Query params (Streamlit >= 1.30)
params = st.query_params
_u = params.get("user")
_t = params.get("reset_token")
if _u and _t:
    if isinstance(_u, list): _u = _u[0]
    if isinstance(_t, list): _t = _t[0]
    st.session_state["_pending_user"] = _u
    st.session_state["_pending_token"] = _t
import os, time, time

from app.email_utils import send_email
from app.datastore import set_password, set_account_email, set_recovery_email, get_emails_for_user, set_profile, get_password_reset, create_password_reset, clear_password_reset

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

def pagina_progreso():
    """Progreso de ejercicios basado en los entrenamientos guardados (usuarios_data/<user>.json).
    Muestra evolución por sesión (día) y detalle por sets, con métricas y exportación.
    """
    import pandas as pd
    import streamlit as st
    from datetime import date as _date

    st.subheader("📈 Progreso de ejercicios")

    user = st.session_state.get("user")
    if not user:
        st.info("Inicia sesión para ver tu progreso.")
        return

    entrenos = list_training(user)
    if not entrenos:
        st.info("Aún no tienes entrenamientos guardados. Registra alguna serie para ver el progreso aquí.")
        return

    df = pd.DataFrame(entrenos)
    # Normalizar columnas esperadas
    for col in ["date", "exercise", "set", "reps", "weight"]:
        if col not in df.columns:
            df[col] = None

    df["exercise"] = df["exercise"].astype(str).str.strip()
    df["date_dt"] = pd.to_datetime(df["date"], errors="coerce")
    df = df.dropna(subset=["date_dt"])
    df["Fecha"] = df["date_dt"].dt.date
    df["Set"] = pd.to_numeric(df["set"], errors="coerce").fillna(0).astype(int)
    df["Reps"] = pd.to_numeric(df["reps"], errors="coerce").fillna(0).astype(int)
    df["Peso"] = pd.to_numeric(df["weight"], errors="coerce").fillna(0.0).astype(float)

    df = df[(df["exercise"] != "") & (df["exercise"].notna())].copy()
    if df.empty:
        st.info("No se encontraron registros válidos de entrenamientos.")
        return

    # Selector de ejercicio (prioriza los que tienen datos)
    exercises_with_data = sorted(df["exercise"].unique().tolist())
    all_exs = list_all_exercises(user)
    # Mezclar: primero con datos, luego el resto (por si quieres ver un ejercicio sin datos)
    merged = exercises_with_data + [e for e in all_exs if e not in set(exercises_with_data)]

    left, right = st.columns([2, 1])
    with left:
        selected = st.selectbox("Ejercicio", merged, index=0, key="prog_exercise")
    with right:
        mode = st.radio("Vista", ["Por sesión (día)", "Por set"], horizontal=True, key="prog_mode")

    # Meta + imagen
    meta = get_exercise_meta(user, selected) if selected else {"grupo": "Otro", "imagen": None}
    st.caption(f"**Grupo:** {meta.get('grupo','Otro')}")

    if meta.get("imagen"):
        try:
            st.image(meta["imagen"], caption=selected, use_container_width=True)
        except Exception:
            pass

    df_ex = df[df["exercise"] == selected].copy()
    if df_ex.empty:
        st.info("Este ejercicio aún no tiene series registradas.")
        return

    # Rango de fechas
    min_d = df_ex["Fecha"].min()
    max_d = df_ex["Fecha"].max()

    c1, c2, c3 = st.columns([1, 1, 1])
    with c1:
        d_from = st.date_input("Desde", value=min_d, min_value=min_d, max_value=max_d, key="prog_from")
    with c2:
        d_to = st.date_input("Hasta", value=max_d, min_value=min_d, max_value=max_d, key="prog_to")
    with c3:
        smooth = st.checkbox("Suavizado (media móvil)", value=False, key="prog_smooth")

    if d_from > d_to:
        d_from, d_to = d_to, d_from

    df_ex = df_ex[(df_ex["Fecha"] >= d_from) & (df_ex["Fecha"] <= d_to)].copy()
    if df_ex.empty:
        st.info("No hay registros en ese rango de fechas.")
        return

    # 1RM estimado (Epley)
    df_ex["1RM"] = df_ex.apply(lambda r: float(r["Peso"]) * (1.0 + float(r["Reps"]) / 30.0) if r["Peso"] > 0 and r["Reps"] > 0 else 0.0, axis=1)
    df_ex["Volumen"] = df_ex["Peso"] * df_ex["Reps"]

    # Métricas rápidas
    pr_w_row = df_ex.loc[df_ex["Peso"].idxmax()] if not df_ex.empty else None
    pr_1rm_row = df_ex.loc[df_ex["1RM"].idxmax()] if not df_ex.empty else None
    last_day = df_ex["Fecha"].max()

    total_sessions = df_ex["Fecha"].nunique()
    total_sets = len(df_ex)
    total_reps = int(df_ex["Reps"].sum())
    total_volume = float(df_ex["Volumen"].sum())

    m1, m2, m3, m4 = st.columns(4)
    m1.metric("Sesiones", total_sessions)
    m2.metric("Series", total_sets)
    m3.metric("Reps totales", total_reps)
    m4.metric("Volumen total", f"{total_volume:,.0f} kg·rep".replace(",", "."))

    pr1, pr2, pr3 = st.columns(3)
    if pr_w_row is not None:
        pr1.metric("PR Peso", f"{float(pr_w_row['Peso']):g} kg", help=f"{int(pr_w_row['Reps'])} reps — {pr_w_row['Fecha']}")
    if pr_1rm_row is not None:
        pr2.metric("Mejor 1RM est.", f"{float(pr_1rm_row['1RM']):.1f} kg", help=f"{float(pr_1rm_row['Peso']):g} kg x {int(pr_1rm_row['Reps'])} — {pr_1rm_row['Fecha']}")
    pr3.metric("Última sesión", str(last_day))

    st.markdown("---")

    if mode == "Por sesión (día)":
        # Agregación por día
        def _best_set(g):
            # Devuelve set con mayor 1RM; si empate, mayor peso; si empate, mayor reps
            gg = g.sort_values(["1RM", "Peso", "Reps"], ascending=[False, False, False])
            return gg.iloc[0]

        agg = df_ex.groupby("Fecha", as_index=False).apply(_best_set)
        # groupby.apply crea índice compuesto; normalizar
        if isinstance(agg.index, pd.MultiIndex):
            agg = agg.reset_index(drop=True)

        day = df_ex.groupby("Fecha", as_index=False).agg(
            Series=("Peso", "count"),
            Reps_tot=("Reps", "sum"),
            Volumen=("Volumen", "sum"),
        )
        series = agg[["Fecha", "Peso", "Reps", "1RM"]].merge(day, on="Fecha", how="left").sort_values("Fecha")
        series = series.rename(columns={"Peso": "Mejor peso", "Reps": "Reps en mejor set", "1RM": "Mejor 1RM est."})

        # Suavizado
        win = 3
        if smooth and len(series) >= win:
            for col in ["Mejor peso", "Mejor 1RM est.", "Volumen"]:
                if col in series.columns:
                    series[col + " (MM)"] = series[col].rolling(win, min_periods=1).mean()

        # Gráficas
        st.markdown("### Evolución")
        g1, g2 = st.columns(2)
        with g1:
            st.write("**Mejor peso por sesión**")
            plot_df = series.set_index("Fecha")
            cols = ["Mejor peso"] + (["Mejor peso (MM)"] if "Mejor peso (MM)" in plot_df.columns else [])
            st.line_chart(plot_df[cols])
        with g2:
            st.write("**Mejor 1RM estimado por sesión**")
            plot_df = series.set_index("Fecha")
            cols = ["Mejor 1RM est."] + (["Mejor 1RM est. (MM)"] if "Mejor 1RM est. (MM)" in plot_df.columns else [])
            st.line_chart(plot_df[cols])

        st.write("**Volumen por sesión**")
        plot_df = series.set_index("Fecha")
        cols = ["Volumen"] + (["Volumen (MM)"] if "Volumen (MM)" in plot_df.columns else [])
        st.bar_chart(plot_df[cols])

        st.markdown("### Sesiones (detalle)")
        st.dataframe(
            series[["Fecha", "Mejor peso", "Reps en mejor set", "Mejor 1RM est.", "Series", "Reps_tot", "Volumen"]],
            use_container_width=True,
            hide_index=True,
        )

        # Export
        csv1 = series.to_csv(index=False).encode("utf-8")
        st.download_button("⬇️ Descargar progreso (CSV)", data=csv1, file_name=f"progreso_{selected}.csv", mime="text/csv")

    else:
        # Por set
        st.markdown("### Sets (filtrados)")
        show_cols = ["Fecha", "Set", "Reps", "Peso", "1RM", "Volumen"]
        st.dataframe(df_ex[show_cols].sort_values(["Fecha", "Set"]), use_container_width=True, hide_index=True)

        st.markdown("### Evolución por set")
        # Preparar serie temporal: mejor peso por día (simple), y nube de sets por día (tabla + chart)
        per_day = df_ex.groupby("Fecha", as_index=False).agg(Max_peso=("Peso","max"), Max_1RM=("1RM","max"), Volumen=("Volumen","sum")).sort_values("Fecha")
        st.write("**Máximo peso por día (a partir de sets)**")
        st.line_chart(per_day.set_index("Fecha")[["Max_peso"]])

        st.write("**Máximo 1RM estimado por día (a partir de sets)**")
        st.line_chart(per_day.set_index("Fecha")[["Max_1RM"]])

        csv2 = df_ex[show_cols].sort_values(["Fecha","Set"]).to_csv(index=False).encode("utf-8")
        st.download_button("⬇️ Descargar sets (CSV)", data=csv2, file_name=f"sets_{selected}.csv", mime="text/csv")



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
            "👤 Perfil",
        ],
        index=0 if "user" not in st.session_state else 1,
    )

if page == "🔐 Login / Registro":
    st.title("Acceso")

    col1, col2 = st.columns(2)

    with col1:
        st.subheader("Iniciar sesión")
        u = st.text_input("Usuario")
        p = st.text_input("Contraseña", type="password")

        # Reseteo por token desde URL (?user=&reset_token=)
        if st.session_state.get("_pending_user") and st.session_state.get("_pending_token"):
            u_tok = st.session_state.pop("_pending_user")
            tk = st.session_state.pop("_pending_token")
            data_tok = get_password_reset(u_tok)
            if data_tok and data_tok.get("token") == tk and data_tok.get("expires_at", 0) >= int(time.time()):
                st.success(f"Token válido para **{u_tok}**. Establece nueva contraseña:")
                with st.form("reset_from_link"):
                    p1 = st.text_input("Nueva contraseña", type="password")
                    p2 = st.text_input("Repite la nueva contraseña", type="password")
                    done = st.form_submit_button("Guardar")
                if done:
                    if p1 and p1 == p2:
                        set_password(u_tok, p1)
                        clear_password_reset(u_tok)
                        st.success("Contraseña actualizada. Ya puedes iniciar sesión.")
                    else:
                        st.error("Las contraseñas no coinciden.")
            else:
                st.error("El enlace/código de recuperación no es válido o ha caducado.")

        with st.expander("Olvidé mi contraseña"):
            rec_id = st.text_input("Tu usuario o email de recuperación", key="forgot_id")
            if st.button("Enviar enlace de recuperación", key="forgot_btn"):
                target_user = None
                if rec_id:
                    try:
                        _ = load_user(rec_id)  # como usuario
                        target_user = rec_id
                    except Exception:
                        pass
                if not target_user:
                    import glob, json
                    from pathlib import Path as _P
                    for pth in glob.glob(str((_P(".")/"usuarios_data"/"*.json").resolve())):
                        try:
                            d = json.load(open(pth, "r", encoding="utf-8"))
                            if d.get("recovery_email") == rec_id or d.get("email") == rec_id:
                                target_user = _P(pth).stem
                                break
                        except Exception:
                            pass
                if not target_user:
                    st.info("Si existe, te llegará un correo con instrucciones.")
                else:
                    token = __import__("secrets").token_urlsafe(24)
                    create_password_reset(target_user, token, ttl_seconds=3600)
                    base_url = os.getenv("APP_BASE_URL", "")
                    link = f"{base_url}?user={target_user}&reset_token={token}" if base_url else f"(Configura APP_BASE_URL) token: {token}"
                    acc, rec = get_emails_for_user(target_user)
                    to_email = rec or acc
                    ok, msg = send_email(to_email, "Recuperación de contraseña",
                        f"<p>Hola {target_user},</p><p>Enlace para restablecer (1h): <a href='{link}'>{link}</a></p><p>Código: <b>{token}</b></p>",
                        text=f"Enlace: {link}\nCódigo: {token}")
                    if ok:
                        st.info("Si existe, te llegará un correo con instrucciones.")
                    else:
                        st.warning("No se pudo enviar email. Usa este código en la app: " + token)

        if st.button("Iniciar sesión"):
            if not u or not p:
                st.warning("Completa usuario y contraseña.")
            else:
                if authenticate(u, p):
                    st.session_state["user"] = u
                    st.success("Sesión iniciada.")
                    st.rerun()
                else:
                    st.error("Usuario o contraseña incorrectos.")

    with col2:
        st.subheader("Crear cuenta")
        with st.form("register_form"):
            u2 = st.text_input("Nuevo usuario", key="reg_user")
            e2 = st.text_input("Email", key="reg_email")
            p2 = st.text_input("Nueva contraseña", type="password", key="reg_pass")
            submit_reg = st.form_submit_button("Registrarme")
        if submit_reg:
            if not u2 or not e2 or not p2:
                st.warning("Completa usuario, email y contraseña.")
            else:
                created = False
                try:
                    created = register_user(u2, p2, e2)
                except TypeError:
                    created = register_user(u2, p2)
                    data = load_user(u2)
                    data["email"] = e2
                    data["recovery_email"] = e2
                    save_user(u2, data)
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

    tabs = st.tabs(["Listado", "📈 Progreso de ejercicios"])

    with tabs[0]:
        st.subheader("Listado de ejercicios")

        # --- Carga de datos ---
        ejercicios = list_all_exercises(user)
        entrenos = list_training(user)

        # Stats por ejercicio
        stats = {ex: {"sesiones": 0, "series": 0, "reps_totales": 0, "ultimo": None, "ultimo_peso": None, "ultimas_reps": None,
                      "mejor_peso": 0.0, "mejor_1rm": 0.0} for ex in ejercicios}

        # Para contar sesiones por fecha
        fechas_por_ex = {ex: set() for ex in ejercicios}

        for r in entrenos:
            ex = r.get("exercise")
            if ex not in stats:
                # ejercicios detectados (por si aparecen en entrenos pero no están en base/custom)
                ejercicios.append(ex)
                stats[ex] = {"sesiones": 0, "series": 0, "reps_totales": 0, "ultimo": None, "ultimo_peso": None, "ultimas_reps": None,
                             "mejor_peso": 0.0, "mejor_1rm": 0.0}
                fechas_por_ex[ex] = set()

            d = str(r.get("date") or "")
            reps = int(r.get("reps") or 0)
            peso = float(r.get("weight") or 0.0)

            fechas_por_ex[ex].add(d)
            stats[ex]["series"] += 1
            stats[ex]["reps_totales"] += reps

            # último (por fecha ISO)
            if d and (stats[ex]["ultimo"] is None or d > stats[ex]["ultimo"]):
                stats[ex]["ultimo"] = d
                stats[ex]["ultimo_peso"] = peso
                stats[ex]["ultimas_reps"] = reps

            # mejor peso
            if peso > (stats[ex]["mejor_peso"] or 0.0):
                stats[ex]["mejor_peso"] = peso

            # 1RM estimado (Epley)
            if peso > 0 and reps > 0:
                one_rm = peso * (1.0 + reps / 30.0)
                if one_rm > (stats[ex]["mejor_1rm"] or 0.0):
                    stats[ex]["mejor_1rm"] = one_rm

        for ex in stats:
            stats[ex]["sesiones"] = len(fechas_por_ex.get(ex, set()))

        # Meta (grupo/imagen)
        filas = []
        for ex in ejercicios:
            meta = get_exercise_meta(user, ex)
            filas.append({
                "Ejercicio": ex,
                "Grupo": meta.get("grupo", "Otro"),
                "Sesiones": stats.get(ex, {}).get("sesiones", 0),
                "Series": stats.get(ex, {}).get("series", 0),
                "Reps totales": stats.get(ex, {}).get("reps_totales", 0),
                "Último": stats.get(ex, {}).get("ultimo", None),
                "Último peso": stats.get(ex, {}).get("ultimo_peso", None),
                "Últimas reps": stats.get(ex, {}).get("ultimas_reps", None),
                "Mejor peso": stats.get(ex, {}).get("mejor_peso", 0.0),
                "Mejor 1RM": round(stats.get(ex, {}).get("mejor_1rm", 0.0), 2),
                "Tiene imagen": bool(meta.get("imagen")),
            })

        df = pd.DataFrame(filas)

        # --- Filtros ---
        c1, c2, c3 = st.columns([2, 1, 1])
        with c1:
            q = st.text_input("Buscar ejercicio", value="", placeholder="Ej: Press banca, Sentadilla...", key="ex_search")
        with c2:
            grupo_sel = st.selectbox("Grupo", ["Todos"] + GRUPOS, index=0, key="ex_group_filter")
        with c3:
            solo_con_entrenos = st.checkbox("Solo con entrenos", value=False, key="ex_only_with_trainings")

        df_f = df.copy()
        if q:
            df_f = df_f[df_f["Ejercicio"].str.contains(q, case=False, na=False)]
        if grupo_sel != "Todos":
            df_f = df_f[df_f["Grupo"] == grupo_sel]
        if solo_con_entrenos:
            df_f = df_f[df_f["Series"] > 0]

        st.dataframe(df_f.sort_values(["Grupo", "Ejercicio"]), use_container_width=True, hide_index=True)

        # --- Detalle editable ---
        opciones = df_f["Ejercicio"].tolist()
        if not opciones:
            st.info("No hay ejercicios con esos filtros.")
        else:
            # Mantener selección estable
            default_idx = 0
            prev = st.session_state.get("ex_selected")
            if prev in opciones:
                default_idx = opciones.index(prev)

            seleccionado = st.selectbox("Ver detalle de ejercicio", opciones, index=default_idx, key="ex_detail_select")
            st.session_state["ex_selected"] = seleccionado

            meta = get_exercise_meta(user, seleccionado)
            grupo_actual = meta.get("grupo", "Otro")
            if grupo_actual not in GRUPOS:
                grupo_actual = "Otro"
            imagen_rel = meta.get("imagen")

            st.markdown("---")
            st.markdown(f"## {seleccionado}")

            colA, colB = st.columns([1, 1])

            # ---- Columna A: editar grupo ----
            with colA:
                st.markdown("### Datos")
                key_safe = "".join(ch if ch.isalnum() else "_" for ch in seleccionado)

                grupo_nuevo = st.selectbox(
                    "Grupo muscular",
                    GRUPOS,
                    index=GRUPOS.index(grupo_actual),
                    key=f"ex_group_edit_{key_safe}",
                )

                if st.button("💾 Guardar grupo", key=f"ex_save_group_{key_safe}"):
                    save_exercise_meta(user, seleccionado, grupo_nuevo, imagen_rel)
                    st.success("Grupo actualizado.")
                    st.rerun()

                st.markdown("### Estadísticas")
                st.write({
                    "sesiones": stats.get(seleccionado, {}).get("sesiones", 0),
                    "series": stats.get(seleccionado, {}).get("series", 0),
                    "reps_totales": stats.get(seleccionado, {}).get("reps_totales", 0),
                    "ultimo": stats.get(seleccionado, {}).get("ultimo", None),
                    "ultimo_peso": stats.get(seleccionado, {}).get("ultimo_peso", None),
                    "ultimas_reps": stats.get(seleccionado, {}).get("ultimas_reps", None),
                    "mejor_peso": stats.get(seleccionado, {}).get("mejor_peso", 0.0),
                    "mejor_1rm": round(stats.get(seleccionado, {}).get("mejor_1rm", 0.0), 2),
                })

            # ---- Columna B: imagen ----
            with colB:
                st.markdown("### Imagen")
                img_path = None
                if imagen_rel:
                    # imagen_rel suele ser ruta relativa (ej: exercise_images/user/xxx.png)
                    if os.path.exists(imagen_rel):
                        img_path = imagen_rel

                if img_path:
                    st.image(img_path, use_container_width=True)
                    if st.button("🧹 Quitar imagen", key=f"ex_remove_img_{key_safe}"):
                        save_exercise_meta(user, seleccionado, grupo_actual, None)
                        st.success("Imagen eliminada.")
                        st.rerun()
                else:
                    st.info("Este ejercicio no tiene imagen todavía.")

                up = st.file_uploader(
                    "Subir/actualizar imagen (png/jpg/jpeg/webp)",
                    type=["png", "jpg", "jpeg", "webp"],
                    key=f"ex_img_upload_{key_safe}",
                )
                if up is not None:
                    rel = store_exercise_image(user, up.name, up.getvalue())
                    # Guardamos meta con el grupo que esté seleccionado ahora mismo
                    save_exercise_meta(user, seleccionado, grupo_nuevo, rel)
                    st.success("Imagen guardada.")
                    st.rerun()

    with tabs[-1]:
        pagina_progreso()


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

        import os, json
        import datetime as _dt
        import pandas as pd
        import streamlit as st
        from app.ai_generator import call_gpt, build_prompt
        from app.rules_fallback import generate_fallback
        from app.pdf_export import rutina_a_pdf_bytes
        from app.routines import add_routine, list_routines

        user = st.session_state.get("user", "default")
        st.info("Genera tu plan con IA, se guarda en memoria y se muestra como tablas por día (tipo PDF).")

        # ---------- Formulario de entrada ----------
        with st.form("ia_form"):

            col1, col2 = st.columns(2)

            with col1:
                nivel = st.selectbox("Nivel", ["principiante","intermedio","avanzado"], index=1)
                dias = st.number_input("Días/semana", min_value=1, max_value=6, value=4, step=1)
                duracion = st.slider("Duración (min)", min_value=30, max_value=120, value=60, step=5)
                disponibilidad = st.multiselect(
                    "Disponibilidad (elige días)",
                    ["Lunes","Martes","Miércoles","Jueves","Viernes","Sábado","Domingo"],
                    default=["Lunes","Martes","Jueves","Viernes"]
                )
                progresion_pref = st.selectbox("Progresión preferida", ["doble_progresion","lineal","RPE_autorregulada"], index=0)
                volumen_tol = st.select_slider("Tolerancia a volumen", options=["baja","media","alta"], value="media")
                semanas_ciclo = st.number_input("Semanas del ciclo", min_value=4, max_value=12, value=6)

            with col2:
                objetivo = st.selectbox("Objetivo", ["fuerza","hipertrofia","resistencia","mixto"], index=0)

                # --- Material (con preset) ---
                material_preset = st.radio("Material (preset)", ["Todo", "Personalizado"], index=0, horizontal=True)
                material_personalizado = []
                if material_preset == "Personalizado":
                    material_personalizado = st.multiselect(
                        "Material disponible",
                        ["barra","mancuernas","poleas","máquinas","banco","rack","prensa","dominadas","anillas","gomas","kettlebells","discos"]
                    )
                material = (["todo"] if material_preset == "Todo" else material_personalizado)

                limitaciones = st.text_input("Lesiones/limitaciones (opcional)", placeholder="Hombro, rodilla, ...")
                superseries_ok = st.checkbox("Permitir superseries", value=True)
                deload_semana_pref = st.number_input("Deload preferido (semana)", min_value=0, max_value=12, value=5, help="0 = sin preferencia")
                unidades = st.selectbox("Unidades", ["kg","lb"], index=0)
                idioma = st.selectbox("Idioma", ["es","en"], index=0)

            # ---------- Experiencia y PR ----------
            st.markdown("#### Experiencia y PR recientes")
            c1, c2, c3 = st.columns(3)
            with c1:
                exp_banca = st.text_input("Banca (experiencia)", value="2 años")
                pr_banca = st.number_input("Banca 1x3 (kg)", value=80, step=2)
            with c2:
                exp_sentadilla = st.text_input("Sentadilla (experiencia)", value="1 año")
                pr_senta = st.number_input("Sentadilla 1x3 (kg)", value=110, step=2)
            with c3:
                exp_muerto = st.text_input("Peso muerto (experiencia)", value="1 año")
                pr_muerto = st.number_input("Muerto 1x3 (kg)", value=130, step=2)

            enfasis = st.multiselect("Énfasis accesorios", ["espalda alta","gluteo","triceps","biceps","core"], default=["espalda alta","core"])
            evitar_txt = st.text_input("Evitar movimientos (separar por comas)", value="press militar de pie pesado")
            calentamiento = st.selectbox("Calentamiento", ["breve","medio","largo"], index=0)

            agrupacion = st.selectbox(
                "Estructura de grupos por día",
                ["Varios grupos principales por día", "Un solo grupo principal por día"],
                index=0
            )

            detalles_ia = st.text_area(
                "Detalles adicionales para la IA (opcional)",
                placeholder="Ej.: evitar press militar por hombro • añadir 1 día de cardio + core • priorizar glúteo...",
                height=120
            )

            submitted = st.form_submit_button("Generar rutina")
        # ---------- Función de render tipo PDF ----------
        def render_rutina_tabular(rutina: dict):
            st.subheader("Plan (vista tipo PDF)")
            dias = rutina.get("dias", [])
            if not dias:
                st.info("No hay días en la rutina.")
                return
            # Construcción de tabs segura
            tab_labels = [d.get("nombre", f"Día {i+1}") for i, d in enumerate(dias)]
            tab_labels.append("📈 Progreso de ejercicios")
            tabs = st.tabs(tab_labels)

            for i, dia in enumerate(dias):
                with tabs[i]:
                    rows = [{
                        "Ejercicio": ej.get("nombre",""),
                        "Series": ej.get("series",""),
                        "Reps": ej.get("reps",""),
                        "Descanso": ej.get("descanso",""),
                        "Intensidad": ej.get("intensidad","") or ""
                    } for ej in dia.get("ejercicios", [])]
                    import pandas as _pd
                    st.table(_pd.DataFrame(rows, columns=["Ejercicio","Series","Reps","Descanso","Intensidad"]))
                    if dia.get("notas"):
                        st.caption("Notas: " + dia["notas"])

    # Pestaña adicional: Progreso de ejercicios
            prog = rutina.get("progresion", {})
            st.markdown("### Progresión")
            st.write(
                f"- **Principales:** {prog.get('principales','')}\n"
                f"- **Accesorios:** {prog.get('accesorios','')}\n"
                f"- **Deload (semana):** {prog.get('deload_semana','')}"
            )

        # ---------- Llamada a IA / Fallback ----------
        if submitted:
            if "datos_usuario" not in st.session_state:
                st.session_state["datos_usuario"] = {}
            ia_detalles_value = " " + (ia_notas if "ia_notas" in locals() else st.session_state.get("ia_notas", ""))
            datos_usuario = {
                "ia_detalles": ia_detalles_value,

                "nivel": nivel,
                "dias": int(dias),
                "duracion": int(duracion),
                "objetivo": objetivo,
                "material": material,
                "lesiones": limitaciones.strip(),
                "disponibilidad": disponibilidad,
                "progresion_preferida": progresion_pref,
                "volumen_tolerancia": volumen_tol,
                "semanas_ciclo": int(semanas_ciclo),
                "superseries_ok": bool(superseries_ok),
                "deload_preferido_semana": int(deload_semana_pref),
                "unidades": unidades,
                "idioma": idioma,
                "experiencia": {"banca": exp_banca, "sentadilla": exp_sentadilla, "peso_muerto": exp_muerto,
        "agrupacion": agrupacion
    ,
        "comentarios": (detalles_ia or "").strip()
    },
                "pr_recientes": {"banca_1x3": pr_banca, "sentadilla_1x3": pr_senta, "muerto_1x3": pr_muerto, "unidad": unidades},
                "enfasis_accesorios": enfasis,
                "evitar": [s.strip() for s in evitar_txt.split(",") if s.strip()],
                "calentamiento": calentamiento
            }
            api_key_ok = bool(os.getenv("OPENAI_API_KEY"))
            if api_key_ok:
                with st.spinner("Generando con IA..."):
                    result = call_gpt(datos_usuario)
                    if result.get("ok"):
                        st.session_state["rutina_ia"] = result["data"]
                        # Guardar prompt/system para depurar
                        try:
                            st.session_state["ia_prompt"] = result.get("prompt") or build_prompt(datos_usuario)
                        except Exception:
                            st.session_state["ia_prompt"] = None
                        st.session_state["ia_system"] = result.get("system")
                    else:
                        _asegurar_dias_minimos(datos_usuario)
                        st.session_state["rutina_ia"] = generate_fallback(datos_usuario)
                        # Guardar prompt/system aunque haya fallo
                        try:
                            st.session_state["ia_prompt"] = result.get("prompt") or build_prompt(datos_usuario)
                        except Exception:
                            st.session_state["ia_prompt"] = build_prompt(datos_usuario)
                        st.session_state["ia_system"] = result.get("system")
                        err = result.get("error","Error desconocido")
                        if not os.getenv("OPENAI_API_KEY"):
                            st.warning("Se usó el plan de respaldo. Falta OPENAI_API_KEY en el entorno.")
                        else:
                            st.warning("Se usó el plan de respaldo por fallo al generar con OpenAI.")
                        st.error(f"Fallo al generar con OpenAI: {err}")
            else:
                st.session_state["rutina_ia"] = generate_fallback(datos_usuario)
                try:
                    st.session_state["ia_prompt"] = build_prompt(datos_usuario)
                except Exception:
                    st.session_state["ia_prompt"] = None
                st.session_state["ia_system"] = None
                st.warning("Se usó el plan de respaldo. Falta OPENAI_API_KEY en el entorno.")
                st.error(f"Fallo al generar con OpenAI: {st.session_state.get('ia_error', 'error desconocido')}")
                st.session_state["rutina_meta"] = {"nivel": nivel, "objetivo": objetivo, "duracion": int(duracion)}

        # ---------- Mostrar desde sesión ----------
        rutina_view = st.session_state.get("rutina_ia")
        if rutina_view:
            render_rutina_tabular(rutina_view)

            pdf_bytes = rutina_a_pdf_bytes(rutina_view)
            st.download_button("📄 Descargar PDF", data=pdf_bytes, file_name="rutina.pdf", mime="application/pdf")
            st.download_button("📥 Descargar JSON", data=json.dumps(rutina_view, ensure_ascii=False, indent=2),
                               file_name="rutina.json", mime="application/json")

            st.markdown("---")
            st.subheader("📅 Nombra, asigna días y programa semanas")

            dias_semana = ["Lunes","Martes","Miércoles","Jueves","Viernes","Sábado","Domingo"]
            with st.form("planificacion_form", clear_on_submit=False):
                schedule = []
                for i, dia in enumerate(rutina_view.get("dias", [])):
                    st.write(f"**{i+1}. {dia.get('nombre','Día')}**")
                    c1, c2 = st.columns(2)
                    weekday = c1.selectbox("Día de la semana", dias_semana, key=f"weekday_ai_{i}")
                    custom_name = c2.text_input("Nombre de la rutina", value=dia.get("nombre","Día"), key=f"dname_ai_{i}")
                    schedule.append({
                        "day_index": i,
                        "weekday": dias_semana.index(weekday),
                        "name": custom_name
                    })
                cA, cB, cC = st.columns(3)
                start_date = cA.date_input("Inicio", value=_dt.date.today(), key="plan_start")
                weeks = cB.number_input("Semanas", min_value=1, max_value=52, value=4, step=1, key="plan_weeks")
                guardar = cC.form_submit_button("💾 Guardar y programar")

            if guardar:
                existing = [r["name"] for r in list_routines(user)]
                def _ensure_unique(name, existing_names):
                    base, n, cand = name, 1, name
                    while cand in existing_names:
                        n += 1
                        cand = f"{base} ({n})"
                    existing_names.append(cand)
                    return cand

                created = []
                for s in schedule:
                    d = rutina_view["dias"][s["day_index"]]
                    rname = _ensure_unique(s["name"].strip() or d.get("nombre","Día"), existing)
                    items = []
                    for ej in d.get("ejercicios", []):
                        reps = ej.get("reps","10")
                        try:
                            reps_val = int(str(reps).replace("–","-").split("-")[-1].strip())
                        except:
                            reps_val = 10
                        items.append({"exercise": ej.get("nombre",""), "sets": int(ej.get("series",3)), "reps": reps_val, "weight": 0.0})
                    add_routine(user, rname, items)
                    created.append((s["weekday"], rname))

                try:
                    base_mon = start_date - _dt.timedelta(days=start_date.weekday())
                    for w in range(int(weeks)):
                        for wd, rname in created:
                            d = base_mon + _dt.timedelta(weeks=w, days=int(wd))
                            _set_plan(user, d.isoformat(), rname)
                    st.success("Rutinas guardadas y programadas ✅")
                except NameError:
                    st.warning("No se encontró _set_plan; se guardaron las rutinas, pero no se pudo programar en calendario.")
                except Exception as e:
                    st.error(f"Error al programar: {e}")

            # 🧠 Mostrar prompt utilizado para la IA
            if st.session_state.get("ia_prompt"):
                with st.expander("🧠 Ver prompt construido con tus parámetros", expanded=False):
                    st.code(st.session_state.get("ia_prompt"))

            with st.expander("Ver JSON (avanzado)", expanded=False):
                st.json(rutina_view)

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



elif page == "👤 Perfil":
    require_auth()
    st.title("👤 Mi perfil")
    user = st.session_state["user"]
    data = load_user(user)
    profile = data.get("profile", {})
    with st.form("perfil_form"):
        c1, c2 = st.columns(2)
        with c1:
            first_name = st.text_input("Nombre", value=profile.get("first_name",""))
            birthdate = st.text_input("Fecha de nacimiento (YYYY-MM-DD)", value=profile.get("birthdate",""))
        with c2:
            last_name = st.text_input("Apellidos", value=profile.get("last_name",""))
            gender = st.selectbox("Género", ["", "Masculino", "Femenino", "No binario", "Prefiero no decir"], index=0 if profile.get("gender","") not in ["","Masculino","Femenino","No binario","Prefiero no decir"] else ["","Masculino","Femenino","No binario","Prefiero no decir"].index(profile.get("gender","")))
        notes = st.text_area("Notas", value=profile.get("notes",""))
        save_btn = st.form_submit_button("Guardar perfil")
    if save_btn:
        set_profile(user, {"first_name": first_name, "last_name": last_name, "birthdate": birthdate, "gender": gender, "notes": notes})
        st.success("Perfil actualizado.")

    st.subheader("Cambiar contraseña")
    with st.form("pass_form"):
        cur = st.text_input("Contraseña actual", type="password")
        p1  = st.text_input("Nueva contraseña", type="password")
        p2  = st.text_input("Repite nueva contraseña", type="password")
        sbt = st.form_submit_button("Actualizar contraseña")
    if sbt:
        if not authenticate(user, cur):
            st.error("La contraseña actual no es correcta.")
        elif not p1 or p1 != p2:
            st.error("Las nuevas contraseñas no coinciden.")
        else:
            set_password(user, p1)
            st.success("Contraseña actualizada.")

    st.subheader("Emails")
    acc, rec = get_emails_for_user(user)
    with st.form("email_form"):
        new_acc = st.text_input("Email de cuenta", value=acc or "")
        new_rec = st.text_input("Email de recuperación", value=rec or acc or "")
        sbt2 = st.form_submit_button("Guardar emails")
    if sbt2:
        if new_acc: set_account_email(user, new_acc)
        if new_rec: set_recovery_email(user, new_rec)
        st.success("Emails actualizados.")

# === Nueva sección integrada: Progreso de ejercicios ===


    st.subheader("📈 Progreso de ejercicios")
    st.caption("Visualiza la evolución de peso y repeticiones por ejercicio.")

    @st.cache_data(show_spinner=False)
    def discover_data_sources(base_dir: str):
        dbs, csvs = [], []
        for root, _, files in os.walk(base_dir):
            for f in files:
                low = f.lower()
                if low.endswith((".db", ".sqlite", ".sqlite3")):
                    dbs.append(os.path.join(root, f))
                if low.endswith(".csv"):
                    csvs.append(os.path.join(root, f))
        return dbs, csvs

    def _fetch_exercises_from_sqlite(db_path: str) -> Optional[List[str]]:
        try:
            con = sqlite3.connect(db_path)
            cur = con.cursor()
            cur.execute("SELECT name FROM sqlite_master WHERE type='table'")
            tables = [r[0] for r in cur.fetchall()]
            candidates = [t for t in tables if any(k in t.lower() for k in ["serie","series","sets","entren","workout","training","registro"])]
            exercises = set()
            for t in (candidates or tables):
                cur.execute(f"PRAGMA table_info('{t}')")
                cols = [c[1].lower() for c in cur.fetchall()]
                has_ex = any(c in cols for c in ["ejercicio","exercise","nombre_ejercicio"])
                has_weight = any(c in cols for c in ["peso","weight","kg"])
                has_reps = any(c in cols for c in ["reps","repeticiones","rep"])
                if has_ex and (has_weight or has_reps):
                    ex_col = "ejercicio" if "ejercicio" in cols else ("exercise" if "exercise" in cols else "nombre_ejercicio")
                    cur.execute(f"SELECT DISTINCT {ex_col} FROM '{t}' WHERE {ex_col} IS NOT NULL AND TRIM({ex_col})<>'' LIMIT 5000")
                    exercises.update([r[0] for r in cur.fetchall()])
            con.close()
            return sorted(e for e in exercises if e)
        except Exception:
            return None

    def _fetch_progress_from_sqlite(db_path: str, exercise: str) -> Optional[pd.DataFrame]:
        try:
            con = sqlite3.connect(db_path)
            cur = con.cursor()
            cur.execute("SELECT name FROM sqlite_master WHERE type='table'")
            tables = [r[0] for r in cur.fetchall()]
            frames = []
            for t in tables:
                cur.execute(f"PRAGMA table_info('{t}')")
                cols_info = cur.fetchall()
                cols = [c[1] for c in cols_info]
                lcols = [c.lower() for c in cols]
                def pick(*opts):
                    for o in opts:
                        if o in lcols:
                            return cols[lcols.index(o)]
                    return None
                col_ex = pick("ejercicio","exercise","nombre_ejercicio")
                col_date = pick("fecha","date","created_at","day","session_date")
                col_weight = pick("peso","weight","kg")
                col_reps = pick("reps","repeticiones","rep","repetition")
                if not col_ex or not (col_weight or col_reps):
                    continue
                select_cols = [col_ex]
                if col_date: select_cols.append(col_date)
                if col_weight: select_cols.append(col_weight)
                if col_reps: select_cols.append(col_reps)
                try:
                    df = pd.read_sql_query(f"SELECT {', '.join(select_cols)} FROM '{t}' WHERE {col_ex} = ?", con, params=[exercise])
                except Exception:
                    continue
                if df.empty:
                    continue
                df.rename(columns={
                    col_ex: "Ejercicio",
                    col_date: "Fecha" if col_date else None,
                    col_weight: "Peso",
                    col_reps: "Reps",
                }, inplace=True)
                if "Fecha" in df.columns:
                    for fmt in ("%Y-%m-%d","%Y/%m/%d","%d/%m/%Y","%d-%m-%Y","%Y-%m-%d %H:%M:%S","%Y/%m/%d %H:%M:%S"):
                        try:
                            df["Fecha"] = pd.to_datetime(df["Fecha"], format=fmt, errors="ignore")
                        except Exception:
                            pass
                    df["Fecha"] = pd.to_datetime(df["Fecha"], errors="coerce")
                else:
                    df["Fecha"] = pd.NaT
                if "Peso" in df.columns:
                    df["Peso"] = pd.to_numeric(df["Peso"], errors="coerce")
                else:
                    df["Peso"] = pd.NA
                if "Reps" in df.columns:
                    df["Reps"] = pd.to_numeric(df["Reps"], errors="coerce")
                else:
                    df["Reps"] = pd.NA
                frames.append(df[["Fecha","Peso","Reps"]])
            con.close()
            if not frames:
                return None
            out = pd.concat(frames, ignore_index=True)
            out = out.dropna(how="all", subset=["Fecha","Peso","Reps"])
            if out["Fecha"].notna().any():
                out = out.sort_values("Fecha")
            else:
                out = out.reset_index(drop=True)
            return out
        except Exception:
            return None

    def _fetch_from_csvs(csv_paths: List[str]) -> List[str]:
        exs = set()
        for p in csv_paths:
            try:
                df = pd.read_csv(p)
            except Exception:
                try:
                    df = pd.read_csv(p, sep=";")
                except Exception:
                    continue
            lcols = [c.lower() for c in df.columns]
            def pick(*opts):
                for o in opts:
                    if o in lcols:
                        return df.columns[lcols.index(o)]
                return None
            col_ex = pick("ejercicio","exercise","nombre_ejercicio")
            if col_ex is not None:
                exs.update(df[col_ex].dropna().astype(str).str.strip().unique().tolist())
        return sorted(e for e in exs if e)

    def _progress_from_csvs(csv_paths: List[str], exercise: str) -> Optional[pd.DataFrame]:
        frames = []
        for p in csv_paths:
            try:
                df = pd.read_csv(p)
            except Exception:
                try:
                    df = pd.read_csv(p, sep=";")
                except Exception:
                    continue
            lcols = [c.lower() for c in df.columns]
            def pick(*opts):
                for o in opts:
                    if o in lcols:
                        return df.columns[lcols.index(o)]
                return None
            col_ex = pick("ejercicio","exercise","nombre_ejercicio")
            if col_ex is None:
                continue
            sub = df[df[col_ex].astype(str).str.strip() == exercise].copy()
            if sub.empty:
                continue
            col_date = pick("fecha","date","created_at","day","session_date")
            col_weight = pick("peso","weight","kg")
            col_reps = pick("reps","repeticiones","rep","repetition")
            sub.rename(columns={
                col_date: "Fecha" if col_date else None,
                col_weight: "Peso",
                col_reps: "Reps",
            }, inplace=True)
            if "Fecha" in sub.columns:
                for fmt in ("%Y-%m-%d","%Y/%m/%d","%d/%m/%Y","%d-%m-%Y","%Y-%m-%d %H:%M:%S","%Y/%m/%d %H:%M:%S"):
                    try:
                        sub["Fecha"] = pd.to_datetime(sub["Fecha"], format=fmt, errors="ignore")
                    except Exception:
                        pass
                sub["Fecha"] = pd.to_datetime(sub["Fecha"], errors="coerce")
            else:
                sub["Fecha"] = pd.NaT
            if "Peso" in sub.columns:
                sub["Peso"] = pd.to_numeric(sub["Peso"], errors="coerce")
            else:
                sub["Peso"] = pd.NA
            if "Reps" in sub.columns:
                sub["Reps"] = pd.to_numeric(sub["Reps"], errors="coerce")
            else:
                sub["Reps"] = pd.NA
            frames.append(sub[["Fecha","Peso","Reps"]])
        if not frames:
            return None
        out = pd.concat(frames, ignore_index=True)
        out = out.dropna(how="all", subset=["Fecha","Peso","Reps"])
        if out["Fecha"].notna().any():
            out = out.sort_values("Fecha")
        else:
            out = out.reset_index(drop=True)
        return out

    base_dir = os.path.dirname(__file__)
    dbs, csvs = discover_data_sources(os.path.abspath(os.path.join(base_dir, "..")))

    detected_exercises = set()
    for db in dbs:
        exs = _fetch_exercises_from_sqlite(db)
        if exs:
            detected_exercises.update(exs)
    if not detected_exercises:
        detected_exercises.update(_fetch_from_csvs(csvs))

    if detected_exercises:
        ejercicio = st.selectbox("Elige un ejercicio", sorted(detected_exercises))
    else:
        st.info("No se detectaron ejercicios automáticamente. Puedes escribir uno manualmente.")
        ejercicio = st.text_input("Nombre del ejercicio")

    if ejercicio:
        df = None
        src = ""
        for db in dbs:
            df = _fetch_progress_from_sqlite(db, ejercicio)
            if df is not None and not df.empty:
                src = f"SQLite: {os.path.basename(db)}"
                break
        if (df is None or df.empty) and csvs:
            df = _progress_from_csvs(csvs, ejercicio)
            src = "CSV"
        if df is not None and not df.empty:
            st.success(f"Datos encontrados desde {src}.")
            col1, col2, col3, col4 = st.columns(4)
            if df["Peso"].notna().any() and df["Reps"].notna().any():
                df["1RM"] = df.apply(lambda r: r["Peso"] * (1 + (r["Reps"]/30)) if pd.notna(r["Peso"]) and pd.notna(r["Reps"]) else pd.NA, axis=1)
                best_1rm = df["1RM"].max(skipna=True)
                col1.metric("Mejor 1RM estimada", f"{best_1rm:.1f} kg" if isinstance(best_1rm, (int,float)) else "—")
            else:
                col1.metric("Mejor 1RM estimada", "—")
            max_peso = df["Peso"].max(skipna=True) if "Peso" in df.columns else None
            col2.metric("Máx. peso", f"{max_peso:.1f} kg" if isinstance(max_peso, (int,float)) else "—")
            if df["Fecha"].notna().any():
                first = df["Fecha"].min(); last = df["Fecha"].max()
                col3.metric("Rango de fechas", f"{first.date()} → {last.date()}")
            else:
                col3.metric("Rango de fechas", "—")
            col4.metric("Registros", f"{df.shape[0]}")

            st.subheader("Tendencia de Peso")
            if df["Fecha"].notna().any():
                st.line_chart(df.set_index("Fecha")[["Peso"]])
            else:
                st.line_chart(df[["Peso"]])

            st.subheader("Tendencia de Reps")
            if df["Fecha"].notna().any():
                st.line_chart(df.set_index("Fecha")[["Reps"]])
            else:
                st.line_chart(df[["Reps"]])

            with st.expander("Ver tabla de datos"):
                st.dataframe(df)
        else:
            st.warning("No se encontraron datos de progresión. Agrega registros con columnas de ejercicio, peso, repeticiones y opcionalmente fecha.")