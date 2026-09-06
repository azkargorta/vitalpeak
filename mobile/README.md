# VitalPeak móvil

Esta carpeta contiene una PWA **local-first** independiente de Streamlit. Una vez abierta desde HTTPS, se puede instalar en Android (menú del navegador → Instalar aplicación) o iPhone (Safari → Compartir → Añadir a pantalla de inicio).

## Qué funciona sin red

- La interfaz instalada y sus recursos.
- Registro de series y sesiones.
- Rutinas, peso corporal y panel de progreso.
- Exportar/importar una copia de seguridad JSON.

Los datos se almacenan en IndexedDB del propio teléfono. No requieren ni envían conexión para guardarse. La copia de seguridad es importante: al borrar los datos del navegador también se borra su almacenamiento local.

## Publicación

Sirve la carpeta `mobile/` como sitio estático HTTPS. Para una prueba local:

```bash
cd mobile
python -m http.server 8080
```

El servicio de Streamlit sigue intacto en la raíz del repositorio. La sincronización automática con las cuentas existentes de Streamlit requiere exponer una API autenticada; no se debe conectar el navegador directamente a las credenciales del servidor.
