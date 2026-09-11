const CACHE = "vitalpeak-mobile-v72";

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
  if (event.request.mode === "navigate") {
    event.respondWith(networkFirst(event.request, "./index.html"));
    return;
  }
  if (
    url.pathname.endsWith("/app.js") ||
    url.pathname.endsWith("/catalog-data.js") ||
    url.pathname.endsWith("/routine-generator-ui.js") ||
    url.pathname.endsWith("/routines-redesign.js") ||
    url.pathname.endsWith("/routine-navigation-fix.js") ||
    url.pathname.endsWith("/routines-accordion.js") ||
    url.pathname.endsWith("/training-notifications.js") ||
    url.pathname.endsWith("/account-progress-share-stable.js")
  ) {
    event.respondWith(networkFirst(event.request));
    return;
  }
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

self.addEventListener("notificationclick", event => {
  event.notification.close();
  event.waitUntil(
    clients.matchAll({ type: "window", includeUncontrolled: true }).then(list => {
      for (const client of list) {
        if ("focus" in client) return client.focus();
      }
      return clients.openWindow("./");
    })
  );
});
