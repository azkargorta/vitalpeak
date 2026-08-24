# Desplegar VitalPeak en Streamlit Cloud

Guía paso a paso (Fase 1). Hazlo **después** del push con `.gitignore` actualizado.

## 1. Entrar

1. Abre [share.streamlit.io](https://share.streamlit.io).
2. Inicia sesión con la misma cuenta de GitHub que tiene el repo (`azkargorta/vitalpeak`).

## 2. Crear la app

1. Pulsa **Create app** (o **New app**).
2. **Repository:** `azkargorta/vitalpeak`
3. **Branch:** `main`
4. **Main file path:** `streamlit_app.py`
5. **App URL (opcional):** elige un nombre, ej. `vitalpeak-gym`
6. **Deploy**

La primera build puede tardar varios minutos (imágenes y GIFs en el repo).

## 3. Secrets (Settings → Secrets)

Pega en el editor TOML. Solo lo que uses:

```toml
# IA (opcional — Creador de rutinas)
OPENAI_API_KEY = "sk-..."
OPENAI_MODEL = "gpt-4o-mini"

# Demo admin: desactivar en producción real
VITALPEAK_SEED = "1"
VITALPEAK_ADMIN_USER = "admin"
VITALPEAK_ADMIN_PASSWORD = "admin"
VITALPEAK_ADMIN_EMAIL = "demo@ejemplo.com"
```

Para pruebas internas puedes dejar el seed. Antes de usuarios reales: `VITALPEAK_SEED = "0"`.

## 4. Comprobar

1. Abre la URL (`https://<nombre>.streamlit.app`).
2. Entra con `admin` / `admin` (demo) o crea cuenta.
3. Prueba **Hoy** → **Entrenar** → guardar una serie.
4. Abre la misma URL en el móvil.

## 5. Limitaciones (importante)

| Qué | En Cloud |
|-----|----------|
| Datos en `usuarios_data/` | Se pierden al reiniciar **si no hay Supabase** |
| GIFs / imágenes | Van con el repo (OK) |
| Persistencia real | Ver `SUPABASE.md` (Fase 2) |

## 6. Si falla el deploy

- **Logs:** Manage app → Logs (errores de `pip install` o imports).
- **requirements.txt:** debe listar todas las dependencias.
- **Archivo grande:** GitHub limita 100 MB por archivo; los GIFs actuales están bien.

## Siguiente paso

Cuando la URL funcione, seguimos con **Fase 2** en `NOTA_PUBLICAR.md`: Supabase para guardar datos.
