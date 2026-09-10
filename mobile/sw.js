const CACHE = "vitalpeak-mobile-v57";
const APP_SHELL = [
  "./",
  "./index.html",
  "./styles.css",
  "./catalog-data.js",
  "./cardio-catalog.js",
  "./cardio-training.js",
  "./app.js",
  "./routine-enhancements.js",
  "./routine-generator-ui.js",
  "./routine-muscle-filter.js",
  "./calendar-mobile.js",
  "./training-intelligence.js",
  "./routine-navigation-fix.js",
  "./routines-accordion.js",
  "./routine-filter-persistence.js",
  "./training-set-editor.js",
  "./manifest.webmanifest",
  "./icon-cover.png",
  "./icons/icon-192.svg",
  "./apple-touch-icon.png",
  "./cardio-images/cinta-de-correr.webp",
  "./cardio-images/caminata-cinta-inclinacion.webp",
  "./cardio-images/bicicleta-estatica.webp",
  "./cardio-images/bicicleta-aire.webp",
  "./cardio-images/bicicleta-eliptica.webp",
  "./cardio-images/remo-ergometro.webp",
  "./cardio-images/escaladora.webp",
  "./cardio-images/saltar-comba.webp",
  "./cardio-images/carrera-exterior.webp",
  "./cardio-images/caminata-rapida.webp"
];

self.addEventListener("install", event => event.waitUntil(
  caches.open(CACHE).then(cache => cache.addAll(APP_SHELL)).then(() => self.skipWaiting())
));

self.addEventListener("activate", event => event.waitUntil(
  caches.keys()
    .then(keys => Promise.all(keys.filter(key => key !== CACHE).map(key => caches.delete(key))))
    .then(() => self.clients.claim())
));

self.addEventListener("fetch", event => {
  if (event.request.method !== "GET") return;
  event.respondWith(
    fetch(event.request)
      .then(response => {
        if (response.ok && new URL(event.request.url).origin === location.origin) {
          const copy = response.clone();
          caches.open(CACHE).then(cache => cache.put(event.request, copy));
        }
        return response;
      })
      .catch(() => caches.match(event.request).then(cached => cached || caches.match("./index.html")))
  );
});
