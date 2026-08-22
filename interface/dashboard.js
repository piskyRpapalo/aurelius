/* Aurelius · el tablero.
 *
 * Mismas dos reglas que el panel: la interfaz no cuenta -- los numeros vienen
 * del servidor -- y nada se promete antes de comprobarlo.
 */
"use strict";

const $ = (id) => document.getElementById(id);
let hablando = false;
let idioma = "es";

/* Las dos columnas, como en textos.py del producto. La cara declaraba hablar
 * los dos idiomas y las tenia incrustadas en castellano: el perfil decia `en`
 * y el tablero seguia en español. Una traduccion que falta es una clave que
 * falta, y aqui se ve de un vistazo. */
const T = {
  es: {
    listo: "listo para hablar",
    sin_cerebro: "puedo preguntar y recordar, todavía no conversar",
    sin_servidor: "no alcanzo al servidor",
    pensando: "pensando… esto puede tardar minutos",
    tarde: "tardó más de la cuenta. Prueba con algo más corto.",
    fallo: "no pude responder ahora mismo.",
    sin_red: "no alcancé al servidor.",
    sin_micro: "no me diste permiso para el micrófono.",
    sin_oir: "no te oí bien. Prueba a escribirlo.",
    hablar: "Hablar", escribir: "Escribir",
    escuchando: "Escuchando… toca para parar",
    nota_motor: "En un teléfono cada respuesta tarda minutos. No es que se haya colgado.",
    nota_sin: "Sin cerebro instalado, Aurelius pregunta y recuerda pero no conversa.",
    instalado: "instalado", sin_instalar: "sin instalar",
    encendido: "encendido", apagado: "apagado",
    dilo: "Dilo", memoria: "Memoria", frontera: "Frontera", ajustes: "Ajustes",
    tu_memoria: "Tu memoria", la_frontera: "La frontera", los_ajustes: "Ajustes",
  },
  en: {
    listo: "ready to talk",
    sin_cerebro: "I can ask and remember, not converse yet",
    sin_servidor: "cannot reach the server",
    pensando: "thinking… this can take minutes",
    tarde: "it took too long. Try something shorter.",
    fallo: "I could not answer just now.",
    sin_red: "I could not reach the server.",
    sin_micro: "you did not give me microphone permission.",
    sin_oir: "I did not hear you. Try writing it.",
    hablar: "Talk", escribir: "Write",
    escuchando: "Listening… tap to stop",
    nota_motor: "On a phone each answer takes minutes. It has not frozen.",
    nota_sin: "With no brain installed, Aurelius asks and remembers but does not converse.",
    instalado: "installed", sin_instalar: "not installed",
    encendido: "on", apagado: "off",
    dilo: "Say it", memoria: "Memory", frontera: "Border", ajustes: "Settings",
    tu_memoria: "Your memory", la_frontera: "The border", los_ajustes: "Settings",
  },
};
const t = (clave) => (T[idioma] || T.es)[clave];

/* --- cajones ----------------------------------------------------------- */
const velo = $("velo");
function abrir(cual) {
  document.querySelectorAll(".cajon").forEach((c) => {
    const suyo = c.id === "cajon-" + cual;
    if (suyo) { c.hidden = false; requestAnimationFrame(() => c.classList.add("abierto")); }
    else { c.classList.remove("abierto"); c.hidden = true; }
  });
  velo.classList.add("visible");
  if (cual === "memoria" || cual === "ajustes") pulso();
}
function cerrar() {
  document.querySelectorAll(".cajon").forEach((c) => {
    c.classList.remove("abierto");
    setTimeout(() => { c.hidden = true; }, 220);
  });
  velo.classList.remove("visible");
}
document.querySelectorAll("[data-cajon]").forEach((b) =>
  b.addEventListener("click", () => abrir(b.dataset.cajon)));
velo.addEventListener("click", cerrar);

/* Deslizar hacia abajo cierra el cajon: es el gesto que la gente ya conoce. */
let y0 = null;
document.querySelectorAll(".cajon").forEach((c) => {
  c.addEventListener("touchstart", (e) => { y0 = e.changedTouches[0].clientY; },
                     { passive: true });
  c.addEventListener("touchend", (e) => {
    if (y0 !== null && e.changedTouches[0].clientY - y0 > 70) cerrar();
    y0 = null;
  }, { passive: true });
});

/* --- estado ------------------------------------------------------------ */
async function pulso() {
  try {
    const r = await fetch("/api/estado");
    const d = await r.json();
    idioma = d.idioma === "en" ? "en" : "es";
    document.documentElement.lang = idioma;
    $("pulso").textContent = d.motor ? t("listo") : t("sin_cerebro");
    $("hablar").textContent = hablando ? t("escuchando")
      : (window.SpeechRecognition || window.webkitSpeechRecognition
         ? t("hablar") : t("escribir"));
    $("dicho").placeholder = idioma === "en" ? "…or write it here"
                                             : "…o escríbelo aquí";
    // Las etiquetas del marco tambien: estaban escritas en el HTML y por eso
    // no cambiaban. Un tablero que declara hablar dos idiomas y solo traduce
    // los mensajes esta a medio traducir, que se nota mas que no traducir.
    $("mandar").textContent = t("dilo");
    const rotulos = { memoria: "memoria", frontera: "frontera", ajustes: "ajustes" };
    document.querySelectorAll("[data-cajon]").forEach((b) => {
      b.textContent = t(rotulos[b.dataset.cajon]);
    });
    const titulos = { memoria: "tu_memoria", frontera: "la_frontera",
                      ajustes: "los_ajustes" };
    for (const [cual, clave] of Object.entries(titulos)) {
      const h = document.querySelector("#cajon-" + cual + " h2");
      if (h) h.textContent = t(clave);
    }
    $("hablar").disabled = !d.motor;
    $("mandar").disabled = !d.motor;
    $("m-turnos").textContent = d.turnos.turnos;
    $("m-consent").textContent = d.turnos.consentidos;
    $("m-corr").textContent = d.turnos.corregidos;
    $("a-idioma").textContent = d.idioma === "en" ? "English" : "Español";
    $("a-motor").textContent = d.motor ? t("instalado") : t("sin_instalar");
    $("a-captura").textContent = d.captura_activa ? t("encendido") : t("apagado");
    $("a-nota").textContent = d.motor ? t("nota_motor") : t("nota_sin");
  } catch {
    $("pulso").textContent = t("sin_servidor");
    $("hablar").disabled = true;
    $("mandar").disabled = true;
  }
}

/* --- decir ------------------------------------------------------------- */
function linea(texto, clase) {
  const p = document.createElement("p");
  if (clase) p.className = clase;
  p.textContent = texto;
  $("dice").appendChild(p);
  p.scrollIntoView({ block: "end" });
  return p;
}

async function turno(texto) {
  if (!texto.trim()) return;
  linea(texto, "mio");
  $("hablar").disabled = true;
  $("mandar").disabled = true;
  $("busto").classList.add("piensa");
  const esperando = linea(t("pensando"), "espera");
  try {
    const r = await fetch("/api/charla", {
      method: "POST", headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ texto }),
    });
    const d = await r.json();
    esperando.remove();
    if (r.ok) linea(d.texto);
    else linea(d.estado === "tarde" ? t("tarde") : t("fallo"), "malo");
  } catch {
    esperando.remove();
    linea(t("sin_red"), "malo");
  }
  $("busto").classList.remove("piensa");
  pulso();
}

$("escribir").addEventListener("submit", (e) => {
  e.preventDefault();
  const t = $("dicho").value;
  $("dicho").value = "";
  turno(t);
});

/* --- voz --------------------------------------------------------------- */
/* Reconocimiento del navegador. Se comprueba que existe antes de ofrecerlo:
 * un boton "Hablar" que no escucha es peor que un boton que no esta. */
const Reconocedor = window.SpeechRecognition || window.webkitSpeechRecognition;
if (!Reconocedor) {
  $("hablar").textContent = t("escribir");
  $("hablar").addEventListener("click", () => $("dicho").focus());
} else {
  const oido = new Reconocedor();
  oido.lang = idioma === "en" ? "en-US" : "es-ES";
  oido.interimResults = false;
  oido.maxAlternatives = 1;

  $("hablar").addEventListener("click", () => {
    if (hablando) { oido.stop(); return; }
    try { oido.start(); } catch { /* ya estaba */ }
  });
  oido.addEventListener("start", () => {
    hablando = true;
    $("hablar").classList.add("escuchando");
    $("hablar").textContent = t("escuchando");
  });
  oido.addEventListener("end", () => {
    hablando = false;
    $("hablar").classList.remove("escuchando");
    $("hablar").textContent = t("hablar");
  });
  oido.addEventListener("result", (e) => {
    const dicho = e.results[0][0].transcript;
    $("dicho").value = dicho;
    turno(dicho);
  });
  oido.addEventListener("error", (e) => {
    // Se dice cual fallo. "No se pudo" manda a mirar donde no es.
    linea(e.error === "not-allowed" ? t("sin_micro") : t("sin_oir"), "malo");
  });
}

if ("serviceWorker" in navigator) {
  navigator.serviceWorker.register("/sw.js").catch(() => {});
}
pulso();
