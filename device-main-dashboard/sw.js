const CACHE_NAME = "device-main-dashboard-0bc0d773b979";
const CACHE_PREFIX = "device-main-dashboard-";
const PRECACHE_URLS = [
  "./",
  "./index.html",
  "./assets/data/device_filter_data.js",
  "./assets/fonts/gotham-rounded-bold.f6281701cdb9.woff2",
  "./assets/fonts/hk-yuan-w7.a0f4d903956d.woff2"
];

self.addEventListener('install', event => {
  event.waitUntil(caches.open(CACHE_NAME).then(cache => cache.addAll(PRECACHE_URLS)));
  self.skipWaiting();
});

self.addEventListener('activate', event => {
  event.waitUntil(caches.keys().then(keys => Promise.all(
    keys.filter(key => key.startsWith(CACHE_PREFIX) && key !== CACHE_NAME)
      .map(key => caches.delete(key))
  )));
  self.clients.claim();
});

self.addEventListener('fetch', event => {
  if (event.request.method !== 'GET') return;
  const url = new URL(event.request.url);
  if (url.origin !== self.location.origin) return;
  event.respondWith(
    fetch(event.request).then(response => {
      if (response.ok) {
        const copy = response.clone();
        caches.open(CACHE_NAME).then(cache => cache.put(event.request, copy));
      }
      return response;
    }).catch(() => caches.match(event.request).then(cached =>
      cached || (event.request.mode === 'navigate' ? caches.match('./index.html') : undefined)
    ))
  );
});
