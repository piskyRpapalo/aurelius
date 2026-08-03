"use strict";
/* Modo presentación de la cara de Aurelius (§5.3). Con ?present=1 sustituye valores
 * sensibles por placeholders VISIBLEMENTE marcados, para poder CAPTURAR el drawer con
 * sus módulos (que muestran comandos con rutas ~/…) sin fugas. NO oculta: DECLARA
 * (badge fijo). Espejo de los patrones CRIT de tools/scrub_check.js y del present.ts
 * del dashboard; los placeholders son idempotentes (no vuelven a casar). Cubre texto
 * (incl. lo que camino.js pinta async, vía MutationObserver) y atributos. Se incluye
 * también en camino.html standalone. Vanilla JS, sin dependencias, sin red. */
(function () {
  var params = new URLSearchParams(window.location.search);
  if (params.get("present") !== "1") return;

  var REGLAS = [
    [/\b[a-z0-9-]+\.tail[a-z0-9]{4,8}\.ts\.net\b/gi, "node.local"],
    [/\b\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}\b/g, "node.local"],
    [/\b[a-z0-9_-]+\.(?:near|testnet)\b/gi, "wallet.example"],
    [/\b(?:pisky[0-9a-z]*|jetson|ubuntu|pi)@[a-z0-9.-]+/gi, "operador@nodo"],
    [/david[ _]?pecero(?:[ _]?caballero)?|davidpecero@[a-z0-9.-]+/gi, "operador@nodo"],
    [/(?:\/home\/[a-z0-9._-]+|~)(?:\/[^\s"'<>)\]]*)?/g, "[ruta]"],
    [/\bhxl-[a-z0-9-]{3,}\b/gi, "[clave]"],
    [/\bid_hexelion\b/g, "[clave]"],
    [/ed25519:[1-9A-HJ-NP-Za-km-z]{30,}/g, "[clave]"],
    [/\b(?:la-fragua|el-vig[ií]a|la-torre)\b/gi, "nodo"],
    [/\b(?:soberano|fragua|cortex|legi[oó]n|osiris|vig[ií]a|torre)\b/gi, "nodo"],
  ];
  var ATTRS = ["href", "src", "title", "alt", "aria-label", "value", "placeholder", "content"];

  function sustituir(t) {
    for (var i = 0; i < REGLAS.length; i++) { REGLAS[i][0].lastIndex = 0; t = t.replace(REGLAS[i][0], REGLAS[i][1]); }
    return t;
  }
  function esBadge(n) { var el = n.nodeType === 1 ? n : n.parentElement; return !!(el && el.closest && el.closest("[data-present-badge]")); }
  function sanearTexto(t) { var v = t.nodeValue; if (v == null || v.replace(/\s/g, "") === "" || esBadge(t)) return; var nv = sustituir(v); if (nv !== v) t.nodeValue = nv; }
  function sanearAttrs(el) { if (esBadge(el)) return; for (var i = 0; i < ATTRS.length; i++) { var a = el.getAttribute && el.getAttribute(ATTRS[i]); if (a) { var na = sustituir(a); if (na !== a) el.setAttribute(ATTRS[i], na); } } }
  function sanearArbol(raiz) {
    if (raiz.nodeType === 3) { sanearTexto(raiz); return; }
    if (raiz.nodeType !== 1 || esBadge(raiz)) return;
    sanearAttrs(raiz);
    var w = document.createTreeWalker(raiz, NodeFilter.SHOW_TEXT | NodeFilter.SHOW_ELEMENT);
    var n = w.nextNode();
    while (n) { if (n.nodeType === 3) sanearTexto(n); else sanearAttrs(n); n = w.nextNode(); }
  }
  function montarBadge() {
    if (document.querySelector("[data-present-badge]")) return;
    var b = document.createElement("div");
    b.setAttribute("data-present-badge", "1"); b.id = "present-badge"; b.setAttribute("role", "status");
    b.textContent = "● PRESENTATION MODE · values substituted";
    document.body.appendChild(b);
  }
  var CFG = { subtree: true, childList: true, characterData: true, attributes: true, attributeFilter: ATTRS };
  function arrancar() {
    document.documentElement.setAttribute("data-present", "1");
    montarBadge();
    sanearArbol(document.body);
    var obs = new MutationObserver(function (muts) {
      obs.disconnect();
      muts.forEach(function (m) {
        if (m.type === "characterData") sanearTexto(m.target);
        else if (m.type === "attributes" && m.target.nodeType === 1) sanearAttrs(m.target);
        else m.addedNodes.forEach(function (x) { sanearArbol(x); });
      });
      obs.observe(document.body, CFG);
    });
    obs.observe(document.body, CFG);
  }
  if (document.body) arrancar();
  else window.addEventListener("DOMContentLoaded", arrancar, { once: true });
})();
