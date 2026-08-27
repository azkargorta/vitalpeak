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
  padding: 1.2rem 1.3rem 1.35rem;
  margin-bottom: 1.15rem;
  box-shadow: 0 8px 28px rgba(20, 40, 48, 0.05);
  animation: vpFadeIn 0.5s ease-out;
}}
.vp-today h3 {{
  margin-top: 0 !important;
  margin-bottom: 0.65rem !important;
}}

.vp-week-day {{
  background: #FFFFFF;
  border: 1px solid var(--vp-border);
  border-radius: 12px;
  padding: 0.65rem 0.35rem 0.75rem;
  text-align: center;
  min-height: 5.6rem;
  box-shadow: 0 4px 14px rgba(20, 40, 48, 0.04);
}}
.vp-week-day--today {{
  border-color: #3AA899;
  background: #E6F6F3;
  box-shadow: 0 4px 16px rgba(58, 168, 153, 0.18);
}}
.vp-week-abbr {{
  font-size: 0.68rem;
  font-weight: 700;
  letter-spacing: 0.08em;
  text-transform: uppercase;
  color: #6A7F88;
}}
.vp-week-num {{
  font-family: 'Barlow Condensed', sans-serif;
  font-size: 1.45rem;
  font-weight: 700;
  color: #142830;
  line-height: 1.1;
  margin: 0.15rem 0 0.35rem;
}}
.vp-week-rt {{
  font-size: 0.68rem;
  font-weight: 600;
  color: #2A4450;
  line-height: 1.25;
  word-break: break-word;
}}
.vp-week-day--today .vp-week-rt {{
  color: #1B3A44;
}}

/* Botones principales (contenido) — no forzar el sidebar */
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
/* Sidebar: anular el primary global (menú activo) */
section[data-testid="stSidebar"] div.stButton > button[kind="primary"],
section[data-testid="stSidebar"] div.stButton > button[data-testid="baseButton-primary"] {{
  background: #E6F6F3 !important;
  color: #142830 !important;
  border: 1px solid #3AA899 !important;
  box-shadow: none !important;
}}
section[data-testid="stSidebar"] div.stButton > button[kind="primary"] p,
section[data-testid="stSidebar"] div.stButton > button[kind="primary"] span,
section[data-testid="stSidebar"] div.stButton > button[data-testid="baseButton-primary"] p,
section[data-testid="stSidebar"] div.stButton > button[data-testid="baseButton-primary"] span {{
  color: #142830 !important;
}}
/* Logout (último botón del sidebar) */
section[data-testid="stSidebar"] div[data-testid="stVerticalBlockBorderWrapper"] div.stButton:last-of-type > button,
section[data-testid="stSidebar"] .stButton:has(button#btn_logout) > button {{
  background: #3AA899 !important;
  color: #FFFFFF !important;
  border: none !important;
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
section[data-testid="stSidebar"] div.stButton > button[kind="secondary"] {{
  background: transparent !important;
  border-color: transparent !important;
  color: #142830 !important;
  box-shadow: none !important;
}}
section[data-testid="stSidebar"] div.stButton > button[kind="secondary"]:hover {{
  background: #F0F5F3 !important;
  border-color: rgba(20,40,48,0.08) !important;
  color: #142830 !important;
}}
section[data-testid="stSidebar"] div.stButton > button[kind="secondary"] p,
section[data-testid="stSidebar"] div.stButton > button[kind="secondary"] span {{
  color: #142830 !important;
}}
/* Logout forzado */
section[data-testid="stSidebar"] button[kind="secondary"][data-testid="baseButton-secondary"] {{
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

/* Cabecera Streamlit: no tapar el contenido (menú ☰) */
header[data-testid="stHeader"] {{
  background: rgba(255, 255, 255, 0.92) !important;
  backdrop-filter: blur(8px);
}}
div[data-testid="stToolbar"] {{
  right: 0.5rem !important;
}}

/* —— Móvil / WebView (Camino A) —— */
@media (max-width: 768px) {{
  .block-container {{
    padding-left: max(0.85rem, env(safe-area-inset-left)) !important;
    padding-right: max(0.85rem, env(safe-area-inset-right)) !important;
    /* Espacio para el botón ☰ del menú (no tape el hero) */
    padding-top: 3.25rem !important;
    padding-bottom: max(2rem, env(safe-area-inset-bottom)) !important;
    max-width: 100% !important;
  }}
  .vp-hero {{
    margin-top: 0 !important;
  }}
  /* Empuja el contenido bajo el toggle del sidebar */
  section.main > div {{
    padding-top: 0.25rem !important;
  }}


  h1 {{ font-size: 1.85rem !important; }}
  h2 {{ font-size: 1.35rem !important; }}
  h3 {{ font-size: 1.15rem !important; }}

  .vp-today {{
    padding: 1rem 0.95rem 1.1rem;
  }}

  /* Botones táctiles */
  div.stButton > button {{
    min-height: 2.85rem !important;
    font-size: 1rem !important;
  }}
  div.stButton > button[kind="primary"],
  div.stButton > button[data-testid="baseButton-primary"] {{
    min-height: 3rem !important;
  }}

  /* Inputs cómodos */
  .stTextInput input,
  .stNumberInput input,
  .stSelectbox [data-baseweb="select"] > div,
  .stDateInput input {{
    min-height: 2.75rem !important;
    font-size: 16px !important; /* evita zoom iOS */
  }}

  /* Tablas: scroll horizontal */
  div[data-testid="stDataFrame"],
  div[data-testid="stTable"] {{
    overflow-x: auto !important;
    max-width: 100%;
  }}

  /* Columnas: apilar en móvil (excepto filas marcadas) */
  div[data-testid="stHorizontalBlock"]:not(.vp-keep-row) {{
    flex-wrap: wrap !important;
    gap: 0.35rem !important;
  }}
  div[data-testid="stHorizontalBlock"]:not(.vp-keep-row) > div[data-testid="column"] {{
    width: 100% !important;
    min-width: 100% !important;
    flex: 1 1 100% !important;
  }}

  /* Métricas */
  [data-testid="stMetric"] {{
    padding: 0.7rem 0.85rem;
  }}

  /* Sidebar: targets grandes */
  section[data-testid="stSidebar"] div.stButton > button {{
    min-height: 3rem !important;
    font-size: 1.05rem !important;
    margin-bottom: 0.15rem !important;
  }}

  /* Semana como lista */
  .vp-week-list {{
    display: flex;
    flex-direction: column;
    gap: 0.45rem;
  }}
  .vp-week-row {{
    display: flex;
    align-items: center;
    gap: 0.75rem;
    background: #FFFFFF;
    border: 1px solid var(--vp-border);
    border-radius: 12px;
    padding: 0.7rem 0.85rem;
  }}
  .vp-week-row--today {{
    border-color: #3AA899;
    background: #E6F6F3;
  }}
  .vp-week-row .vp-week-abbr {{
    min-width: 2.4rem;
  }}
  .vp-week-row .vp-week-num {{
    min-width: 1.6rem;
    margin: 0;
    font-size: 1.25rem;
  }}
  .vp-week-row .vp-week-rt {{
    flex: 1;
    font-size: 0.85rem;
    text-align: left;
  }}
}}

/* Semana lista también en escritorio (compacta y usable en WebView) */
.vp-week-list {{
  display: flex;
  flex-direction: column;
  gap: 0.4rem;
  margin-bottom: 0.5rem;
}}
.vp-week-row {{
  display: flex;
  align-items: center;
  gap: 0.75rem;
  background: #FFFFFF;
  border: 1px solid var(--vp-border);
  border-radius: 12px;
  padding: 0.65rem 0.85rem;
  box-shadow: 0 2px 10px rgba(20, 40, 48, 0.03);
}}
.vp-week-row--today {{
  border-color: #3AA899;
  background: #E6F6F3;
}}
.vp-week-row .vp-week-num {{
  margin: 0;
}}
.vp-week-row .vp-week-rt {{
  flex: 1;
  text-align: left;
  font-size: 0.82rem;
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


def render_mode_switch(options: list[str], current: str, *, key: str) -> str:
    """Interruptor de modos. En móvil: selectbox si hay 3+ opciones."""
    if current not in options:
        current = options[0]

    # Teléfono primero: muchas pestañas en fila no caben
    if len(options) >= 3:
        idx = options.index(current) if current in options else 0
        chosen = st.selectbox(
            "Sección",
            options,
            index=idx,
            key=f"{key}_select",
            label_visibility="collapsed",
        )
        st.session_state[key] = chosen
        hints = {
            "Plantillas": "Elige un plan listo y personalízalo",
            "Planificar": "Pon tus rutinas en el calendario",
            "Ejercicios": "Catálogo y evolución",
            "Historial": "Series registradas",
            "Objetivos": "Metas semanales y por ejercicio",
            "Peso": "Seguimiento corporal",
        }
        hint = hints.get(chosen, "")
        if hint:
            st.caption(hint)
        return chosen

    st.markdown(
        """
<style>
div[data-testid="column"] button[kind="primary"] {
  min-height: 3rem;
  font-size: 1.05rem !important;
}
div[data-testid="column"] button[kind="secondary"] {
  min-height: 3rem;
  font-size: 1.05rem !important;
}
.vp-switch-hint {
  font-size: 0.78rem;
  color: #6A7F88;
  margin: -0.35rem 0 0.85rem 0;
}
</style>
        """,
        unsafe_allow_html=True,
    )
    cols = st.columns(len(options))
    chosen = current
    for i, opt in enumerate(options):
        with cols[i]:
            active = opt == current
            if st.button(
                opt,
                key=f"{key}_{opt}",
                use_container_width=True,
                type="primary" if active else "secondary",
            ):
                chosen = opt
                st.session_state[key] = opt
                st.rerun()
    hints = {
        "Plantillas": "Elige un plan listo y personalízalo",
        "Planificar": "Pon tus rutinas en el calendario",
        "Ejercicios": "Catálogo y evolución",
        "Historial": "Series registradas",
        "Objetivos": "Metas semanales y por ejercicio",
        "Peso": "Seguimiento corporal",
    }
    hint = hints.get(chosen, "")
    if hint:
        st.markdown(f'<p class="vp-switch-hint">{hint}</p>', unsafe_allow_html=True)
    return st.session_state.get(key, chosen)


# Menú compacto (sin iconos)
NAV_META = [
    ("Hoy", "Hoy"),
    ("Entrenar", "Entrenar"),
    ("Rutinas", "Rutinas"),
    ("Progreso", "Progreso"),
    ("Cuenta", "Cuenta"),
]


def render_sidebar_nav(current: str | None) -> str:
    """Menú lateral corto, solo texto."""
    st.markdown(
        """
<style>
/* Botones de navegación: claros; activo resaltado */
section[data-testid="stSidebar"] div.stButton > button[kind="secondary"] {
  background: transparent !important;
  background-color: transparent !important;
  border: 1px solid transparent !important;
  color: #142830 !important;
  text-align: left !important;
  justify-content: flex-start !important;
  font-weight: 600 !important;
  border-radius: 10px !important;
  padding: 0.6rem 0.85rem !important;
  box-shadow: none !important;
}
section[data-testid="stSidebar"] div.stButton > button[kind="secondary"]:hover {
  background: #F0F5F3 !important;
  border-color: rgba(20,40,48,0.08) !important;
  color: #142830 !important;
}
section[data-testid="stSidebar"] div.stButton > button[kind="secondary"] p,
section[data-testid="stSidebar"] div.stButton > button[kind="secondary"] span {
  color: #142830 !important;
}
section[data-testid="stSidebar"] div.stButton > button[kind="primary"] {
  background: #E6F6F3 !important;
  background-color: #E6F6F3 !important;
  border: 1px solid #3AA899 !important;
  color: #142830 !important;
  text-align: left !important;
  justify-content: flex-start !important;
  font-weight: 700 !important;
  border-radius: 10px !important;
  box-shadow: none !important;
}
section[data-testid="stSidebar"] div.stButton > button[kind="primary"] p,
section[data-testid="stSidebar"] div.stButton > button[kind="primary"] span {
  color: #142830 !important;
}
/* Cerrar sesión: sólido y visible */
section[data-testid="stSidebar"] button[data-testid="baseButton-secondary"]#btn_logout,
section[data-testid="stSidebar"] div.stButton:has(button[kind="secondary"]) {
  /* fallback abajo */
}
.vp-nav-user {
  font-size: 0.85rem;
  color: #6A7F88;
  margin: 0.2rem 0 0.6rem;
}
/* Cerrar sesión: botón junto al marcador */
section[data-testid="stSidebar"] [data-testid="stMarkdownContainer"]:has(.vp-logout-mark) {
  display: none !important;
  height: 0 !important;
  margin: 0 !important;
  padding: 0 !important;
}
section[data-testid="stSidebar"] [data-testid="element-container"]:has(.vp-logout-mark) + [data-testid="element-container"] button {
  background: #3AA899 !important;
  background-color: #3AA899 !important;
  color: #FFFFFF !important;
  border: none !important;
  font-weight: 700 !important;
  box-shadow: 0 2px 8px rgba(58, 168, 153, 0.28) !important;
}
section[data-testid="stSidebar"] [data-testid="element-container"]:has(.vp-logout-mark) + [data-testid="element-container"] button p,
section[data-testid="stSidebar"] [data-testid="element-container"]:has(.vp-logout-mark) + [data-testid="element-container"] button span {
  color: #FFFFFF !important;
}
</style>
        """,
        unsafe_allow_html=True,
    )

    valid = {k for k, _ in NAV_META}
    chosen = current if current in valid else "Hoy"
    for key, label in NAV_META:
        active = key == chosen
        if st.button(
            label,
            key=f"nav_{key}",
            use_container_width=True,
            type="primary" if active else "secondary",
        ):
            st.session_state["nav_page"] = key
            st.rerun()
    return st.session_state.get("nav_page", chosen)
