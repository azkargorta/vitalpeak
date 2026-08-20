# Creador de Rutinas (IA) — Ollama local

## Qué hace
Página Streamlit `pages/03_Creador_Rutinas_IA.py` que genera planes personalizados.
Usa Ollama (gratis) u OpenAI. Si la IA falla → `app/rules_fallback.py`.

## Setup rápido (Ollama)

1. Instala https://ollama.com y ábrelo.
2. Descarga el modelo:
   ```bash
   ollama pull qwen2.5:14b
   ```
3. Copia `.env.example` → `.env` (ya viene preparado para Ollama).
4. Arranca la app:
   ```bash
   run.bat
   ```
   o `streamlit run streamlit_app.py`
5. En el menú lateral de Streamlit abre **Creador Rutinas IA**.

## Variables

| Variable | Ejemplo Ollama | Ejemplo OpenAI |
|----------|----------------|----------------|
| `OPENAI_API_KEY` | `ollama` | `sk-...` |
| `OPENAI_BASE_URL` | `http://localhost:11434/v1` | *(vacío)* |
| `OPENAI_MODEL` | `qwen2.5:14b` | `gpt-4o-mini` |

## Notas
- Ollama puede tardar 30 s–2 min por rutina (el código puede reintentar hasta 3 veces).
- Con poca RAM usa `llama3.1:8b`.
- Sin API / sin Ollama: el formulario sigue generando con el plan de respaldo.
