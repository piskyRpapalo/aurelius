import { defineConfig } from "@playwright/test";

/* Viewports de la misión Móvil y Cabeceros Fijos (2026-07-26): 360 (Android
   común) · 390 (referencia dura) · 768 · 1280 · 1440. Corre contra el servidor
   real de la cara (scripts/servir_interfaz.py, :8050). El estado del Camino se
   lee de sovereign_vault/estado_del_soberano.json (M0 por defecto). */
export default defineConfig({
  testDir: "./tests",
  fullyParallel: true,
  reporter: [["list"]],
  use: {
    baseURL: "http://127.0.0.1:8050",
  },
  projects: [
    { name: "movil-360", use: { viewport: { width: 360, height: 800 } } },
    { name: "movil-390", use: { viewport: { width: 390, height: 844 } } },
    { name: "tablet-768", use: { viewport: { width: 768, height: 1024 } } },
    { name: "escritorio-1280", use: { viewport: { width: 1280, height: 800 } } },
    { name: "escritorio-1440", use: { viewport: { width: 1440, height: 900 } } },
  ],
  webServer: {
    command: "python3 scripts/servir_interfaz.py --puerto 8050 --host 127.0.0.1",
    url: "http://127.0.0.1:8050/aurelius_face.html",
    reuseExistingServer: true,
    timeout: 20_000,
  },
});
