"""VitalPeak UI theme — marca, tipografía y layout base (Streamlit).

Dirección: clara, luminosa, atlética. Teal suave sobre fondos claros.
"""

from __future__ import annotations

import streamlit as st

# Paleta
INK = "#142830"
INK_SOFT = "#2A4450"
ACCENT = "#3AA899"
ACCENT_SOFT = "#E6F6F3"
SURFACE = "#FAFCFB"
SURFACE_2 = "#F0F5F3"
TEXT = "#1A2E36"
MUTED = "#6A7F88"
BORDER = "rgba(20, 40, 48, 0.10)"


def apply_theme() -> None:
    """Inyecta CSS global."""
    st.markdown(
        f"""
<style>
@import url('https://fonts.googleapis.com/css2?family=Barlow+Condensed:wght@600;700;800&family=Manrope:wght@400;500;600;700&display=swap');

:root {{
  --vp-ink: {INK};
  --vp-accent: {ACCENT};
  --vp-accent-soft: {ACCENT_SOFT};
  --vp-surface: {SURFACE};
  --vp-text: {TEXT};
  --vp-muted: {MUTED};
  --vp-border: {BORDER};
}}

html, body, [class*="css"] {{
  font-family: 'Manrope', sans-serif;
  color: var(--vp-text);
}}

.stApp {{
  background:
    radial-gradient(900px 420px at 0% 0%, rgba(58, 168, 153, 0.12), transparent 55%),
    radial-gradient(700px 380px at 100% 8%, rgba(20, 40, 48, 0.04), transparent 50%),
    linear-gradient(180deg, #FFFFFF 0%, #F5F9F7 55%, #EEF4F1 100%);
  background-attachment: fixed;
}}

[data-testid="stSidebarNav"] {{
  display: none !important;
}}

/* Sidebar clara */
section[data-testid="stSidebar"] {{
  background: #FFFFFF !important;
  border-right: 1px solid var(--vp-border);
  box-shadow: 4px 0 24px rgba(20, 40, 48, 0.04);
}}
section[data-testid="stSidebar"] > div {{
  background: transparent !important;
}}
section[data-testid="stSidebar"] h1,
section[data-testid="stSidebar"] h2,
section[data-testid="stSidebar"] h3,
section[data-testid="stSidebar"] p,
section[data-testid="stSidebar"] span,
section[data-testid="stSidebar"] label,
section[data-testid="stSidebar"] .stMarkdown {{
  color: var(--vp-ink) !important;
}}
section[data-testid="stSidebar"] [data-testid="stCaption"] {{
  color: var(--vp-muted) !important;
}}

section[data-testid="stSidebar"] .stRadio label {{
  font-family: 'Manrope', sans-serif;
  font-weight: 600;
  color: var(--vp-ink) !important;
  padding: 0.45rem 0.55rem;
  border-radius: 8px;
}}
section[data-testid="stSidebar"] div[role="radiogroup"] label:hover {{
  background: var(--vp-accent-soft);
}}
section[data-testid="stSidebar"] [data-baseweb="radio"] > div:first-child {{
  background-color: var(--vp-accent) !important;
  border-color: var(--vp-accent) !important;
}}

/* Botón Cerrar sesión — siempre visible */
section[data-testid="stSidebar"] div.stButton > button,
section[data-testid="stSidebar"] div.stButton > button[kind="secondary"],
section[data-testid="stSidebar"] button[data-testid="baseButton-secondary"],
section[data-testid="stSidebar"] button[kind="secondary"] {{
  background: var(--vp-accent) !important;
  background-color: var(--vp-accent) !important;
  color: #FFFFFF !important;
  border: none !important;
  border-radius: 8px !important;
  font-family: 'Manrope', sans-serif !important;
  font-weight: 700 !important;
  letter-spacing: 0.02em;
  box-shadow: 0 2px 8px rgba(58, 168, 153, 0.28);
}}
section[data-testid="stSidebar"] div.stButton > button:hover {{
  background: #2F8F82 !important;
  background-color: #2F8F82 !important;
  color: #FFFFFF !important;
}}
section[data-testid="stSidebar"] div.stButton > button p,
section[data-testid="stSidebar"] div.stButton > button span {{
  color: #FFFFFF !important;
}}

/* Tipografía */
h1, h2, h3, .vp-brand, .vp-display {{
  font-family: 'Barlow Condensed', Impact, sans-serif !important;
  letter-spacing: 0.02em;
  text-transform: uppercase;
  color: var(--vp-ink) !important;
}}
h1 {{ font-weight: 800 !important; font-size: 2.45rem !important; line-height: 0.95 !important; }}
h2 {{ font-weight: 700 !important; }}
h3 {{ font-weight: 700 !important; }}

/* Hero más claro y amable */
.vp-hero {{
  position: relative;
  overflow: hidden;
  padding: 2rem 1.75rem 1.85rem;
  margin: -1rem -1rem 1.35rem -1rem;
  background:
    linear-gradient(125deg, #1B3A44 0%, #245560 42%, #2A6B66 100%);
  color: #F7FBFA;
  border-radius: 0 0 18px 18px;
  animation: vpFadeIn 0.65s ease-out;
}}
.vp-hero::after {{
  content: "";
  position: absolute;
  right: -40px;
  top: -40px;
  width: 220px;
  height: 220px;
  border-radius: 50%;
  background: rgba(58, 168, 153, 0.22);
  pointer-events: none;
}}
.vp-hero .vp-brand {{
  color: #FFFFFF !important;
  font-size: clamp(2.7rem, 7vw, 4.6rem);
  margin: 0;
  line-height: 0.9;
  position: relative;
  z-index: 1;
}}
.vp-hero .vp-kicker {{
  color: rgba(255,255,255,0.75);
  font-size: 0.8rem;
  font-weight: 600;
  letter-spacing: 0.14em;
  text-transform: uppercase;
  margin-bottom: 0.5rem;
  position: relative;
  z-index: 1;
}}
.vp-hero .vp-lead {{
  color: rgba(255,255,255,0.9);
  font-size: 1.05rem;
  max-width: 34rem;
  margin: 0.75rem 0 0;
  font-family: 'Manrope', sans-serif;
  text-transform: none;
  letter-spacing: 0;
  font-weight: 500;
  line-height: 1.45;
  position: relative;
  z-index: 1;
}}
.vp-hero-panel {{
  margin-top: 1.2rem;
  padding: 0.95rem 1.05rem;
  border-left: 4px solid #7ED4C6;
  background: rgba(255,255,255,0.12);
  backdrop-filter: blur(6px);
  border-radius: 0 10px 10px 0;
  max-width: 28rem;
  animation: vpSlide 0.8s ease-out;
  position: relative;
  z-index: 1;
}}
.vp-hero-panel strong {{
  color: #B8F0E6;
  font-family: 'Barlow Condensed', sans-serif;
  font-size: 1.3rem;
  letter-spacing: 0.04em;
  text-transform: uppercase;
}}

.vp-section-label {{
  font-family: 'Manrope', sans-serif;
  font-size: 0.72rem;
  font-weight: 700;
  letter-spacing: 0.12em;
  text-transform: uppercase;
  color: var(--vp-muted);
  margin: 1.1rem 0 0.45rem;
}}

.vp-today {{
  background: #FFFFFF;
  border: 1px solid var(--vp-border);
  border-radius: 14px;
  padding: 1.2rem 1.3rem;
  margin-bottom: 1rem;
  box-shadow: 0 8px 28px rgba(20, 40, 48, 0.05);
  animation: vpFadeIn 0.5s ease-out;
}}
.vp-today h3 {{
  margin-top: 0 !important;
}}

/* Botones principales (contenido) */
div.stButton > button[kind="primary"],
div.stButton > button[data-testid="baseButton-primary"] {{
  background: var(--vp-accent) !important;
  color: #FFFFFF !important;
  border: none !important;
  border-radius: 8px !important;
  font-family: 'Manrope', sans-serif !important;
  font-weight: 700 !important;
  box-shadow: 0 2px 10px rgba(58, 168, 153, 0.25);
}}
div.stButton > button[kind="primary"]:hover,
div.stButton > button[data-testid="baseButton-primary"]:hover {{
  background: #2F8F82 !important;
  color: #FFFFFF !important;
}}
div.stButton > button {{
  border-radius: 8px !important;
  font-family: 'Manrope', sans-serif;
  font-weight: 600;
  border: 1px solid var(--vp-border) !important;
  background: #FFFFFF !important;
  color: var(--vp-ink) !important;
}}
div.stButton > button:hover {{
  border-color: var(--vp-accent) !important;
  color: var(--vp-accent) !important;
}}

[data-testid="stMetric"] {{
  background: #FFFFFF;
  border: 1px solid var(--vp-border);
  padding: 0.85rem 1rem;
  border-radius: 12px;
  box-shadow: 0 4px 16px rgba(20, 40, 48, 0.04);
}}

div[data-testid="stExpander"] {{
  background: #FFFFFF;
  border: 1px solid var(--vp-border);
  border-radius: 12px;
}}

hr {{
  border: none;
  border-top: 1px solid var(--vp-border);
  margin: 1.35rem 0;
}}

@keyframes vpFadeIn {{
  from {{ opacity: 0; }}
  to {{ opacity: 1; }}
}}
@keyframes vpSlide {{
  from {{ opacity: 0; transform: translateY(10px); }}
  to {{ opacity: 1; transform: translateY(0); }}
}}

@media (max-width: 768px) {{
  .vp-hero {{
    margin: -0.5rem -0.5rem 1rem -0.5rem;
    padding: 1.5rem 1.1rem 1.4rem;
    border-radius: 0 0 14px 14px;
  }}
  .vp-hero .vp-brand {{ font-size: 2.6rem; }}
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
          <div style="margin-top:0.35rem;font-family:Manrope,sans-serif;text-transform:none;letter-spacing:0;color:rgba(255,255,255,0.9);font-size:0.95rem;line-height:1.4;">{panel_body}</div>
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


# Iconos cortos para menú visual (sin radio)
NAV_META = [
    ("Hoy", "Hoy", "◆"),
    ("Registrar entrenamiento", "Entrenar", "●"),
    ("Plantillas", "Plantillas", "▣"),
    ("Planificar rutinas", "Planificar", "▦"),
    ("Ejercicios y progreso", "Ejercicios", "▲"),
    ("Historial", "Historial", "☰"),
    ("Objetivos", "Objetivos", "◎"),
    ("Peso corporal", "Peso", "○"),
    ("Técnica", "Técnica", "◇"),
    ("Mi cuenta", "Cuenta", "▣"),
]


def render_sidebar_nav(current: str | None) -> str:
    """Menú lateral con botones (más visual que el radio)."""
    st.markdown(
        """
<style>
section[data-testid="stSidebar"] div[data-testid="stVerticalBlock"] > div:has(button[kind="secondary"]),
section[data-testid="stSidebar"] div[data-testid="stVerticalBlock"] > div:has(button[kind="primary"]) {
  margin-bottom: -0.35rem;
}
section[data-testid="stSidebar"] button[kind="secondary"] {
  background: transparent !important;
  border: 1px solid transparent !important;
  color: #142830 !important;
  text-align: left !important;
  justify-content: flex-start !important;
  font-weight: 600 !important;
  border-radius: 10px !important;
  padding: 0.55rem 0.75rem !important;
}
section[data-testid="stSidebar"] button[kind="secondary"]:hover {
  background: #E6F6F3 !important;
  border-color: rgba(58,168,153,0.25) !important;
  color: #142830 !important;
}
section[data-testid="stSidebar"] button[kind="primary"] {
  background: #E6F6F3 !important;
  border: 1px solid #3AA899 !important;
  color: #142830 !important;
  text-align: left !important;
  justify-content: flex-start !important;
  font-weight: 700 !important;
  border-radius: 10px !important;
  box-shadow: none !important;
}
section[data-testid="stSidebar"] button[kind="primary"] p,
section[data-testid="stSidebar"] button[kind="primary"] span {
  color: #142830 !important;
}
.vp-nav-user {
  font-size: 0.85rem;
  color: #6A7F88;
  margin: 0.2rem 0 0.6rem;
}
</style>
        """,
        unsafe_allow_html=True,
    )

    chosen = current if current in {k for k, _, _ in NAV_META} else "Hoy"
    for key, label, icon in NAV_META:
        active = key == chosen
        if st.button(
            f"{icon}  {label}",
            key=f"nav_{key}",
            use_container_width=True,
            type="primary" if active else "secondary",
        ):
            chosen = key
            st.session_state["nav_page"] = key
            st.rerun()
    return st.session_state.get("nav_page", chosen)
