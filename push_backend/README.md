# VitalPeak Web Push

Backend preparado para enviar recordatorios de entrenamiento aunque la PWA esté cerrada.

## Variables de entorno

- `VAPID_PUBLIC_KEY`: clave pública VAPID.
- `VAPID_PRIVATE_KEY`: clave privada VAPID. **No subir al repositorio.**
- `VAPID_SUBJECT`: normalmente `mailto:tu-email@dominio.com`.
- `CRON_SECRET`: secreto usado por el cron para llamar a `/api/push/send-due`.
- `ALLOWED_ORIGINS`: origen de la PWA, por ejemplo `https://azkargorta.github.io`.
- `PUSH_DB_PATH`: opcional. Ruta del SQLite persistente.

## Arranque local

```bash
pip install -r push_backend/requirements.txt
uvicorn push_backend.app:app --host 0.0.0.0 --port 8000
```

## Flujo

1. La PWA pide permiso de notificaciones.
2. Se registra con `PushManager` usando la clave pública VAPID obtenida de `/api/push/public-key`.
3. La PWA envía la suscripción, hora elegida, zona horaria y próximas fechas de entrenamiento a `/api/push/subscribe`.
4. Un cron llama a `/api/push/send-due` cada minuto con la cabecera `X-Cron-Secret`.
5. El backend envía el Web Push y el service worker lo muestra aunque la app esté cerrada.

## Conectar la PWA

Cuando el backend esté publicado, editar `mobile/push-config.js`:

```js
window.VITALPEAK_PUSH_CONFIG = {
  apiBase: "https://TU-BACKEND"
};
```

## Producción

Para una primera puesta en marcha se puede usar SQLite si el hosting ofrece disco persistente. Si VitalPeak pasa a varios usuarios, conviene mover las suscripciones a Supabase/PostgreSQL.

En iPhone, Web Push funciona para PWAs instaladas en la pantalla de inicio y con permiso de notificaciones concedido por el usuario.
