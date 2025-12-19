from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import List, Dict

import streamlit as st

from .technique_cards import get_card, render_card, render_card_editor
from .technique_animation_component import render_minimal_3d_animation


@dataclass
class TechniqueItem:
    label: str
    exercise_id: str
    video_filename: str
    cues: List[str]


def assets_dir() -> Path:
    # app/technique_library.py -> app -> project root
    return Path(__file__).resolve().parent.parent / "assets" / "technique"


def get_library() -> Dict[str, TechniqueItem]:
    return {
        "Sentadilla": TechniqueItem(
            label="Sentadilla",
            exercise_id="squat",
            video_filename="sentadilla_tecnica.mp4",
            cues=[
                "Brace: abdomen firme antes de iniciar la bajada.",
                "Pie completo apoyado: talón y metatarso en el suelo.",
                "Rodillas siguen la línea del pie (sin colapsar hacia dentro).",
                "Torso estable y controlado: no pierdas tensión.",
                "Sube con cadera y pecho a la vez (sin que la cadera se dispare).",
            ],
        ),
        "Peso muerto": TechniqueItem(
            label="Peso muerto",
            exercise_id="deadlift",
            video_filename="peso_muerto_tecnica.mp4",
            cues=[
                "Bisagra de cadera: cadera atrás, espalda neutra.",
                "Tensión antes de tirar: 'quita la holgura' y empuja el suelo.",
                "Barra pegada al cuerpo durante todo el recorrido.",
                "Cadera y pecho suben juntos (no 'rompas' primero con la cadera).",
                "Bloquea con glúteo; evita hiperextender la zona lumbar.",
            ],
        ),
        "Press banca": TechniqueItem(
            label="Press banca",
            exercise_id="bench_press",
            video_filename="press_banca_tecnica.mp4",
            cues=[
                "Escápulas atrás y abajo: pecho arriba, hombros estables.",
                "Pies firmes en el suelo (estabilidad).",
                "Muñeca sobre codo: evita doblar la muñeca hacia atrás.",
                "Baja controlado al pecho y sube con trayectoria estable.",
                "Codos en un ángulo cómodo y consistente (ni pegados ni totalmente abiertos).",
            ],
        ),
    }


def render_technique_page() -> None:
    st.subheader("🎥 Técnica")
    st.caption("Ficha estándar por ejercicio + mini-animación 3D minimal (2 vistas) + vídeo opcional.")

    user = st.session_state.get("user")
    if not user:
        st.warning("Inicia sesión para ver/editar tus fichas técnicas.")
        return

    lib = get_library()
    exercise = st.selectbox("Ejercicio", list(lib.keys()), index=0, key="tech_exercise")
    item = lib[exercise]

    tab_card, tab_anim, tab_video = st.tabs(["📄 Ficha técnica", "🧍 Mini-animación 3D", "🎬 Vídeo (opcional)"])

    with tab_card:
        card = get_card(user, exercise)
        render_card(card)

        with st.expander("Editar ficha", expanded=False):
            render_card_editor(user, exercise, initial=card)

    with tab_anim:
        st.caption("Plantilla 3D reutilizable (mismo estilo para todo). 2 vistas fijas: lateral + frontal.")
        # Preferimos los cues de la ficha si existen; si no, usamos los del item.
        card = get_card(user, exercise)
        cues = (card.get("quick_cues") or []) if isinstance(card, dict) else []
        cues = [c for c in cues if str(c).strip()]
        if not cues:
            cues = item.cues[:3]
        render_minimal_3d_animation(item.exercise_id, cues=cues)

    with tab_video:
        video_path = assets_dir() / item.video_filename
        if video_path.exists():
            st.video(str(video_path))
        else:
            st.warning("No se encontró el vídeo de técnica en assets/technique.")
            st.code(str(video_path))

        st.markdown("### Claves técnicas (rápidas)")
        for cue in item.cues:
            st.markdown(f"- {cue}")
