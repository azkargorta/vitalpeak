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
    """Indexa todos los GIF disponibles, tengan o no meta.json."""
    result: dict[str, dict] = {}
    if not SEQUENCES.is_dir():
        return result

    for folder in SEQUENCES.iterdir():
        if not folder.is_dir():
            continue
        gif = folder / "movimiento.gif"
        if not gif.is_file():
            continue

        info: dict = {}
        metadata = folder / "meta.json"
        if metadata.is_file():
            try:
                info = json.loads(metadata.read_text(encoding="utf-8"))
            except (OSError, json.JSONDecodeError):
                info = {}

        animation = {
            "path": f"exercise-gifs/{folder.name}/movimiento.gif",
            "steps": info.get("steps", []),
        }
        result[key(folder.name)] = animation
        label = info.get("label")
        if label:
            result[key(label)] = animation

    # Alias legacy utilizado por la versión original de VitalPeak.
    press_banca = result.get(key("press_banca"))
    if press_banca:
        result[key("Press con barra en banco horizontal")] = press_banca
        result[key("Press banca")] = press_banca

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
    print(f"Catálogo móvil: {len(TEMPLATES)} rutinas, {len(exercises)} ejercicios, {sum(bool(x['animation']) for x in exercises)} con GIF.")


if __name__ == "__main__":
    main()
