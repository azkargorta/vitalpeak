# Creador de Rutinas (IA) — Integración Opción B

Se añadió la página Streamlit `pages/03_Creador_Rutinas_IA.py` y los módulos:
- `app/ai_generator.py` (llamada a OpenAI, salida JSON)
- `app/rules_fallback.py` (plan de respaldo)

## Variables en Render
- `OPENAI_API_KEY=sk-...`
- (opcional) `OPENAI_MODEL=gpt-4o-mini`

## Comandos Render
- Build: `pip install -r requirements.txt`
- Start: `streamlit run streamlit_app.py --server.port 10000 --server.address 0.0.0.0`

Si no existe `pages/`, se creó automáticamente. Si ya existía un archivo con el mismo nombre, se guardó como `_v2`.
