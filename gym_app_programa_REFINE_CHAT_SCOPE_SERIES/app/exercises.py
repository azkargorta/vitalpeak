from __future__ import annotations
from pathlib import Path
from typing import Dict, List, Optional
from .datastore import load_user, save_user, exercise_image_dir

DATA_DIR = Path("data")
BASE_FILE = DATA_DIR / "base_exercises.txt"

def _load_base_from_file() -> List[str]:
    exs: List[str] = []
    if BASE_FILE.exists():
        for line in BASE_FILE.read_text(encoding="utf-8").splitlines():
            line = line.strip()
            if not line or line.startswith("#"):
                continue
            exs.append(line)
    return exs

# Fallback si no hay archivo
DEFAULT_BASE = [
    "Press banca", "Dominadas", "Sentadilla", "Peso muerto",
    "Press militar", "Remo con barra", "Curl bíceps", "Extensión tríceps",
    "Zancadas", "Elevaciones laterales", "Plancha", "Ab wheel",
]

def _base_exercises() -> List[str]:
    file_list = _load_base_from_file()
    return file_list if file_list else DEFAULT_BASE

GRUPOS = ["Pecho", "Espalda", "Hombro", "Pierna", "Brazo", "Core", "Otro"]

def list_all_exercises(username: str) -> List[str]:
    data = load_user(username)
    customs = data.get("custom_exercises", [])
    seen = set()
    merged: List[str] = []
    for name in _base_exercises() + customs:
        if name not in seen:
            seen.add(name)
            merged.append(name)
    return merged


def add_custom_exercise(username: str, name: str) -> None:
    data = load_user(username)
    customs = data.get("custom_exercises", [])
    if name and name not in customs:
        customs.append(name)
        data["custom_exercises"] = customs
        save_user(username, data)


def remove_custom_exercise(username: str, name: str) -> None:
    data = load_user(username)
    customs = data.get("custom_exercises", [])
    if name in customs:
        customs.remove(name)
        data["custom_exercises"] = customs
    meta = data.get("exercise_meta", {})
    if name in meta:
        del meta[name]
        data["exercise_meta"] = meta
    save_user(username, data)


def rename_custom_exercise(username: str, old: str, new: str) -> None:
    data = load_user(username)
    customs = data.get("custom_exercises", [])
    if old in customs and new and new not in customs:
        customs[customs.index(old)] = new
        data["custom_exercises"] = customs
    meta = data.get("exercise_meta", {})
    if old in meta and new not in meta:
        meta[new] = meta.pop(old)
        data["exercise_meta"] = meta
    for e in data.get("entrenamientos", []):
        if e.get("exercise") == old:
            e["exercise"] = new
    save_user(username, data)


def save_exercise_meta(username: str, name: str, grupo: str, imagen_rel: Optional[str]) -> None:
    data = load_user(username)
    meta = data.get("exercise_meta", {})
    meta[name] = {"grupo": grupo, "imagen": imagen_rel}
    data["exercise_meta"] = meta
    save_user(username, data)


def get_exercise_meta(username: str, name: str) -> Dict:
    data = load_user(username)
    meta = data.get("exercise_meta", {})
    return meta.get(name, {"grupo": "Otro", "imagen": None})


def store_exercise_image(username: str, filename: str, content: bytes) -> str:
    d = exercise_image_dir(username)
    safe = "".join(ch for ch in filename if ch.isalnum() or ch in (".", "_", "-", " ")).strip()
    if not safe:
        safe = "image.png"
    path = d / safe
    path.write_bytes(content)
    return str(path.relative_to("."))