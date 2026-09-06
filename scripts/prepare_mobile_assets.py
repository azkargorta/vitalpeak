"""Prepara los GIF existentes para la distribución estática de VitalPeak móvil."""

from __future__ import annotations

import shutil
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "exercise_images" / "sequences"
TARGET = ROOT / "mobile" / "exercise-gifs"


def main() -> None:
    for movement in SOURCE.glob("*/movimiento.gif"):
        destination = TARGET / movement.parent.name / movement.name
        destination.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(movement, destination)


if __name__ == "__main__":
    main()
