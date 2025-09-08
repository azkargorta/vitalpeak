import os, json
import streamlit as st
from app.ai_generator import call_gpt
from app.rules_fallback import generate_fallback
from app.pdf_export import rutina_a_pdf_bytes
from app.routines_store import save_plan, list_plans, get_plan, delete_plan

st.set_page_config(page_title="Auto-configurador de rutinas (chat)", page_icon="🤖", layout="centered")
st.title("🤖 Auto-configurador de rutinas (chat)")

with st.form("form_datos"):
    col1, col2 = st.columns(2)
    with col1:
        nivel = st.selectbox("Nivel", ["principiante","intermedio","avanzado"], index=1)
        dias = st.number_input("Días/semana", min_value=1, max_value=6, value=4, step=1)
        duracion = st.slider("Duración (min)", min_value=30, max_value=120, value=60, step=5)
    with col2:
        objetivo = st.selectbox("Objetivo", ["fuerza","hipertrofia","resistencia","mixto"], index=0)
        material = st.multiselect("Material disponible", ["barra","mancuernas","poleas","máquinas","banco","rack","ninguno"])
        limitaciones = st.text_input("Lesiones/limitaciones (opcional)", placeholder="Hombro, rodilla, ...")
    submitted = st.form_submit_button("Generar rutina")

rutina = None
used_fallback = False
error = None

if submitted:
    datos_usuario = {
        "nivel": nivel,
        "dias": int(dias),
        "duracion": int(duracion),
        "objetivo": objetivo,
        "material": material,
        "limitaciones": limitaciones.strip()
    }

    api_key_ok = bool(os.getenv("OPENAI_API_KEY"))
    if api_key_ok:
        with st.spinner("Generando con ChatGPT..."):
            result = call_gpt(datos_usuario)
            if result.get("ok"):
                rutina = result["data"]
            else:
                used_fallback = True
                error = result.get("error","Error desconocido")
                rutina = generate_fallback(datos_usuario)
    else:
        used_fallback = True
        rutina = generate_fallback(datos_usuario)

    st.subheader("Rutina generada")
    if used_fallback:
        st.warning("Se usó el plan de respaldo. Configura OPENAI_API_KEY para usar ChatGPT.")
        if error:
            with st.expander("Detalle del error de IA"):
                st.code(error)

    st.json(rutina)

    pdf_bytes = rutina_a_pdf_bytes(rutina)
    st.download_button("📄 Descargar PDF", data=pdf_bytes, file_name="rutina.pdf", mime="application/pdf")

    st.markdown("---")
    st.subheader("📅 Programación y guardado")

    plan_title = st.text_input("Nombre del plan", value=f"Plan {objetivo.capitalize()} ({nivel})")
    weeks = st.number_input("Número de semanas", min_value=1, max_value=52, value=4, step=1)

    dias_semana = ["Lunes","Martes","Miércoles","Jueves","Viernes","Sábado","Domingo"]
    schedule = []
    for i, dia in enumerate(rutina.get("dias", [])):
        with st.container():
            st.write(f"**{i+1}. {dia.get('nombre','Día')}**")
            cols = st.columns(2)
            with cols[0]:
                weekday = st.selectbox("Día de la semana", dias_semana, key=f"weekday_{i}")
            with cols[1]:
                custom_name = st.text_input("Nombre del día", value=dia.get("nombre","Día"), key=f"dname_{i}")
            schedule.append({
                "day_index": i,
                "weekday": dias_semana.index(weekday),
                "name": custom_name
            })

    if st.button("💾 Guardar en registro"):
        rutina_to_save = dict(rutina)
        meta = rutina_to_save.get("meta", {})
        if "duracion" in meta and "duracion_min" not in meta:
            meta["duracion_min"] = meta.pop("duracion")
        rutina_to_save["meta"] = meta
        plan_id = save_plan(plan_title, int(weeks), rutina_to_save, schedule)
        st.success(f"Guardado como plan #{plan_id}")

st.markdown("---")
st.subheader("📚 Registro de rutinas")
plans = list_plans()
if not plans:
    st.info("No hay planes guardados todavía.")
else:
    for p in plans:
        with st.expander(f"#{p['id']} — {p['title']}  |  {p['weeks']} semanas"):
            colA, colB, colC, colD = st.columns([1,1,1,2])
            with colA:
                if st.button("Ver JSON", key=f"view_{p['id']}"):
                    data = get_plan(p["id"])
                    st.json(data)
            with colB:
                if st.button("Descargar PDF", key=f"pdf_{p['id']}"):
                    data = get_plan(p["id"])
                    if data:
                        pdf = rutina_a_pdf_bytes(data["plan"])
                        st.download_button("⬇️ PDF", data=pdf, file_name=f"plan_{p['id']}.pdf", mime="application/pdf", key=f"dl_{p['id']}")
            with colC:
                if st.button("Eliminar", key=f"del_{p['id']}"):
                    if delete_plan(p["id"]):
                        st.warning("Eliminado. Recarga la página para actualizar la lista.")
            with colD:
                st.caption(f"Creado: {p.get('created_at','')}")

