
import os, json
import streamlit as st
from app.ai_generator import call_gpt
from app.rules_fallback import generate_fallback
from app.pdf_export import rutina_a_pdf_bytes

st.set_page_config(page_title="Creador de Rutinas (IA)", page_icon="💪", layout="centered")
st.title("💪 Creador de Rutinas (IA)")
st.caption("Genera tu rutina con ChatGPT. Si la IA falla, usamos un plan base fiable.")

with st.form("form_datos"):
    tabs = st.tabs(["Datos", "Material", "Preferencias"])
    with tabs[0]:
        col1, col2 = st.columns(2)
        with col1:
            nivel = st.selectbox("Nivel", ["principiante","intermedio","avanzado"], index=1)
            dias = st.number_input("Días/semana", min_value=1, max_value=6, value=4, step=1)
            duracion = st.slider("Duración (min)", min_value=30, max_value=120, value=60, step=5)
        with col2:
            objetivo = st.selectbox("Objetivo", ["fuerza","hipertrofia","resistencia","mixto"], index=0)
            limitaciones = st.text_input("Lesiones/limitaciones (opcional)", placeholder="Hombro, rodilla, ...")

    with tabs[1]:
        st.caption("Selecciona el material disponible. Por defecto se asume **Todo**.")
        material_preset = st.radio("Preset de material", ["Todo", "Gomas", "Personalizado"], index=0, horizontal=True)
        material_personalizado = []
        if material_preset == "Personalizado":
            material_personalizado = st.multiselect(
                "Material disponible (personalizado)",
                ["barra","mancuernas","poleas","máquinas","banco","rack","gomas","ninguno"]
            )

    with tabs[2]:
        agrupacion = st.selectbox(
            "Estructura de grupos por día",
            ["Varios grupos principales por día", "Un solo grupo principal por día"],
            index=0,
            help="Elige si prefieres combinar varios grupos musculares principales en el mismo día o centrarte en uno."
        )
        comentarios = st.text_area(
            "Comentarios y observaciones (opcional)",
            placeholder="Ej.: solo un día de pierna/glúteo • añadir 1 día de cardio + core • evitar press militar por hombro...",
            height=120,
            help="Añadidos o modificaciones que quieres en el programa generado."
        )

    submitted = st.form_submit_button("Generar rutina")

if submitted:
    datos_usuario = {
        "nivel": nivel,
        "dias": int(dias),
        "duracion": int(duracion),
        "objetivo": objetivo,
        "material": (["todo"] if material_preset=="Todo" else (["gomas"] if material_preset=="Gomas" else material_personalizado)),
        "agrupacion": agrupacion,
        "comentarios": comentarios.strip(),
        "limitaciones": limitaciones.strip()
    }

    api_key_ok = bool(os.getenv("OPENAI_API_KEY"))
    data_out = None
    used_fallback = False
    error = None

    if api_key_ok:
        with st.spinner("Generando con ChatGPT..."):
            result = call_gpt(datos_usuario)
            if result.get("ok"):
                data_out = result["data"]
            else:
                used_fallback = True
                error = result.get("error","Error desconocido")
                data_out = generate_fallback(datos_usuario)
    else:
        used_fallback = True
        data_out = generate_fallback(datos_usuario)

    st.subheader("Rutina generada")
    if used_fallback:
        st.warning("Se usó el plan de respaldo. Configura OPENAI_API_KEY para usar ChatGPT.")
        if error:
            with st.expander("Detalle del error de IA"):
                st.code(error)
    st.json(data_out)

    st.download_button(
        "📥 Descargar JSON",
        data=json.dumps(data_out, ensure_ascii=False, indent=2),
        file_name="rutina.json",
        mime="application/json"
    )

