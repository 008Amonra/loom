// TSG Prompt Forge – Service Worker v1.0
const CACHE = "tsg-forge-v1";
const SHELL = [
  "/TSG-prompt-forge.html",
  "/TSG-prompt-forge.css",
  "/TSG-prompt-forge.js",
  "/icon-192.png",
  "/icon-512.png",
  "/apple-touch-icon.png"
];

self.addEventListener("install", (e) => {
  e.waitUntil(
    caches.open(CACHE).then((c) => c.addAll(SHELL)).then(() => self.skipWaiting())
  );
});

self.addEventListener("activate", (e) => {
  e.waitUntil(
    caches.keys().then((keys) =>
      Promise.all(keys.filter((k) => k !== CACHE).map((k) => caches.delete(k)))
    ).then(() => self.clients.claim())
  );
});

self.addEventListener("fetch", (e) => {
  // Network-first for API calls, cache-first for shell
  if (e.request.url.includes("api.") || e.request.url.includes("paypal")) return;
  
  e.respondWith(
    caches.match(e.request).then((cached) => {
      if (cached) return cached;
      return fetch(e.request).then((resp) => {
        if (resp.status === 200 && e.request.method === "GET") {
          const clone = resp.clone();
          caches.open(CACHE).then((c) => c.put(e.request, clone));
        }
        return resp;
      }).catch(() => {
        // Offline fallback
        if (e.request.destination === "document") {
          return caches.match("/TSG-prompt-forge.html");
        }
      });
    })
  );
});
