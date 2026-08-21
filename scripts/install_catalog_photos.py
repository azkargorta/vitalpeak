import json
import shutil
from pathlib import Path

from app.exercises import get_exercise_meta, resolve_exercise_image_path

assets = Path(
    r"C:\Users\azkargorta.unai\.cursor\projects"
    r"\c-Users-azkargorta-unai-OneDrive-SMC-Corporation-Global-Documentos-GitHub-vitalpeak"
    r"\assets"
)
catalog = Path("exercise_images/catalog")
rows = json.loads((catalog / "_gen_map.json").read_text(encoding="utf-8"))

ok, missing = 0, []
for r in rows:
    src = assets / f"ref_{r['i']:02d}.png"
    dst = catalog / f"{r['slug']}.png"
    if not src.is_file():
        missing.append(r["i"])
        continue
    shutil.copy2(src, dst)
    ok += 1

print(f"copied={ok} missing={missing}")

for name in [
    "Jalón de triceps en polea alta",
    "Press con barra en banco horizontal",
    "Curl predicador con barra Z",
]:
    m = get_exercise_meta("azkardurant", name)
    p = resolve_exercise_image_path(m.get("imagen"))
    size = p.stat().st_size if p else 0
    print(f"{name} -> {m.get('imagen')} bytes={size}")
