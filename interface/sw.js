// Service worker · Solo cachea el armazón, jamás una respuesta de la memoria.
//
// Cachear /api/* haría que la interfaz enseñara recuerdos viejos como si
// fueran los de ahora, y que un contador de la frontera sobreviviera al texto
// que lo produjo. Un número correcto en el momento equivocado es un número
// falso, así que aquí solo entra lo que no cambia.
const Cache = "aurelius-armazon-v1";
const Armazon = ["/", "/app.html", "/app.css", "/app.js", "/manifest.json"];

self.addEventListener("install", (e) => {
  e.waitUntil(caches.open(Cache).then((c) => c.addAll(Armazon)));
});

self.addEventListener("activate", (e) => {
  e.waitUntil(caches.keys().then((ks) =>
    Promise.all(ks.filter((k) => k !== Cache).map((k) => caches.delete(k)))));
});

self.addEventListener("fetch", (e) => {
  const url = new URL(e.request.url);
  if (url.pathname.startsWith("/api/")) return;   // nunca de la caché
  e.respondWith(caches.match(e.request).then((r) => r || fetch(e.request)));
});
