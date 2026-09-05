const CACHE_NAME = 'material-inventory-dashboard-a02a8427711f';
const PRECACHE_URLS = [
  "./",
  "./index.html",
  "./assets/data/core.cf13bcd010ab.js",
  "./assets/data/device_outbound.d9ca9b39f635.js",
  "./assets/data/province_material.91ad57496230.js",
  "./assets/data/province_outbound.ee2539864d9a.js",
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
      keys.filter(key => key.startsWith('material-inventory-dashboard-') && key !== CACHE_NAME)
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
