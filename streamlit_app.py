import matplotlib.pyplot as plt
from datetime import date
from pathlib import Path

import pandas as pd
import streamlit as st
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
    from app.routines import add_routine, list_routines, schedule_workouts
    user = st.session_state.get("user", "anon")
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
                schedule_workouts(user, rname, base_mon + _dt.timedelta(days=int(wd) + 7*w))
        st.success("Plan guardado y programado ✅")
    except Exception as e:
        st.warning(f"Plan guardado, pero no se pudo programar: {e}")
