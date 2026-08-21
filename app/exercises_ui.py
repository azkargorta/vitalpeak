"""UI de detalle de ejercicio — diseño VitalPeak + imágenes."""

from __future__ import annotations

from typing import Any, Dict, Optional

import streamlit as st

from app.exercises import (
    GRUPOS,
    resolve_exercise_image_path,
    save_exercise_meta,
    store_exercise_image,
)


def _fmt_num(v: Any) -> str:
    if v is None or v == "":
        return "—"
    if isinstance(v, float):
        if v == int(v):
            return str(int(v))
        return f"{v:.1f}"
    return str(v)


def render_exercise_detail(
    user: str,
    exercise: str,
    stats: Dict[str, Any],
    *,
    grupo_actual: str,
    imagen_rel: Optional[str],
) -> None:
    """Panel de detalle: stats visuales + grupo + imagen asignable."""
    key_safe = "".join(ch if ch.isalnum() else "_" for ch in exercise)[:80]
    if grupo_actual not in GRUPOS:
        grupo_actual = "Otro"

    st.markdown(
        f"""
<style>
.vp-ex-hero {{
  margin: 0.4rem 0 1rem 0;
  padding: 1.1rem 1.25rem;
  border-radius: 14px;
  background:
    linear-gradient(135deg, rgba(58,168,153,0.14), rgba(20,40,48,0.04)),
    #fff;
  border: 1px solid rgba(20,40,48,0.08);
}}
.vp-ex-hero h2 {{
  margin: 0 !important;
  font-family: 'Barlow Condensed', sans-serif !important;
  font-size: 1.75rem !important;
  font-weight: 800 !important;
  letter-spacing: 0.02em;
  text-transform: uppercase;
  color: #142830 !important;
}}
.vp-ex-chip {{
  display: inline-block;
  margin-top: 0.45rem;
  padding: 0.2rem 0.65rem;
  border-radius: 999px;
  background: #E6F6F3;
  color: #2A4450;
  font-size: 0.78rem;
  font-weight: 600;
}}
.vp-stat-grid {{
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 0.55rem;
  margin: 0.35rem 0 0.85rem 0;
}}
.vp-stat {{
  background: #fff;
  border: 1px solid rgba(20,40,48,0.08);
  border-radius: 12px;
  padding: 0.7rem 0.8rem;
}}
.vp-stat .lbl {{
  font-size: 0.68rem;
  font-weight: 700;
  letter-spacing: 0.06em;
  text-transform: uppercase;
  color: #6A7F88;
}}
.vp-stat .val {{
  font-family: 'Barlow Condensed', sans-serif;
  font-size: 1.45rem;
  font-weight: 700;
  color: #142830;
  line-height: 1.15;
  margin-top: 0.15rem;
}}
.vp-stat .sub {{
  font-size: 0.72rem;
  color: #6A7F88;
  margin-top: 0.1rem;
}}
.vp-img-box {{
  background: #fff;
  border: 1px dashed rgba(58,168,153,0.45);
  border-radius: 14px;
  padding: 0.85rem;
  min-height: 220px;
  display: flex;
  align-items: center;
  justify-content: center;
  text-align: center;
}}
.vp-img-empty {{
  color: #6A7F88;
  font-size: 0.9rem;
}}
</style>
<div class="vp-ex-hero">
  <h2>{exercise}</h2>
  <span class="vp-ex-chip">{grupo_actual}</span>
</div>
        """,
        unsafe_allow_html=True,
    )

    s = stats or {}
    ultimo = s.get("ultimo")
    ultimo_txt = _fmt_num(ultimo) if ultimo else "Sin registros"
    ultimo_sub = ""
    if s.get("ultimo_peso") is not None and s.get("ultimas_reps") is not None and ultimo:
        ultimo_sub = f"{_fmt_num(s.get('ultimo_peso'))} kg × {_fmt_num(s.get('ultimas_reps'))} reps"

    col_stats, col_img = st.columns([1.15, 1], gap="large")

    with col_stats:
        st.markdown("##### Estadísticas")
        st.markdown(
            f"""
<div class="vp-stat-grid">
  <div class="vp-stat"><div class="lbl">Sesiones</div><div class="val">{_fmt_num(s.get('sesiones', 0))}</div></div>
  <div class="vp-stat"><div class="lbl">Series</div><div class="val">{_fmt_num(s.get('series', 0))}</div></div>
  <div class="vp-stat"><div class="lbl">Reps totales</div><div class="val">{_fmt_num(s.get('reps_totales', 0))}</div></div>
  <div class="vp-stat"><div class="lbl">Mejor peso</div><div class="val">{_fmt_num(s.get('mejor_peso', 0))} <span class="sub">kg</span></div></div>
  <div class="vp-stat"><div class="lbl">Mejor 1RM</div><div class="val">{_fmt_num(round(float(s.get('mejor_1rm') or 0), 1))} <span class="sub">kg</span></div></div>
  <div class="vp-stat"><div class="lbl">Último entreno</div><div class="val" style="font-size:1.05rem">{ultimo_txt}</div><div class="sub">{ultimo_sub}</div></div>
</div>
            """,
            unsafe_allow_html=True,
        )

        st.markdown("##### Grupo muscular")
        g1, g2 = st.columns([2, 1])
        with g1:
            grupo_nuevo = st.selectbox(
                "Grupo",
                GRUPOS,
                index=GRUPOS.index(grupo_actual),
                key=f"ex_group_edit_{key_safe}",
                label_visibility="collapsed",
            )
        with g2:
            if st.button("Guardar grupo", use_container_width=True, key=f"ex_save_group_{key_safe}"):
                save_exercise_meta(user, exercise, grupo_nuevo, imagen_rel)
                st.success("Grupo guardado.")
                st.rerun()

    with col_img:
        st.markdown("##### Referencia visual")
        tab_foto, tab_mov = st.tabs(["Foto", "Movimiento"])

        with tab_foto:
            img_path = resolve_exercise_image_path(imagen_rel)

            if img_path:
                st.image(str(img_path), use_container_width=True)
                if st.button("Quitar imagen", use_container_width=True, key=f"ex_remove_img_{key_safe}"):
                    g = st.session_state.get(f"ex_group_edit_{key_safe}", grupo_actual)
                    save_exercise_meta(user, exercise, g, None)
                    st.success("Imagen eliminada.")
                    st.rerun()
            else:
                st.markdown(
                    '<div class="vp-img-box"><div class="vp-img-empty">'
                    "Sin imagen todavía.<br/>Sube una foto o esquema del ejercicio."
                    "</div></div>",
                    unsafe_allow_html=True,
                )

            up = st.file_uploader(
                "PNG, JPG o WEBP",
                type=["png", "jpg", "jpeg", "webp"],
                key=f"ex_img_upload_{key_safe}",
                help="Asigna una imagen a este ejercicio. Se guarda en tu cuenta.",
            )
            if up is not None:
                st.caption(f"Seleccionada: **{up.name}** ({len(up.getvalue()) // 1024} KB)")
                if st.button(
                    "Guardar imagen",
                    type="primary",
                    use_container_width=True,
                    key=f"ex_save_img_{key_safe}",
                ):
                    g = st.session_state.get(f"ex_group_edit_{key_safe}", grupo_actual)
                    rel = store_exercise_image(
                        user,
                        up.name,
                        up.getvalue(),
                        exercise_name=exercise,
                    )
                    save_exercise_meta(user, exercise, g, rel)
                    st.success("Imagen asignada al ejercicio.")
                    st.rerun()

        with tab_mov:
            from app.movement_sequences import get_movement_sequence

            seq = get_movement_sequence(exercise)
            if seq:
                st.caption(f"Movimiento · {seq['label']}")
                if seq.get("gif"):
                    st.image(seq["gif"], use_container_width=True)
                    st.caption("GIF del movimiento (mismo ángulo en todas las fases).")
                with st.expander("Ver pasos uno a uno", expanded=not bool(seq.get("gif"))):
                    steps = seq["steps"]
                    if not steps:
                        st.info("No hay fotogramas todavía.")
                    else:
                        key_step = f"ex_mov_step_{key_safe}"
                        if key_step not in st.session_state:
                            st.session_state[key_step] = 0
                        idx = int(st.session_state[key_step]) % len(steps)
                        step = steps[idx]
                        st.markdown(f"**{step['title']}**")
                        st.caption(step["tip"])
                        st.image(step["path"], use_container_width=True)
                        n1, n2, n3 = st.columns([1, 1, 2])
                        with n1:
                            if st.button("← Anterior", use_container_width=True, key=f"ex_mov_prev_{key_safe}"):
                                st.session_state[key_step] = (idx - 1) % len(steps)
                                st.rerun()
                        with n2:
                            if st.button("Siguiente →", use_container_width=True, key=f"ex_mov_next_{key_safe}"):
                                st.session_state[key_step] = (idx + 1) % len(steps)
                                st.rerun()
                        with n3:
                            st.caption(f"Paso {idx + 1} de {len(steps)}")
            else:
                st.info(
                    "Todavía no hay secuencia de movimiento para este ejercicio. "
                    "Prueba con **Press con barra en banco horizontal**."
                )
