"""Secuencias de movimiento por ejercicio (GIF + pasos).

Estructura:
  exercise_images/sequences/<slug>/
    movimiento.gif
    01_*.png, 02_*.png, 03_*.png  (opcional)
    meta.json  (opcional)
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import List, Optional

from app.catalog_images import slugify

SEQUENCES_DIR = Path("exercise_images/sequences")

# Alias: varios nombres de ejercicio → misma carpeta
ALIASES: dict[str, str] = {
    "press con barra en banco horizontal": "press_banca",
    "press banca": "press_banca",
}


def _folder_for(exercise_name: str) -> Path:
    key = (exercise_name or "").strip().lower()
    if key in ALIASES:
        return SEQUENCES_DIR / ALIASES[key]
    # carpeta legacy press_banca
    if any(
        k in key
        for k in (
            "press con barra en banco horizontal",
            "banco horizontal",
        )
    ) and "inclin" not in key and "mancuerna" not in key and "estrecho" not in key:
        legacy = SEQUENCES_DIR / "press_banca"
        if legacy.is_dir():
            return legacy
    return SEQUENCES_DIR / slugify(exercise_name)


def _load_meta(folder: Path) -> dict:
    p = folder / "meta.json"
    if p.is_file():
        try:
            return json.loads(p.read_text(encoding="utf-8"))
        except Exception:
            pass
    return {}


def get_movement_sequence(exercise_name: str) -> Optional[dict]:
    """Devuelve {id, label, gif, steps} o None."""
    folder = _folder_for(exercise_name)
    if not folder.is_dir():
        return None

    meta = _load_meta(folder)
    gif = folder / "movimiento.gif"
    steps: List[dict] = []

    # Pasos: meta.steps o PNG numerados
    meta_steps = meta.get("steps") or []
    if meta_steps:
        for s in meta_steps:
            fp = folder / s.get("file", "")
            if fp.is_file():
                steps.append(
                    {
                        "title": s.get("title") or fp.stem,
                        "tip": s.get("tip") or "",
                        "path": fp.as_posix(),
                    }
                )
    else:
        pngs = sorted(folder.glob("0*.png"))
        defaults = [
            ("1 · Inicio", "Posición inicial."),
            ("2 · Fondo", "Punto más bajo del movimiento."),
            ("3 · Empuje", "Vuelta a la posición alta."),
        ]
        for i, fp in enumerate(pngs[:3]):
            title, tip = defaults[i] if i < len(defaults) else (fp.stem, "")
            steps.append({"title": title, "tip": tip, "path": fp.as_posix()})

    if not gif.is_file() and not steps:
        return None

    label = meta.get("label") or exercise_name
    return {
        "id": folder.name,
        "label": label,
        "gif": gif.as_posix() if gif.is_file() else None,
        "steps": steps,
    }


def list_sequence_ids() -> List[str]:
    if not SEQUENCES_DIR.is_dir():
        return []
    return sorted(
        p.name
        for p in SEQUENCES_DIR.iterdir()
        if p.is_dir() and (p / "movimiento.gif").is_file()
    )
