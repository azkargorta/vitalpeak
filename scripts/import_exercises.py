"""
Importador de ejercicios desde datos antiguos.
- Recolecta todos los nombres de ejercicios que existan en usuarios_data/*.json
  (en entrenamientos y en custom_exercises).
- Genera/actualiza data/base_exercises.txt con la lista unificada (únicos, ordenados).
- Opcional: puede insertar los nuevos nombres como personalizados en cada usuario (bulk).
Uso:
    python -m scripts.import_exercises --write-custom true
"""
from __future__ import annotations
import argparse, json
from pathlib import Path

DATA_DIR = Path("data")
BASE_FILE = DATA_DIR / "base_exercises.txt"
USERS_DIR = Path("usuarios_data")

def gather_all_exercises() -> list[str]:
    seen = set()
    ordered = []
    for j in USERS_DIR.glob("*.json"):
        data = json.loads(j.read_text(encoding="utf-8"))
        # entrenamientos
        for e in data.get("entrenamientos", []):
            name = str(e.get("exercise", "")).strip()
            if name and name not in seen:
                seen.add(name); ordered.append(name)
        # custom_exercises
        for name in data.get("custom_exercises", []):
            name = str(name).strip()
            if name and name not in seen:
                seen.add(name); ordered.append(name)
        # exercise_meta keys
        for name in (data.get("exercise_meta", {}) or {}).keys():
            name = str(name).strip()
            if name and name not in seen:
                seen.add(name); ordered.append(name)
    return ordered

def write_base_file(names: list[str]) -> None:
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    header = "# Generado por scripts/import_exercises.py\n# Uno por línea\n"
    BASE_FILE.write_text(header + "\n".join(names) + "\n", encoding="utf-8")

def write_into_users(names: list[str]) -> None:
    for j in USERS_DIR.glob("*.json"):
        data = json.loads(j.read_text(encoding="utf-8"))
        customs = data.get("custom_exercises", [])
        changed = False
        for n in names:
            if n not in customs:
                customs.append(n); changed = True
        if changed:
            data["custom_exercises"] = customs
            j.write_text(json.dumps(data, indent=2, ensure_ascii=False), encoding="utf-8")
            print(f"Actualizado: {j.name}")

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--write-custom", type=str, default="false", help="true/false para insertar en cada usuario")
    args = ap.parse_args()
    names = gather_all_exercises()
    if not names:
        print("No se encontraron ejercicios en usuarios_data/"); return
    write_base_file(names)
    print(f"Escritos {len(names)} ejercicios en {BASE_FILE}")
    if str(args.write_custom).lower() in ("true","1","yes","y"):
        write_into_users(names)

if __name__ == "__main__":
    main()
