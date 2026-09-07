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
        animation = {"path": f"exercise-gifs/{folder.name}/movimiento.gif", "steps": info.get("steps", [])}
        result[key(folder.name)] = animation
        if info.get("label"):
            result[key(info["label"])] = animation
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

    payload = {"templates": TEMPLATES, "exercises": exercises}
    bootstrap = r'''
try {
  const custom = JSON.parse(localStorage.getItem('vitalpeak-custom-exercises') || '[]');
  if (Array.isArray(custom)) {
    const names = new Set(window.VITALPEAK_CATALOG.exercises.map(x => String(x.name).toLocaleLowerCase('es')));
    for (const item of custom) {
      const name = String(item?.name || '').trim();
      if (name && !names.has(name.toLocaleLowerCase('es'))) {
        window.VITALPEAK_CATALOG.exercises.push(item);
        names.add(name.toLocaleLowerCase('es'));
      }
    }
  }
} catch {}

window.VP_VIEW_TEMPLATE_ID = null;
window.VP_VIEW_DAY = 0;
document.addEventListener('click', event => {
  const template = event.target.closest?.('[data-action="view-template"]');
  if (template) { window.VP_VIEW_TEMPLATE_ID = template.dataset.template; window.VP_VIEW_DAY = 0; }
  const day = event.target.closest?.('[data-action="select-template-day"]');
  if (day) window.VP_VIEW_DAY = Number(day.dataset.day || 0);
}, true);

function renderTemplate() {
  const esc = value => String(value ?? '').replace(/[&<>"']/g, c => ({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
  const cat = window.VITALPEAK_CATALOG || {templates:[]};
  const t = cat.templates.find(x => x.id === window.VP_VIEW_TEMPLATE_ID) || cat.templates[0];
  if (!t) return '<div class="card empty">No hay rutinas disponibles.</div>';
  const day = Math.min(Number(window.VP_VIEW_DAY || 0), Math.max(0, (t.days || []).length - 1));
  const d = t.days?.[day] || {};
  const list = d.items || [];
  return `<header class="hero"><div class="app-brand"><img src="./apple-touch-icon.png" alt="VitalPeak"><div class="wordmark">Vital<span>Peak</span></div></div><div class="eyebrow">RUTINA</div><h1>${esc(t.name)}</h1><p>${esc(t.description || 'Consulta los días y ejercicios de la rutina.')}</p></header><div class="session-picker">${(t.days || []).map((x,i)=>`<button class="${i===day?'selected':''}" data-action="select-template-day" data-day="${i}">${esc(x.name || `Día ${i+1}`)}</button>`).join('')}</div><div class="card"><h2>${esc(d.name || `Día ${day+1}`)}</h2><div class="planned-workout-list">${list.map((x,i)=>`<div class="planned-exercise"><div><b>${i+1}. ${esc(x.exercise)}</b><div class="muted small">${x.sets || 3} × ${x.reps || 10} · descanso ${x.rest_sec || 90}s</div></div><button class="secondary" data-action="exercise-detail" data-exercise="${esc(x.exercise)}">Ver</button></div>`).join('')}</div></div><button class="primary wide" data-action="activate-template" data-id="${esc(t.id)}">Guardar esta rutina</button><button class="secondary wide" data-route="routines">Volver a rutinas</button>`;
}

for (const src of ['./routine-enhancements.js?v=25', './progress-enhancements.js?v=25']) {
  const script = document.createElement('script');
  script.src = src;
  script.defer = true;
  document.head.appendChild(script);
}
'''
    OUTPUT.write_text(
        "/* Archivo generado desde el catálogo de VitalPeak. No editar a mano. */\n"
        f"window.VITALPEAK_CATALOG = {json.dumps(payload, ensure_ascii=False, separators=(',', ':'))};\n"
        + bootstrap,
        encoding="utf-8",
    )
    print(f"Catálogo móvil: {len(TEMPLATES)} rutinas, {len(exercises)} ejercicios, {sum(bool(x['animation']) for x in exercises)} con GIF.")


if __name__ == "__main__":
    main()
