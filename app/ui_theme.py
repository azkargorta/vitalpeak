"""VitalPeak UI theme — marca, tipografía y layout base (Streamlit).

Dirección visual: atlético, luz de día, tinta profunda + acento lima.
Evita el look genérico Streamlit (morado, flat blanco, menú interminable).
"""

from __future__ import annotations

import streamlit as st

# Paleta
INK = "#0B1F2A"
INK_SOFT = "#1A3340"
ACCENT = "#4DB8A8"  # teal suave (legible sobre oscuro y claro)
ACCENT_DARK = "#3A9A8C"
SURFACE = "#F3F6F4"
SURFACE_2 = "#E7EEE9"
TEXT = "#12262F"
MUTED = "#5A6F78"


def apply_theme() -> None:
    """Inyecta CSS global una sola vez por sesión de render."""
    st.markdown(
        f"""
<style>
@import url('https://fonts.googleapis.com/css2?family=Barlow+Condensed:wght@600;700;800&family=Manrope:wght@400;500;600;700&display=swap');

:root {{
  --vp-ink: {INK};
  --vp-ink-soft: {INK_SOFT};
  --vp-accent: {ACCENT};
  --vp-accent-dark: {ACCENT_DARK};
  --vp-surface: {SURFACE};
  --vp-surface-2: {SURFACE_2};
  --vp-text: {TEXT};
  --vp-muted: {MUTED};
}}

html, body, [class*="css"] {{
  font-family: 'Manrope', sans-serif;
  color: var(--vp-text);
}}

/* Fondo con atmósfera (no flat) */
.stApp {{
  background:
    radial-gradient(1200px 600px at 10% -10%, rgba(77, 184, 168, 0.18), transparent 55%),
    radial-gradient(900px 500px at 100% 0%, rgba(11, 31, 42, 0.08), transparent 50%),
    linear-gradient(165deg, #F7FAF8 0%, #EAF1EC 45%, #F3F6F4 100%);
  background-attachment: fixed;
}}

/* Ocultar navegación multipágina nativa (usamos menú propio) */
[data-testid="stSidebarNav"] {{
  display: none !important;
}}

section[data-testid="stSidebar"] {{
  background: linear-gradient(180deg, {INK} 0%, {INK_SOFT} 100%);
  border-right: none;
}}
section[data-testid="stSidebar"] * {{
  color: #F4F7F5 !important;
}}
section[data-testid="stSidebar"] .stRadio label {{
  font-family: 'Manrope', sans-serif;
  font-weight: 600;
  letter-spacing: 0.01em;
  padding: 0.35rem 0.2rem;
}}
section[data-testid="stSidebar"] div[role="radiogroup"] label:hover {{
  background: rgba(77, 184, 168, 0.16);
  border-radius: 8px;
}}
section[data-testid="stSidebar"] [data-baseweb="radio"] > div:first-child {{
  background-color: var(--vp-accent) !important;
  border-color: var(--vp-accent) !important;
}}

/* Tipografía de títulos */
h1, h2, h3, .vp-brand, .vp-display {{
  font-family: 'Barlow Condensed', Impact, sans-serif !important;
  letter-spacing: 0.02em;
  text-transform: uppercase;
  color: var(--vp-ink) !important;
}}
h1 {{ font-weight: 800 !important; font-size: 2.6rem !important; line-height: 0.95 !important; }}
h2 {{ font-weight: 700 !important; }}
h3 {{ font-weight: 700 !important; }}

.vp-hero {{
  position: relative;
  overflow: hidden;
  padding: 2.4rem 1.8rem 2.2rem;
  margin: -1rem -1rem 1.5rem -1rem;
  background:
    linear-gradient(115deg, rgba(11,31,42,0.92) 0%, rgba(26,51,64,0.88) 48%, rgba(11,31,42,0.75) 100%),
    repeating-linear-gradient(
      -12deg,
      transparent,
      transparent 12px,
      rgba(77,184,168,0.05) 12px,
      rgba(77,184,168,0.05) 24px
    );
  color: #F7FAF8;
  animation: vpFadeIn 0.7s ease-out;
}}
.vp-hero .vp-brand {{
  color: #7ED4C6 !important;
  font-size: clamp(3rem, 8vw, 5.2rem);
  margin: 0;
  line-height: 0.88;
}}
.vp-hero .vp-kicker {{
  color: rgba(247,250,248,0.72);
  font-size: 0.85rem;
  font-weight: 600;
  letter-spacing: 0.14em;
  text-transform: uppercase;
  margin-bottom: 0.6rem;
}}
.vp-hero .vp-lead {{
  color: rgba(247,250,248,0.88);
  font-size: 1.1rem;
  max-width: 34rem;
  margin: 0.85rem 0 0;
  font-family: 'Manrope', sans-serif;
  text-transform: none;
  letter-spacing: 0;
  font-weight: 500;
  line-height: 1.45;
}}
.vp-hero-panel {{
  margin-top: 1.4rem;
  padding: 1rem 1.1rem;
  border-left: 4px solid var(--vp-accent);
  background: rgba(255,255,255,0.06);
  max-width: 28rem;
  animation: vpSlide 0.85s ease-out;
}}
.vp-hero-panel strong {{
  color: #9FE0D4;
  font-family: 'Barlow Condensed', sans-serif;
  font-size: 1.35rem;
  letter-spacing: 0.04em;
  text-transform: uppercase;
}}

.vp-section-label {{
  font-family: 'Manrope', sans-serif;
  font-size: 0.75rem;
  font-weight: 700;
  letter-spacing: 0.12em;
  text-transform: uppercase;
  color: var(--vp-muted);
  margin: 1.2rem 0 0.4rem;
}}

.vp-action-row {{
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(160px, 1fr));
  gap: 0.75rem;
  margin: 0.5rem 0 1.25rem;
}}
.vp-chip {{
  display: block;
  padding: 0.9rem 1rem;
  background: rgba(11, 31, 42, 0.92);
  color: #F7FAF8 !important;
  border-radius: 4px;
  text-decoration: none !important;
  font-weight: 700;
  font-family: 'Barlow Condensed', sans-serif;
  letter-spacing: 0.06em;
  text-transform: uppercase;
  font-size: 1.15rem;
  transition: transform 0.2s ease, background 0.2s ease;
}}
.vp-chip:hover {{
  transform: translateY(-2px);
  background: #152B35;
}}
.vp-chip span {{
  display: block;
  font-family: 'Manrope', sans-serif;
  font-size: 0.72rem;
  font-weight: 500;
  letter-spacing: 0;
  text-transform: none;
  color: rgba(247,250,248,0.65);
  margin-top: 0.25rem;
}}

.vp-today {{
  background: linear-gradient(135deg, #FFFFFF 0%, var(--vp-surface-2) 100%);
  border: 1px solid rgba(11,31,42,0.08);
  border-radius: 6px;
  padding: 1.25rem 1.4rem;
  margin-bottom: 1rem;
  animation: vpFadeIn 0.55s ease-out;
}}
.vp-today h3 {{
  margin-top: 0 !important;
}}

div.stButton > button[kind="primary"],
div.stButton > button[data-testid="baseButton-primary"] {{
  background: var(--vp-ink) !important;
  color: #E8FFFB !important;
  border: 1px solid var(--vp-accent) !important;
  font-family: 'Barlow Condensed', sans-serif !important;
  font-weight: 700 !important;
  letter-spacing: 0.06em;
  text-transform: uppercase;
  font-size: 1.05rem !important;
}}
div.stButton > button {{
  border-radius: 4px !important;
  font-family: 'Manrope', sans-serif;
  font-weight: 600;
}}

[data-testid="stMetric"] {{
  background: rgba(255,255,255,0.72);
  border: 1px solid rgba(11,31,42,0.06);
  padding: 0.75rem 0.9rem;
  border-radius: 6px;
}}

hr {{
  border: none;
  border-top: 1px solid rgba(11,31,42,0.1);
  margin: 1.4rem 0;
}}

@keyframes vpFadeIn {{
  from {{ opacity: 0; }}
  to {{ opacity: 1; }}
}}
@keyframes vpSlide {{
  from {{ opacity: 0; transform: translateY(12px); }}
  to {{ opacity: 1; transform: translateY(0); }}
}}

@media (max-width: 768px) {{
  .vp-hero {{
    margin: -0.5rem -0.5rem 1rem -0.5rem;
    padding: 1.6rem 1.1rem 1.5rem;
  }}
  .vp-hero .vp-brand {{ font-size: 2.8rem; }}
}}
</style>
        """,
        unsafe_allow_html=True,
    )


def render_brand_hero(
    *,
    title: str = "VitalPeak",
    kicker: str = "Entrenamiento · Salud · Progreso",
    lead: str = "",
    panel_title: str = "",
    panel_body: str = "",
) -> None:
    panel = ""
    if panel_title or panel_body:
        panel = f"""
        <div class="vp-hero-panel">
          <strong>{panel_title}</strong>
          <div style="margin-top:0.35rem;font-family:Manrope,sans-serif;text-transform:none;letter-spacing:0;color:rgba(247,250,248,0.85);font-size:0.95rem;line-height:1.4;">{panel_body}</div>
        </div>
        """
    st.markdown(
        f"""
        <div class="vp-hero">
          <div class="vp-kicker">{kicker}</div>
          <div class="vp-brand">{title}</div>
          <p class="vp-lead">{lead}</p>
          {panel}
        </div>
        """,
        unsafe_allow_html=True,
    )


def section_label(text: str) -> None:
    st.markdown(f'<div class="vp-section-label">{text}</div>', unsafe_allow_html=True)
