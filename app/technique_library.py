from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import List, Dict

import streamlit as st


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
    st.subheader("🎥 Técnica de ejercicios (animación)")
    st.caption("Vídeos cortos tipo esquema + claves técnicas. Cámara lateral recomendada.")

    lib = get_library()
    exercise = st.selectbox("Ejercicio", list(lib.keys()), index=0, key="tech_exercise")
    item = lib[exercise]

    video_path = assets_dir() / item.video_filename
    if video_path.exists():
        st.video(str(video_path))
    else:
        st.warning("No se encontró el vídeo de técnica en assets/technique.")
        st.code(str(video_path))

    st.markdown("### Claves técnicas")
    for cue in item.cues:
        st.markdown(f"- {cue}")

    st.info("Tip: estos vídeos están pensados como guía rápida. Si quieres, puedo añadir versión 'errores comunes' por ejercicio.")
