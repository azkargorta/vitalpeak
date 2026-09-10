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
from app.training_volume import public_volume_config
from app.exercise_selector import public_selector_config
from app.routine_engine import public_routine_engine_config

SEQUENCES = ROOT / "exercise_images" / "sequences"
OUTPUT = ROOT / "mobile" / "catalog-data.js"
METADATA_FILE = ROOT / "data" / "exercise_metadata.json"

CARDIO_EXERCISES = [
    {"name": "Cinta de correr", "group": "Cardio", "cardio": True, "cardioType": "treadmill", "cues": ["Empieza con unos minutos suaves antes de subir el ritmo.", "Mantén una zancada natural y evita agarrarte a la consola salvo necesidad."], "animation": {"path": "cardio-images/cinta-de-correr.webp", "kind": "image"}},
    {"name": "Caminata en cinta con inclinación", "group": "Cardio", "cardio": True, "cardioType": "treadmill", "cues": ["Mantén el tronco erguido y una inclinación que puedas sostener con buena técnica.", "Ajusta velocidad e inclinación para controlar la intensidad sin tener que correr."], "animation": {"path": "cardio-images/caminata-cinta-inclinacion.webp", "kind": "image"}},
    {"name": "Bicicleta estática", "group": "Cardio", "cardio": True, "cardioType": "bike", "cues": ["Ajusta el sillín para que la rodilla quede ligeramente flexionada abajo.", "Pedalea de forma fluida y controla la resistencia sin perder cadencia."], "animation": {"path": "cardio-images/bicicleta-estatica.webp", "kind": "image"}},
    {"name": "Bicicleta de aire", "group": "Cardio", "cardio": True, "cardioType": "air-bike", "cues": ["Empuja y tira con brazos mientras mantienes un pedaleo constante.", "En intervalos intensos prioriza una postura estable antes que la velocidad máxima."], "animation": {"path": "cardio-images/bicicleta-aire.webp", "kind": "image"}},
    {"name": "Bicicleta elíptica", "group": "Cardio", "cardio": True, "cardioType": "elliptical", "cues": ["Mantén el apoyo completo del pie y el tronco estable.", "Aumenta resistencia antes de acelerar si buscas más intensidad con menos impacto."], "animation": {"path": "cardio-images/bicicleta-eliptica.webp", "kind": "image"}},
    {"name": "Remo ergómetro", "group": "Cardio", "cardio": True, "cardioType": "rower", "cues": ["Empuja primero con las piernas, después acompaña con tronco y brazos.", "En la vuelta recupera brazos, tronco y finalmente piernas."], "animation": {"path": "cardio-images/remo-ergometro.webp", "kind": "image"}},
    {"name": "Escaladora", "group": "Cardio", "cardio": True, "cardioType": "stair-climber", "cues": ["Evita descargar el peso sobre las manos.", "Usa pasos controlados y regula el ritmo para mantener la intensidad objetivo."], "animation": {"path": "cardio-images/escaladora.webp", "kind": "image"}},
    {"name": "Saltar a la comba", "group": "Cardio", "cardio": True, "cardioType": "jump-rope", "cues": ["Haz saltos bajos y suaves, principalmente desde los tobillos.", "Mantén los codos cerca del cuerpo y mueve la cuerda con las muñecas."], "animation": {"path": "cardio-images/saltar-comba.webp", "kind": "image"}},
    {"name": "Carrera exterior", "group": "Cardio", "cardio": True, "cardioType": "running", "cues": ["Empieza suave y aumenta progresivamente el ritmo.", "Adapta el esfuerzo al terreno y a las condiciones del día."], "animation": {"path": "cardio-images/carrera-exterior.webp", "kind": "image"}},
    {"name": "Caminata rápida", "group": "Cardio", "cardio": True, "cardioType": "walking", "cues": ["Busca un paso vivo que puedas mantener sin perder postura.", "Usa el movimiento natural de brazos para acompañar el ritmo."], "animation": {"path": "cardio-images/caminata-rapida.webp", "kind": "image"}},
]


def key(value: str) -> str:
    plain = unicodedata.normalize("NFKD", value).encode("ascii", "ignore").decode()
    return re.sub(r"[^a-z0-9]+", "", plain.lower())


def load_exercise_metadata() -> dict[str, dict]:
    if not METADATA_FILE.is_file():
        return {}
    try:
        raw = json.loads(METADATA_FILE.read_text(encoding="utf-8"))
        return raw if isinstance(raw, dict) else {}
    except (OSError, json.JSONDecodeError):
        return {}


def animation_index() -> dict[str, dict]:
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
        animation = {"path": f"exercise-gifs/{folder.name}/movimiento.gif", "kind": "gif", "steps": info.get("steps", [])}
        result[key(folder.name)] = animation
        label = info.get("label")
        if label:
            result[key(label)] = animation

    press_banca = result.get(key("press_banca"))
    if press_banca:
        result[key("Press con barra en banco horizontal")] = press_banca
        result[key("Press banca")] = press_banca

    back_squat = result.get(key("Sentadillas con barra con las piernas separadas"))
    if back_squat:
        result[key("Sentadilla trasera con barra")] = back_squat
    return result


def generic_cues(name: str, group: str) -> list[str]:
    common = ["Mantén el movimiento controlado y una postura estable.", "Detén la serie si aparece dolor agudo."]
    cues = {
        "Pecho": ["Escápulas estables y pecho abierto.", "Controla la bajada antes de empujar."],
        "Espalda": ["Inicia el gesto llevando los hombros lejos de las orejas.", "Lleva el codo hacia atrás sin balancearte."],
        "Hombro": ["Mantén el core firme y evita encoger los hombros.", "Sube con control y baja sin dejar caer la carga."],
        "Pierna": ["Apoya todo el pie y alinea rodillas con la punta de los pies.", "Controla el rango que puedas mantener con técnica."],
        "Brazo": ["Mantén el codo estable durante el recorrido.", "Evita usar impulso del tronco."],
        "Core": ["Mantén el tronco estable y respira de forma controlada.", "Evita compensar con la zona lumbar."],
    }
    return cues.get(group, [f"Realiza {name} con un ritmo controlado.", *common])


def main() -> None:
    animations = animation_index()
    metadata = load_exercise_metadata()
    exercises = []
    missing_metadata = []

    for name in load_base_exercises():
        group = get_grupo(name)
        item = {"name": name, "group": group, "cues": generic_cues(name, group), "animation": animations.get(key(name), {})}
        advanced = metadata.get(name)
        if isinstance(advanced, dict):
            item["metadata"] = advanced
        else:
            missing_metadata.append(name)
        exercises.append(item)

    if missing_metadata:
        raise SystemExit("Faltan metadatos para ejercicios base: " + ", ".join(missing_metadata))

    existing_names = {key(item["name"]) for item in exercises}
    for cardio in CARDIO_EXERCISES:
        if key(cardio["name"]) not in existing_names:
            exercises.append(cardio)
            existing_names.add(key(cardio["name"]))

    payload = {
        "templates": TEMPLATES,
        "exercises": exercises,
        "volumeEngine": public_volume_config(),
        "exerciseSelector": public_selector_config(),
        "routineEngine": public_routine_engine_config(),
    }
    OUTPUT.write_text(
        "/* Archivo generado desde el catálogo de VitalPeak. No editar a mano. */\n"
        f"window.VITALPEAK_CATALOG = {json.dumps(payload, ensure_ascii=False, separators=(',', ':'))};\n"
        "try {\n"
        "  const custom = JSON.parse(localStorage.getItem('vitalpeak-custom-exercises') || '[]');\n"
        "  if (Array.isArray(custom)) {\n"
        "    const names = new Set(window.VITALPEAK_CATALOG.exercises.map(x => String(x.name).toLocaleLowerCase('es')));\n"
        "    for (const item of custom) { const name = String(item?.name || '').trim(); if (name && !names.has(name.toLocaleLowerCase('es'))) { window.VITALPEAK_CATALOG.exercises.push(item); names.add(name.toLocaleLowerCase('es')); } }\n"
        "  }\n"
        "} catch {}\n"
        "window.VITALPEAK_ASSET_URL = path => './' + String(path || '').replace(/^\\.\\//, '').replace(/^\\//, '');\n"
        "const vpOriginalFetch = window.fetch.bind(window);\n"
        "window.fetch = async (...args) => {\n"
        "  const response = await vpOriginalFetch(...args);\n"
        "  const target = String(args[0]?.url || args[0] || '');\n"
        "  if (!target.includes('app.js')) return response;\n"
        "  const text = await response.text();\n"
        "  let fixed = text.replace('template:renderTemplate', 'template:renderRoutines');\n"
        "  fixed = fixed.replace('${x.animation?.path?`<small>Movimiento guiado</small>`:\"\"}', '${x.animation?.path?`<small>${x.cardio||x.group===\"Cardio\"?\"Imagen de referencia\":\"Movimiento guiado\"}</small>`:\"\"}');\n"
        "  fixed = fixed.replace('<b>Movimiento guiado</b><span>El GIF queda disponible sin conexión después de verlo una vez.</span>', '<b>${x.cardio||x.group===\"Cardio\"?\"Imagen del ejercicio\":\"Movimiento guiado\"}</b><span>${x.cardio||x.group===\"Cardio\"?\"Referencia visual del ejercicio de cardio.\":\"GIF animado de técnica del ejercicio.\"}</span>');\n"
        "  return new Response(fixed, { status: response.status, statusText: response.statusText, headers: response.headers });\n"
        "};\n"
        "for (const src of ['./routine-enhancements.js?v=36', './routine-generator-ui.js?v=4', './routine-muscle-filter.js?v=36', './calendar-mobile.js?v=36', './training-intelligence.js?v=36', './routine-navigation-fix.js?v=36', './routines-accordion.js?v=36']) { const script = document.createElement('script'); script.src = src; script.defer = true; script.onerror = () => console.warn('VitalPeak: mejora opcional no cargada', src); document.head.appendChild(script); }\n",
        encoding="utf-8",
    )

    visual_count = sum(bool(x["animation"]) for x in exercises)
    gif_count = sum(x.get("animation", {}).get("kind") == "gif" for x in exercises)
    image_count = sum(x.get("animation", {}).get("kind") == "image" for x in exercises)
    print(f"Catálogo móvil: {len(TEMPLATES)} rutinas, {len(exercises)} ejercicios, {visual_count} con recurso visual ({gif_count} GIF, {image_count} imágenes), motor de volumen, selector y motor de rutinas exportados.")


if __name__ == "__main__":
    main()
