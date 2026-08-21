"""Ilustraciones de catálogo por ejercicio (VitalPeak)."""

from __future__ import annotations

import hashlib
from pathlib import Path
from typing import Optional

from PIL import Image, ImageDraw, ImageFont

from app.exercise_catalog import infer_grupo, load_base_exercises

OUT_DIR = Path("exercise_images/catalog")

GROUP_COLORS = {
    "Pecho": ((230, 244, 248), (58, 168, 153), (20, 40, 48)),
    "Espalda": ((232, 240, 248), (74, 124, 155), (20, 40, 48)),
    "Hombro": ((245, 238, 248), (139, 107, 174), (20, 40, 48)),
    "Pierna": ((236, 245, 232), (107, 143, 113), (20, 40, 48)),
    "Brazo": ((248, 236, 236), (184, 92, 110), (20, 40, 48)),
    "Core": ((245, 242, 232), (196, 154, 74), (20, 40, 48)),
    "Otro": ((240, 244, 242), (106, 127, 136), (20, 40, 48)),
}


def slugify(name: str) -> str:
    s = "".join(ch if ch.isalnum() else "_" for ch in name).strip("_")
    while "__" in s:
        s = s.replace("__", "_")
    return (s[:90] or "ejercicio")


def catalog_image_path(name: str) -> Path:
    return OUT_DIR / f"{slugify(name)}.png"


def default_catalog_image(name: str) -> Optional[str]:
    p = catalog_image_path(name)
    if p.is_file():
        return p.as_posix()
    return None


def _font(size: int, bold: bool = False) -> ImageFont.ImageFont:
    candidates = []
    if bold:
        candidates += [
            "C:/Windows/Fonts/arialbd.ttf",
            "C:/Windows/Fonts/segoeuib.ttf",
            "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
        ]
    candidates += [
        "C:/Windows/Fonts/arial.ttf",
        "C:/Windows/Fonts/segoeui.ttf",
        "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
    ]
    for p in candidates:
        if Path(p).is_file():
            return ImageFont.truetype(p, size)
    return ImageFont.load_default()


def _wrap(draw: ImageDraw.ImageDraw, text: str, font: ImageFont.ImageFont, max_w: int) -> list[str]:
    words = text.split()
    lines: list[str] = []
    cur = ""
    for w in words:
        trial = f"{cur} {w}".strip()
        if draw.textlength(trial, font=font) <= max_w:
            cur = trial
        else:
            if cur:
                lines.append(cur)
            cur = w
    if cur:
        lines.append(cur)
    return lines or [text]


def _draw_figure(draw: ImageDraw.ImageDraw, grupo: str, accent: tuple, cx: int, cy: int, seed: int) -> None:
    rng = (seed % 7) / 7.0
    if grupo == "Pecho":
        draw.ellipse([cx - 70, cy - 50, cx + 70, cy + 55], outline=accent, width=5)
        draw.line([cx - 95, cy, cx + 95, cy], fill=accent, width=6)
        draw.ellipse([cx - 18, cy - 18, cx + 18, cy + 18], fill=accent)
    elif grupo == "Espalda":
        draw.arc([cx - 80, cy - 60, cx + 80, cy + 40], 200, 340, fill=accent, width=6)
        draw.line([cx, cy - 55, cx, cy + 70], fill=accent, width=5)
        draw.line([cx - 55, cy + 20, cx + 55, cy + 20], fill=accent, width=4)
    elif grupo == "Hombro":
        draw.arc([cx - 90, cy - 30, cx + 90, cy + 90], 200, 340, fill=accent, width=6)
        draw.ellipse([cx - 12, cy - 55, cx + 12, cy - 30], fill=accent)
        draw.line([cx - 70, cy + 10, cx + 70, cy + 10], fill=accent, width=5)
    elif grupo == "Pierna":
        draw.line([cx - 25, cy - 60, cx - 35, cy + 70], fill=accent, width=7)
        draw.line([cx + 25, cy - 60, cx + 35, cy + 70], fill=accent, width=7)
        draw.line([cx - 40, cy + 70, cx - 10, cy + 70], fill=accent, width=5)
        draw.line([cx + 10, cy + 70, cx + 40, cy + 70], fill=accent, width=5)
        draw.ellipse([cx - 18, cy - 85, cx + 18, cy - 50], outline=accent, width=4)
    elif grupo == "Brazo":
        draw.arc([cx - 40, cy - 70, cx + 80, cy + 40], 40, 220, fill=accent, width=7)
        draw.ellipse([cx + 55, cy - 25, cx + 85, cy + 5], fill=accent)
        draw.line([cx - 30, cy + 50, cx + 40, cy + 55], fill=accent, width=5)
    elif grupo == "Core":
        draw.rounded_rectangle([cx - 45, cy - 55, cx + 45, cy + 55], radius=18, outline=accent, width=5)
        for i in range(3):
            y = cy - 25 + i * 22
            draw.line([cx - 28, y, cx + 28, y], fill=accent, width=3)
    else:
        draw.ellipse([cx - 60, cy - 60, cx + 60, cy + 60], outline=accent, width=5)
        draw.line([cx - 40, cy, cx + 40, cy], fill=accent, width=4)

    r = 18 + int(rng * 20)
    draw.ellipse([cx + 70, cy - 80, cx + 70 + r, cy - 80 + r], outline=accent, width=3)


def generate_exercise_image(name: str, *, overwrite: bool = False) -> Path:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    out = catalog_image_path(name)
    if out.exists() and not overwrite:
        return out

    grupo = infer_grupo(name)
    bg, accent, ink = GROUP_COLORS.get(grupo, GROUP_COLORS["Otro"])
    seed = int(hashlib.md5(name.encode("utf-8")).hexdigest()[:8], 16)

    W, H = 720, 720
    img = Image.new("RGB", (W, H), bg)
    draw = ImageDraw.Draw(img)

    for i in range(6):
        alpha_shift = 8 + (seed + i * 17) % 18
        c = tuple(min(255, x + alpha_shift) for x in bg)
        draw.ellipse([-80 + i * 40, -40 + i * 30, 280 + i * 50, 260 + i * 40], fill=c)

    draw.rectangle([0, 0, W, 64], fill=(20, 40, 48))
    draw.rectangle([0, 64, W, 70], fill=accent)
    draw.text((28, 16), "VitalPeak", font=_font(28, bold=True), fill=(214, 240, 236))
    draw.text((W - 28, 22), grupo.upper(), font=_font(18, bold=True), fill=accent, anchor="rt")

    _draw_figure(draw, grupo, accent, W // 2, 290, seed)

    title_font = _font(34, bold=True)
    lines = _wrap(draw, name, title_font, W - 80)
    y = 470
    for line in lines[:4]:
        draw.text((W // 2, y), line, font=title_font, fill=ink, anchor="ma")
        y += 42

    draw.rounded_rectangle([40, H - 70, W - 40, H - 28], radius=14, fill=(255, 255, 255))
    draw.text(
        (W // 2, H - 49),
        "Referencia de ejercicio",
        font=_font(18),
        fill=(106, 127, 136),
        anchor="mm",
    )

    img.save(out, format="PNG", optimize=True)
    return out


def generate_all_catalog_images(*, overwrite: bool = False) -> list[Path]:
    return [generate_exercise_image(n, overwrite=overwrite) for n in load_base_exercises()]
