import { defineConfig } from "vite";

// Aurelius se sirve bajo /aurelius (destino canónico: la cara del Puente del
// dashboard ya apunta ahí). El gateway de fragua monta ~/aurelius/dist en
// /aurelius — paso de despliegue, coordinado (como el Nexo en /ui).
export default defineConfig({
  base: "/aurelius/",
  build: {
    target: "es2022",
  },
});
