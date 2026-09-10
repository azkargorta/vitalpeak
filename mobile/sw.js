const CACHE = "vitalpeak-mobile-v61";

// Solo precargamos lo imprescindible para que la interfaz aparezca rápido.
// Los GIF e imágenes se guardan en caché cuando el usuario los abre.
const APP_SHELL = [
  "./",
  "./index.html",
  "./styles.css",
  "./catalog-data.js",
  "./app.js",
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
