# VitalPeak — Móvil / Camino A (envoltorio)

La app sigue siendo **web Streamlit**. El Camino A = abrir esa URL dentro de una app Android/iOS (Capacitor o TWA).

Antes de empaquetar, la UI debe ir **bien en teléfono**.

---

## Qué ya está preparado (UI)

- CSS móvil: padding, safe-area, botones ≥ ~44px, inputs sin zoom iOS
- Columnas apiladas en pantallas estrechas
- **Hoy**: semana en lista (no 7 columnas)
- **Entrenar**: formulario a pantalla completa; movimiento en expander
- **Rutinas / Progreso**: selectbox si hay 3+ secciones
- **Plantillas**: edición de ejercicios en vertical
- Menú: sidebar Streamlit (hamburger) con botones grandes

---

## Cómo probar en el móvil

1. Abre tu URL `https://….streamlit.app` en el teléfono.
2. Recorre: Hoy → Entrenar → Rutinas → Progreso → Cuenta.
3. Comprueba: botones, teclado, scroll, login, guardar serie.

Checklist rápido:

- [ ] Login / crear cuenta
- [ ] Hoy: lista + empezar
- [ ] Entrenar: guardar serie + descanso
- [ ] Rutinas: plantilla + planificar
- [ ] Progreso: cambiar sección
- [ ] Cuenta: perfil / email
- [ ] Menú lateral se abre y cierra bien

---

## Siguiente: envoltorio (Capacitor / TWA)

Cuando la web móvil te convenza:

1. Crear proyecto Capacitor (o Trusted Web Activity en Android).
2. `server.url` = tu `APP_BASE_URL` de Streamlit.
3. Icono + splash.
4. Build APK/AAB para Play Store (Android primero).

iOS App Store es más estricto con apps que solo muestran una web; Android TWA/Capacitor es el camino más realista primero.

---

## Límites de Streamlit en móvil

- El sidebar no es una tab bar nativa.
- Algunas tablas anchas necesitan scroll horizontal.
- No hay notificaciones push nativas sin capa extra.

Eso es normal en el Camino A; el Camino B (app nativa) lo resolvería más adelante.
