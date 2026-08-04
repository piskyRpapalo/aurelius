"use strict";
/* EL ANCLAJE DE CALIBRACIÓN — Método v1 §3.  [aur:anclaje]

   Mide la distancia entre lo que el usuario CREE que sabe y lo que demuestra.
   No mide capacidad. No emite juicio. Registra trayectoria.

   Cumple la Regla Única porque la declaración previa ES la predicción: el usuario
   firma su confianza ANTES del módulo, y después ve el hueco contra lo observado.

   ─── LOS CINCO SUELOS (§3.4). No se enmiendan. Si tocas este fichero, léelos ───
   · CERO BIOMETRÍA. En este módulo no hay ni un `Date.now()` alrededor de un
     campo de entrada, ni un listener de `keydown` que mida cadencia, ni nada que
     infiera el estado interno del usuario a partir de su cuerpo. El servidor
     guarda la FECHA y no la hora, precisamente para que ni siquiera restando dos
     registros se pueda derivar cuánto tardó.
   · CERO OPACIDAD. La fórmula se imprime en pantalla, literal, y los dos ficheros
     de texto plano se muestran crudos. No hay ningún ajuste escondido "para
     evitar que el usuario haga trampas": este registro es del usuario, y vigilar
     al alumno con su propia herramienta lo convierte en otra cosa.
   · CERO JUICIO SOBRE LA PERSONA. Las únicas etiquetas que produce este código
     describen el DELTA (sobreestimación / infraestimación / calibrado), jamás a
     quien lo produjo. Nunca "eres lento", nunca "nivel bajo".
   · CERO USO EXTERNO. El delta no se exporta, no se comparte, no se compara.
   · BORRADO TOTAL sin fricción: un clic, sin diálogo de confirmación. Es
     deliberado — ver `cablearBorrado()`. No le añadas un "¿estás seguro?".

   Y §3.5: con el delta NO se hace nada automático. Se muestra la curva y el
   usuario decide. Este módulo no bloquea, no adapta y no recomienda nada solo.

   API: window.AURELIUS_ANCLAJE
     Fórmula pura (testeable y reproducible a mano):
       confianzaNormalizada(c) · resultadoNormalizado(r) · delta(c, r)
       emparejar(declaraciones, resultados) · mediaMovil(pares) · curva(pares)
     UI: montar(raiz) → { refrescar }
   Requiere que i18n.js esté cargado antes. */

window.AURELIUS_ANCLAJE = (function () {
  /* Ventana del indicador. §3.3: «la MEDIA MÓVIL de los últimos 5 módulos, nunca
     un módulo aislado. Un dato suelto no dice nada sobre nadie.» */
  var VENTANA = 5;

  var RESULTADOS = { completo: 1.0, parcial: 0.5, no: 0.0 };

  /* Umbral de la etiqueta "calibrado". No es un ajuste oculto: se imprime en la
     interfaz junto a la fórmula, y el usuario ve el número crudo al lado. */
  var CERCA_DE_CERO = 0.1;

  // ───────────────────────────── LA FÓRMULA ─────────────────────────────────
  // Transcrita de §3.3 sin re-derivarla. Si alguna vez discrepan, manda el
  // documento: docs/AURELIUS_METODO_v1.txt.

  /** confianza_normalizada = (confianza - 1) / 4 → entre 0 y 1.
      Devuelve null si la confianza no es un entero de 1 a 5 (jamás un valor
      plausible inventado: honest sensors aplicado también a la entrada). */
  function confianzaNormalizada(confianza) {
    var c = typeof confianza === "string" ? parseInt(confianza, 10) : confianza;
    if (typeof c !== "number" || !isFinite(c) || Math.floor(c) !== c) return null;
    if (c < 1 || c > 5) return null;
    return (c - 1) / 4;
  }

  /** resultado_normalizado: completo = 1.0 · parcial = 0.5 · no = 0.0.
      Cualquier otra cosa → null. Tres valores y ninguno más: cada valor nuevo
      cambiaría la escala de la fórmula. */
  function resultadoNormalizado(resultado) {
    if (typeof resultado !== "string") return null;
    var r = resultado.trim().toLowerCase();
    return Object.prototype.hasOwnProperty.call(RESULTADOS, r) ? RESULTADOS[r] : null;
  }

  /** delta = confianza_normalizada - resultado_normalizado.
      positivo → sobreestimación · negativo → infraestimación · ~0 → calibrado.
      null si falta cualquiera de los dos: un módulo declarado y sin terminar NO
      tiene delta, y no se rellena con un cero que parecería calibración perfecta. */
  function delta(confianza, resultado) {
    var cn = confianzaNormalizada(confianza);
    var rn = resultadoNormalizado(resultado);
    if (cn === null || rn === null) return null;
    return cn - rn;
  }

  // ─────────────────────── EMPAREJAMIENTO DECLARACIÓN ↔ RESULTADO ────────────
  /** Empareja los dos ficheros. REGLA, escrita para que se pueda repetir a mano:
      cada línea de `resultados` es UN dato, en el orden en que está en el fichero,
      y se empareja con la declaración k-ésima de ESE MISMO módulo (la primera vez
      que hiciste el tema va con lo que declaraste la primera vez).

      Un resultado sin declaración que lo respalde queda con delta null y se
      declara como tal — no se le inventa una confianza.

      Devuelve { pares, pendientes }:
        pares      un objeto por línea de resultados, en orden, con su delta.
        pendientes módulos declarados que aún no tienen resultado. NO entran en la
                   media móvil; están aquí para que el usuario los vea. */
  function emparejar(declaraciones, resultados) {
    var decs = Array.isArray(declaraciones) ? declaraciones : [];
    var res = Array.isArray(resultados) ? resultados : [];

    // Declaraciones agrupadas por módulo, en orden de aparición.
    var porModulo = {};
    decs.forEach(function (d) {
      if (!d || typeof d.modulo !== "string") return;
      if (!porModulo[d.modulo]) porModulo[d.modulo] = [];
      porModulo[d.modulo].push(d);
    });

    var consumidas = {};
    var pares = res.map(function (r) {
      var mod = r && typeof r.modulo === "string" ? r.modulo : "";
      var k = consumidas[mod] || 0;
      var lista = porModulo[mod] || [];
      var dec = k < lista.length ? lista[k] : null;
      consumidas[mod] = k + 1;
      var conf = dec ? dec.confianza : null;
      return {
        modulo: mod,
        fecha: r && r.fecha ? r.fecha : "",
        confianza: conf,
        sinAyuda: dec ? dec.sin_ayuda : null,
        resultado: r && r.resultado ? r.resultado : "",
        delta: delta(conf, r && r.resultado),
      };
    });

    var pendientes = [];
    Object.keys(porModulo).forEach(function (mod) {
      var sobran = porModulo[mod].length - (consumidas[mod] || 0);
      for (var i = porModulo[mod].length - sobran; i < porModulo[mod].length; i++) {
        if (i >= 0) pendientes.push(porModulo[mod][i]);
      }
    });

    return { pares: pares, pendientes: pendientes };
  }

  /** Media móvil de los últimos `n` módulos CON delta. Los módulos sin resultado
      —o con resultado pero sin declaración— no ocupan hueco en la ventana: se
      ignoran por completo, no cuentan como un cero. Devuelve null si no hay
      ninguno (NO DATA honesto, jamás un 0 que parecería calibración perfecta). */
  function mediaMovil(pares, n) {
    var ventana = typeof n === "number" && n > 0 ? n : VENTANA;
    var deltas = (Array.isArray(pares) ? pares : [])
      .filter(function (p) { return p && typeof p.delta === "number" && isFinite(p.delta); })
      .map(function (p) { return p.delta; });
    if (deltas.length === 0) return null;
    var ultimos = deltas.slice(-ventana);
    var suma = ultimos.reduce(function (a, b) { return a + b; }, 0);
    return suma / ultimos.length;
  }

  /** Curva histórica: para cada módulo medido, la media móvil hasta ese punto.
      Es lo que se dibuja y lo que se lista en texto. */
  function curva(pares, n) {
    var ventana = typeof n === "number" && n > 0 ? n : VENTANA;
    var medidos = (Array.isArray(pares) ? pares : [])
      .filter(function (p) { return p && typeof p.delta === "number" && isFinite(p.delta); });
    return medidos.map(function (p, i) {
      var hasta = medidos.slice(0, i + 1);
      return {
        modulo: p.modulo,
        fecha: p.fecha,
        resultado: p.resultado,
        delta: p.delta,
        media: mediaMovil(hasta, ventana),
        n: Math.min(i + 1, ventana),
      };
    });
  }

  /** Etiqueta del delta. Describe el NÚMERO, nunca a la persona (§3.4). */
  function etiquetaDe(valor) {
    if (typeof valor !== "number" || !isFinite(valor)) return null;
    if (Math.abs(valor) < CERCA_DE_CERO) return "calibrado";
    return valor > 0 ? "sobre" : "infra";
  }

  // ─────────────────────────────── INTERFAZ ─────────────────────────────────

  function esc(s) { var d = document.createElement("div"); d.textContent = String(s); return d.innerHTML; }
  function n2(x) { return (Math.round(x * 100) / 100).toFixed(2); }

  function montar(opts) {
    opts = opts || {};
    var raiz = opts.raiz || document;
    var I = window.AURELIUS_I18N;
    var zona = raiz.querySelector ? raiz.querySelector("#an-zone") : document.getElementById("an-zone");
    if (!zona) return { refrescar: function () {} };

    function slugSoberano() {
      try { return localStorage.getItem("aurelius.soberano") || null; } catch (e) { return null; }
    }
    function apiUrl(path) {
      var s = slugSoberano();
      return s ? path + (path.indexOf("?") >= 0 ? "&" : "?") + "soberano=" + encodeURIComponent(s) : path;
    }

    var registro = { declaraciones: [], resultados: [], crudo: { declaraciones: "", resultados: "" } };
    var aviso = "";

    async function cargar() {
      var r = await fetch(apiUrl("/api/anclaje"), { cache: "no-store" });
      registro = await r.json();
    }

    async function enviar(ruta, cuerpo) {
      var r = await fetch(apiUrl(ruta), {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(cuerpo || {}),
      });
      var j = await r.json();
      if (!r.ok || !j.ok) throw new Error(j.error || ("HTTP " + r.status));
      if (j.anclaje) registro = j.anclaje;
      return j;
    }

    /* La FÓRMULA, impresa literal. §3.3: «Una métrica que no se puede reproducir
       a mano no es una medida: es un veredicto.» Por eso está aquí y por eso los
       dos ficheros crudos se muestran más abajo. */
    function vistaFormula() {
      var f =
        "confianza_normalizada = (confianza - 1) / 4          -> valor entre 0 y 1\n" +
        "resultado_normalizado:  exito completo = 1.0\n" +
        "                        exito parcial  = 0.5\n" +
        "                        no completado  = 0.0\n" +
        "delta = confianza_normalizada - resultado_normalizado\n" +
        "\n" +
        "delta positivo  -> sobreestimacion\n" +
        "delta negativo  -> infraestimacion\n" +
        "|delta| < " + CERCA_DE_CERO + "    -> calibrado\n" +
        "\n" +
        "indicador = media de los ultimos " + VENTANA + " modulos CON resultado\n" +
        "            (un modulo declarado y sin terminar no cuenta ni como cero)";
      return '<section class="an-card"><h2>' + esc(I.t("an.formulaTitle")) + "</h2>"
        + '<pre class="an-formula" id="an-formula">' + esc(f) + "</pre>"
        + '<p class="an-nota">' + esc(I.t("an.formulaWhy")) + "</p></section>";
    }

    function vistaIndicador(pares) {
      var media = mediaMovil(pares);
      var medidos = pares.filter(function (p) { return typeof p.delta === "number"; }).length;
      var cuerpo;
      if (media === null) {
        // honest sensors: sin módulos medidos no hay indicador. NO DATA, no un 0.
        cuerpo = '<div class="an-nodata" id="an-indicador">' + esc(I.t("an.noData")) + "</div>";
      } else {
        var et = etiquetaDe(media);
        cuerpo = '<div class="an-valor" id="an-indicador" data-etiqueta="' + esc(et) + '">'
          + '<span class="an-num">' + esc((media > 0 ? "+" : "") + n2(media)) + "</span>"
          + '<span class="an-et">' + esc(I.t("an.et." + et)) + "</span></div>"
          + '<p class="an-nota">' + esc(I.t("an.window", { n: Math.min(medidos, VENTANA), total: medidos })) + "</p>";
      }
      return '<section class="an-card"><h2>' + esc(I.t("an.indicatorTitle")) + "</h2>" + cuerpo + "</section>";
    }

    /* Curva histórica: SVG + la MISMA serie en texto. El dibujo es comodidad; el
       texto es el contrato (todo el sistema debe poder leerse sin la interfaz). */
    function vistaCurva(pares) {
      var pts = curva(pares);
      if (pts.length === 0) {
        return '<section class="an-card"><h2>' + esc(I.t("an.curveTitle")) + "</h2>"
          + '<p class="an-nodata">' + esc(I.t("an.curveEmpty")) + "</p></section>";
      }
      var W = 620, H = 160, PAD = 24;
      var paso = pts.length > 1 ? (W - PAD * 2) / (pts.length - 1) : 0;
      function y(v) { return PAD + ((1 - v) / 2) * (H - PAD * 2); } // delta ∈ [-1, 1]
      var d = pts.map(function (p, i) { return (i === 0 ? "M" : "L") + (PAD + i * paso).toFixed(1) + "," + y(p.media).toFixed(1); }).join(" ");
      var circulos = pts.map(function (p, i) {
        return '<circle cx="' + (PAD + i * paso).toFixed(1) + '" cy="' + y(p.media).toFixed(1) + '" r="3" />';
      }).join("");
      var svg = '<svg class="an-svg" viewBox="0 0 ' + W + " " + H + '" role="img" aria-label="' + esc(I.t("an.curveTitle")) + '">'
        + '<line class="an-cero" x1="' + PAD + '" y1="' + y(0) + '" x2="' + (W - PAD) + '" y2="' + y(0) + '" />'
        + '<text class="an-eje" x="4" y="' + (y(1) + 4) + '">+1</text>'
        + '<text class="an-eje" x="4" y="' + (y(0) + 4) + '">0</text>'
        + '<text class="an-eje" x="4" y="' + (y(-1) + 4) + '">-1</text>'
        + '<path class="an-linea" d="' + d + '" />' + circulos + "</svg>";

      var filas = pts.map(function (p) {
        return esc(p.fecha) + "\t" + esc(p.modulo) + "\t" + esc(p.resultado || "")
          + "\tdelta=" + esc((p.delta > 0 ? "+" : "") + n2(p.delta))
          + "\tmedia(" + p.n + ")=" + esc((p.media > 0 ? "+" : "") + n2(p.media));
      }).join("\n");

      return '<section class="an-card"><h2>' + esc(I.t("an.curveTitle")) + "</h2>" + svg
        + '<pre class="an-serie" id="an-serie">' + filas + "</pre></section>";
    }

    function vistaDeclarar(pendientes) {
      var pend = pendientes.length
        ? '<p class="an-nota" id="an-pendientes">' + esc(I.t("an.pending", {
            lista: pendientes.map(function (p) { return p.modulo; }).join(", "),
          })) + "</p>"
        : "";
      var radios = [1, 2, 3, 4, 5].map(function (v) {
        return '<label class="an-radio"><input type="radio" name="an-conf" value="' + v + '" /> ' + v + "</label>";
      }).join("");
      return '<section class="an-card"><h2>' + esc(I.t("an.declareTitle")) + "</h2>"
        + '<p class="an-nota">' + esc(I.t("an.declareWhen")) + "</p>"
        + '<div class="an-campo"><label for="an-dec-mod">' + esc(I.t("an.module")) + "</label>"
        + '<input type="text" id="an-dec-mod" placeholder="' + esc(I.t("an.modulePh")) + '" /></div>'
        + '<div class="an-campo"><span class="an-lbl">' + esc(I.t("an.confidence")) + "</span>"
        + '<div class="an-radios" id="an-conf">' + radios + "</div></div>"
        + '<p class="an-nota">' + esc(I.t("an.confidenceHint")) + "</p>"
        + '<div class="an-campo"><span class="an-lbl">' + esc(I.t("an.alone")) + "</span>"
        + '<div class="an-radios" id="an-alone">'
        + '<label class="an-radio"><input type="radio" name="an-alone" value="si" /> ' + esc(I.t("an.yes")) + "</label>"
        + '<label class="an-radio"><input type="radio" name="an-alone" value="no" /> ' + esc(I.t("an.no")) + "</label></div></div>"
        + '<button type="button" class="an-btn" id="an-dec-btn">' + esc(I.t("an.declareBtn")) + "</button>"
        + pend + '<div class="an-aviso" id="an-dec-aviso" role="alert"></div></section>';
    }

    function vistaResultado() {
      return '<section class="an-card"><h2>' + esc(I.t("an.resultTitle")) + "</h2>"
        + '<p class="an-nota">' + esc(I.t("an.resultWhen")) + "</p>"
        + '<div class="an-campo"><label for="an-res-mod">' + esc(I.t("an.module")) + "</label>"
        + '<input type="text" id="an-res-mod" placeholder="' + esc(I.t("an.modulePh")) + '" /></div>'
        + '<div class="an-radios" id="an-res">'
        + '<label class="an-radio"><input type="radio" name="an-res" value="completo" /> ' + esc(I.t("an.res.completo")) + "</label>"
        + '<label class="an-radio"><input type="radio" name="an-res" value="parcial" /> ' + esc(I.t("an.res.parcial")) + "</label>"
        + '<label class="an-radio"><input type="radio" name="an-res" value="no" /> ' + esc(I.t("an.res.no")) + "</label></div>"
        + '<button type="button" class="an-btn" id="an-res-btn">' + esc(I.t("an.resultBtn")) + "</button>"
        + '<div class="an-aviso" id="an-res-aviso" role="alert"></div></section>';
    }

    /* Los dos ficheros, crudos. Sin esto la fórmula impresa sería decorativa: el
       usuario necesita SUS datos para rehacer la cuenta y obtener el mismo número. */
    function vistaFicheros() {
      var d = registro.crudo && registro.crudo.declaraciones ? registro.crudo.declaraciones : "";
      var r = registro.crudo && registro.crudo.resultados ? registro.crudo.resultados : "";
      var vacio = !d && !r;
      return '<section class="an-card"><h2>' + esc(I.t("an.filesTitle")) + "</h2>"
        + '<p class="an-nota">' + esc(I.t("an.filesHint")) + "</p>"
        + (vacio
          ? '<p class="an-nodata" id="an-ficheros-vacio">' + esc(I.t("an.filesEmpty")) + "</p>"
          : '<pre class="an-fichero" id="an-fichero-dec">' + esc(d) + "</pre>"
            + '<pre class="an-fichero" id="an-fichero-res">' + esc(r) + "</pre>")
        + "</section>";
    }

    function vistaBorrado() {
      return '<section class="an-card an-card-borrar"><h2>' + esc(I.t("an.wipeTitle")) + "</h2>"
        + '<p class="an-nota">' + esc(I.t("an.wipeHint")) + "</p>"
        + '<button type="button" class="an-btn an-btn-borrar" id="an-wipe">' + esc(I.t("an.wipeBtn")) + "</button>"
        + '<div class="an-aviso" id="an-wipe-aviso" role="status"></div></section>';
    }

    function seleccionado(nombre) {
      var el = document.querySelector('input[name="' + nombre + '"]:checked');
      return el ? el.value : null;
    }

    function cablear() {
      var decBtn = document.getElementById("an-dec-btn");
      var decAviso = document.getElementById("an-dec-aviso");
      decBtn.addEventListener("click", async function () {
        var mod = (document.getElementById("an-dec-mod").value || "").trim().toLowerCase();
        var conf = seleccionado("an-conf");
        var alone = seleccionado("an-alone");
        if (!/^[a-z0-9][a-z0-9-]{0,39}$/.test(mod)) { decAviso.className = "an-aviso err"; decAviso.textContent = I.t("an.errModule"); return; }
        if (conf === null || alone === null) { decAviso.className = "an-aviso err"; decAviso.textContent = I.t("an.errIncomplete"); return; }
        decBtn.disabled = true;
        try {
          await enviar("/api/anclaje/declaracion", { modulo: mod, confianza: parseInt(conf, 10), sin_ayuda: alone === "si" });
          aviso = I.t("an.declared", { modulo: mod });
          render();
        } catch (e) {
          decAviso.className = "an-aviso err"; decAviso.textContent = "— " + e.message; decBtn.disabled = false;
        }
      });

      var resBtn = document.getElementById("an-res-btn");
      var resAviso = document.getElementById("an-res-aviso");
      resBtn.addEventListener("click", async function () {
        var mod = (document.getElementById("an-res-mod").value || "").trim().toLowerCase();
        var res = seleccionado("an-res");
        if (!/^[a-z0-9][a-z0-9-]{0,39}$/.test(mod)) { resAviso.className = "an-aviso err"; resAviso.textContent = I.t("an.errModule"); return; }
        if (res === null) { resAviso.className = "an-aviso err"; resAviso.textContent = I.t("an.errIncomplete"); return; }
        resBtn.disabled = true;
        try {
          await enviar("/api/anclaje/resultado", { modulo: mod, resultado: res });
          aviso = I.t("an.recorded", { modulo: mod });
          render();
        } catch (e) {
          resAviso.className = "an-aviso err"; resAviso.textContent = "— " + e.message; resBtn.disabled = false;
        }
      });

      cablearBorrado();
    }

    /* §3.4: «EL USUARIO PUEDE BORRARLO ENTERO en cualquier momento, sin fricción y
       sin preguntas de confirmación culpabilizadoras.» Un clic. Deliberadamente NO
       hay confirm(): un diálogo es fricción, y el que pregunta "¿seguro que
       quieres borrar tu progreso?" además culpabiliza. El registro no es rehén de
       nadie. Si alguien añade aquí una confirmación, está enmendando un suelo. */
    function cablearBorrado() {
      var btn = document.getElementById("an-wipe");
      var av = document.getElementById("an-wipe-aviso");
      btn.addEventListener("click", async function () {
        btn.disabled = true;
        try {
          await enviar("/api/anclaje/borrar", {});
          aviso = I.t("an.wiped");
          render();
        } catch (e) {
          av.className = "an-aviso err"; av.textContent = "— " + e.message; btn.disabled = false;
        }
      });
    }

    function render() {
      var emp = emparejar(registro.declaraciones, registro.resultados);
      zona.innerHTML =
        (aviso ? '<div class="an-aviso ok" id="an-flash" role="status">' + esc(aviso) + "</div>" : "")
        + vistaIndicador(emp.pares)
        + vistaCurva(emp.pares)
        + vistaFormula()
        + vistaDeclarar(emp.pendientes)
        + vistaResultado()
        + vistaFicheros()
        + vistaBorrado();
      aviso = "";
      cablear();
    }

    async function refrescar() {
      try { await cargar(); }
      catch (e) {
        zona.innerHTML = '<section class="an-card"><h2>' + esc(I.t("path.serverDown.title")) + "</h2>"
          + '<p class="an-nota">' + esc(I.t("path.serverDown.body")) + "</p></section>";
        return;
      }
      render();
    }

    refrescar();
    return { refrescar: refrescar };
  }

  return {
    VENTANA: VENTANA,
    CERCA_DE_CERO: CERCA_DE_CERO,
    confianzaNormalizada: confianzaNormalizada,
    resultadoNormalizado: resultadoNormalizado,
    delta: delta,
    emparejar: emparejar,
    mediaMovil: mediaMovil,
    curva: curva,
    etiquetaDe: etiquetaDe,
    montar: montar,
  };
})();
