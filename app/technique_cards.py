from __future__ import annotations

from typing import Any, Dict, List

import streamlit as st

from .datastore import ensure_user, save_user


Card = Dict[str, Any]


def _lines_to_list(text: str) -> List[str]:
    out: List[str] = []
    for raw in (text or "").splitlines():
        s = raw.strip().lstrip("-•").strip()
        if s:
            out.append(s)
    return out


def _list_to_lines(items: List[str]) -> str:
    return "\n".join([str(x).strip() for x in (items or []) if str(x).strip()])


def default_card_for(exercise_name: str) -> Card:
    """Ficha técnica estándar. Puedes ampliarla/editarla desde la UI."""
    name = (exercise_name or "").strip().lower()

    # Defaults iniciales (3 ejercicios base). El resto usa una plantilla genérica.
    if "sentadilla" in name or name == "squat":
        return {
            "setup": [
                "Coloca los pies a anchura de hombros y punta ligeramente abierta.",
                "Inhala y haz brace (abdomen firme) antes de iniciar.",
                "Mantén el pie completo apoyado (talón y metatarso).",
                "Mirada al frente, espalda neutra y pecho estable.",
            ],
            "execution": [
                "Baja controlado llevando la cadera atrás y abajo.",
                "Rodillas siguen la línea del pie (sin colapsar hacia dentro).",
                "Mantén la tensión del tronco durante todo el recorrido.",
                "Sube empujando el suelo: cadera y pecho suben a la vez.",
            ],
            "quick_cues": [
                "Empuja el suelo.",
                "Costillas abajo + brace.",
                "Rodillas hacia fuera (siguen el pie).",
            ],
            "common_errors": [
                {"error": "Rodillas colapsan hacia dentro", "fix": "Abre ligeramente las puntas y piensa 'rodillas siguen el pie'"},
                {"error": "Pierdes talón / te vas a la punta", "fix": "Mantén 'pie trípode' y ajusta la profundidad"},
                {"error": "Te desplomas de tronco", "fix": "Brace antes de bajar y controla la velocidad"},
            ],
            "should_feel": ["Cuádriceps", "Glúteo", "Abdomen (estabilidad)"],
            "should_not_feel": ["Dolor agudo en rodilla", "Pinzazo en cadera", "Dolor lumbar"],
        }

    if "peso muerto" in name or "deadlift" in name:
        return {
            "setup": [
                "Pies a la anchura de cadera; barra cerca de las tibias.",
                "Agarra la barra y 'rompe' el suelo con los pies (tensión).",
                "Espalda neutra; hombros ligeramente por delante de la barra.",
                "Inhala y brace antes de despegar.",
            ],
            "execution": [
                "Empuja el suelo y sube con cadera y pecho a la vez.",
                "Mantén la barra pegada al cuerpo todo el recorrido.",
                "Pasa la rodilla y extiende la cadera (glúteo) para bloquear.",
                "Baja con bisagra de cadera: cadera atrás, barra cerca.",
            ],
            "quick_cues": [
                "Quita la holgura.",
                "Barra pegada.",
                "Bisagra de cadera.",
            ],
            "common_errors": [
                {"error": "Redondeas la espalda", "fix": "Menos peso, brace y lleva el pecho 'orgulloso'"},
                {"error": "La barra se separa", "fix": "Activa dorsales y roza tibias/muslos"},
                {"error": "Hiperextiendes arriba", "fix": "Bloquea con glúteo; costillas abajo"},
            ],
            "should_feel": ["Glúteo", "Isquios", "Espalda alta/dorsales (tensión)"] ,
            "should_not_feel": ["Dolor lumbar", "Pinzazo en espalda", "Dolor agudo en rodilla"],
        }

    if "press" in name and "banca" in name or "bench" in name:
        return {
            "setup": [
                "Ojos debajo de la barra; pies firmes en el suelo.",
                "Escápulas atrás y abajo (pecho arriba).",
                "Agarre estable; muñeca sobre codo.",
                "Inhala y brace ligero; glúteos siempre en el banco.",
            ],
            "execution": [
                "Baja controlado hacia la parte media del pecho.",
                "Codos en un ángulo cómodo (≈45–70°), sin abrirlos en exceso.",
                "Pausa suave y empuja la barra arriba con trayectoria estable.",
                "Mantén hombros 'metidos' y escápulas fijas.",
            ],
            "quick_cues": [
                "Rompe la barra (tensión).",
                "Escápulas atrás y abajo.",
                "Muñeca sobre codo.",
            ],
            "common_errors": [
                {"error": "Hombros se elevan al subir", "fix": "Re-coloca escápulas y reduce peso"},
                {"error": "Muñeca doblada hacia atrás", "fix": "Cierra el puño y alinea muñeca con antebrazo"},
                {"error": "Rebote en el pecho", "fix": "Baja más controlado y pausa ligera"},
            ],
            "should_feel": ["Pectoral", "Tríceps", "Deltoides anterior (secundario)"],
            "should_not_feel": ["Dolor anterior de hombro", "Pinzazo en codo", "Dolor de muñeca"],
        }

    # Plantilla genérica
    return {
        "setup": ["Ajusta la posición inicial para que sea estable y repetible."],
        "execution": ["Recorre el movimiento controlado manteniendo tensión."],
        "quick_cues": ["Control + tensión.", "Rango estable."],
        "common_errors": [
            {"error": "Pierdes la postura", "fix": "Reduce carga y prioriza control"},
            {"error": "Rango inconsistente", "fix": "Repite el mismo recorrido en cada rep"},
            {"error": "Vas con prisa", "fix": "Baja controlado y acelera solo al final"},
        ],
        "should_feel": ["Músculo objetivo"],
        "should_not_feel": ["Dolor articular"],
    }


def get_card(username: str, exercise_name: str) -> Card:
    d = ensure_user(username)
    cards = d.get("technique_cards") or {}
    if isinstance(cards, dict) and exercise_name in cards and isinstance(cards[exercise_name], dict):
        return cards[exercise_name]
    return default_card_for(exercise_name)


def save_card(username: str, exercise_name: str, card: Card) -> None:
    d = ensure_user(username)
    d.setdefault("technique_cards", {})
    d["technique_cards"][exercise_name] = card
    save_user(username, d)


def render_card(card: Card) -> None:
    def section(title: str, items: List[str]):
        st.markdown(f"#### {title}")
        for it in items or []:
            st.markdown(f"- {it}")

    section("Setup", card.get("setup") or [])
    section("Ejecución", card.get("execution") or [])

    st.markdown("#### Cues rápidos")
    cues = card.get("quick_cues") or []
    if cues:
        st.info(" · ".join([c for c in cues if str(c).strip()]))
    else:
        st.caption("(Sin cues)")

    st.markdown("#### Errores comunes (y corrección)")
    errs = card.get("common_errors") or []
    for e in errs:
        if not isinstance(e, dict):
            continue
        err = (e.get("error") or "").strip()
        fix = (e.get("fix") or "").strip()
        if err or fix:
            st.markdown(f"- **{err or 'Error'}** → {fix or 'Corrección'}")

    section("Qué debería sentir", card.get("should_feel") or [])
    section("Qué NO debería sentir", card.get("should_not_feel") or [])


def render_card_editor(username: str, exercise_name: str, *, initial: Card) -> None:
    st.markdown("#### Editar ficha")
    st.caption("Formato recomendado: Setup/Ejecución 3–5 bullets, Cues 2–3, Errores 3.")

    with st.form(f"tech_card_form_{exercise_name}", clear_on_submit=False):
        setup = st.text_area("Setup (una línea = 1 bullet)", value=_list_to_lines(initial.get("setup") or []), height=120)
        execution = st.text_area("Ejecución (una línea = 1 bullet)", value=_list_to_lines(initial.get("execution") or []), height=120)
        quick_cues = st.text_area("Cues rápidos (2–3 frases, una por línea)", value=_list_to_lines(initial.get("quick_cues") or []), height=90)

        st.markdown("**Errores comunes (3) + corrección**")
        errs = initial.get("common_errors") or []
        # Aseguramos 3 filas
        rows = []
        for i in range(3):
            base = errs[i] if i < len(errs) and isinstance(errs[i], dict) else {"error": "", "fix": ""}
            c1, c2 = st.columns(2)
            with c1:
                err = st.text_input(f"Error #{i+1}", value=str(base.get("error") or ""), key=f"err_{exercise_name}_{i}")
            with c2:
                fix = st.text_input(f"Corrección #{i+1}", value=str(base.get("fix") or ""), key=f"fix_{exercise_name}_{i}")
            rows.append({"error": err.strip(), "fix": fix.strip()})

        should_feel = st.text_area("Qué debería sentir (músculos objetivo)", value=_list_to_lines(initial.get("should_feel") or []), height=90)
        should_not_feel = st.text_area("Qué NO debería sentir (dolor/articulación)", value=_list_to_lines(initial.get("should_not_feel") or []), height=90)

        colA, colB = st.columns([1, 1])
        submit = colA.form_submit_button("Guardar ficha", use_container_width=True)
        reset = colB.form_submit_button("Restaurar plantilla", use_container_width=True)

    if reset:
        save_card(username, exercise_name, default_card_for(exercise_name))
        st.success("Plantilla restaurada.")
        st.rerun()

    if submit:
        new_card: Card = {
            "setup": _lines_to_list(setup)[:5],
            "execution": _lines_to_list(execution)[:5],
            "quick_cues": _lines_to_list(quick_cues)[:3],
            "common_errors": rows[:3],
            "should_feel": _lines_to_list(should_feel)[:6],
            "should_not_feel": _lines_to_list(should_not_feel)[:6],
        }
        save_card(username, exercise_name, new_card)
        st.success("Ficha guardada.")
        st.rerun()
