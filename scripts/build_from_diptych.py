"""Parte un diptych horizontal en 2 frames y monta el GIF de secuencia."""

from __future__ import annotations

import sys
from pathlib import Path

from PIL import Image

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from app.catalog_images import slugify
from scripts.build_movement_gif import ASSETS, SIZE, build_gif


def split_diptych(dip_name: str, out_a: str, out_b: str) -> tuple[str, str]:
    dip = Image.open(ASSETS / dip_name).convert("RGB")
    w, h = dip.size
    mid = w // 2
    left = dip.crop((0, 0, mid, h))
    right = dip.crop((mid, 0, w, h))

    def sq(im: Image.Image) -> Image.Image:
        iw, ih = im.size
        side = min(iw, ih)
        l = (iw - side) // 2
        t = (ih - side) // 2
        return im.crop((l, t, l + side, t + side)).resize(SIZE, Image.Resampling.LANCZOS)

    a, b = sq(left), sq(right)
    a.save(ASSETS / out_a)
    b.save(ASSETS / out_b)
    return out_a, out_b


def build_from_diptych(
    exercise_name: str,
    dip_file: str,
    tips: list[tuple[str, str]],
) -> Path:
    a, b = split_diptych(dip_file, f"_tmp_a_{slugify(exercise_name)[:40]}.png", f"_tmp_b_{slugify(exercise_name)[:40]}.png")
    # ciclo: inicio -> fondo -> inicio
    return build_gif(
        slugify(exercise_name),
        [a, b, a],
        label=exercise_name,
        tips=tips,
    )


if __name__ == "__main__":
    print("helper ok")
