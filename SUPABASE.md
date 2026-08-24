# VitalPeak — Fase 2: guardar datos en Supabase

Sin esto, Streamlit Cloud pierde usuarios y entrenos al reiniciar. Con esto, `load_user` / `save_user` escriben en Postgres.

Hazlo **en este orden**.

---

## 1. Crear proyecto (5 min)

1. Entra en [supabase.com](https://supabase.com) → **Start your project**.
2. **New project**
   - Name: `vitalpeak`
   - Database password: **guárdala** (no la pongas en GitHub)
   - Region: la más cercana (p. ej. `Frankfurt` / `eu-central-1`)
3. Espera a que el proyecto esté **Ready**.

---

## 2. Crear las tablas

1. En el menú: **SQL Editor** → **New query**.
2. Copia el contenido de `sql/supabase_user_accounts.sql` (está en el repo).
3. **Run**. Debe salir *Success*.

Comprueba: **Table Editor** → aparecen `user_accounts` y `password_resets`.

---

## 3. Copiar URL y clave

1. **Project Settings** (engranaje) → **API**.
2. Copia:
   - **Project URL** → `https://xxxx.supabase.co`
   - **service_role** (secret) → clave larga (`eyJ...`)

Usa **service_role**, no la `anon` key. Solo va en Streamlit Secrets (servidor), nunca en el código.

---

## 4. Pegar secrets en Streamlit Cloud

1. App en [share.streamlit.io](https://share.streamlit.io) → **Manage app** → **Settings** → **Secrets**.
2. Añade (completa lo que ya tengas):

```toml
[supabase]
url = "https://xxxx.supabase.co"
service_role_key = "eyJ...."
```

O en plano:

```toml
SUPABASE_URL = "https://xxxx.supabase.co"
SUPABASE_SERVICE_ROLE_KEY = "eyJ...."
```

3. **Save** y **Reboot** la app.

---

## 5. Comprobar

1. Abre la app → **Crear cuenta** (usuario nuevo, no el demo si quieres).
2. **Entrenar** → guarda una serie.
3. En Supabase → **Table Editor** → `user_accounts` → debe haber una fila.
4. En Streamlit: **Reboot app** otra vez.
5. Entra con el mismo usuario: la serie **sigue ahí**.

Si no hay fila en `user_accounts`, los secrets no se leyeron (revisa URL/key y el reboot).

---

## Local (opcional)

En `.env` (no se sube a GitHub):

```
SUPABASE_URL=https://xxxx.supabase.co
SUPABASE_SERVICE_ROLE_KEY=eyJ....
```

Sin estas variables, en el PC sigue usando `usuarios_data/*.json`.

---

## Qué hace el código

Con secrets presentes, todo el JSON de cada usuario (entrenos, rutinas, peso, objetivos, perfil) se guarda en `user_accounts.data`. El resto de la app no cambia.
