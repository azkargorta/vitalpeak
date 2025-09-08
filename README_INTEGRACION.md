# Auto-configurador de rutinas (chat) — Paquete completo

Copia estas rutas dentro de tu repo:
- `pages/02_Auto-configurador de rutinas (chat).py`  → sustituye la página antigua (borra la vieja si existía).
- `app/ai_generator.py`, `app/schema_rutina.py`, `app/pdf_export.py`, `app/routines_store.py`.

En `requirements.txt` asegúrate de incluir las versiones de `requirements_additions.txt`.
En Render añade (Environment):
- `OPENAI_API_KEY=sk-...`
- (opcional) `OPENAI_MODEL=gpt-4o-mini`
- (opcional) `DATABASE_URL=postgresql://user:pass@host:5432/db?sslmode=require`

**La página aparecerá en el menú exactamente como:** “Auto-configurador de rutinas (chat)”.

