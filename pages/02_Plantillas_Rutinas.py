"""Página multipágina (compat). Preferir la sección integrada en la app principal."""

from __future__ import annotations

import streamlit as st

from app.ui_theme import apply_theme
from app.templates_ui import render_templates_page

st.set_page_config(page_title="Plantillas | VitalPeak", page_icon="VP", layout="wide")
apply_theme()
render_templates_page(embedded=False)
