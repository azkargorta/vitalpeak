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

CARDIO_EXERCISES = [
    {"name": "Cinta de correr", "group": "Cardio", "cardio": True, "cardioType": "treadmill", "cues": ["Empieza con unos minutos suaves antes de subir el ritmo.", "Mantén una zancada natural y evita agarrarte a la consola salvo necesidad."], "animation": {"path": "cardio-media/cinta-de-correr.webp", "fallback": "cardio-media/cinta-de-correr.svg", "kind": "image"}},
    {"name": "Caminata en cinta con inclinación", "group": "Cardio", "cardio": True, "cardioType": "treadmill", "cues": ["Mantén el tronco erguido y una inclinación que puedas sostener con buena técnica.", "Ajusta velocidad e inclinación para controlar la intensidad sin tener que correr."], "animation": {"path": "cardio-media/caminata-cinta-inclinacion.webp", "fallback": "cardio-media/caminata-cinta-inclinacion.svg", "kind": "image"}},
    {"name": "Bicicleta estática", "group": "Cardio", "cardio": True, "cardioType": "bike", "cues": ["Ajusta el sillín para que la rodilla quede ligeramente flexionada abajo.", "Pedalea de forma fluida y controla la resistencia sin perder cadencia."], "animation": {"path": "cardio-media/bicicleta-estatica.webp", "fallback": "cardio-media/bicicleta-estatica.svg", "kind": "image"}},
    {"name": "Bicicleta de aire", "group": "Cardio", "cardio": True, "cardioType": "air-bike", "cues": ["Empuja y tira con brazos mientras mantienes un pedaleo constante.", "En intervalos intensos prioriza una postura estable antes que la velocidad máxima."], "animation": {"path": "cardio-media/bicicleta-aire.webp", "fallback": "cardio-media/bicicleta-aire.svg", "kind": "image"}},
    {"name": "Bicicleta elíptica", "group": "Cardio", "cardio": True, "cardioType": "elliptical", "cues": ["Mantén el apoyo completo del pie y el tronco estable.", "Aumenta resistencia antes de acelerar si buscas más intensidad con menos impacto."], "animation": {"path": "cardio-media/bicicleta-eliptica.webp", "fallback": "cardio-media/bicicleta-eliptica.svg", "kind": "image"}},
    {"name": "Remo ergómetro", "group": "Cardio", "cardio": True, "cardioType": "rower", "cues": ["Empuja primero con las piernas, después acompaña con tronco y brazos.", "En la vuelta recupera brazos, tronco y finalmente piernas."], "animation": {"path": "cardio-media/remo-ergometro.webp", "fallback": "cardio-media/remo-ergometro.svg", "kind": "image"}},
    {"name": "Escaladora", "group": "Cardio", "cardio": True, "cardioType": "stair-climber", "cues": ["Evita descargar el peso sobre las manos.", "Usa pasos controlados y regula el ritmo para mantener la intensidad objetivo."], "animation": {"path": "cardio-media/escaladora.svg", "kind": "image"}},
    {"name": "Saltar a la comba", "group": "Cardio", "cardio": True, "cardioType": "jump-rope", "cues": ["Haz saltos bajos y suaves, principalmente desde los tobillos.", "Mantén los codos cerca del cuerpo y mueve la cuerda con las muñecas."], "animation": {"path": "cardio-media/saltar-comba.svg", "kind": "image"}},
    {"name": "Carrera exterior", "group": "Cardio", "cardio": True, "cardioType": "running", "cues": ["Empieza suave y aumenta progresivamente el ritmo.", "Adapta el esfuerzo al terreno y a las condiciones del día."], "animation": {"path": "cardio-media/carrera-exterior.svg", "kind": "image"}},
    {"name": "Caminata rápida", "group": "Cardio", "cardio": True, "cardioType": "walking", "cues": ["Busca un paso vivo que puedas mantener sin perder postura.", "Usa el movimiento natural de brazos para acompañar el ritmo."], "animation": {"path": "cardio-media/caminata-rapida.svg", "kind": "image"}},
]


def key(value: str) -> str:
    plain = unicodedata.normalize("NFKD", value).encode("ascii", "ignore").decode()
    return re.sub(r"[^a-z0-9]+", "", plain.lower())


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
        exercises.append({"name": name, "group": group, "cues": generic_cues(name, group), "animation": animations.get(key(name), {})})

    existing_names = {key(item["name"]) for item in exercises}
    for cardio in CARDIO_EXERCISES:
        if key(cardio["name"]) not in existing_names:
            exercises.append(cardio)
            existing_names.add(key(cardio["name"]))

    payload = {"templates": TEMPLATES, "exercises": exercises}
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
        "window.VITALPEAK_ASSET_URL = function(path){\n"
        "  const clean=String(path||'').replace(/^\\.\\//,'').replace(/^\\//,'');\n"
        "  return clean ? new URL(clean, document.baseURI).href : '';\n"
        "};\n"
        "window.VITALPEAK_VISUAL = function(name){\n"
        "  const x=(window.VITALPEAK_CATALOG?.exercises||[]).find(e=>e.name===name);\n"
        "  const a=x?.animation||{}; if(!a.path)return null;\n"
        "  const kind=a.kind||(x?.cardio||x?.group==='Cardio'?'image':'gif');\n"
        "  return {path:a.path,fallback:a.fallback||'',kind,label:kind==='gif'?'Movimiento guiado':'Imagen del ejercicio',note:kind==='gif'?'GIF de técnica del ejercicio.':'Referencia visual del ejercicio de cardio.'};\n"
        "};\n"
        "window.VITALPEAK_BIND_VISUAL = function(img,visual,title){\n"
        "  if(!img||!visual)return; let triedFallback=false;\n"
        "  img.onerror=()=>{ if(!triedFallback&&visual.fallback){ triedFallback=true; img.src=window.VITALPEAK_ASSET_URL(visual.fallback); return; } img.removeAttribute('src'); img.alt='Recurso visual no disponible'; img.classList.add('visual-missing'); };\n"
        "  img.src=window.VITALPEAK_ASSET_URL(visual.path); img.alt=(visual.kind==='gif'?'Movimiento de ':'Imagen de ')+title;\n"
        "};\n"
        "function vpEnsureExerciseVisual(){\n"
        "  const app=document.querySelector('#app'), title=app?.querySelector('.hero h1')?.textContent?.trim(); if(!app||!title)return;\n"
        "  const visual=window.VITALPEAK_VISUAL(title); if(!visual)return; const card=app.querySelector('.card.stack'); if(!card)return;\n"
        "  let box=card.querySelector('.movement-placeholder'); if(!box){ box=document.createElement('div'); box.className='movement-placeholder'; box.innerHTML='<img><b></b><span></span>'; card.prepend(box); }\n"
        "  let img=box.querySelector('img'); if(!img){ img=document.createElement('img'); box.prepend(img); }\n"
        "  img.loading='eager'; img.decoding='async'; img.style.width='100%'; img.style.height='auto'; img.style.maxHeight='380px'; img.style.objectFit='contain'; window.VITALPEAK_BIND_VISUAL(img,visual,title);\n"
        "  const b=box.querySelector('b'); if(b)b.textContent=visual.label; const s=box.querySelector('span'); if(s)s.textContent=visual.note;\n"
        "}\n"
        "let vpVisualTimer=null; const vpStartVisualObserver=()=>{ const app=document.querySelector('#app'); if(!app)return setTimeout(vpStartVisualObserver,50); new MutationObserver(()=>{clearTimeout(vpVisualTimer);vpVisualTimer=setTimeout(vpEnsureExerciseVisual,20)}).observe(app,{childList:true,subtree:true}); vpEnsureExerciseVisual(); }; vpStartVisualObserver();\n"
        "const vpOriginalFetch = window.fetch.bind(window);\n"
        "window.fetch = async (...args) => {\n"
        "  const response = await vpOriginalFetch(...args); const target = String(args[0]?.url || args[0] || ''); if (!target.includes('app.js')) return response;\n"
        "  const text = await response.text(); let fixed = text.replace('template:renderTemplate', 'template:renderRoutines');\n"
        "  fixed = fixed.replace('${x.animation?.path?`<small>Movimiento guiado</small>`:\"\"}', '${x.animation?.path?`<small>${x.cardio||x.group===\"Cardio\"?\"Imagen de referencia\":\"Movimiento guiado\"}</small>`:\"\"}');\n"
        "  fixed = fixed.replace('<img src=\"./${encodeURI(a.path)}\" alt=\"Movimiento de ${esc(x.name)}\">', '<img data-vp-visual=\"${esc(x.name)}\" src=\"${window.VITALPEAK_ASSET_URL(a.path)}\" alt=\"${x.cardio||x.group===\\\"Cardio\\\"?\\\"Imagen de \\\" : \\\"Movimiento de \\\"}${esc(x.name)}\">');\n"
        "  fixed = fixed.replace('<b>Movimiento guiado</b><span>El GIF queda disponible sin conexión después de verlo una vez.</span>', '<b>${x.cardio||x.group===\"Cardio\"?\"Imagen del ejercicio\":\"Movimiento guiado\"}</b><span>${x.cardio||x.group===\"Cardio\"?\"Referencia visual del ejercicio de cardio.\":\"GIF de técnica del ejercicio.\"}</span>');\n"
        "  fixed = fixed.replace('<img src=\"./${encodeURI(info.animation.path)}\" alt=\"Movimiento de ${esc(info.name)}\">', '<img src=\"${window.VITALPEAK_ASSET_URL(info.animation.path)}\" alt=\"Movimiento de ${esc(info.name)}\">');\n"
        "  return new Response(fixed, { status: response.status, statusText: response.statusText, headers: response.headers });\n"
        "};\n"
        "document.addEventListener('error',e=>{ const img=e.target; if(!(img instanceof HTMLImageElement))return; const name=img.dataset?.vpVisual; if(!name)return; const visual=window.VITALPEAK_VISUAL(name); if(visual?.fallback&&img.src!==window.VITALPEAK_ASSET_URL(visual.fallback))img.src=window.VITALPEAK_ASSET_URL(visual.fallback); },true);\n"
        "for (const src of ['./routine-enhancements.js?v=36', './routine-muscle-filter.js?v=36', './calendar-mobile.js?v=36', './training-intelligence.js?v=36', './routine-navigation-fix.js?v=36', './routines-accordion.js?v=36']) { const script = document.createElement('script'); script.src = src; script.defer = true; script.onerror = () => console.warn('VitalPeak: mejora opcional no cargada', src); document.head.appendChild(script); }\n",
        encoding="utf-8",
    )
    visual_count = sum(bool(x["animation"]) for x in exercises)
    gif_count = sum(x.get("animation", {}).get("kind") == "gif" for x in exercises)
    image_count = sum(x.get("animation", {}).get("kind") == "image" for x in exercises)
    print(f"Catálogo móvil: {len(TEMPLATES)} rutinas, {len(exercises)} ejercicios, {visual_count} con recurso visual ({gif_count} GIF, {image_count} imágenes).")


if __name__ == "__main__":
    main()
