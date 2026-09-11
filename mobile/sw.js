const CACHE = "vitalpeak-mobile-v69";

// Solo precargamos lo imprescindible para que la interfaz aparezca rápido.
// Los GIF e imágenes se guardan en caché cuando el usuario los abre.
const APP_SHELL = [
  "./",
  "./index.html",
  "./styles.css",
  "./catalog-data.js?v=69",
  "./app.js?v=69",
  "./routine-generator-ui.js",
  "./manifest.webmanifest",
  "./icon-cover.png",
  "./icons/icon-192.svg",
  "./apple-touch-icon.png"
];

self.addEventListener("install", event => event.waitUntil(
  caches.open(CACHE)
    .then(cache => cache.addAll(APP_SHELL))
    .then(() => self.skipWaiting())
));

self.addEventListener("activate", event => event.waitUntil(
  caches.keys()
    .then(keys => Promise.all(keys.filter(key => key !== CACHE).map(key => caches.delete(key))))
    .then(() => self.clients.claim())
    // La PWA de iOS puede mantener abierto el HTML de una versión anterior.
    // Al activar v69 navegamos una sola vez para cargar el catálogo actual.
    .then(() => self.clients.matchAll({ type: "window" }))
    .then(clients => Promise.all(clients.map(client => client.navigate(client.url).catch(() => undefined))))
));

function updateInBackground(request) {
  fetch(request).then(response => {
    if (!response || !response.ok) return;
    const url = new URL(request.url);
    if (url.origin !== self.location.origin) return;
    caches.open(CACHE).then(cache => cache.put(request, response.clone()));
  }).catch(() => {});
}

self.addEventListener("fetch", event => {
  if (event.request.method !== "GET") return;

  const url = new URL(event.request.url);
  if (url.origin !== self.location.origin) return;

  // Las navegaciones consultan primero la red para que una versión recién
  // desplegada aparezca al abrir la PWA, conservando el HTML en caché como
  // respaldo cuando el móvil está sin conexión.
  if (event.request.mode === "navigate") {
    event.respondWith(
      fetch(event.request)
        .then(response => {
          if (response && response.ok) {
            const copy = response.clone();
            caches.open(CACHE).then(cache => cache.put("./index.html", copy));
          }
          return response;
        })
        .catch(() => caches.match("./index.html"))
    );
    return;
  }

  // App shell y recursos estáticos: responder inmediatamente desde caché
  // y refrescar la copia en segundo plano. Evita esperar a la red móvil.
  event.respondWith(
    caches.match(event.request).then(cached => {
      if (cached) {
        event.waitUntil(Promise.resolve(updateInBackground(event.request)));
        return cached;
      }

      return fetch(event.request)
        .then(response => {
          if (response && response.ok) {
            const copy = response.clone();
            caches.open(CACHE).then(cache => cache.put(event.request, copy));
          }
          return response;
        })
        .catch(() => caches.match("./index.html"));
    })
  );
});
