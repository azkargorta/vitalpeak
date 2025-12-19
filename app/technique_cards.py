from __future__ import annotations

from typing import Dict, Any, List
from .datastore import load_user, save_user


def _normalize_exercise_key(exercise: str) -> str:
    """Stable key for user JSON. Keep it simple: trimmed string."""
    return (exercise or "").strip()


def default_card(exercise: str) -> Dict[str, Any]:
    ex = (exercise or "").strip() or "Ejercicio"
    return {
        "exercise": ex,
        "setup": [
            "Colócate estable y alineado antes de empezar.",
            "Ajusta agarre/apoyo para que muñecas, codos y hombros estén cómodos.",
            "Tensa el core y fija la postura (costillas abajo).",
        ],
        "execution": [
            "Controla el recorrido (2–3 s bajada) y evita rebotes.",
            "Mantén una trayectoria consistente y el cuello neutro.",
            "Exhala al superar la parte más difícil y mantén la tensión.",
        ],
        "quick_cues": [
            "Costillas abajo, core firme.",
            "Muñeca sobre codo, hombros estables.",
        ],
        "common_errors": [
            {"error": "Perder la postura (lumbar se arquea / hombros se elevan).", "fix": "Reduce carga y refuerza core y escápulas; pausa y vuelve a tensar."},
            {"error": "Recorrido inestable (trayectoria serpentea).", "fix": "Baja el peso, controla la bajada y marca puntos de referencia."},
            {"error": "Rebotar o tirar con impulso.", "fix": "Ralentiza la excéntrica y haz una pausa corta en el punto de control."},
        ],
        "should_feel": [
            "Músculos objetivo del ejercicio (tensión localizada).",
            "Trabajo del core como estabilidad.",
        ],
        "should_not_feel": [
            "Dolor punzante en articulaciones.",
            "Hormigueo o dolor irradiado.",
            "Pinzamiento en hombro/rodilla/cadera.",
        ],
    }


def get_card(username: str, exercise: str) -> Dict[str, Any]:
    data = load_user(username) or {}
    cards = data.get("technique_cards") or {}
    key = _normalize_exercise_key(exercise)
    card = cards.get(key)
    if not isinstance(card, dict):
        card = default_card(exercise)
    return card


def save_card(username: str, exercise: str, card: Dict[str, Any]) -> None:
    data = load_user(username) or {}
    cards = data.setdefault("technique_cards", {})
    key = _normalize_exercise_key(exercise)
    cards[key] = card
    save_user(username, data)


def card_to_markdown(card: Dict[str, Any]) -> str:
    def bullets(items: List[str]) -> str:
        return "\n".join([f"- {x}" for x in items if str(x).strip()]) or "- (pendiente)"

    def errors(items: List[Dict[str, str]]) -> str:
        out=[]
        for it in items or []:
            e=str(it.get("error","")).strip()
            f=str(it.get("fix","")).strip()
            if e and f:
                out.append(f"- **Error:** {e}\n  - ✅ **Corrección:** {f}")
            elif e:
                out.append(f"- **Error:** {e}")
        return "\n".join(out) or "- (pendiente)"

    quick = card.get("quick_cues") or []
    quick_text = " — ".join([str(x).strip() for x in quick if str(x).strip()]) or "(pendiente)"

    md = f"""
### {card.get("exercise","Técnica")}

**Setup**
{bullets(card.get("setup") or [])}

**Ejecución**
{bullets(card.get("execution") or [])}

**Cues rápidos**
{quick_text}

**Errores comunes + corrección**
{errors(card.get("common_errors") or [])}

**Qué debería sentir**
{bullets(card.get("should_feel") or [])}

**Qué NO debería sentir**
{bullets(card.get("should_not_feel") or [])}
"""
    return md.strip()
