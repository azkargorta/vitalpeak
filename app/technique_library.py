from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, List

import streamlit as st

from app.technique_cards import (
    SECTION_LABELS,
    get_card,
    save_card,
    textarea_to_list,
    list_to_textarea,
)
from app.technique_3d_component import render_mannequin_3d


@dataclass
class TechniqueExercise:
    label: str
    exercise_id: str
    default_cues: List[str]


def get_library() -> Dict[str, TechniqueExercise]:
    # Biblioteca inicial: añade más ejercicios aquí
    items = [
        TechniqueExercise(
            label="Press banca",
            exercise_id="bench_press",
            default_cues=[
                "Escápulas atrás y abajo; pecho arriba sin arquear lumbar en exceso.",
                "Muñecas neutras; antebrazo vertical cerca del punto medio.",
                "Baja con control al pecho y empuja “hacia arriba y ligeramente atrás”.",
            ],
        ),
        TechniqueExercise(
            label="Sentadilla",
            exercise_id="squat",
            default_cues=[
                "Pies firmes, rodillas siguen la línea de los pies.",
                "Core firme (“costillas abajo”), espalda neutra.",
                "Baja controlado, sube empujando el suelo.",
            ],
        ),
        TechniqueExercise(
            label="Peso muerto",
            exercise_id="deadlift",
            default_cues=[
                "Barra pegada al cuerpo; hombros sobre la barra al inicio.",
                "Bisagra de cadera: siente isquios/glúteo, no la espalda baja.",
                "Empuja el suelo y extiende cadera al final sin hiperextender.",
            ],
        ),
    ]
    return {i.label: i for i in items}


def _render_card_view(card: dict) -> None:
    st.markdown(f"### {card.get('exercise_label','')}")
    st.markdown("---")

    st.markdown(f"**{SECTION_LABELS['setup']}**")
    for x in card["setup"]:
        st.markdown(f"- {x}")

    st.markdown(f"**{SECTION_LABELS['execution']}**")
    for x in card["execution"]:
        st.markdown(f"- {x}")

    st.markdown(f"**{SECTION_LABELS['quick_cues']}**")
    for x in card["quick_cues"]:
        st.markdown(f"- {x}")

    st.markdown(f"**{SECTION_LABELS['common_errors']}**")
    for ce in card["common_errors"]:
        if isinstance(ce, dict):
            st.markdown(f"- **Error:** {ce.get('error','')}  \n  ✅ **Corrección:** {ce.get('fix','')}")
        else:
            st.markdown(f"- {ce}")

    st.markdown(f"**{SECTION_LABELS['should_feel']}**")
    for x in card["should_feel"]:
        st.markdown(f"- {x}")

    st.markdown(f"**{SECTION_LABELS['should_not_feel']}**")
    for x in card["should_not_feel"]:
        st.markdown(f"- {x}")


def render_technique_page() -> None:
    st.title("🎥 Técnica")
    st.caption("Tarjeta técnica + mini-animación 3D (plantilla única, 2 ángulos).")

    lib = get_library()
    exercise_label = st.selectbox("Ejercicio", list(lib.keys()), index=0, key="tech_exercise")
    ex = lib[exercise_label]

    user = st.session_state.get("user", "anon")

    tabs = st.tabs(["📄 Tarjeta técnica", "🧍 Mini-animación 3D"])
    with tabs[0]:
        card = get_card(user, ex.exercise_id, ex.label)
        _render_card_view(card)

        with st.expander("Editar ficha (opcional)", expanded=False):
            st.write("Escribe 1 punto por línea (bullets).")

            setup_t = st.text_area("Setup", value=list_to_textarea(card["setup"]), height=110)
            exec_t = st.text_area("Ejecución", value=list_to_textarea(card["execution"]), height=110)
            cues_t = st.text_area("Cues rápidos", value=list_to_textarea(card["quick_cues"]), height=90)

            # Errores: formato simple "error => corrección"
            default_err_lines = []
            for e in card["common_errors"]:
                if isinstance(e, dict):
                    default_err_lines.append(f"{e.get('error','')} => {e.get('fix','')}")
                else:
                    default_err_lines.append(str(e))
            err_t = st.text_area("Errores comunes (usa: error => corrección)", value="\n".join(default_err_lines), height=120)

            feel_t = st.text_area("Qué debería sentir", value=list_to_textarea(card["should_feel"]), height=80)
            notfeel_t = st.text_area("Qué NO debería sentir", value=list_to_textarea(card["should_not_feel"]), height=80)

            if st.button("Guardar ficha", type="primary", use_container_width=True):
                new_card = {
                    "exercise_label": ex.label,
                    "setup": textarea_to_list(setup_t),
                    "execution": textarea_to_list(exec_t),
                    "quick_cues": textarea_to_list(cues_t),
                    "common_errors": [],
                    "should_feel": textarea_to_list(feel_t),
                    "should_not_feel": textarea_to_list(notfeel_t),
                }
                # parse errores
                errs = []
                for ln in textarea_to_list(err_t):
                    if "=>" in ln:
                        a, b = ln.split("=>", 1)
                        errs.append({"error": a.strip(), "fix": b.strip()})
                    else:
                        errs.append({"error": ln.strip(), "fix": ""})
                new_card["common_errors"] = errs

                save_card(user, ex.exercise_id, new_card)
                st.success("Ficha guardada ✅ (por usuario)")

    with tabs[1]:
        st.markdown("### Cues en pantalla")
        for c in ex.default_cues[:3]:
            st.markdown(f"- {c}")

        st.markdown("### Mini-animación 3D (frontal + lateral)")
        render_mannequin_3d(ex.exercise_id, cues=ex.default_cues)

        st.markdown("---")
        st.caption(
            "Atribución requerida (CC BY): "
            "Manequin - Low Poly Model por Miarintsoa (Sketchfab), licencia CC Attribution."
        )
