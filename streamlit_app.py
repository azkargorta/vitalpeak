def _asegurar_dias_minimos(datos_usuario: dict):
    dias = datos_usuario.get("dias")
    if not dias or not isinstance(dias, (list, tuple)) or len(dias) == 0:
        # Si el usuario no seleccionó nada, por defecto 3 días
        datos_usuario["dias"] = ["Lunes", "Miércoles", "Viernes"]

import matplotlib.pyplot as plt
from datetime import date

import pandas as pd
import streamlit as st

# ---- Streamlit compat patch ----
# Some deployments ship a Streamlit build missing streamlit._escape_markdown,
# but internal Streamlit elements (e.g., st.warning/st.info/st.code) may expect it.
# We provide a minimal implementation to avoid AttributeError crashes.
if not hasattr(st, "_escape_markdown"):
    def _escape_markdown(text) -> str:
        s = "" if text is None else str(text)
        # Basic escaping for common markdown special chars.
        for ch in ["\\", "`", "*", "_", "{", "}", "[", "]", "(", ")", "#", "+", "-", ".", "!", "|", ">"]:
            s = s.replace(ch, f"\\{ch}")
        return s
    st._escape_markdown = _escape_markdown  # type: ignore[attr-defined]
# -------------------------------
from dotenv import load_dotenv
import os

# Config (debe ir antes de usar componentes de Streamlit)
st.set_page_config(page_title="VitalPeak", page_icon="VP", layout="wide")

load_dotenv()

from app.ui_theme import apply_theme, render_brand_hero, section_label, render_sidebar_nav, NAV_META, render_mode_switch
from app.templates_ui import render_templates_page
from app.planner_ui import render_planner_page

apply_theme()

# En Streamlit Cloud, secrets → variables de entorno (OpenAI, SMTP, etc.).
try:
    if hasattr(st, "secrets"):
        _secret_keys = (
            "OPENAI_API_KEY",
            "OPENAI_MODEL",
            "OPENAI_BASE_URL",
            "OPENAI_API_BASE",
            "SMTP_HOST",
            "SMTP_PORT",
            "SMTP_USER",
            "SMTP_PASS",
            "SMTP_FROM",
            "APP_BASE_URL",
            "VITALPEAK_SEED",
            "VITALPEAK_ADMIN_USER",
            "VITALPEAK_ADMIN_PASSWORD",
            "VITALPEAK_ADMIN_EMAIL",
        )
        for _k in _secret_keys:
            if _k in st.secrets and str(st.secrets[_k]).strip():
                if _k == "OPENAI_API_KEY" and os.getenv("OPENAI_API_KEY"):
                    continue
                os.environ[_k] = str(st.secrets[_k]).strip()
        # Tabla anidada [smtp]
        try:
            smtp_tbl = st.secrets.get("smtp")
            if smtp_tbl:
                for src, dst in (
                    ("host", "SMTP_HOST"),
                    ("port", "SMTP_PORT"),
                    ("user", "SMTP_USER"),
                    ("pass", "SMTP_PASS"),
                    ("password", "SMTP_PASS"),
                    ("from", "SMTP_FROM"),
                ):
                    if src in smtp_tbl and str(smtp_tbl[src]).strip():
                        os.environ[dst] = str(smtp_tbl[src]).strip()
        except Exception:
            pass
except Exception:
    pass
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

# Crear un usuario DEMO para pruebas (admin/admin) con datos realistas de ~2 meses.
# Se puede desactivar con: VITALPEAK_SEED=0
from app.demo_seed import maybe_seed_admin
maybe_seed_admin()

# Query params (Streamlit >= 1.30)
params = st.query_params
_u = params.get("user")
_t = params.get("reset_token")
if _u and _t:
    if isinstance(_u, list): _u = _u[0]
    if isinstance(_t, list): _t = _t[0]
    st.session_state["_pending_user"] = _u
    st.session_state["_pending_token"] = _t
import os, time

from app.email_utils import send_email
from app.datastore import (
    set_password, set_account_email, set_recovery_email, get_emails_for_user, set_profile,
    get_password_reset, create_password_reset, clear_password_reset, load_user,
)
try:
    from app.datastore import resolve_login_identifier
except ImportError:
    def resolve_login_identifier(identifier: str):
        """Fallback si el deploy aún no tiene la función en datastore."""
        ident = (identifier or "").strip()
        if not ident:
            return None
        return ident if load_user(ident) else None

from app.datastore import (
    register_user, authenticate, load_user, save_user,
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
from app.goals import (
    get_goals, save_goals,
    set_weekly_days_goal, set_target_body_weight,
    set_exercise_goal, remove_exercise_goal,
    weekly_workout_counts, week_range,
)
from app.routines import (
    list_routines, add_routine, delete_routine, rename_routine, apply_routine
)

from app.today_ui import render_today_page

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
            from app.exercises import resolve_exercise_image_path

            p = resolve_exercise_image_path(meta["imagen"])
            if p:
                st.image(str(p), caption=selected, use_container_width=True)
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

def _goto(page_name: str) -> None:
    st.session_state["nav_page"] = page_name
    st.rerun()

NAV_ITEMS = [k for k, _ in NAV_META]

logged_in = bool(st.session_state.get("user"))

with st.sidebar:
    st.markdown("## VitalPeak")
    if logged_in:
        st.markdown(
            f'<div class="vp-nav-user">{st.session_state["user"]}</div>',
            unsafe_allow_html=True,
        )
        st.markdown("---")
        if st.session_state.get("nav_page") not in NAV_ITEMS:
            # Migrar nombres antiguos del menú
            legacy = {
                "Registrar entrenamiento": "Entrenar",
                "Plantillas": "Rutinas",
                "Planificar rutinas": "Rutinas",
                "Ejercicios y progreso": "Progreso",
                "Historial": "Progreso",
                "Objetivos": "Progreso",
                "Peso corporal": "Progreso",
                "Mi cuenta": "Cuenta",
                "Técnica": "Hoy",
            }
            cur = st.session_state.get("nav_page")
            st.session_state["nav_page"] = legacy.get(cur, "Hoy")
            if cur in ("Plantillas",):
                st.session_state["rutinas_tab"] = "Plantillas"
            elif cur in ("Planificar rutinas",):
                st.session_state["rutinas_tab"] = "Planificar"
            elif cur in ("Ejercicios y progreso",):
                st.session_state["progreso_tab"] = "Ejercicios"
            elif cur == "Historial":
                st.session_state["progreso_tab"] = "Historial"
            elif cur == "Objetivos":
                st.session_state["progreso_tab"] = "Objetivos"
            elif cur == "Peso corporal":
                st.session_state["progreso_tab"] = "Peso"
        page = render_sidebar_nav(st.session_state.get("nav_page"))
        st.markdown("---")
        st.markdown('<span class="vp-logout-mark"></span>', unsafe_allow_html=True)
        if st.button("Cerrar sesión", use_container_width=True, key="btn_logout"):
            logout()
    else:
        st.caption("Entra para ver tu plan y registrar series.")
        page = "Entrar"

# ---------- Pantalla de acceso (marca primero) ----------
if not logged_in or page == "Entrar":
    render_brand_hero(
        title="VitalPeak",
        kicker="Gimnasio · Salud · Progreso",
        lead="Tu entrenamiento organizado: qué toca hoy y cómo mejoras.",
        panel_title="Empieza en 30 segundos",
        panel_body="Entra con tu cuenta o crea una. Demo: admin / admin",
    )

    tab_login, tab_reg = st.tabs(["Entrar", "Crear cuenta"])

    with tab_login:
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

        with st.form("login_form"):
            u = st.text_input("Usuario")
            p = st.text_input("Contraseña", type="password")
            submit_login = st.form_submit_button("Entrar", type="primary", use_container_width=True)
        if submit_login:
            if not u or not p:
                st.warning("Completa usuario y contraseña.")
            elif authenticate(u, p):
                st.session_state["user"] = u
                st.session_state["nav_page"] = "Hoy"
                st.rerun()
            else:
                st.error("Usuario o contraseña incorrectos.")

        with st.expander("Olvidé mi contraseña"):
            rec_id = st.text_input("Tu usuario o email de recuperación", key="forgot_id")
            if st.button("Enviar enlace de recuperación", key="forgot_btn"):
                target_user = resolve_login_identifier(rec_id) if rec_id else None
                if not target_user:
                    st.info("Si existe, te llegará un correo con instrucciones.")
                else:
                    payload = create_password_reset(target_user, ttl_seconds=3600)
                    if not payload:
                        st.info("Si existe, te llegará un correo con instrucciones.")
                    else:
                        token = payload["token"]
                        base_url = os.getenv("APP_BASE_URL", "").rstrip("/")
                        link = (
                            f"{base_url}?user={target_user}&reset_token={token}"
                            if base_url
                            else f"(Configura APP_BASE_URL) token: {token}"
                        )
                        emails = get_emails_for_user(target_user)
                        to_email = emails.get("recovery_email") or emails.get("email")
                        if not to_email:
                            st.warning("No hay email de recuperación. Usa este código: " + token)
                        else:
                            ok, msg = send_email(
                                to_email,
                                "Recuperación de contraseña",
                                f"<p>Hola {target_user},</p><p>Enlace para restablecer (1h): <a href='{link}'>{link}</a></p><p>Código: <b>{token}</b></p>",
                                text=f"Enlace: {link}\nCódigo: {token}",
                            )
                            if ok:
                                st.info("Si existe, te llegará un correo con instrucciones.")
                            else:
                                st.warning(
                                    "No se pudo enviar email ("
                                    + msg
                                    + "). Usa este código en la app: "
                                    + token
                                )

    with tab_reg:
        with st.form("register_form"):
            u2 = st.text_input("Nuevo usuario", key="reg_user")
            e2 = st.text_input("Email", key="reg_email")
            p2 = st.text_input("Nueva contraseña", type="password", key="reg_pass")
            submit_reg = st.form_submit_button("Crear cuenta", type="primary", use_container_width=True)
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
                    st.success("Cuenta creada. Ahora inicia sesión.")
                else:
                    st.error("Ese usuario ya existe.")

    st.stop()

# ---------- App autenticada ----------
if page == "Hoy":
    require_auth()
    render_today_page(st.session_state["user"])

elif page == "Rutinas":
    require_auth()
    _rt = ["Plantillas", "Planificar"]
    _cur = st.session_state.get("rutinas_tab", "Plantillas")
    _sub = render_mode_switch(_rt, _cur, key="rutinas_tab")
    if _sub == "Plantillas":
        render_templates_page(embedded=True)
        page = None
    else:
        render_planner_page(st.session_state["user"])
        page = None

elif page == "Progreso":
    require_auth()
    _pt = ["Ejercicios", "Historial", "Objetivos", "Peso"]
    _pmap = {
        "Ejercicios": "Ejercicios y progreso",
        "Historial": "Historial",
        "Objetivos": "Objetivos",
        "Peso": "Peso corporal",
    }
    _curp = st.session_state.get("progreso_tab", "Ejercicios")
    _subp = render_mode_switch(_pt, _curp, key="progreso_tab")
    page = _pmap[_subp]

elif page == "Plantillas":
    require_auth()
    render_templates_page(embedded=True)
    page = None

if page == "Entrenar":
    require_auth()
    from app.train_session_ui import render_train_page
    render_train_page(st.session_state["user"])

elif page == "Ejercicios y progreso":
    require_auth()
    st.title("Ejercicios y progreso")
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
            imagen_rel = meta.get("imagen")

            st.markdown("---")
            from app.exercises_ui import render_exercise_detail

            render_exercise_detail(
                user,
                seleccionado,
                stats.get(seleccionado, {}),
                grupo_actual=grupo_actual,
                imagen_rel=imagen_rel,
            )

    with tabs[-1]:
        pagina_progreso()


elif page == "Historial":
    require_auth()
    st.title("Historial de entrenamientos")
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
                        if sheet_name not in writer.sheets:
                            writer.book.add_worksheet(sheet_name)
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
                            if sheet not in writer.sheets:
                                writer.book.add_worksheet(sheet)
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


elif page == "Objetivos":
    require_auth()
    st.title("Objetivos")
    user = st.session_state["user"]

    goals = get_goals(user)

    st.subheader("✅ Objetivo semanal")
    ws, we = week_range(date.today())
    this_week_done = weekly_workout_counts(user, weeks_back=1, anchor=date.today())[0]["workouts"]
    goal_days = int(goals.get("dias_semana", 0) or 0)

    c1, c2, c3 = st.columns([1.2, 1.2, 2.6])
    with c1:
        new_goal_days = st.number_input(
            "Días de entreno/semana",
            min_value=0,
            max_value=7,
            value=goal_days,
            step=1,
            key="obj_week_days",
        )
    with c2:
        if st.button("Guardar", key="obj_week_save", use_container_width=True):
            set_weekly_days_goal(user, int(new_goal_days))
            st.success("Objetivo semanal actualizado.")
            st.rerun()
    with c3:
        st.metric(
            "Esta semana",
            f"{this_week_done}/{goal_days} días" if goal_days > 0 else f"{this_week_done} días",
            help=f"Semana: {ws.isoformat()} → {we.isoformat()} (Lunes–Domingo)",
        )
        if goal_days > 0:
            st.progress(min(1.0, this_week_done / goal_days))
        else:
            st.progress(0.0)

    hist = weekly_workout_counts(user, weeks_back=8, anchor=date.today())
    if hist:
        df_hist = pd.DataFrame(hist)
        df_hist["Semana"] = df_hist["week_start"].apply(lambda d: d.strftime("%d/%m"))
        df_hist = df_hist[["Semana", "workouts"]].set_index("Semana")
        st.caption("Histórico de días entrenados (últimas 8 semanas)")
        st.bar_chart(df_hist)

    st.markdown("---")

    st.subheader("⚖️ Peso objetivo")
    weights = list_weights(user)
    current_w = None
    current_w_date = None
    if weights:
        try:
            # último por fecha
            w_sorted = sorted(weights, key=lambda x: str(x.get("date", "")))
            last = w_sorted[-1]
            current_w = float(last.get("weight"))
            current_w_date = str(last.get("date"))
        except Exception:
            current_w = None

    with st.form("obj_weight_form"):
        use_weight_goal = st.checkbox(
            "Quiero establecer un peso objetivo",
            value=(goals.get("peso_objetivo") is not None),
            key="obj_use_weight_goal",
        )
        default_w_goal = goals.get("peso_objetivo")
        if default_w_goal is None:
            default_w_goal = 70.0
        w_goal = st.number_input(
            "Peso objetivo (kg)",
            min_value=0.0,
            step=0.1,
            value=float(default_w_goal),
            disabled=not use_weight_goal,
            key="obj_weight_goal",
        )
        save_w = st.form_submit_button("Guardar peso objetivo")
    if save_w:
        set_target_body_weight(user, float(w_goal) if use_weight_goal else None)
        st.success("Peso objetivo actualizado.")
        st.rerun()

    peso_obj = goals.get("peso_objetivo")
    if current_w is not None:
        if peso_obj is not None:
            diff = current_w - float(peso_obj)
            st.metric(
                "Peso actual vs objetivo",
                f"{current_w:.1f} kg",
                delta=f"{diff:+.1f} kg",
                help=f"Último registro: {current_w_date}",
            )
        else:
            st.metric("Peso actual", f"{current_w:.1f} kg", help=f"Último registro: {current_w_date}")
    else:
        st.info("Aún no hay registros de peso. Ve a **Salud (Peso)** para añadirlos.")

    st.markdown("---")

    st.subheader("🏋️ Objetivos por ejercicio")

    all_exs = list_all_exercises(user)
    ex_goals = (goals.get("ejercicios") or {})
    ex_goal_names = sorted(ex_goals.keys())

    with st.expander("➕ Añadir / editar objetivo", expanded=True):
        # Si ya hay objetivos, por defecto selecciona el primero; si no, el primero del listado
        default_ex = ex_goal_names[0] if ex_goal_names else (all_exs[0] if all_exs else "")
        selected_ex = st.selectbox("Ejercicio", all_exs, index=(all_exs.index(default_ex) if default_ex in all_exs else 0), key="obj_ex_sel")
        current_meta = ex_goals.get(selected_ex, {}) if selected_ex else {}
        c1, c2, c3 = st.columns(3)
        with c1:
            t_w = st.number_input(
                "Peso objetivo (kg)",
                min_value=0.0,
                step=0.5,
                value=float(current_meta.get("peso") or 0.0),
                key="obj_ex_weight",
            )
        with c2:
            t_r = st.number_input(
                "Reps objetivo",
                min_value=1,
                max_value=100,
                step=1,
                value=int(current_meta.get("reps") or 8),
                key="obj_ex_reps",
            )
        with c3:
            if st.button("Guardar objetivo", key="obj_ex_save", use_container_width=True):
                set_exercise_goal(user, selected_ex, peso_objetivo=float(t_w), reps_objetivo=int(t_r))
                st.success("Objetivo guardado.")
                st.rerun()

    # Tabla de comparación objetivo vs último valor
    if not ex_goals:
        st.info("Aún no tienes objetivos por ejercicio. Añade alguno arriba.")
    else:
        rows = []
        for ex_name, meta in sorted(ex_goals.items(), key=lambda x: x[0].lower()):
            t_w = meta.get("peso")
            t_r = meta.get("reps")
            last = last_values_for_exercise(user, ex_name)
            last_r, last_w = (None, None)
            if last:
                last_r, last_w = last

            # Estado: si hay datos
            status = "—"
            if last is not None:
                ok_w = True if t_w is None else (float(last_w) >= float(t_w))
                ok_r = True if t_r is None else (int(last_r) >= int(t_r))
                status = "✅" if (ok_w and ok_r) else "⏳"

            rows.append(
                {
                    "Ejercicio": ex_name,
                    "Objetivo (kg)": ("" if t_w is None else float(t_w)),
                    "Objetivo (reps)": ("" if t_r is None else int(t_r)),
                    "Último (kg)": ("" if last_w is None else float(last_w)),
                    "Último (reps)": ("" if last_r is None else int(last_r)),
                    "Estado": status,
                }
            )

        df_obj = pd.DataFrame(rows)
        st.dataframe(df_obj, use_container_width=True, hide_index=True)

        st.caption("*El ‘Último’ valor es la última serie guardada para ese ejercicio (por fecha y set).* ")

        st.markdown("#### 🗑️ Eliminar objetivo")
        del_ex = st.selectbox("Selecciona un objetivo para borrar", ex_goal_names, key="obj_ex_del_sel")
        if st.button("Eliminar", key="obj_ex_del_btn"):
            remove_exercise_goal(user, del_ex)
            st.success("Objetivo eliminado.")
            st.rerun()


elif page == "Peso corporal":
    require_auth()
    st.title("Peso corporal")
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

elif page == "Planificar rutinas":
    require_auth()
    render_planner_page(st.session_state["user"])


elif page in ("Cuenta", "Mi cuenta"):
    require_auth()
    st.title("Cuenta")
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
