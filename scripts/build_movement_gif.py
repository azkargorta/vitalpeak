"""Construye GIF nítido (3 fases) desde assets o carpeta de secuencia."""

from __future__ import annotations

import json
import sys
from pathlib import Path

from PIL import Image

ROOT = Path(__file__).resolve().parents[1]
ASSETS = Path(
    r"C:\Users\azkargorta.unai\.cursor\projects"
    r"\c-Users-azkargorta-unai-OneDrive-SMC-Corporation-Global-Documentos-GitHub-vitalpeak"
    r"\assets"
)
OUT_ROOT = ROOT / "exercise_images" / "sequences"
SIZE = (720, 720)


def _load(path: Path) -> Image.Image:
    im = Image.open(path).convert("RGB")
    w, h = im.size
    side = min(w, h)
    left = (w - side) // 2
    top = (h - side) // 2
    im = im.crop((left, top, left + side, top + side))
    return im.resize(SIZE, Image.Resampling.LANCZOS)


def build_gif(
    slug: str,
    frame_files: list[str],
    *,
    label: str,
    tips: list[tuple[str, str]],
    durations: list[int] | None = None,
) -> Path:
    """frame_files: 3 nombres en ASSETS (inicio, fondo, empuje)."""
    out = OUT_ROOT / slug
    out.mkdir(parents=True, exist_ok=True)

    frames = [_load(ASSETS / n) for n in frame_files]
    names = ["01_inicio.png", "02_fondo.png", "03_empuje.png"]
    for im, name in zip(frames, names):
        im.save(out / name, format="PNG", optimize=True)

    meta_steps = []
    for i, (title, tip) in enumerate(tips[:3]):
        meta_steps.append({"title": title, "tip": tip, "file": names[i]})
    (out / "meta.json").write_text(
        json.dumps({"label": label, "steps": meta_steps}, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )

    # ciclo: inicio → fondo → empuje → inicio
    seq = [
        (frames[0], 750),
        (frames[1], 700),
        (frames[2], 450),
        (frames[0], 550),
    ]
    if durations and len(durations) == 4:
        seq = list(zip(frames + [frames[0]], durations))

    imgs = [im for im, _ in seq]
    durs = [ms for _, ms in seq]
    gif = out / "movimiento.gif"
    imgs[0].save(
        gif,
        save_all=True,
        append_images=imgs[1:],
        duration=durs,
        loop=0,
        optimize=False,
        disposal=2,
    )
    return gif


if __name__ == "__main__":
    # Ejemplo: python scripts/build_movement_gif.py press_banca f1 f2 f3
    if len(sys.argv) < 5:
        print("Uso: build_movement_gif.py <slug> <f1> <f2> <f3>")
        raise SystemExit(1)
    slug, a, b, c = sys.argv[1:5]
    p = build_gif(
        slug,
        [a, b, c],
        label=slug,
        tips=[
            ("1 · Inicio", "Posición inicial."),
            ("2 · Fondo", "Punto más bajo."),
            ("3 · Empuje", "Vuelta arriba."),
        ],
    )
    print(p)
