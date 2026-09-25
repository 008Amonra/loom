// TSG Prompt Forge - Service Worker v2
// FIX 2026-09-25: nur noch SHELL cache-first, alle anderen Seiten network-first,
// damit die Startseite + neue Elemente nicht mehr einfrieren (v1 cache-te alles).
const CACHE = "tsg-forge-v2";
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
  const req = e.request;
  if (req.method !== "GET") return;

  const url = new URL(req.url);
  if (url.origin !== self.location.origin) return; // nur same-origin

  const isShell = SHELL.some((p) => url.pathname === p);

  if (isShell) {
    // Shell: cache-first (Offline-Faehigkeit der Forge)
    e.respondWith(
      caches.match(req).then((cached) => {
        if (cached) return cached;
        return fetch(req).then((resp) => {
          if (resp.status === 200) {
            const clone = resp.clone();
            caches.open(CACHE).then((c) => c.put(req, clone));
          }
          return resp;
        });
      })
    );
    return;
  }

  // Alles andere (Startseite, Hub, assets): network-first, damit Updates durchkommen
  e.respondWith(
    fetch(req).then((resp) => {
      if (resp.status === 200 && resp.type === "basic") {
        const clone = resp.clone();
        caches.open(CACHE).then((c) => c.put(req, clone));
      }
      return resp;
    }).catch(async () => {
      const cached = await caches.match(req);
      if (cached) return cached;
      if (req.destination === "document") return caches.match("/TSG-prompt-forge.html");
    })
  );
});