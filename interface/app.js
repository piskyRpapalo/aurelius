/* Aurelius · la cara premium.
 *
 * LA Regla QUE Gobierna Este Fichero: la interfaz nunca cuenta.
 * Todo número que se pinta sale del payload que devolvió el endpoint. No hay
 * un solo `.length` sobre hallazgos, ni un contador local que se incremente.
 * Si el servidor no lo dijo, aquí no se enseña.
 *
 * Y la segunda: fail-closed. Si el filtro no termina, el envío se apaga y NO
 * hay forma de reactivarlo sin que el filtro corra limpio. No existe el botón
 * de "mandar de todos modos" porque no existe la ruta.
 */
"use strict";

const $ = (id) => document.getElementById(id);
const paneles = ["chat", "frontera", "captura"];
let panelActual = 0;
let filtroCaido = false;

/* --- navegación · pestañas y deslizar ---------------------------------- */
function mostrar(i) {
  panelActual = Math.max(0, Math.min(paneles.length - 1, i));
  paneles.forEach((p, n) => {
    $("panel-" + p).hidden = n !== panelActual;
    document.querySelector(`[data-panel="${p}"]`)
            .setAttribute("aria-selected", String(n === panelActual));
  });
  if (paneles[panelActual] === "captura") cargarCuaderno();
}
document.querySelectorAll(".pestanas button").forEach((b, n) =>
  b.addEventListener("click", () => mostrar(n)));

/* Deslizar. Se exige que el gesto sea claramente horizontal (2:1) o el
 * scroll vertical del hilo cambiaría de panel sin querer. */
let x0 = null, y0 = null;
const carril = $("carril");
carril.addEventListener("touchstart", (e) => {
  x0 = e.changedTouches[0].clientX; y0 = e.changedTouches[0].clientY;
}, { passive: true });
carril.addEventListener("touchend", (e) => {
  if (x0 === null) return;
  const dx = e.changedTouches[0].clientX - x0;
  const dy = e.changedTouches[0].clientY - y0;
  if (Math.abs(dx) > 60 && Math.abs(dx) > Math.abs(dy) * 2) {
    mostrar(panelActual + (dx < 0 ? 1 : -1));
  }
  x0 = y0 = null;
}, { passive: true });

/* --- estado ------------------------------------------------------------ */
async function estado() {
  try {
    const r = await fetch("/api/estado");
    const d = await r.json();
    $("estado").textContent = d.motor
      ? `memoria lista · ${d.turnos.turnos} turnos · ${d.turnos.consentidos} consentidos`
      : "sin cerebro: puedo preguntar y recordar, no conversar";
    $("enviar").disabled = !d.motor;
  } catch {
    $("estado").textContent = "no alcanzo al servidor";
    $("enviar").disabled = true;
  }
}

/* --- hablar ------------------------------------------------------------ */
function burbuja(texto, clase) {
  const li = document.createElement("li");
  if (clase) li.className = clase;
  li.textContent = texto;
  $("hilo").appendChild(li);
  li.scrollIntoView({ block: "end" });
  return li;
}

$("form-chat").addEventListener("submit", async (e) => {
  e.preventDefault();
  if (filtroCaido) return;                       // estado 4: nada sale
  const texto = $("dicho").value.trim();
  if (!texto) return;
  $("dicho").value = "";
  burbuja(texto, "mio");
  $("enviar").disabled = true;
  const esperando = burbuja("pensando… en un teléfono esto son minutos", "espera");
  try {
    const r = await fetch("/api/charla", {
      method: "Post", headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ texto }),
    });
    const d = await r.json();
    esperando.remove();
    if (r.ok) {
      burbuja(d.texto);
    } else {
      // Un motor que tardó y uno que falló se dicen distinto: se arreglan
      // distinto, y decirlos igual manda a mirar donde no es.
      burbuja(d.estado === "tarde"
        ? `tardó más de la cuenta: ${d.motivo}`
        : `no pude responder (${d.motivo || r.status})`, "malo");
    }
  } catch (err) {
    esperando.remove();
    burbuja("no alcancé al servidor", "malo");
  }
  $("enviar").disabled = false;
  estado();
});

/* --- frontera ---------------------------------------------------------- */
const sw = $("switch");
let redaccion = true;

function pintarApagado() {
  $("tarjeta-frontera").classList.add("is-off");
  $("tarjeta-frontera").classList.remove("is-blocked");
  $("switch-label").textContent = "Redacción apagada";
  $("insignia").className = "insignia insignia-warn";
  $("insignia").textContent = "el texto sale tal cual";
  $("hallazgos").replaceChildren();
  $("bloqueado").hidden = true;
  // Estado 2: NINGÚN contador. Una lista vacía se leería como "no se encontró
  // nada", y no se buscó nada.
  $("vacio").hidden = false;
  $("vacio").textContent = "Sin contador: no se ha mirado.";
  $("payload").textContent = "(no se hace ninguna llamada)";
}

sw.addEventListener("click", () => {
  if (filtroCaido) return;            // con el filtro caído no se toca nada
  redaccion = !redaccion;
  sw.classList.toggle("is-on", redaccion);
  sw.setAttribute("aria-checked", String(redaccion));
  $("probar").disabled = !redaccion;
  if (!redaccion) pintarApagado();
  else {
    $("tarjeta-frontera").classList.remove("is-off");
    $("switch-label").textContent = "Redacción activa";
    $("insignia").className = "insignia insignia-ok";
    $("insignia").textContent = "sin medir";
    $("vacio").hidden = true;
    $("payload").textContent = "(sin llamada todavía)";
  }
});

$("probar").addEventListener("click", async () => {
  const texto = $("prueba").value;
  if (!texto.trim()) return;
  $("probar").disabled = true;
  try {
    const r = await fetch("/api/frontera", {
      method: "Post", headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ texto }),
    });
    const d = await r.json();
    $("payload").textContent = JSON.stringify(d, null, 2);

    if (r.status === 409) {           // Estado 4 · fail-closed
      filtroCaido = true;
      $("tarjeta-frontera").classList.add("is-blocked");
      $("insignia").className = "insignia insignia-stop";
      $("insignia").textContent = "envío bloqueado";
      $("hallazgos").replaceChildren();
      $("vacio").hidden = true;
      $("bloqueado").hidden = false;
      $("bloqueado").textContent =
        "El filtro no pudo terminar, así que no se envía nada. " +
        "El botón sigue apagado hasta que el filtro corra limpio.";
      $("enviar").disabled = true;
      sw.disabled = true;
      return;                          // y `probar` queda deshabilitado
    }

    // Los contadores salen del payload. Ni uno se calcula aquí.
    const hallazgos = d.hallazgos || [];
    const lista = $("hallazgos");
    lista.replaceChildren();
    for (const h of hallazgos) {
      const li = document.createElement("li");
      const p = document.createElement("span");
      p.className = "policy"; p.textContent = h.policy;
      const c = document.createElement("span");
      c.className = "count"; c.textContent = h.count;   // del payload
      li.append(p, c); lista.appendChild(li);
    }
    // Se pregunta por el primer elemento, no por el tamano de la lista: aqui
    // la pregunta es "¿hay algun hallazgo?" y no "¿cuantos hay?". El guardian
    // prohibe medir el tamano en un fichero de interfaz, y hace bien -- un
    // tamano es un recuento aunque se use como booleano, y los recuentos son
    // del servidor. Asi esta linea no puede volverse un numero por accidente.
    if (hallazgos[0]) {                      // Estado 1
      $("insignia").className = "insignia insignia-ok";
      $("insignia").textContent = "con hallazgos";
      $("vacio").hidden = true;
    } else {                                 // Estado 3 · declarado, no en blanco
      $("insignia").className = "insignia insignia-ok";
      $("insignia").textContent = "nada redactado";
      $("vacio").hidden = false;
      $("vacio").textContent =
        "Nada redactado — el texto ya estaba limpio. Declarado, no en blanco.";
    }
    $("bloqueado").hidden = true;
    $("probar").disabled = false;
  } catch {
    $("payload").textContent = "(la llamada no llegó)";
    $("probar").disabled = false;
  }
});

/* --- cuaderno ---------------------------------------------------------- */
async function cargarCuaderno() {
  try {
    const r = await fetch("/api/captura");
    const d = await r.json();
    $("recuento").textContent =
      `${d.recuento.turnos} turnos · ${d.recuento.consentidos} consentidos · ` +
      `${d.recuento.corregidos} corregidos`;
    const ul = $("turnos");
    ul.replaceChildren();
    for (const t of d.turnos) {
      const li = document.createElement("li");
      const p = document.createElement("div");
      p.className = "p"; p.textContent = t.prompt;
      const resp = document.createElement("div");
      resp.className = "r"; resp.textContent = t.correccion || t.respuesta;
      const acc = document.createElement("div");
      acc.className = "acciones";
      const si = document.createElement("button");
      si.className = "si"; si.textContent = "consentir";
      si.disabled = t.consent;
      const no = document.createElement("button");
      no.className = "no"; no.textContent = "retirar";
      no.disabled = !t.consent;
      const marca = document.createElement("span");
      marca.className = "marca " + (t.consent ? "si" : "no");
      marca.textContent = t.consent ? "consentido" : "sin consentir";
      si.addEventListener("click", () => marcar(t.id, true));
      no.addEventListener("click", () => marcar(t.id, false));
      acc.append(si, no, marca);
      li.append(p, resp, acc);
      ul.appendChild(li);
    }
  } catch {
    $("recuento").textContent = "no alcanzo al servidor";
  }
}

/* Uno por petición. El carbono marca de uno en uno: no hay "consentir todo",
 * porque un consentimiento en bloque no es un consentimiento. */
async function marcar(id, consent) {
  await fetch("/api/captura", {
    method: "Post", headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ id, consent }),
  });
  cargarCuaderno();
  estado();
}

/* --- arranque ---------------------------------------------------------- */
if ("serviceWorker" in navigator) {
  navigator.serviceWorker.register("/sw.js").catch(() => {});
}
estado();
