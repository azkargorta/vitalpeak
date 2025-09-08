
# Rutinas IA — paquete listo para web (Opción B + mejoras)

Incluye:
- `pages/03_Creador_Rutinas_IA.py` — página Streamlit con formulario, JSON y botón **PDF**.
- `app/ai_generator.py` — **v2** con validación y refinado automático.
- `app/schema_rutina.py` — validaciones Pydantic + reglas de negocio.
- `app/pdf_export.py` — exportador PDF limpio (Intensidad en vez de Peso).

## Render
- Env vars: `OPENAI_API_KEY=sk-...` (y opcional `OPENAI_MODEL=gpt-4o-mini`).
- Build: `pip install -r requirements.txt`
- Start: `streamlit run streamlit_app.py --server.port 10000 --server.address 0.0.0.0`

## Notas
- Si el modelo devuelve JSON inválido o con errores de negocio, se intenta **autocorregir**.
- El PDF usa columnas: **Ejercicio | Series | Reps | Descanso | Intensidad**.

