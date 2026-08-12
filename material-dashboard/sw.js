const CACHE_NAME = 'material-dashboard-3990286558f7';
const PRECACHE_URLS = [
  "./",
  "./index.html",
  "./assets/data/core.56b069684b73.js",
  "./assets/data/device_outbound.8e0f5d35a300.js",
  "./assets/data/province_material.c966bc447a9c.js",
  "./assets/data/province_outbound.f6fc44c6bcea.js",
  "./assets/fonts/gotham-rounded-bold.f6281701cdb9.woff2",
  "./assets/fonts/hk-yuan-w7.a0f4d903956d.woff2"
];

self.addEventListener('install', event => {
  event.waitUntil(caches.open(CACHE_NAME).then(cache => cache.addAll(PRECACHE_URLS)));
  self.skipWaiting();
});

self.addEventListener('activate', event => {
  event.waitUntil(
    caches.keys().then(keys => Promise.all(
      keys.filter(key => key.startsWith('material-dashboard-') && key !== CACHE_NAME)
        .map(key => caches.delete(key))
    ))
  );
  self.clients.claim();
});

self.addEventListener('fetch', event => {
  if (event.request.method !== 'GET') return;
  const url = new URL(event.request.url);
  if (url.origin !== self.location.origin) return;

  if (url.pathname.endsWith('/') || url.pathname.endsWith('/index.html')) {
    event.respondWith(
      fetch(event.request).then(response => {
        const copy = response.clone();
        caches.open(CACHE_NAME).then(cache => cache.put(event.request, copy));
        return response;
      }).catch(() => caches.match(event.request))
    );
    return;
  }

  event.respondWith(
    caches.match(event.request).then(cached => cached || fetch(event.request).then(response => {
      const copy = response.clone();
      caches.open(CACHE_NAME).then(cache => cache.put(event.request, copy));
      return response;
    }))
  );
});
