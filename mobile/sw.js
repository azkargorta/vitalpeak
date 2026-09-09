const CACHE = "vitalpeak-mobile-v49";
const APP_SHELL = [
  "./", "./index.html", "./styles.css", "./catalog-data.js", "./cardio-catalog.js", "./cardio-training.js", "./cardio-ui-polish.js", "./app.js", "./routine-enhancements.js", "./routine-muscle-filter.js", "./calendar-mobile.js", "./training-intelligence.js", "./routine-navigation-fix.js", "./routines-accordion.js", "./routine-filter-persistence.js", "./training-set-editor.js", "./manifest.webmanifest", "./icon-cover.png", "./icons/icon-192.svg", "./apple-touch-icon.png",
  "./cardio-media/cinta-de-correr.svg",
  "./cardio-media/caminata-cinta-inclinacion.svg",
  "./cardio-media/bicicleta-estatica.svg",
  "./cardio-media/bicicleta-aire.svg",
  "./cardio-media/bicicleta-eliptica.svg",
  "./cardio-media/remo-ergometro.svg",
  "./cardio-media/escaladora.svg",
  "./cardio-media/saltar-comba.svg",
  "./cardio-media/carrera-exterior.svg",
  "./cardio-media/caminata-rapida.svg",
  "./cardio-media/cinta-de-correr.webp",
  "./cardio-media/caminata-cinta-inclinacion.webp",
  "./cardio-media/bicicleta-estatica.webp",
  "./cardio-media/bicicleta-aire.webp",
  "./cardio-media/bicicleta-eliptica.webp",
  "./cardio-media/remo-ergometro.webp"
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