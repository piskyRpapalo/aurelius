import { expect, test } from "@playwright/test";

/* Modo presentación de la cara (§5.3): con ?present=1 sustituye valores sensibles por
   placeholders visibles + badge, para capturar el drawer/módulos sin fugas. Sin él,
   nada cambia. Espejo de los CRIT de scrub_check. */

const SENSIBLE =
  "node soberano at 100.82.94.83 · la-torre.tailb9e0f7.ts.net · /home/pisky/aurelius/sovereign_vault · hexelion.near · hxl-lisboa-01";

test("present=1: badge + valores sustituidos (texto inyectado tras el arranque)", async ({ page }) => {
  await page.goto("/aurelius_face.html?present=1");
  await expect(page.locator("[data-present-badge]")).toBeVisible();
  await expect(page.locator("[data-present-badge]")).toContainText("PRESENTATION MODE");
  await page.evaluate((txt) => {
    const d = document.createElement("div");
    d.id = "inj";
    d.textContent = txt;
    document.body.appendChild(d);
  }, SENSIBLE);
  await expect.poll(async () => (await page.locator("#inj").textContent()) ?? "", { timeout: 4000 })
    .not.toContain("100.82.94.83");
  const t = (await page.locator("#inj").textContent()) ?? "";
  for (const fuga of ["100.82.94.83", "soberano", "/home/pisky", "hexelion.near", "tailb9e0f7.ts.net", "hxl-lisboa-01"]) {
    expect(t).not.toContain(fuga);
  }
  for (const marca of ["node.local", "[ruta]", "wallet.example", "[clave]", "nodo"]) {
    expect(t).toContain(marca);
  }
});

test("sin ?present: sin badge y sin sustitución (cara normal)", async ({ page }) => {
  await page.goto("/aurelius_face.html");
  await expect(page.locator("[data-present-badge]")).toHaveCount(0);
});
