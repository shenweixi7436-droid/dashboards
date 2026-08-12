const CACHE_NAME = 'material-main-dashboard-60f6f8bc4dea';
const PRECACHE_URLS = [
  "./",
  "./index.html",
  "./assets/data/material_freight_dashboard_data.6848da8ee75f.js",
  "./assets/data/material_development_gantt_data.55a02038c5f5.js",
  "./assets/data/inventory_outbound_data.eacf6ae1d96a.js",
  "./assets/data/supplier_payable_data.20683c5951cf.js",
  "./assets/data/equipment_region_data.7c29d16c2b11.js",
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
