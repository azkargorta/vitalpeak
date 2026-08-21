"""CLI: genera ilustraciones de catálogo."""

from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from app.catalog_images import OUT_DIR, generate_all_catalog_images

if __name__ == "__main__":
    paths = generate_all_catalog_images(overwrite="--overwrite" in sys.argv)
    print(f"Generadas {len(paths)} imagenes en {OUT_DIR.resolve()}")
