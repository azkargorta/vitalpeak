
import os, json
import streamlit as st
from app.ai_generator import call_gpt
from app.rules_fallback import generate_fallback
from app.pdf_export import rutina_a_pdf_bytes

st.set_page_config(page_title="Creador de Rutinas (IA)", page_icon="💪", layout="centered")
st.title("💪 Creador de Rutinas (IA)")
st.caption("Genera tu rutina con ChatGPT. Si la IA falla, usamos un plan base fiable.")

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

    # Comentarios y vista previa de reglas

    comentarios = st.text_area(

        "Comentarios para la IA (opcional)",

        placeholder="Ej: solo 1 día de pierna; 2 días de bíceps; quiero 1 día de cardio; evitar peso muerto...",

        height=100,

    )

    try:

        from app.ai_generator import _compile_user_conditions as _ui_compile

        _ui_conds = _ui_compile(comentarios or "")

        with st.expander("Reglas entendidas (previas a IA)", expanded=True):

            colA, colB = st.columns(2)

            with colA:

                st.markdown("**MUST (obligatorio)**")

                if _ui_conds.get("MUST"):

                    for it in _ui_conds["MUST"]:

                        st.markdown(f"- {it}")

                else:

                    st.caption("— Ninguno —")

                st.markdown("**NEVER (prohibido)**")

                if _ui_conds.get("NEVER"):

                    for it in _ui_conds["NEVER"]:

                        st.markdown(f"- {it}")

                else:

                    st.caption("— Ninguno —")

            with colB:

                st.markdown("**LIMITS detectados**")

                _limits = _ui_conds.get("LIMITS", {})

                _ldm = _limits.get("leg_days_max")

                if _ldm:

                    st.write(f"Pierna: como máximo {_ldm} día(s)/semana.")

                _cardio = _limits.get("cardio_days", {})

                if _cardio:

                    if "exact" in _cardio:

                        st.write(f"Cardio: exactamente {_cardio['exact']} día(s)/semana.")

                    else:

                        if "min" in _cardio:

                            st.write(f"Cardio: al menos {_cardio['min']} día(s)/semana.")

                        if "max" in _cardio:

                            st.write(f"Cardio: como máximo {_cardio['max']} día(s)/semana.")

                _gdays = _limits.get("group_days", {})

                if _gdays:

                    for g, spec in _gdays.items():

                        parts = []

                        if "exact" in spec: parts.append(f"exactamente {spec['exact']}")

                        if "min" in spec: parts.append(f"min {spec['min']}")

                        if "max" in spec: parts.append(f"max {spec['max']}")

                        if parts:

                            st.write(f"{g}: " + ", ".join(parts) + " día(s)/semana.")

                if not (_ldm or _cardio or _gdays):

                    st.caption("— Sin límites detectados —")

            st.caption("Estas reglas se inyectan en el prompt y además se validan tras la generación.")

    except Exception as _e:

        st.caption(f"No se pudo interpretar Comentarios: {_e}")

    submitted = st.form_submit_button("Generar rutina")

if submitted:
    datos_usuario = {
        "nivel": nivel,
        "dias": int(dias),
        "duracion": int(duracion),
        "objetivo": objetivo,
        "material": material,
        "limitaciones": limitaciones.strip()
    ,
        "comentarios": (comentarios or "").strip()
    }

    api_key_ok = bool(os.getenv("OPENAI_API_KEY"))
    data_out = None
    used_fallback = False
    error = None

    if api_key_ok:
        with st.spinner("Generando con IA..."):
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
        st.error(f"Fallo al generar con OpenAI: {st.session_state.get('ia_error', 'error desconocido')}")
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