
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
    submitted = st.form_submit_button("Generar rutina")

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
    # --- Características usadas en el prompt (debajo del entreno) ---
    try:
        _prompt = result.get("prompt_used") if 'result' in locals() else None
        _system = result.get("system_prompt") if 'result' in locals() else None
        if _prompt:
            with st.expander("Características usadas en el prompt", expanded=False):
                import re as _re_ui
                st.caption("Resumen de parámetros y reglas inyectadas en la generación.")
                _params_match = _re_ui.search(r"=== PARAMS ===\s*(.*?)\s*=== /PARAMS ===", _prompt, flags=_re_ui.DOTALL)
                if _params_match:
                    st.markdown("**Parámetros**")
                    for line in _params_match.group(1).splitlines():
                        st.code(line.strip(), language="")
                _conds_match = _re_ui.search(r"CONDICIONES_USUARIO[^\n]*:\s*(.*?)(?:\n{2,}|SALIDA \(JSON\)|$)", _prompt, flags=_re_ui.DOTALL)
                if _conds_match:
                    st.markdown("**Condiciones del usuario interpretadas**")
                    st.code(_conds_match.group(1).strip(), language="")
                st.markdown("**Prompt completo (auditoría)**")
                st.code(_prompt, language="")
        else:
            st.info("No se pudo capturar el prompt usado en esta ejecución.")
    except Exception as _e:
        st.warning(f"No se pudo mostrar el prompt usado: {_e}")


    st.download_button(
        "📥 Descargar JSON",
        data=json.dumps(data_out, ensure_ascii=False, indent=2),
        file_name="rutina.json",
        mime="application/json"
    )