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

Objetivo: que cada usuario conserve entrenos, rutinas, peso y plan al reiniciar la app.

1. Crear proyecto en [Supabase](https://supabase.com).
2. Crear tablas (mínimo):
   - `profiles` (usuario, email, perfil)
   - `trainings` (series / sesiones)
   - `routines` (plantillas)
   - `routine_plan` (día → rutina)
   - `weights`
   - `goals`
3. (Recomendado) Activar **Auth** de Supabase o migrar el login actual a guardar en Postgres.
4. En el código VitalPeak:
   - Adaptar `app/datastore.py` (y lo que use `load_user` / `save_user`) para leer/escribir en Supabase.
   - Dejar de depender de `usuarios_data/*.json` en producción.
5. Poner URL y keys en Streamlit Secrets.
6. Probar: crear cuenta → guardar serie → refrescar / redeploy → los datos siguen.

Hasta que esto esté hecho, la web pública es solo demo.

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
- Datos locales: `usuarios_data/<user>.json` (vale en PC, no en Cloud).
- Ya hay utilidades `app/supabase_utils.py` (usadas en posture); falta migrar el núcleo (`datastore`) a DB.
- Menú actual: Hoy · Entrenar · Rutinas · Progreso · Cuenta (sin Técnica).
- GIFs de movimiento viven en `exercise_images/`; asegúrate de que están en el repo o en storage si el deploy no los incluye.

---

## Siguiente acción concreta

Cuando digas “empezamos”, el primer trabajo de código debería ser:

1. Diseño de tablas Supabase.  
2. Adaptar `datastore.py` a Postgres/Supabase.  
3. Redeploy en Streamlit Cloud con secrets.
