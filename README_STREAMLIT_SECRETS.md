# VitalPeak en Streamlit Cloud (API Key)

Para que el **Creador de rutinas** use la IA en Streamlit Cloud, configura la API key usando **Secrets**.

## 1) Dónde pegar la API Key

1. Entra a tu app en Streamlit Cloud.
2. Abre **Manage app** → **Settings** → **Secrets**.
3. Pega este bloque (formato TOML) y sustituye la key:

```toml
OPENAI_API_KEY = "sk-..."
OPENAI_MODEL = "gpt-4o-mini"
```

## 2) Cómo se lee en el código

El proyecto carga automáticamente:

- `.env` (solo local)
- `st.secrets` (Streamlit Cloud)

Desde `app/config.py`.
