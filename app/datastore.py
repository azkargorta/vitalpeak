from __future__ import annotations
import json
from pathlib import Path
from typing import Dict

BASE_DIR = Path(".")
USERS_DIR = BASE_DIR / "usuarios_data"


def ensure_base_dirs() -> None:
    USERS_DIR.mkdir(parents=True, exist_ok=True)


def user_json_path(username: str) -> Path:
    return USERS_DIR / f"{username}.json"


def ensure_user(username: str) -> Dict:
    ensure_base_dirs()
    path = user_json_path(username)
    if not path.exists():
        data = {
            "password": "",
            "entrenamientos": [],
            "rutinas": [],
            "custom_exercises": [],
            "exercise_meta": {},
            "weights": [],
        }
        path.write_text(json.dumps(data, indent=2, ensure_ascii=False), encoding="utf-8")
    return json.loads(path.read_text(encoding="utf-8"))


def load_user(username: str) -> Dict:
    ensure_base_dirs()
    path = user_json_path(username)
    if not path.exists():
        raise FileNotFoundError(f"User {username} does not exist.")
    return json.loads(path.read_text(encoding="utf-8"))


def save_user(username: str, data: Dict) -> None:
    ensure_base_dirs()
    path = user_json_path(username)
    path.write_text(json.dumps(data, indent=2, ensure_ascii=False), encoding="utf-8")


def register_user(username: str, password: str) -> bool:
    ensure_base_dirs()
    path = user_json_path(username)
    if path.exists():
        return False
    data = ensure_user(username)
    data["password"] = password  # NOTE: plaintext; cambia a hash si lo publicas
    save_user(username, data)
    return True


def authenticate(username: str, password: str) -> bool:
    try:
        data = load_user(username)
    except FileNotFoundError:
        return False
    return data.get("password", "") == password


def exercise_image_dir(username: str) -> Path:
    d = USERS_DIR / username / "exercise_images"
    d.mkdir(parents=True, exist_ok=True)
    return d
