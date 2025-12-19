from __future__ import annotations

from typing import List, Dict, Any

import streamlit as st

from .exercises import list_all_exercises
from .technique_cards import get_card, save_card, card_to_markdown
from .technique_animation_component import render_minimal_3d_animation


def _split_lines(text: str) -> List[str]:
    # Accept either bullet list or newline separated.
    lines = []
    for raw in (text or "").splitlines():
        t = raw.strip()
        if t.startswith("-"):
            t = t.lstrip("-").strip()
        if t:
            lines.append(t)
    return lines


def _edit_card_ui(card: Dict[str, Any], *, key_prefix: str) -> Dict[str, Any]:
    st.caption("Estructura estándar (misma para todos los ejercicios). Puedes editar y guardar.")
    colA, colB = st.columns(2)
    with colA:
        setup_txt = st.text_area("Setup (3–5 bullets)", value="\n".join(card.get("setup") or []), height=140, key=f"{key_prefix}_setup")
        exec_txt = st.text_area("Ejecución (3–5 bullets)", value="\n".join(card.get("execution") or []), height=140, key=f"{key_prefix}_exec")
        cues_txt = st.text_area("Cues rápidos (2–3 frases)", value="\n".join(card.get("quick_cues") or []), height=110, key=f"{key_prefix}_cues")
    with colB:
        feel_txt = st.text_area("Qué debería sentir (músculos objetivo)", value="\n".join(card.get("should_feel") or []), height=140, key=f"{key_prefix}_feel")
        notfeel_txt = st.text_area("Qué NO debería sentir (dolor/articulación)", value="\n".join(card.get("should_not_feel") or []), height=140, key=f"{key_prefix}_notfeel")

    st.markdown("**Errores comunes (3) + corrección**")
    errs = card.get("common_errors") or []
    # Ensure exactly 3 rows in UI
    while len(errs) < 3:
        errs.append({"error": "", "fix": ""})
    errs = errs[:3]

    ecols = st.columns(2)
    new_errs = []
    for i in range(3):
        with ecols[0]:
            e = st.text_input(f"Error #{i+1}", value=str(errs[i].get("error","")), key=f"{key_prefix}_err_{i}")
        with ecols[1]:
            f = st.text_input(f"Corrección #{i+1}", value=str(errs[i].get("fix","")), key=f"{key_prefix}_fix_{i}")
        new_errs.append({"error": e.strip(), "fix": f.strip()})

    updated = dict(card)
    updated["setup"] = _split_lines(setup_txt)
    updated["execution"] = _split_lines(exec_txt)
    updated["quick_cues"] = _split_lines(cues_txt)
    updated["common_errors"] = new_errs
    updated["should_feel"] = _split_lines(feel_txt)
    updated["should_not_feel"] = _split_lines(notfeel_txt)
    return updated


def render_technique_page() -> None:
    st.title("🎥 Técnica")

    user = st.session_state.get("user")
    if not user:
        st.info("Inicia sesión para ver la técnica.")
        return

    exercises = list_all_exercises(user)
    if not exercises:
        st.warning("No hay ejercicios disponibles todavía.")
        return

    ex = st.selectbox("Ejercicio", options=exercises, index=0)

    card = get_card(user, ex)

    tab_card, tab_anim = st.tabs(["📄 Tarjeta técnica", "🧍 Mini-animación 3D"])

    with tab_card:
        st.markdown(card_to_markdown(card))

        with st.expander("✍️ Editar y guardar ficha", expanded=False):
            updated = _edit_card_ui(card, key_prefix=f"tc_{ex}")
            if st.button("💾 Guardar ficha", type="primary", use_container_width=True):
                updated["exercise"] = ex
                save_card(user, ex, updated)
                st.success("Ficha guardada.")
                st.rerun()

    with tab_anim:
        # Use cues from the card (2–3), fall back to a couple of defaults if empty
        cues = card.get("quick_cues") or []
        if not cues:
            cues = ["Costillas abajo.", "Controla la trayectoria."]

        st.caption("Plantilla visual reutilizable (mismo estilo para todos). 2 ángulos fijos: frontal + lateral.")
        render_minimal_3d_animation(ex, cues=cues, height=560)

        st.info("Si no se ve la animación: requiere internet para cargar Three.js (CDN).")
