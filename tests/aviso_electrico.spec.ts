import { expect, test } from "@playwright/test";

/* ADVERTENCIA ELÉCTRICA (Método v1 §2.3) — «aparece al inicio del tema, no en un
 * pie de página, y no se puede desactivar».
 *
 * Los tres verbos de esa frase se comprueban aquí por separado: que APARECE en un
 * tema eléctrico, que está al INICIO, y que no hay forma de DESACTIVARLA. El
 * último es el que se olvida y el que importa: una advertencia con interruptor es
 * una advertencia que alguien apagará.
 *
 * El componente se ejerce sobre camino.html, que ya lo carga. No existe todavía
 * ningún tema eléctrico —la Fase 1 no autoriza construir temas—, así que el test
 * monta el componente sobre un contenedor propio, que es exactamente lo que hará
 * la vista de tema cuando se construya. */

interface AvisoAPI {
  readonly TEMAS_ELECTRICOS: readonly string[];
  esElectrico(tema: unknown): boolean;
  verificar(raiz: Element | Document): boolean;
  montar(opts: { raiz?: Element; tema?: string }): boolean;
}

type VentanaConAviso = { AURELIUS_AVISO_ELECTRICO: AvisoAPI };

async function irAlHost(page: import("@playwright/test").Page): Promise<void> {
  // camino.html carga aviso_electrico.js; /api/estado se mockea porque el CI no
  // tiene el backend con estado (mismo patrón que prediccion.spec.ts).
  await page.route("**/api/estado**", (r) =>
    r.fulfill({ json: { nombre: "", modulo_actual: "M0", modulos_completados: [] } }),
  );
  await page.goto("/camino.html");
  await page.waitForFunction(() => "AURELIUS_AVISO_ELECTRICO" in window);
}

test("los temas eléctricos están declarados y la lista está congelada", async ({ page }) => {
  await irAlHost(page);

  const r = await page.evaluate(() => {
    const A = (window as unknown as VentanaConAviso).AURELIUS_AVISO_ELECTRICO;
    const antes = A.TEMAS_ELECTRICOS.length;
    // Sacar un tema de la lista en caliente sería desactivar la advertencia por
    // la puerta de atrás. La lista está congelada: el intento no hace nada.
    try { (A.TEMAS_ELECTRICOS as string[]).length = 0; } catch { /* modo estricto */ }
    try { (A.TEMAS_ELECTRICOS as string[]).pop(); } catch { /* modo estricto */ }
    return {
      antes,
      despues: A.TEMAS_ELECTRICOS.length,
      lista: [...A.TEMAS_ELECTRICOS],
      congelada: Object.isFrozen(A.TEMAS_ELECTRICOS),
      tema2: A.esElectrico("tema-2"),
      mision2: A.esElectrico("mision-2"),
      tema1: A.esElectrico("tema-1"),
      basura: A.esElectrico(null),
    };
  });

  expect(r.congelada).toBe(true);
  expect(r.despues).toBe(r.antes);
  expect(r.lista).toContain("tema-2"); // Electricidad continua (<= 24 V CC)
  expect(r.lista).toContain("tema-3"); // Componentes
  expect(r.lista).toContain("mision-2"); // El Circuito
  expect(r.tema2).toBe(true);
  expect(r.mision2).toBe(true);
  expect(r.tema1).toBe(false); // Magnitudes y medida: no toca electricidad
  expect(r.basura).toBe(false);
});

test("se renderiza como PRIMER hijo del tema, no en un pie de página", async ({ page }) => {
  await irAlHost(page);

  const r = await page.evaluate(() => {
    const A = (window as unknown as VentanaConAviso).AURELIUS_AVISO_ELECTRICO;
    const cont = document.createElement("div");
    cont.innerHTML = "<h2>Ley de Ohm</h2><p>contenido del tema</p>";
    document.body.appendChild(cont);
    const montado = A.montar({ raiz: cont, tema: "tema-2" });
    const primero = cont.firstElementChild;
    return {
      montado,
      esPrimero: primero?.getAttribute("data-aviso-electrico") === "obligatorio",
      texto: cont.textContent ?? "",
      // Idempotente: montarla dos veces no la duplica.
      segundaVez: A.montar({ raiz: cont, tema: "tema-2" }),
      cuantas: cont.querySelectorAll("[data-aviso-electrico]").length,
    };
  });

  expect(r.montado).toBe(true);
  expect(r.esPrimero).toBe(true);
  expect(r.segundaVez).toBe(true);
  expect(r.cuantas).toBe(1);

  // El contenido literal de §2.3, no una paráfrasis suavizada.
  expect(r.texto).toContain("24");
  expect(r.texto).toMatch(/3\.3 V, 5 V, 12 V/);
  expect(r.texto).toMatch(/110 V \/ 230 V/);
  expect(r.texto.toLowerCase()).toContain("capacitors");
  expect(r.texto.toLowerCase()).toContain("disconnected");
});

test("un tema NO eléctrico no la monta — no es un banner decorativo", async ({ page }) => {
  await irAlHost(page);

  const r = await page.evaluate(() => {
    const A = (window as unknown as VentanaConAviso).AURELIUS_AVISO_ELECTRICO;
    const cont = document.createElement("div");
    document.body.appendChild(cont);
    return {
      montado: A.montar({ raiz: cont, tema: "tema-1" }),
      presente: A.verificar(cont),
    };
  });

  expect(r.montado).toBe(false);
  expect(r.presente).toBe(false);
});

test("NO EXISTE forma de desactivarla desde la API", async ({ page }) => {
  await irAlHost(page);

  const r = await page.evaluate(() => {
    const A = (window as unknown as VentanaConAviso).AURELIUS_AVISO_ELECTRICO;
    const cont = document.createElement("div");
    document.body.appendChild(cont);

    // Todos los interruptores que a alguien se le ocurriría pasar. Ninguno debe
    // existir: montar() ignora cualquier opción que no sea {raiz, tema}.
    const intentos = [
      { raiz: cont, tema: "tema-2", desactivar: true },
      { raiz: cont, tema: "tema-2", mostrar: false },
      { raiz: cont, tema: "tema-2", silencioso: true },
      { raiz: cont, tema: "tema-2", skip: true },
      { raiz: cont, tema: "tema-2", aviso: false },
    ];
    const resultados = intentos.map((o) => {
      cont.innerHTML = "";
      return A.montar(o as { raiz: Element; tema: string }) && A.verificar(cont);
    });

    // Y la superficie pública: ni ocultar, ni desactivar, ni descartar.
    const metodos = Object.keys(A);
    return { resultados, metodos };
  });

  // Con cualquier "interruptor" que se le pase, la advertencia sigue apareciendo.
  expect(r.resultados).toEqual([true, true, true, true, true]);
  // La API expone exactamente cuatro cosas, y ninguna la apaga.
  expect(r.metodos.sort()).toEqual(["TEMAS_ELECTRICOS", "esElectrico", "montar", "verificar"]);
});

test("verificar() detecta que se ha perdido, para poder reponerla tras un re-render", async ({ page }) => {
  await irAlHost(page);

  const r = await page.evaluate(() => {
    const A = (window as unknown as VentanaConAviso).AURELIUS_AVISO_ELECTRICO;
    const cont = document.createElement("div");
    document.body.appendChild(cont);
    A.montar({ raiz: cont, tema: "tema-3" });
    const tras = A.verificar(cont);
    // Un re-render del tema que rehaga el innerHTML se la lleva por delante: es
    // el modo realista de perderla, y por eso verificar() existe.
    cont.innerHTML = "<p>tema repintado</p>";
    const perdida = A.verificar(cont);
    A.montar({ raiz: cont, tema: "tema-3" });
    return { tras, perdida, repuesta: A.verificar(cont) };
  });

  expect(r.tras).toBe(true);
  expect(r.perdida).toBe(false);
  expect(r.repuesta).toBe(true);
});

test("en un idioma sin revisar humana, lo dice DENTRO del propio aviso", async ({ page }) => {
  await irAlHost(page);

  const r = await page.evaluate(() => {
    const A = (window as unknown as VentanaConAviso).AURELIUS_AVISO_ELECTRICO;
    const I = (window as unknown as { AURELIUS_I18N: { set(l: string): void } }).AURELIUS_I18N;
    function montarEn(loc: string): string {
      I.set(loc);
      const cont = document.createElement("div");
      document.body.appendChild(cont);
      A.montar({ raiz: cont, tema: "tema-2" });
      return cont.textContent ?? "";
    }
    const ru = montarEn("ru"); // sin revisión humana → cae a inglés
    const es = montarEn("es"); // verificado
    I.set("en");
    return { ru, es };
  });

  // El texto de seguridad se muestra igual (en inglés), pero el usuario se entera
  // ahí mismo de por qué. Una advertencia de seguridad no se traduce a máquina y
  // se calla.
  expect(r.ru).toContain("24");
  expect(r.ru.toLowerCase()).toContain("shown in english");
  // En un idioma verificado no aparece esa coletilla, porque no hace falta.
  expect(r.es.toLowerCase()).not.toContain("shown in english");
  expect(r.es).toContain("24 VOLTIOS O MENOS");
});
