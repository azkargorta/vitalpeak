# VitalPeak — Pasos para subir y publicar

Checklist para pasar de “solo en tu PC” a “gente puede entrar, datos se guardan, y luego móvil”.

---

## Fase 0 — Dejar el repo listo (hoy)

- [x] Repo conectado a GitHub (`origin`)
- [x] `.gitignore` con `usuarios_data/`, `.env`, secrets
- [ ] Quitar JSON de usuarios del historial de git (commit pendiente)
- [ ] Push a GitHub

Pasos manuales tras el commit:

```bash
git status
git add .
git commit -m "Describe el cambio"
git push -u origin HEAD
```

Si el repo aún no está en GitHub: crear el repo vacío en github.com y conectar `origin`.

---

## Fase 1 — Publicar la web (que la gente entre)

- [ ] Cuenta en [share.streamlit.io](https://share.streamlit.io) con GitHub
- [ ] New app → repo `vitalpeak` → main file `streamlit_app.py`
- [ ] Secrets configurados (OpenAI si usas IA)
- [ ] App desplegada y URL probada en móvil

Objetivo: URL pública (Streamlit Community Cloud es lo más simple).

1. Ir a [share.streamlit.io](https://share.streamlit.io) e iniciar sesión con GitHub.
2. **New app** → elegir el repo `vitalpeak`.
3. Main file: `streamlit_app.py`.
4. En **Settings → Secrets** pegar lo necesario (ej. OpenAI si usas IA):

```toml
OPENAI_API_KEY = "sk-..."
OPENAI_MODEL = "gpt-4o-mini"

# Más adelante, cuando exista Supabase:
# [supabase]
# url = "https://xxxx.supabase.co"
# service_role_key = "..."
```

5. Desplegar y probar login (demo `admin` / `admin` solo en pruebas; no dejarlo en producción).
6. Guardar la URL (ej. `https://xxxx.streamlit.app`) y probarla en el móvil con el navegador.

**Importante:** en Cloud el disco es temporal. Los JSON de `usuarios_data/` **no** son fiables ahí. Hace falta Fase 2.

---

## Fase 2 — Guardar datos de verdad (prioridad)

Guía detallada: **`SUPABASE.md`**. SQL: **`sql/supabase_user_accounts.sql`**.

- [x] Código: `datastore.py` usa Supabase si hay secrets; si no, JSON local
- [ ] Crear proyecto en [supabase.com](https://supabase.com)
- [ ] Ejecutar el SQL en SQL Editor
- [ ] Pegar URL + **service_role** en Streamlit Secrets
- [ ] Reboot + probar: crear cuenta → guardar serie → reboot → los datos siguen

Hasta que los secrets estén puestos, la web pública sigue perdiendo datos al reiniciar.

---

## Fase 3 — Seguridad básica (antes de gente real)

1. Quitar o desactivar el seed demo (`VITALPEAK_SEED=0`) en producción.
2. No usar `admin/admin` en la URL pública.
3. No exponer la **service_role** key en el frontend; solo en secrets del servidor.
4. Revisar que cada usuario solo vea/edite sus datos (filtros por `user_id`).

---

## Fase 4 — “Como app” en el móvil (después)

Orden recomendado:

1. **Ya:** abrir la URL de Streamlit en el móvil (Safari/Chrome) y “Añadir a pantalla de inicio” si ayuda.
2. **Luego (opcional):** envoltorio tipo Capacitor / TWA que abra esa misma URL → icono en el teléfono.
3. **Solo si hace falta:** app nativa (React Native / Flutter) — es otro proyecto de UI, no Streamlit.

Streamlit no es una app nativa; el camino barato es **web responsive + envoltorio**.

---

## Orden resumido

| # | Qué | Resultado |
|---|-----|-----------|
| 0 | Commit + push a GitHub | Código en la nube |
| 1 | Deploy Streamlit Cloud | Gente entra por URL |
| 2 | Supabase / DB | Datos se guardan de verdad |
| 3 | Seguridad (sin demo admin) | Listo para usuarios reales |
| 4 | Acceso móvil / envoltorio | Icono tipo app |

---

## Notas del estado actual del proyecto

- App: Streamlit (`streamlit_app.py`).
- Datos locales: `usuarios_data/<user>.json` (vale en PC).
- En Cloud: misma API `load_user`/`save_user` → tabla `user_accounts` si hay secrets (`SUPABASE.md`).
- Menú actual: Hoy · Entrenar · Rutinas · Progreso · Cuenta (sin Técnica).
- GIFs de movimiento viven en `exercise_images/`; asegúrate de que están en el repo o en storage si el deploy no los incluye.

---

## Siguiente acción concreta

Tú: crear proyecto Supabase + SQL + secrets (pasos 1–4 de `SUPABASE.md`).
Luego: commit/push del código de datastore y reboot de Streamlit.
