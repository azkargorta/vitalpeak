"""Creador de Rutinas con IA (OpenAI Cloud u Ollama local).

Configuración local recomendada (.env en la raíz del proyecto):

    OPENAI_API_KEY=ollama
    OPENAI_BASE_URL=http://localhost:11434/v1
    OPENAI_MODEL=qwen2.5:14b

Si Ollama/OpenAI no está disponible, se usa el plan de respaldo (rules_fallback).
"""

from __future__ import annotations

import json
import os
import re
from typing import Any, Dict, List, Optional

import streamlit as st

from app.config import load_env, get_openai_api_key
from app.ai_generator import call_gpt, _get_model
from app.rules_fallback import generate_fallback
from app.pdf_export import rutina_a_pdf_bytes

st.set_page_config(page_title="Creador de Rutinas (IA)", page_icon="💪", layout="wide")
load_env()

# Propagar secrets de Streamlit a env (por si se usa en Cloud)
try:
    if hasattr(st, "secrets"):
        for k in ("OPENAI_API_KEY", "OPENAI_MODEL", "OPENAI_BASE_URL", "OPENAI_API_BASE"):
            if k in st.secrets and not os.getenv(k):
                os.environ[k] = str(st.secrets[k]).strip()
except Exception:
    pass


def _provider_label() -> str:
    base = (os.getenv("OPENAI_BASE_URL") or os.getenv("OPENAI_API_BASE") or "").strip()
    model = _get_model()
    if base and ("11434" in base or "ollama" in base.lower()):
        return f"Ollama local · modelo `{model}`"
    if get_openai_api_key() or os.getenv("OPENAI_API_KEY"):
        return f"OpenAI · modelo `{model}`"
    return "Sin API configurada → se usará plan de respaldo"


def _check_ollama_reachable() -> tuple[bool, str]:
    base = (os.getenv("OPENAI_BASE_URL") or "").rstrip("/")
    if not base or "11434" not in base:
        return True, ""  # no aplica
    try:
        import httpx

        # /v1 → raíz Ollama /api/tags
        root = base.replace("/v1", "")
        r = httpx.get(f"{root}/api/tags", timeout=2.0)
        if r.status_code == 200:
            models = [m.get("name", "") for m in (r.json().get("models") or [])]
            wanted = _get_model()
            # ollama lista "qwen2.5:14b" o "qwen2.5:14b-instruct-q4_K_M" etc.
            ok = any(wanted == n or n.startswith(wanted.split(":")[0]) for n in models) if models else False
            if ok or any(wanted in n for n in models):
                return True, f"Ollama OK. Modelos: {', '.join(models[:6]) or '—'}"
            return False, (
                f"Ollama responde, pero no veo el modelo `{wanted}`. "
                f"Ejecuta: `ollama pull {wanted}`. Disponibles: {', '.join(models) or '(ninguno)'}"
            )
        return False, f"Ollama respondió HTTP {r.status_code}"
    except Exception as e:
        return False, f"No se pudo conectar a Ollama ({e}). Arranca con `ollama serve`."


def _parse_reps_to_int(reps: Any) -> int:
    s = str(reps or "10").strip()
    m = re.search(r"(\d+)", s)
    return int(m.group(1)) if m else 10


def _day_to_routine_items(dia: Dict[str, Any]) -> List[Dict[str, Any]]:
    items = []
    for ej in dia.get("ejercicios") or []:
        if not isinstance(ej, dict):
            continue
        nombre = (ej.get("nombre") or ej.get("ejercicio") or "").strip()
        if not nombre:
            continue
        try:
            sets = int(ej.get("series") or 3)
        except Exception:
            sets = 3
        items.append(
            {
                "exercise": nombre,
                "sets": sets,
                "reps": _parse_reps_to_int(ej.get("reps")),
                "weight": 0.0,
            }
        )
    return items


def _render_plan(plan: Dict[str, Any]) -> None:
    meta = plan.get("meta") or {}
    st.markdown(
        f"**Nivel:** {meta.get('nivel', '—')} · "
        f"**Días:** {meta.get('dias', '—')} · "
        f"**Duración:** {meta.get('duracion_min', '—')} min · "
        f"**Objetivo:** {meta.get('objetivo', '—')}"
    )
    for dia in plan.get("dias") or []:
        with st.expander(dia.get("nombre", "Día"), expanded=True):
            rows = []
            for ej in dia.get("ejercicios") or []:
                if not isinstance(ej, dict):
                    continue
                rows.append(
                    {
                        "Ejercicio": ej.get("nombre", ""),
                        "Series": ej.get("series", ""),
                        "Reps": ej.get("reps", ""),
                        "Descanso": ej.get("descanso", ""),
                        "Intensidad": ej.get("intensidad", ""),
                    }
                )
            if rows:
                st.dataframe(rows, use_container_width=True, hide_index=True)
            if dia.get("notas"):
                st.caption(f"Notas: {dia['notas']}")
    prog = plan.get("progresion") or {}
    if prog:
        st.markdown("#### Progresión")
        st.write(
            f"- Principales: {prog.get('principales', '—')}\n"
            f"- Accesorios: {prog.get('accesorios', '—')}\n"
            f"- Deload (semana): {prog.get('deload_semana', '—')}"
        )


st.title("💪 Creador de Rutinas (IA)")
st.caption(
    "Genera un plan personalizado con Ollama (gratis, local) u OpenAI. "
    "Si la IA falla, se usa un plan de respaldo fiable."
)

prov = _provider_label()
st.info(f"Proveedor activo: **{prov}**")

ollama_ok, ollama_msg = _check_ollama_reachable()
if ollama_msg:
    if ollama_ok:
        st.success(ollama_msg)
    else:
        st.warning(ollama_msg)

with st.expander("Cómo configurar Ollama (gratis)", expanded=not ollama_ok and "11434" in (os.getenv("OPENAI_BASE_URL") or "11434")):
    st.markdown(
        """
1. Instala [Ollama](https://ollama.com) y ábrelo.
2. Descarga un modelo (recomendado):
   ```bash
   ollama pull qwen2.5:14b
   ```
   Si tienes poca RAM (~8 GB), prueba: `ollama pull llama3.1:8b`
3. Crea un archivo `.env` en la raíz del proyecto:
   ```env
   OPENAI_API_KEY=ollama
   OPENAI_BASE_URL=http://localhost:11434/v1
   OPENAI_MODEL=qwen2.5:14b
   ```
4. Reinicia Streamlit (`run.bat` o `streamlit run streamlit_app.py`).
        """
    )

with st.form("form_rutina_ia"):
    col1, col2 = st.columns(2)
    with col1:
        nivel = st.selectbox("Nivel", ["principiante", "intermedio", "avanzado"], index=1)
        dias = st.number_input("Días/semana", min_value=1, max_value=6, value=4, step=1)
        duracion = st.slider("Duración por sesión (min)", min_value=30, max_value=120, value=60, step=5)
        disponibilidad = st.multiselect(
            "Días disponibles",
            ["Lunes", "Martes", "Miércoles", "Jueves", "Viernes", "Sábado", "Domingo"],
            default=["Lunes", "Martes", "Jueves", "Viernes"][: int(dias)],
        )
    with col2:
        objetivo = st.selectbox(
            "Objetivo",
            ["fuerza", "hipertrofia", "resistencia", "mixto"],
            index=1,
        )
        material = st.multiselect(
            "Material disponible",
            ["barra", "mancuernas", "poleas", "máquinas", "banco", "rack", "gimnasio completo", "ninguno"],
            default=["gimnasio completo"],
        )
        split_pref = st.selectbox(
            "Split preferido (opcional)",
            ["", "PPL", "Upper/Lower", "Full Body"],
            index=0,
        )
        limitaciones = st.text_input(
            "Lesiones / limitaciones",
            placeholder="Ej: rodilla derecha, evitar sentadilla profunda",
        )

    comentarios = st.text_area(
        "Detalles extra para personalizar",
        placeholder="Ej: solo mancuernas en casa, quiero más espalda y bíceps, 1 día de pierna…",
        height=100,
    )
    force_fallback = st.checkbox("Forzar plan de respaldo (sin IA)", value=False)
    submitted = st.form_submit_button("Generar rutina", type="primary", use_container_width=True)

if submitted:
    datos_usuario: Dict[str, Any] = {
        "nivel": nivel,
        "dias": int(dias),
        "duracion": int(duracion),
        "duracion_min": int(duracion),
        "objetivo": objetivo,
        "material": material,
        "limitaciones": (limitaciones or "").strip(),
        "disponibilidad": disponibilidad or [],
        "comentarios": (comentarios or "").strip(),
        "ia_detalles": (comentarios or "").strip(),
        "split_pref": split_pref,
    }

    api_configured = bool(get_openai_api_key() or os.getenv("OPENAI_API_KEY") or os.getenv("OPENAI_BASE_URL"))
    data_out: Optional[Dict[str, Any]] = None
    used_fallback = False
    error: Optional[str] = None
    source = ""

    if force_fallback or not api_configured:
        used_fallback = True
        data_out = generate_fallback(datos_usuario)
        source = "Plan de respaldo (sin IA)"
    else:
        with st.spinner(f"Generando con {_get_model()}… (Ollama puede tardar 30 s–2 min)"):
            result = call_gpt(datos_usuario)
        if result.get("ok"):
            data_out = result["data"]
            source = f"IA · {_get_model()}"
        else:
            used_fallback = True
            error = result.get("error", "Error desconocido")
            data_out = generate_fallback(datos_usuario)
            source = "Plan de respaldo (IA falló)"

    st.session_state["ia_last_plan"] = data_out
    st.session_state["ia_last_source"] = source
    st.session_state["ia_last_error"] = error
    st.session_state["ia_last_fallback"] = used_fallback

# Mostrar último plan generado
plan = st.session_state.get("ia_last_plan")
if plan:
    st.subheader("Rutina generada")
    st.caption(f"Origen: {st.session_state.get('ia_last_source', '—')}")
    if st.session_state.get("ia_last_fallback"):
        st.warning("Se usó el plan de respaldo.")
        err = st.session_state.get("ia_last_error")
        if err:
            with st.expander("Detalle del error de IA"):
                st.code(err)

    _render_plan(plan)

    c1, c2, c3 = st.columns(3)
    with c1:
        st.download_button(
            "📥 Descargar JSON",
            data=json.dumps(plan, ensure_ascii=False, indent=2),
            file_name="rutina_ia.json",
            mime="application/json",
            use_container_width=True,
        )
    with c2:
        try:
            pdf_bytes = rutina_a_pdf_bytes(plan)
            st.download_button(
                "📄 Descargar PDF",
                data=pdf_bytes,
                file_name="rutina_ia.pdf",
                mime="application/pdf",
                use_container_width=True,
            )
        except Exception as e:
            st.error(f"No se pudo generar PDF: {e}")

    with c3:
        user = st.session_state.get("user")
        if not user:
            st.caption("Inicia sesión en la app principal para guardar las rutinas en tu cuenta.")
        else:
            if st.button("💾 Guardar días como rutinas", use_container_width=True):
                from app.routines import add_routine, list_routines

                existing = {r.get("name") for r in list_routines(user)}
                saved = 0
                for dia in plan.get("dias") or []:
                    name = str(dia.get("nombre") or "Rutina IA").strip()
                    base_name = name
                    n = 2
                    while name in existing:
                        name = f"{base_name} ({n})"
                        n += 1
                    items = _day_to_routine_items(dia)
                    if not items:
                        continue
                    try:
                        add_routine(user, name, items)
                        existing.add(name)
                        saved += 1
                    except Exception as e:
                        st.error(f"Error guardando '{name}': {e}")
                if saved:
                    st.success(f"Se guardaron {saved} rutina(s) en tu cuenta. Véalas en **📘 Rutinas**.")
                else:
                    st.warning("No se guardó ninguna rutina (días vacíos).")

    with st.expander("Ver JSON completo"):
        st.json(plan)
else:
    st.markdown("Completa el formulario y pulsa **Generar rutina**.")
