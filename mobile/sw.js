const CACHE = "vitalpeak-mobile-v71";

// Solo precargamos lo imprescindible para que la interfaz aparezca rápido.
// Los GIF e imágenes se guardan en caché cuando el usuario los abre.
const APP_SHELL = [
  "./",
  "./index.html",
  "./styles.css",
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

function cacheResponse(request, response) {
  if (!response || !response.ok) return response;
  const copy = response.clone();
  caches.open(CACHE).then(cache => cache.put(request, copy)).catch(() => {});
  return response;
}

function networkFirst(request, fallback) {
  return fetch(request, { cache: "no-store" })
    .then(response => cacheResponse(request, response))
    .catch(() => caches.match(request).then(hit => hit || (fallback ? caches.match(fallback) : undefined)));
}

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

  // El HTML siempre intenta red primero. Si no hay conexión, usa la copia local.
  if (event.request.mode === "navigate") {
    event.respondWith(networkFirst(event.request, "./index.html"));
    return;
  }

  // Estos recursos contienen la lógica principal. No usamos stale-while-revalidate:
  // una versión antigua de app.js/catalog-data.js combinada con un index nuevo puede
  // dejar la interfaz visible pero sin navegación hasta la siguiente apertura.
  if (
    url.pathname.endsWith("/app.js") ||
    url.pathname.endsWith("/catalog-data.js") ||
    url.pathname.endsWith("/routine-generator-ui.js") ||
    url.pathname.endsWith("/routines-redesign.js") ||
    url.pathname.endsWith("/routine-navigation-fix.js") ||
    url.pathname.endsWith("/routines-accordion.js")
  ) {
    event.respondWith(networkFirst(event.request));
    return;
  }

  // El resto de recursos estáticos puede responder de caché y actualizarse detrás.
  event.respondWith(
    caches.match(event.request).then(cached => {
      if (cached) {
        event.waitUntil(Promise.resolve(updateInBackground(event.request)));
        return cached;
      }

      return fetch(event.request)
        .then(response => cacheResponse(event.request, response))
        .catch(() => caches.match("./index.html"));
    })
  );
});
