"""Monta GIF de press banca nítido (banco simple, sin rack/J-hooks)."""

from __future__ import annotations

from pathlib import Path

from PIL import Image

ASSETS = Path(
    r"C:\Users\azkargorta.unai\.cursor\projects"
    r"\c-Users-azkargorta-unai-OneDrive-SMC-Corporation-Global-Documentos-GitHub-vitalpeak"
    r"\assets"
)
OUT_DIR = Path("exercise_images/sequences/press_banca")
SIZE = (720, 720)


def _load(name: str) -> Image.Image:
    im = Image.open(ASSETS / name).convert("RGB")
    w, h = im.size
    side = min(w, h)
    left = (w - side) // 2
    top = (h - side) // 2
    im = im.crop((left, top, left + side, top + side))
    return im.resize(SIZE, Image.Resampling.LANCZOS)


def main() -> None:
    OUT_DIR.mkdir(parents=True, exist_ok=True)

    # Solo fotogramas sin rack/J-hooks (la IA añade soportes distintos si hay rack)
    top = _load("bench_clean_01.png")
    bottom = _load("bench_clean_03.png")
    mid_up = _load("bench_clean_04.png")

    top.save(OUT_DIR / "01_bloqueo.png", format="PNG", optimize=True)
    bottom.save(OUT_DIR / "02_pecho.png", format="PNG", optimize=True)
    mid_up.save(OUT_DIR / "03_empuje.png", format="PNG", optimize=True)

    # 3 fases nítidas, ritmo natural
    seq: list[tuple[Image.Image, int]] = [
        (top, 800),
        (bottom, 750),
        (mid_up, 500),
        (top, 600),
    ]

    frames = [im for im, _ in seq]
    durations = [ms for _, ms in seq]

    gif_path = OUT_DIR / "movimiento.gif"
    frames[0].save(
        gif_path,
        save_all=True,
        append_images=frames[1:],
        duration=durations,
        loop=0,
        optimize=False,
        disposal=2,
    )
    total_ms = sum(durations)
    print(
        f"gif={gif_path.resolve()} frames={len(frames)} "
        f"cycle_s={total_ms / 1000:.1f} size={gif_path.stat().st_size}"
    )


if __name__ == "__main__":
    main()
