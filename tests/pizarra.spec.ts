import { expect, test, type Page } from "@playwright/test";

/* La Pizarra (§BLOQUE 4): terminal SIMULADO, cliente-side, cero ejecución. Verifica
   el filesystem ficticio, las salidas HONESTAS (comando no implementado NO inventa
   salida), el badge permanente, el puente COPIAR, y el scaffolding fading (al
   demostrar un comando, deja de explicarlo y solo lo propone). */

async function abrir(page: Page): Promise<void> {
  await page.addInitScript(() => {
    try { localStorage.removeItem("aurelius.pizarra.demostrados"); } catch { /* memoria */ }
  });
  await page.goto("/aurelius_face.html");
  await page.click("#au-pizarra");
  await page.waitForSelector("#pz-in", { state: "visible", timeout: 6000 });
}
async function correr(page: Page, cmd: string): Promise<void> {
  await page.fill("#pz-in", cmd);
  await page.press("#pz-in", "Enter");
}

test("Pizarra: badge + filesystem ficticio (pwd/ls/mkdir/echo>/cat)", async ({ page }) => {
  await abrir(page);
  await expect(page.locator(".pz-badge")).toContainText("RUNS NOTHING");
  await correr(page, "pwd");
  await expect(page.locator(".pz-salida").last()).toHaveText("/");
  await correr(page, "ls");
  await expect(page.locator(".pz-salida").last()).toContainText("notas.txt");
  await correr(page, "mkdir foo");
  await correr(page, "ls");
  await expect(page.locator(".pz-salida").last()).toContainText("foo");
  await correr(page, "echo hola > f.txt");
  await correr(page, "cat f.txt");
  await expect(page.locator(".pz-salida").last()).toHaveText("hola");
});

test("Pizarra: comando NO implementado no inventa salida (honest sensors)", async ({ page }) => {
  await abrir(page);
  await correr(page, "sudo rm -rf /");
  const ultima = page.locator(".pz-salida").last();
  await expect(ultima).toContainText("not on the slate yet");
  await expect(ultima).toHaveClass(/pz-err/);
});

test("Pizarra: scaffolding fading — al demostrar, deja de explicar; y hay puente COPIAR", async ({ page }) => {
  await abrir(page);
  const chipLs = page.locator('.pz-chip[data-cmd="ls"]');
  await expect(chipLs.locator(".pz-chip-exp")).toBeVisible();      // aún explica
  await correr(page, "ls");
  await expect(chipLs).toHaveClass(/pz-chip-hecho/);               // demostrado
  await expect(chipLs.locator(".pz-chip-exp")).toHaveCount(0);     // ya solo propone
  await expect(page.locator(".pz-copiar").first()).toBeVisible();  // "copy → tu terminal"
});
