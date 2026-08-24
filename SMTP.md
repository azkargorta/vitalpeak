# Configurar email (recuperación de contraseña)

Sin SMTP, VitalPeak genera el código pero **no puede enviarlo**. Con SMTP, llega al email de recuperación del usuario.

---

## 1. Opción fácil: Gmail

1. Entra en tu cuenta Google → [Contraseñas de aplicaciones](https://myaccount.google.com/apppasswords)  
   (hace falta **verificación en 2 pasos** activada).
2. Crea una contraseña de aplicación (nombre: `VitalPeak`).
3. Copia las **16 letras** (sin espacios).

---

## 2. Pegar en Streamlit Cloud → Secrets

Añade esto (junto a Supabase / lo que ya tengas):

```toml
# URL pública de tu app (para el enlace del email)
APP_BASE_URL = "https://TU-APP.streamlit.app"

SMTP_HOST = "smtp.gmail.com"
SMTP_PORT = "587"
SMTP_USER = "tu-correo@gmail.com"
SMTP_PASS = "xxxx xxxx xxxx xxxx"
SMTP_FROM = "tu-correo@gmail.com"
```

O en tabla:

```toml
APP_BASE_URL = "https://TU-APP.streamlit.app"

[smtp]
host = "smtp.gmail.com"
port = "587"
user = "tu-correo@gmail.com"
pass = "xxxxxxxxxxxxxxxx"
from = "tu-correo@gmail.com"
```

**Save** → **Reboot app**.

---

## 3. Comprobar

1. El usuario debe tener **email** o **recovery_email** guardado (al crear cuenta se pide email).
2. En **Olvidé mi contraseña** pon el usuario o ese email.
3. Debe salir el mensaje verde/info de “te llegará un correo”, no el aviso amarillo con el código.
4. Revisa bandeja de entrada y spam.

---

## 4. Otras opciones SMTP

| Proveedor | Host | Puerto |
|-----------|------|--------|
| Gmail | `smtp.gmail.com` | 587 |
| Outlook / Hotmail | `smtp.office365.com` | 587 |
| SendGrid | `smtp.sendgrid.net` | 587 (user: `apikey`) |

---

## Notas

- No subas `SMTP_PASS` a GitHub; solo Secrets / `.env` local.
- El enlace del email usa `APP_BASE_URL?user=...&reset_token=...`.
- Si el email falla, la app sigue mostrando el código como respaldo.
