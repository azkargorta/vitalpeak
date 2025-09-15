
import json
import streamlit as st
from app.ai_generator import extract_constraints, validar_constraints, validar_comentarios, enforce_simple_constraints

st.set_page_config(page_title="Test Constraints IA", page_icon="🧪", layout="wide")

st.title("🧪 Test de Constraints (Comentarios → Reglas 100%)")
st.write("Escribe comentarios naturales y valida cómo se traducen a constraints y si tu plan los cumple.")

default_comments = "solo un día de pierna; al menos 4 ejercicios de bíceps; no máquinas; máximo 5 ejercicios por día"
comentarios = st.text_area("Comentarios de ejemplo", value=default_comments, height=120)

st.subheader("Plan de ejemplo (puedes modificarlo)")
sample_plan = {
    "dias": [
        {
            "nombre": "Día 1 - Pecho/Bíceps",
            "grupo_principal": "pecho",
            "ejercicios": [
                {"nombre": "Press banca máquina", "series": 4, "reps": "8-10", "rir": "2", "musculo_principal": "pecho"},
                {"nombre": "Aperturas en polea", "series": 3, "reps": "12", "rir": "2", "musculo_principal": "pecho"},
                {"nombre": "Curl con barra", "series": 3, "reps": "8-10", "rir": "2", "musculo_principal": "bíceps"},
                {"nombre": "Curl martillo", "series": 3, "reps": "10-12", "rir": "1-2", "musculo_principal": "bíceps"},
                {"nombre": "Elevaciones laterales", "series": 3, "reps": "12-15", "rir": "1-2", "musculo_principal": "hombro"},
                {"nombre": "Face pull", "series": 2, "reps": "15", "rir": "2", "musculo_principal": "hombro"},
            ]
        },
        {
            "nombre": "Día 2 - Espalda/Bíceps",
            "grupo_principal": "espalda",
            "ejercicios": [
                {"nombre": "Remo con barra", "series": 4, "reps": "6-8", "rir": "2", "musculo_principal": "espalda"},
                {"nombre": "Jalón en polea", "series": 3, "reps": "10-12", "rir": "2", "musculo_principal": "espalda"},
                {"nombre": "Curl predicador", "series": 3, "reps": "10-12", "rir": "1-2", "musculo_principal": "bíceps"}
            ]
        },
        {
            "nombre": "Día 3 - Pierna/Glúteo",
            "grupo_principal": "pierna",
            "ejercicios": [
                {"nombre": "Sentadilla en máquina Smith", "series": 4, "reps": "6-8", "rir": "2", "musculo_principal": "pierna"},
                {"nombre": "Prensa de pierna", "series": 4, "reps": "8-10", "rir": "1-2", "musculo_principal": "pierna"},
                {"nombre": "Curl femoral en máquina", "series": 3, "reps": "12-15", "rir": "2", "musculo_principal": "pierna"}
            ]
        },
        {
            "nombre": "Día 4 - Pierna ligera/Core",
            "grupo_principal": "pierna",
            "ejercicios": [
                {"nombre": "Zancadas", "series": 3, "reps": "12", "rir": "2", "musculo_principal": "pierna"},
                {"nombre": "Plancha", "series": 3, "reps": "45s", "rir": "3", "musculo_principal": "core"}
            ]
        }
    ]
}
plan_text = st.text_area("Plan (JSON)", value=json.dumps(sample_plan, ensure_ascii=False, indent=2), height=350)
try:
    plan = json.loads(plan_text)
    plan_ok = True
except Exception as e:
    plan_ok = False
    st.error(f"JSON inválido: {e}")

if plan_ok:
    C = extract_constraints(comentarios)
    st.subheader("Constraints extraídos")
    st.code(json.dumps(C, ensure_ascii=False, indent=2), language="json")

    errs_c = validar_constraints(plan, C)
    errs_t = validar_comentarios(plan, comentarios)

    col1, col2 = st.columns(2)
    with col1:
        st.markdown("### Violaciones (constraints)")
        if errs_c:
            for e in errs_c:
                st.markdown(f"- {e}")
        else:
            st.success("✅ Sin violaciones de constraints.")
    with col2:
        st.markdown("### Violaciones (comentarios en texto)")
        if errs_t:
            for e in errs_t:
                st.markdown(f"- {e}")
        else:
            st.success("✅ Sin violaciones desde comentarios.")

    st.divider()
    st.markdown("### Auto-ajuste simple (demo)")
    if st.button("Aplicar auto-ajuste al plan de ejemplo"):
        plan2 = enforce_simple_constraints(plan, C)
        errs_c2 = validar_constraints(plan2, C)
        errs_t2 = validar_comentarios(plan2, comentarios)
        st.markdown("**Plan ajustado (JSON):**")
        st.code(json.dumps(plan2, ensure_ascii=False, indent=2), language="json")
        st.markdown("**Violaciones tras auto-ajuste:**")
        if not errs_c2 and not errs_t2:
            st.success("✅ Sin violaciones tras auto-ajuste.")
        else:
            if errs_c2:
                st.markdown("**Constraints:**")
                for e in errs_c2:
                    st.markdown(f"- {e}")
            if errs_t2:
                st.markdown("**Comentarios:**")
                for e in errs_t2:
                    st.markdown(f"- {e}")
