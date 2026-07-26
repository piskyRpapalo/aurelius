import { expect, test } from "@playwright/test";

/* Móvil y cabeceros fijos (2026-07-26). Ley dura en las dos caras de Aurelius:
   - el header queda pinneado arriba y NO se mueve al scrollear (chat largo);
   - la página no scrollea en horizontal (el header desbordaba ~36px a 360);
   - los clicables del header son ≥44px táctiles.
   Corre en los 5 viewports por projects. */

test.describe("aurelius_face · la cara", () => {
  test("el header aguanta arriba con el chat largo (no se mueve)", async ({ page }) => {
    await page.goto("/aurelius_face.html");
    await page.waitForTimeout(400);
    // Inyecta un chat largo para forzar el scroll del contenedor interno.
    await page.evaluate(() => {
      const log = document.getElementById("log")!;
      document.getElementById("vacio")?.remove();
      for (let i = 0; i < 30; i++) {
        const d = document.createElement("div");
        d.className = "msg " + (i % 2 ? "tu" : "aurelius");
        d.textContent = "Línea " + i + " — texto de prueba para forzar el scroll del chat.";
        log.appendChild(d);
      }
    });
    const header = page.locator("header");
    expect(await header.evaluate((h) => Math.round(h.getBoundingClientRect().top))).toBeLessThanOrEqual(1);
    await page.evaluate(() => {
      const log = document.getElementById("log")!;
      log.scrollTop = log.scrollHeight;
    });
    await page.waitForTimeout(150);
    expect(await header.evaluate((h) => Math.round(h.getBoundingClientRect().top))).toBeLessThanOrEqual(1);
  });

  test("la página no scrollea en horizontal", async ({ page }) => {
    await page.goto("/aurelius_face.html");
    await page.waitForTimeout(400);
    const desborde = await page.evaluate(() => document.scrollingElement!.scrollWidth - document.scrollingElement!.clientWidth);
    expect(desborde).toBeLessThanOrEqual(1);
  });

  test("clicables del header ≥44px táctiles (móvil)", async ({ page }, testInfo) => {
    const w = testInfo.project.use.viewport?.width ?? 9999;
    test.skip(w > 430, "el mínimo táctil de 44px aplica a pantallas de dedo");
    await page.goto("/aurelius_face.html");
    await page.waitForTimeout(400);
    for (const sel of [".au-lang", ".au-chemin"]) {
      const h = await page.locator(sel).evaluate((el) => Math.round(el.getBoundingClientRect().height));
      expect(h, sel).toBeGreaterThanOrEqual(44);
    }
  });
});

test.describe("camino · The Path", () => {
  test("el header queda fijo tras scrollear", async ({ page }) => {
    await page.goto("/camino.html");
    await page.waitForTimeout(600);
    const header = page.locator("header");
    await page.evaluate(() => window.scrollTo(0, document.scrollingElement!.scrollHeight));
    await page.waitForTimeout(150);
    expect(await header.evaluate((h) => Math.round(h.getBoundingClientRect().top))).toBeLessThanOrEqual(1);
  });

  test("la página no scrollea en horizontal", async ({ page }) => {
    await page.goto("/camino.html");
    await page.waitForTimeout(600);
    const desborde = await page.evaluate(() => document.scrollingElement!.scrollWidth - document.scrollingElement!.clientWidth);
    expect(desborde).toBeLessThanOrEqual(1);
  });

  test("el retour es ≥44px táctil (móvil)", async ({ page }, testInfo) => {
    const w = testInfo.project.use.viewport?.width ?? 9999;
    test.skip(w > 430, "el mínimo táctil de 44px aplica a pantallas de dedo");
    await page.goto("/camino.html");
    await page.waitForTimeout(600);
    const retourH = await page.locator("a.retour").evaluate((el) => Math.round(el.getBoundingClientRect().height));
    expect(retourH).toBeGreaterThanOrEqual(44);
  });
});
