"""\nScript de migración de datos antiguos a la estructura web.\n- Convierte fechas a ISO (YYYY-MM-DD) si están en DD/MM/AAAA.\n- Convierte rutas de imágenes absolutas a relativas en usuarios_data/<user>/exercise_images/.\n- Mantiene la estructura de JSON.\nEjecutar desde la raíz del proyecto:\n    python -m scripts.migrate_old_data\n"""\nfrom __future__ import annotations
import shutil
from pathlib import Path
from datetime import datetime
import json

BASE = Path(".")
USERS_DIR = BASE / "usuarios_data"


def parse_date_any(s: str) -> str:
    if not s:
        return s
    try:
        return datetime.fromisoformat(s).date().isoformat()
    except Exception:
        pass
    for fmt in ("%d/%m/%Y", "%d-%m-%Y", "%d/%m/%y"):
        try:
            return datetime.strptime(s, fmt).date().isoformat()
        except Exception:
            continue
    return s


def migrate_user(user_json: Path) -> None:
    data = json.loads(user_json.read_text(encoding="utf-8"))
    user = user_json.stem
    changed = False

    for e in data.get("entrenamientos", []):
        d = e.get("date")
        new = parse_date_any(d) if isinstance(d, str) else d
        if new != d:
            e["date"] = new
            changed = True

    for w in data.get("weights", []):
        d = w.get("date")
        new = parse_date_any(d) if isinstance(d, str) else d
        if new != d:
            w["date"] = new
            changed = True

    meta = data.get("exercise_meta", {})
    img_dir = USERS_DIR / user / "exercise_images"
    img_dir.mkdir(parents=True, exist_ok=True)
    for name, m in list(meta.items()):
        img = m.get("imagen")
        if not img:
            continue
        p = Path(img)
        if p.is_absolute() and p.exists():
            target = img_dir / p.name
            try:
                shutil.copy2(p, target)
                rel = str(target.relative_to(BASE))
                m["imagen"] = rel
                changed = True
            except Exception:
                pass

    if changed:
        user_json.write_text(json.dumps(data, indent=2, ensure_ascii=False), encoding="utf-8")
        print(f"Migrado: {user_json.name}")
    else:
        print(f"Sin cambios: {user_json.name}")


def main():
    if not USERS_DIR.exists():
        print("No existe usuarios_data/")
        return
    for j in USERS_DIR.glob("*.json"):
        migrate_user(j)


if __name__ == "__main__":
    main()
