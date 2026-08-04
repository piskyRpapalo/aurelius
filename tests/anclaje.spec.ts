import { expect, test } from "@playwright/test";

/* EL ANCLAJE (Método v1 §3) — tests exigidos por la Fase 1, tarea 4:
 *   · la fórmula del delta con casos límite (confianza 1 y 5, los tres resultados)
 *   · que la media móvil ignora los módulos sin resultado
 *   · que el borrado deja el registro vacío y no corrompe el resto
 *
 * La fórmula se ejerce a través del MÓDULO REAL cargado en la página, no contra
 * una reimplementación en el test. Un test que recalcula la fórmula por su cuenta
 * pasa aunque el módulo esté mal: solo comprueba que dos copias coinciden.
 *
 * Los tests de persistencia escriben de verdad en el servidor (no hay mock): el
 * Anclaje es un registro en disco y un mock no probaría lo que importa. Cada
 * proyecto de viewport usa su PROPIO slug — la suite corre los 5 en paralelo y
 * compartir el registro los haría pisarse entre sí. */

/** Forma de window.AURELIUS_ANCLAJE tal como la expone interface/anclaje.js.
 *  Tipada aquí (y no con `any`) para que el gate de tipos vigile también la
 *  frontera del test: si el módulo cambia su API, esto deja de compilar. */
interface AnclajeAPI {
  readonly VENTANA: number;
  readonly CERCA_DE_CERO: number;
  confianzaNormalizada(confianza: unknown): number | null;
  resultadoNormalizado(resultado: unknown): number | null;
  delta(confianza: unknown, resultado: unknown): number | null;
  emparejar(
    declaraciones: unknown[],
    resultados: unknown[],
  ): { pares: Array<{ modulo: string; delta: number | null }>; pendientes: Array<{ modulo: string }> };
  mediaMovil(pares: unknown[], n?: number): number | null;
  curva(pares: unknown[], n?: number): unknown[];
  etiquetaDe(valor: number): string | null;
}

type VentanaConAnclaje = { AURELIUS_ANCLAJE: AnclajeAPI };

/** Slug del soberano para un test. Lleva el nombre del proyecto Y una etiqueta
 *  propia por test: la suite corre 5 viewports en paralelo Y los tests de un
 *  mismo fichero también, así que un slug compartido hace que dos tests se
 *  escriban encima del registro. Máx. 40 caracteres, [a-z0-9-] (lista blanca
 *  del servidor). */
function slugDe(info: { project: { name: string } }, etiqueta: string): string {
  return `t-anc-${etiqueta}-${info.project.name}`.toLowerCase().replace(/[^a-z0-9-]+/g, "-").slice(0, 40);
}

async function irAlAnclaje(page: import("@playwright/test").Page, slug: string): Promise<void> {
  await page.addInitScript((s: string) => localStorage.setItem("aurelius.soberano", s), slug);
  await page.goto("/anclaje.html");
  await page.waitForSelector("#an-indicador, #an-ficheros-vacio");
}

/** Deja el registro de este slug vacío antes y después de cada prueba. */
async function limpiar(page: import("@playwright/test").Page, slug: string): Promise<void> {
  await page.request.post(`/api/anclaje/borrar?soberano=${slug}`, { data: {} });
}

// ─────────────────────────── LA FÓRMULA (§3.3) ──────────────────────────────

test("el delta cubre los casos límite: confianza 1 y 5 × los tres resultados", async ({ page }, info) => {
  await irAlAnclaje(page, slugDe(info, "delta"));

  const casos = await page.evaluate(() => {
    const A = (window as unknown as VentanaConAnclaje).AURELIUS_ANCLAJE;
    const combos: Array<[number, string]> = [
      [1, "completo"], [1, "parcial"], [1, "no"],
      [5, "completo"], [5, "parcial"], [5, "no"],
    ];
    return combos.map(([c, r]) => ({ c, r, delta: A.delta(c, r) }));
  });

  // confianza 1 → confianza_normalizada = (1-1)/4 = 0
  expect(casos[0]).toEqual({ c: 1, r: "completo", delta: -1 }); // 0 - 1.0 → infraestimación máxima
  expect(casos[1]).toEqual({ c: 1, r: "parcial", delta: -0.5 }); // 0 - 0.5
  expect(casos[2]).toEqual({ c: 1, r: "no", delta: 0 });         // 0 - 0.0 → calibrado
  // confianza 5 → confianza_normalizada = (5-1)/4 = 1
  expect(casos[3]).toEqual({ c: 5, r: "completo", delta: 0 });   // 1 - 1.0 → calibrado
  expect(casos[4]).toEqual({ c: 5, r: "parcial", delta: 0.5 });  // 1 - 0.5
  expect(casos[5]).toEqual({ c: 5, r: "no", delta: 1 });         // 1 - 0.0 → sobreestimación máxima
});

test("la entrada inválida da null, jamás un número plausible", async ({ page }, info) => {
  await irAlAnclaje(page, slugDe(info, "nulos"));

  const r = await page.evaluate(() => {
    const A = (window as unknown as VentanaConAnclaje).AURELIUS_ANCLAJE;
    return {
      cero: A.confianzaNormalizada(0),
      seis: A.confianzaNormalizada(6),
      decimal: A.confianzaNormalizada(3.5),
      vacio: A.confianzaNormalizada(""),
      resultadoRaro: A.resultadoNormalizado("casi"),
      // Un módulo declarado y SIN resultado no tiene delta. Ojo: si esto
      // devolviera 0 se leería como "calibración perfecta" sin haber medido nada.
      sinResultado: A.delta(3, null),
    };
  });

  expect(r.cero).toBeNull();
  expect(r.seis).toBeNull();
  expect(r.decimal).toBeNull();
  expect(r.vacio).toBeNull();
  expect(r.resultadoRaro).toBeNull();
  expect(r.sinResultado).toBeNull();
});

// ─────────────────────── LA MEDIA MÓVIL IGNORA LO NO MEDIDO ─────────────────

test("la media móvil ignora los módulos sin resultado — no cuentan ni como cero", async ({ page }, info) => {
  await irAlAnclaje(page, slugDe(info, "media"));

  const r = await page.evaluate(() => {
    const A = (window as unknown as VentanaConAnclaje).AURELIUS_ANCLAJE;
    const decs = [
      { modulo: "a", confianza: "5", sin_ayuda: "si" }, // delta +1
      { modulo: "b", confianza: "1", sin_ayuda: "no" }, // delta -1
      { modulo: "c", confianza: "5", sin_ayuda: "si" }, // declarado y SIN terminar
      { modulo: "d", confianza: "3", sin_ayuda: "si" }, // declarado y SIN terminar
    ];
    const res = [
      { modulo: "a", resultado: "no", fecha: "2026-08-04" },
      { modulo: "b", resultado: "completo", fecha: "2026-08-04" },
    ];
    const emp = A.emparejar(decs, res);
    return {
      media: A.mediaMovil(emp.pares),
      pendientes: emp.pendientes.map((p) => p.modulo),
      // Si los dos pendientes contaran como cero, la media sería (1-1+0+0)/4 = 0
      // por el motivo equivocado. Se comprueba el DIVISOR, no solo el resultado.
      medidos: emp.pares.filter((p) => p.delta !== null).length,
    };
  });

  expect(r.media).toBe(0); // (+1 −1) / 2 — dos módulos medidos, no cuatro
  expect(r.medidos).toBe(2);
  expect(r.pendientes).toEqual(["c", "d"]);
});

test("la ventana son los últimos 5 medidos, y un registro vacío es NO DATA (no cero)", async ({ page }, info) => {
  await irAlAnclaje(page, slugDe(info, "ventana"));

  const r = await page.evaluate(() => {
    const A = (window as unknown as VentanaConAnclaje).AURELIUS_ANCLAJE;
    // Seis módulos medidos: el primero debe quedar FUERA de la ventana de 5.
    const decs = [1, 2, 3, 4, 5, 6].map((i) => ({ modulo: `m${i}`, confianza: i === 1 ? "5" : "1", sin_ayuda: "si" }));
    const res = [1, 2, 3, 4, 5, 6].map((i) => ({ modulo: `m${i}`, resultado: i === 1 ? "no" : "no", fecha: "2026-08-04" }));
    const emp = A.emparejar(decs, res);
    return {
      media: A.mediaMovil(emp.pares),
      ventana: A.VENTANA,
      vacio: A.mediaMovil([]),
      sinDatos: A.mediaMovil([{ modulo: "x", delta: null }]),
    };
  });

  expect(r.ventana).toBe(5);
  // m1 (delta +1) queda fuera; los cinco últimos tienen confianza 1 y resultado
  // "no completado" → delta 0 cada uno → media 0.
  expect(r.media).toBe(0);
  // Sin ningún módulo medido NO hay indicador. null, jamás 0: un cero se leería
  // como "calibrado" sin haber medido nada (honest sensors).
  expect(r.vacio).toBeNull();
  expect(r.sinDatos).toBeNull();
});

// ───────────────────────────── LOS SUELOS (§3.4) ────────────────────────────

test("la fórmula queda impresa en la interfaz, reproducible a mano", async ({ page }, info) => {
  await irAlAnclaje(page, slugDe(info, "formula"));

  const formula = await page.textContent("#an-formula");
  expect(formula).toContain("(confianza - 1) / 4");
  expect(formula).toContain("completo = 1.0");
  expect(formula).toContain("parcial  = 0.5");
  expect(formula).toContain("no completado  = 0.0");
  expect(formula).toContain("delta = confianza_normalizada - resultado_normalizado");
  // El umbral de "calibrado" también está a la vista: §3.4 prohíbe los ajustes
  // ocultos, y un umbral que no se enseña es exactamente eso.
  expect(formula).toContain("-> calibrado");
});

test("un registro vacío muestra NO DATA y no un indicador inventado", async ({ page }, info) => {
  const slug = slugDe(info, "vacio");
  await irAlAnclaje(page, slug);
  await limpiar(page, slug);
  await page.reload();
  await page.waitForSelector("#an-indicador");

  await expect(page.locator("#an-indicador")).toHaveText(/NO DATA/);
  await expect(page.locator("#an-ficheros-vacio")).toBeVisible();
});

// ─────────────────── EL BORRADO TOTAL, SIN FRICCIÓN (§3.4) ──────────────────

test("el borrado deja el registro vacío y NO corrompe el resto del estado", async ({ page }, info) => {
  const slug = slugDe(info, "borrado");
  await irAlAnclaje(page, slug);
  await limpiar(page, slug);

  // Estado del Camino ajeno al Anclaje: debe sobrevivir intacto al borrado.
  const pref = await page.request.post(`/api/preferencia?soberano=${slug}`, {
    data: { nivel: "avanzado", verbosidad: "breve" },
  });
  expect(pref.ok()).toBeTruthy();

  // Un módulo completo: declaración + resultado.
  await page.request.post(`/api/anclaje/declaracion?soberano=${slug}`, {
    data: { modulo: "tema-1", confianza: 5, sin_ayuda: true },
  });
  await page.request.post(`/api/anclaje/resultado?soberano=${slug}`, {
    data: { modulo: "tema-1", resultado: "no" },
  });

  await page.reload();
  await page.waitForSelector("#an-indicador");
  await expect(page.locator("#an-indicador")).toHaveAttribute("data-etiqueta", "sobre");
  await expect(page.locator("#an-fichero-dec")).toContainText("tema-1");

  // UN SOLO CLIC. Sin diálogo de confirmación: §3.4 lo exige sin fricción y sin
  // preguntas culpabilizadoras. Si alguien añade un confirm(), este test se cuelga.
  await page.click("#an-wipe");
  await page.waitForSelector("#an-ficheros-vacio");

  await expect(page.locator("#an-indicador")).toHaveText(/NO DATA/);
  const registro = await (await page.request.get(`/api/anclaje?soberano=${slug}`)).json();
  expect(registro.declaraciones).toEqual([]);
  expect(registro.resultados).toEqual([]);
  expect(registro.crudo.declaraciones).toBe("");
  expect(registro.crudo.resultados).toBe("");

  // Y lo que NO es el Anclaje sigue en pie: borrar tu diario de calibración no
  // te cuesta tu progreso en el Camino.
  const estado = await (await page.request.get(`/api/estado?soberano=${slug}`)).json();
  expect(estado.nivel).toBe("avanzado");
  expect(estado.verbosidad).toBe("breve");
});

test("el registro es de anexión: una corrección es una línea nueva", async ({ page }, info) => {
  const slug = slugDe(info, "anexion");
  await page.addInitScript((s: string) => localStorage.setItem("aurelius.soberano", s), slug);
  await page.goto("/anclaje.html");
  await limpiar(page, slug);

  for (const c of [2, 4]) {
    await page.request.post(`/api/anclaje/declaracion?soberano=${slug}`, {
      data: { modulo: "tema-1", confianza: c, sin_ayuda: true },
    });
  }
  const registro = await (await page.request.get(`/api/anclaje?soberano=${slug}`)).json();
  expect(registro.declaraciones).toHaveLength(2);
  expect(registro.declaraciones[0].confianza).toBe("2");
  expect(registro.declaraciones[1].confianza).toBe("4");
  // La cabecera con la fórmula viaja dentro del propio fichero: se puede leer y
  // recalcular sin abrir la interfaz ni el código.
  expect(registro.crudo.declaraciones).toContain("(confianza - 1) / 4");

  await limpiar(page, slug);
});

test("el servidor rechaza lo que rompería la escala de la fórmula", async ({ page }, info) => {
  const slug = slugDe(info, "valida");
  await page.goto("/anclaje.html");

  const conf6 = await page.request.post(`/api/anclaje/declaracion?soberano=${slug}`, {
    data: { modulo: "tema-1", confianza: 6, sin_ayuda: true },
  });
  expect(conf6.status()).toBe(400);

  const resultadoRaro = await page.request.post(`/api/anclaje/resultado?soberano=${slug}`, {
    data: { modulo: "tema-1", resultado: "casi" },
  });
  expect(resultadoRaro.status()).toBe(400);

  // Travesía de rutas en el identificador de módulo: no debe salir del directorio.
  const escape = await page.request.post(`/api/anclaje/declaracion?soberano=${slug}`, {
    data: { modulo: "../../escape", confianza: 3, sin_ayuda: true },
  });
  expect(escape.status()).toBe(400);
});
