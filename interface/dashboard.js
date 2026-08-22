/* Aurelius · el tablero.
 *
 * Mismas dos reglas que el panel: la interfaz no cuenta -- los numeros vienen
 * del servidor -- y nada se promete antes de comprobarlo.
 */
"use strict";

const $ = (id) => document.getElementById(id);
let hablando = false;

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
    $("pulso").textContent = d.motor
      ? "listo para hablar"
      : "puedo preguntar y recordar, todavía no conversar";
    $("hablar").disabled = !d.motor;
    $("mandar").disabled = !d.motor;
    $("m-turnos").textContent = d.turnos.turnos;
    $("m-consent").textContent = d.turnos.consentidos;
    $("m-corr").textContent = d.turnos.corregidos;
    $("a-idioma").textContent = d.idioma === "en" ? "English" : "Español";
    $("a-motor").textContent = d.motor ? "instalado" : "sin instalar";
    $("a-captura").textContent = d.captura_activa ? "encendido" : "apagado";
    $("a-nota").textContent = d.motor
      ? "En un teléfono cada respuesta tarda minutos. No es que se haya colgado."
      : "Sin cerebro instalado, Aurelius pregunta y recuerda pero no conversa.";
  } catch {
    $("pulso").textContent = "no alcanzo al servidor";
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
  const esperando = linea("pensando… esto puede tardar minutos", "espera");
  try {
    const r = await fetch("/api/charla", {
      method: "POST", headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ texto }),
    });
    const d = await r.json();
    esperando.remove();
    if (r.ok) linea(d.texto);
    else linea(d.estado === "tarde"
      ? "tardó más de la cuenta. Prueba con algo más corto."
      : "no pude responder ahora mismo.", "malo");
  } catch {
    esperando.remove();
    linea("no alcancé al servidor.", "malo");
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
  $("hablar").textContent = "Escribir";
  $("hablar").addEventListener("click", () => $("dicho").focus());
} else {
  const oido = new Reconocedor();
  oido.lang = "es-ES";
  oido.interimResults = false;
  oido.maxAlternatives = 1;

  $("hablar").addEventListener("click", () => {
    if (hablando) { oido.stop(); return; }
    try { oido.start(); } catch { /* ya estaba */ }
  });
  oido.addEventListener("start", () => {
    hablando = true;
    $("hablar").classList.add("escuchando");
    $("hablar").textContent = "Escuchando… toca para parar";
  });
  oido.addEventListener("end", () => {
    hablando = false;
    $("hablar").classList.remove("escuchando");
    $("hablar").textContent = "Hablar";
  });
  oido.addEventListener("result", (e) => {
    const dicho = e.results[0][0].transcript;
    $("dicho").value = dicho;
    turno(dicho);
  });
  oido.addEventListener("error", (e) => {
    // Se dice cual fallo. "No se pudo" manda a mirar donde no es.
    linea(e.error === "not-allowed"
      ? "no me diste permiso para el micrófono."
      : "no te oí bien. Prueba a escribirlo.", "malo");
  });
}

if ("serviceWorker" in navigator) {
  navigator.serviceWorker.register("/sw.js").catch(() => {});
}
pulso();
