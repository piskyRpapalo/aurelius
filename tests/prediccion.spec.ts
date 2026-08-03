import { expect, test } from "@playwright/test";

/* Predicción previa (Apéndice B.2 del temario LLM): antes de REVELAR la RAM
 * detectada, Aurelius pide al usuario que adivine. El hueco entre lo que cree y
 * lo medido es donde ocurre el aprendizaje (efecto de generación, Bjork). Este
 * test gatea que el dato se RETENGA hasta la apuesta y que la desviación se pinte.
 *
 * Sin gateway (CI de CPU) /api/estado falla → la cara muestra "serverDown" y M0
 * no renderiza; por eso se mockean las rutas, como en el dashboard. */

async function irM0(page: import("@playwright/test").Page, ramGb: number | null): Promise<void> {
  await page.route("**/api/estado**", (r) =>
    r.fulfill({ json: { nombre: "", modulo_actual: "M0", modulos_completados: [] } }),
  );
  await page.route("**/api/inventario**", (r) =>
    ramGb === null
      ? r.abort()
      : r.fulfill({ json: { hardware: { hardware: { ram_disponible_gb: ramGb } } } }),
  );
  await page.goto("/camino.html");
}

test("la RAM detectada se RETIENE hasta que el usuario apuesta", async ({ page }) => {
  await irM0(page, 64);
  // El gate de predicción está a la vista; el análisis detectado, oculto.
  await expect(page.locator("#on-pred")).toBeVisible();
  await expect(page.locator("#on-hw-wrap")).toBeHidden();
  // El valor medido NO se ve todavía: no se puede "leer la respuesta" antes de adivinar.
  await expect(page.locator("#on-hw")).toBeHidden();
});

test("al revelar tras la apuesta se pinta la desviación firmada", async ({ page }) => {
  await irM0(page, 64);
  await page.locator("#on-pred-ram").fill("16");
  await page.locator("#on-pred-btn").click();
  // El gate desaparece; el análisis + la desviación aparecen.
  await expect(page.locator("#on-pred")).toBeHidden();
  await expect(page.locator("#on-hw-wrap")).toBeVisible();
  // Desviación: apostó 16, detectado 64, se desvió 48 — números en todo idioma.
  const delta = page.locator("#on-pred-delta");
  await expect(delta).toContainText("16");
  await expect(delta).toContainText("64");
  await expect(delta).toContainText("48");
});

test("una apuesta vacía o inválida no revela — pide adivinar primero", async ({ page }) => {
  await irM0(page, 64);
  await page.locator("#on-pred-btn").click(); // sin escribir nada
  await expect(page.locator("#on-hw-wrap")).toBeHidden();
  await expect(page.locator("#on-pred-err")).not.toBeEmpty();
});

test("sin medición: se declara honesto, no se inventa un marcador", async ({ page }) => {
  await irM0(page, null); // inventario cae → RAM no reportada
  await page.locator("#on-pred-ram").fill("32");
  await page.locator("#on-pred-btn").click();
  await expect(page.locator("#on-hw-wrap")).toBeVisible();
  // honest sensors: la apuesta se muestra, pero NO hay una desviación fabricada.
  await expect(page.locator("#on-pred-delta")).toContainText("32");
});
