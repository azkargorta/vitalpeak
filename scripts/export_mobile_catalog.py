"""Exporta el catálogo base de VitalPeak para la PWA sin duplicar datos a mano."""

from __future__ import annotations

import json
import re
import sys
import unicodedata
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from app.exercise_catalog import get_grupo, load_base_exercises
from app.routine_templates import TEMPLATES

SEQUENCES = ROOT / "exercise_images" / "sequences"
OUTPUT = ROOT / "mobile" / "catalog-data.js"


def key(value: str) -> str:
    plain = unicodedata.normalize("NFKD", value).encode("ascii", "ignore").decode()
    return re.sub(r"[^a-z0-9]+", "", plain.lower())


def animation_index() -> dict[str, dict]:
    result: dict[str, dict] = {}
    for metadata in SEQUENCES.glob("*/meta.json"):
        try:
            info = json.loads(metadata.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            continue
        gif = metadata.parent / "movimiento.gif"
        if not gif.exists():
            continue
        result[key(info.get("label", metadata.parent.name))] = {
            "path": f"exercise-gifs/{metadata.parent.name}/movimiento.gif",
            "steps": info.get("steps", []),
        }
    return result


def generic_cues(name: str, group: str) -> list[str]:
    common = ["Mantén el movimiento controlado y una postura estable.", "Detén la serie si aparece dolor agudo."]
    cues = {
        "Pecho": ["Escápulas estables y pecho abierto.", "Controla la bajada antes de empujar."],
        "Espalda": ["Inicia el gesto llevando los hombros lejos de las orejas.", "Lleva el codo hacia atrás sin balancearte."],
        "Hombro": ["Mantén el core firme y evita encoger los hombros.", "Sube con control y baja sin dejar caer la carga."],
        "Pierna": ["Apoya todo el pie y alinea rodillas con la punta de los pies.", "Controla el rango que puedas mantener con técnica."],
        "Brazo": ["Mantén el codo estable durante el recorrido.", "Evita usar impulso del tronco."],
    }
    return cues.get(group, [f"Realiza {name} con un ritmo controlado.", *common])


def main() -> None:
    animations = animation_index()
    exercises = []
    for name in load_base_exercises():
        group = get_grupo(name)
        animation = animations.get(key(name), {})
        exercises.append({
            "name": name,
            "group": group,
            "cues": generic_cues(name, group),
            "animation": animation,
        })
    payload = {"templates": TEMPLATES, "exercises": exercises}
    OUTPUT.write_text(
        "/* Archivo generado desde el catálogo de VitalPeak. No editar a mano. */\n"
        f"window.VITALPEAK_CATALOG = {json.dumps(payload, ensure_ascii=False, separators=(',', ':'))};\n",
        encoding="utf-8",
    )


if __name__ == "__main__":
    main()
