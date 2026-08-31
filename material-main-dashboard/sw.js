const CACHE_NAME = 'material-main-dashboard-23f71c93f5d3';
const PRECACHE_URLS = [
  "./",
  "./index.html",
  "./assets/data/material_freight_dashboard_data.175ed8fac0ef.js",
  "./assets/data/material_development_gantt_data.e76b26bff36d.js",
  "./assets/data/inventory_outbound_data.143c6eb396ae.js",
  "./assets/data/device_weekly_outbound_data.e1298426d1c1.js",
  "./assets/data/material_weekly_outbound_data.646872236618.js",
  "./assets/data/material_inventory_data.c18db6ad4bc1.js",
  "./../material-dashboard/assets/fonts/gotham-rounded-bold.f6281701cdb9.woff2",
  "./../material-dashboard/assets/fonts/hk-yuan-w7.a0f4d903956d.woff2"
];

self.addEventListener('install', event => {
  event.waitUntil(caches.open(CACHE_NAME).then(cache => cache.addAll(PRECACHE_URLS)));
  self.skipWaiting();
});

self.addEventListener('activate', event => {
  event.waitUntil(
    caches.keys().then(keys => Promise.all(
      keys.filter(key => key.startsWith('material-main-dashboard-') && key !== CACHE_NAME)
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
