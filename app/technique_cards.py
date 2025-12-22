from __future__ import annotations

from typing import Dict, Any, List

from app.datastore import load_user, save_user


SECTIONS = [
    "setup",
    "execution",
    "quick_cues",
    "common_errors",
    "should_feel",
    "should_not_feel",
]

SECTION_LABELS = {
    "setup": "Setup",
    "execution": "Ejecución",
    "quick_cues": "Cues rápidos",
    "common_errors": "Errores comunes (y corrección)",
    "should_feel": "Qué debería sentir",
    "should_not_feel": "Qué NO debería sentir",
}


def _default_card(exercise_label: str) -> Dict[str, Any]:
    # Plantilla neutra: el usuario puede personalizarla desde la UI
    return {
        "exercise_label": exercise_label,
        "setup": [
            "Ajusta la posición inicial y el equipo antes de empezar.",
            "Coloca el cuerpo estable (pies, pelvis y escápulas/torso según el ejercicio).",
            "Respira y “bloquea” el core antes de la primera repetición.",
        ],
        "execution": [
            "Controla la bajada (fase excéntrica) y evita perder postura.",
            "Mantén la trayectoria estable y el rango de movimiento seguro.",
            "Finaliza con control, sin rebotes ni tirones.",
        ],
        "quick_cues": [
            "“Costillas abajo” y abdomen firme.",
            "“Empuja el suelo” / “aprieta glúteos” según el movimiento.",
        ],
        "common_errors": [
            {"error": "Perder tensión del core", "fix": "Inhala, bloquea abdomen y mantén la pelvis neutra."},
            {"error": "Trayectoria inestable", "fix": "Reduce peso y busca una ruta repetible (fácil de repetir)."},
            {"error": "Rango demasiado agresivo", "fix": "Recorta ROM a un rango sin molestias y progresa poco a poco."},
        ],
        "should_feel": [
            "Músculos objetivo trabajando (fatiga/quemazón muscular controlada).",
        ],
        "should_not_feel": [
            "Dolor articular punzante (hombro/rodilla/espalda).",
            "Hormigueo o dolor irradiado.",
        ],
    }


def get_card(username: str, exercise_id: str, exercise_label: str) -> Dict[str, Any]:
    data = load_user(username) or {}
    cards = data.get("technique_cards", {})
    card = cards.get(exercise_id)
    if isinstance(card, dict):
        # Asegura claves mínimas
        for k in SECTIONS:
            if k not in card:
                card[k] = _default_card(exercise_label)[k]
        return card
    return _default_card(exercise_label)


def save_card(username: str, exercise_id: str, card: Dict[str, Any]) -> None:
    data = load_user(username) or {}
    cards = data.get("technique_cards", {})
    cards[exercise_id] = card
    data["technique_cards"] = cards
    save_user(username, data)


def textarea_to_list(text: str) -> List[str]:
    return [ln.strip() for ln in (text or "").splitlines() if ln.strip()]


def list_to_textarea(items: List[str]) -> str:
    return "\n".join(items or [])
