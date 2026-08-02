"use strict";
/* El Camino (The Path) como MÓDULO reutilizable. Lo usa tanto la página standalone
   camino.html como el DRAWER de aurelius_face.html — SIN iframe. Al no embeber la
   app dentro de sí misma se elimina de raíz el vector de recursión (antes: el iframe
   cargaba camino.html y su "← Aurelius" navegaba el iframe a aurelius_face.html,
   montando la app dentro de la app en bucle).

   window.AURELIUS_CAMINO.montar(opts) → { refrescar }
     opts.raiz          elemento contenedor (o document). Busca dentro: #zone #rail
                        #salut #cm-titulo #cm-noverif #cm-lang #cm-retour (los que
                        falten se ignoran — el drawer no trae cabecera propia).
     opts.onCerrar      si se pasa, el "Volver/← Aurelius" cierra el panel en vez de
                        navegar (estado local de UI, no ruta).
     opts.onTotemCreado callback directo al crear el Tótem (recompensa de M0). Si no
                        se pasa, cae al postMessage al padre (compat standalone).
   Requiere que i18n.js y oraculo.js estén cargados antes. */

window.AURELIUS_CAMINO = (function () {
  function montar(opts) {
    opts = opts || {};
    var raiz = opts.raiz || document;
    var onCerrar = typeof opts.onCerrar === "function" ? opts.onCerrar : null;
    var onTotemCreado = typeof opts.onTotemCreado === "function" ? opts.onTotemCreado : null;

    var I = window.AURELIUS_I18N;
    var API = ""; // mismo origen (servidor 8050)
    var VAULT = "~/aurelius/sovereign_vault";
    var SCRIPTS = "~/aurelius/scripts";
    // Modelo mostrado en los comandos: DESACOPLADO. resolverModelo() lo resuelve
    // (config real del nodo → manifiesto models.json → este literal solo como
    // ÚLTIMO RECURSO offline). El nombre NO es la fuente de verdad; el manifiesto sí.
    var MODELO = "qwen3:30b-a3b-instruct-2507-q4_K_M";

    // === Identidad del soberano (multiusuario · SEPARACIÓN, no auth). El slug
    //     vive en localStorage (lo fija la cara o el Tótem M0) y viaja en
    //     ?soberano= a la API. Cualquiera con el enlace puede poner otro nombre. ===
    function slugSoberano() {
      try { return localStorage.getItem("aurelius.soberano") || null; } catch (e) { return null; }
    }
    function fijarSlug(slug, nombre) {
      try {
        if (slug) localStorage.setItem("aurelius.soberano", slug);
        if (nombre) localStorage.setItem("aurelius.nombre", nombre.trim());
      } catch (e) { /* memoria */ }
    }
    function apiUrl(path) {
      var s = slugSoberano();
      return s ? path + (path.indexOf("?") >= 0 ? "&" : "?") + "soberano=" + encodeURIComponent(s) : path;
    }

    var CAMINO = ["M0", "M1", "M2", "M3", "M4", "M5", "M6", "M7"];

    // Elementos estáticos, scoped a `raiz`. Los que el host no provee quedan null y
    // se ignoran (el drawer usa su propia barra/cierre; no trae cabecera del Camino).
    var zone = raiz.querySelector ? raiz.querySelector("#zone") : document.getElementById("zone");
    var rail = raiz.querySelector ? raiz.querySelector("#rail") : document.getElementById("rail");
    var salut = raiz.querySelector ? raiz.querySelector("#salut") : document.getElementById("salut");
    var titulo = raiz.querySelector ? raiz.querySelector("#cm-titulo") : document.getElementById("cm-titulo");
    var noverif = raiz.querySelector ? raiz.querySelector("#cm-noverif") : document.getElementById("cm-noverif");
    var sel = raiz.querySelector ? raiz.querySelector("#cm-lang") : document.getElementById("cm-lang");
    var retour = raiz.querySelector ? raiz.querySelector("#cm-retour") : document.getElementById("cm-retour");
    var esStandalone = raiz === document;

    function esc(s) { var d = document.createElement("div"); d.textContent = s; return d.innerHTML; }

    // === i18n: poblar selector, aplicar idioma a los elementos estáticos ===
    if (sel) {
      I.locales.forEach(function (loc) {
        var o = document.createElement("option");
        o.value = loc; o.textContent = I.nombre[loc];
        sel.appendChild(o);
      });
    }

    function aplicarIdioma() {
      if (esStandalone) document.documentElement.lang = I.locale;
      if (titulo) titulo.textContent = I.t("path.title");
      if (esStandalone) document.title = I.t("path.title") + " · Aurelius";
      if (retour) retour.textContent = I.t("path.back");
      if (sel && sel.value !== I.locale) sel.value = I.locale;
      if (noverif) noverif.hidden = I.esVerificado(); // aviso honesto: idioma sin revisar humano
    }

    if (sel) {
      sel.addEventListener("change", function (ev) {
        I.set(ev.target.value);
        aplicarIdioma();
        render(); // re-pinta las vistas en el nuevo idioma
      });
    }

    // "Volver / ← Aurelius": si el host da onCerrar (drawer), cierra el panel (estado
    // local de UI). Sin onCerrar (standalone), el <a href> navega nativamente.
    if (retour && onCerrar) {
      retour.addEventListener("click", function (e) { e.preventDefault(); onCerrar(); });
    }

    function bloc(titre, cmd) {
      return '<div class="bloc"><div class="bloc-titre">' + esc(titre) + '</div>' +
        '<pre class="cmd"><button class="copier" type="button">' + esc(I.t("copy")) + '</button>' +
        '<span class="cmd-txt">' + esc(cmd) + '</span></pre></div>';
    }

    function cablerCopieurs(scope) {
      scope.querySelectorAll("button.copier").forEach(function (b) {
        b.addEventListener("click", function () {
          var pre = b.parentElement;
          var span = pre.querySelector(".cmd-txt");
          var txt = span ? span.textContent : pre.textContent.replace(new RegExp("^" + I.t("copy")), "");
          copiar(txt, b, span);
        });
      });
    }

    // Copia ROBUSTA en contexto NO seguro: Aurelius se sirve por http:// vía el
    // hostname del tailnet (≠ localhost), así que navigator.clipboard está
    // BLOQUEADO por el navegador (mismo motivo que el micrófono). Fallback a
    // execCommand con un textarea temporal; si tampoco, se SELECCIONA el comando
    // visible para copia manual. Se marca "copiado" SOLO si de verdad copió — un
    // botón que miente es peor que ninguno. El comando SIEMPRE queda visible (IronClaw).
    function copiar(txt, btn, span) {
      function marca(clave, ms) {
        btn.textContent = I.t(clave);
        setTimeout(function () { btn.textContent = I.t("copy"); }, ms || 1200);
      }
      function manual() {
        if (span) {
          var r = document.createRange(); r.selectNodeContents(span);
          var s = window.getSelection(); s.removeAllRanges(); s.addRange(r);
        }
        marca("copyManual", 3000);
      }
      if (window.isSecureContext && navigator.clipboard) {
        navigator.clipboard.writeText(txt).then(function () { marca("copyOk"); }).catch(manual);
        return;
      }
      var ta = document.createElement("textarea");
      ta.value = txt; ta.setAttribute("readonly", "");
      ta.style.position = "fixed"; ta.style.top = "-1000px"; ta.style.opacity = "0";
      document.body.appendChild(ta); ta.focus(); ta.select();
      var ok = false;
      try { ok = document.execCommand("copy"); } catch (e) { ok = false; }
      document.body.removeChild(ta);
      if (ok) marca("copyOk"); else manual();
    }

    async function getEstado() {
      var r = await fetch(apiUrl(API + "/api/estado"));
      return r.json();
    }

    function pintarRail(estado) {
      if (!rail) return;
      rail.innerHTML = "";
      CAMINO.forEach(function (code) {
        var etat = estado.modulos_completados.indexOf(code) >= 0 ? "fait"
          : (estado.modulo_actual === code ? "actuel" : "attente");
        var d = document.createElement("div");
        d.className = "etape"; d.setAttribute("data-etat", etat);
        d.innerHTML = esc(code) + "<small>" + esc(I.t("step." + code)) + "</small>";
        rail.appendChild(d);
      });
    }

    // ---------- M0 · El Tótem ----------
    // Onboarding GUIADO (BLOQUE A): preguntas cortas que "despiertan" el Tótem.
    // NO se pregunta lo que el sistema ya sabe (el hardware lo audita el Oráculo:
    // se MUESTRA y solo se confirma/corrige).
    function vueM0() {
      return '<div class="module"><h2>' + esc(I.t("m0.title")) + '</h2>'
        + '<p class="obj">' + esc(I.t("m0.obj")) + '</p>'
        + '<ol class="on-guia">'
        + '<li><div class="on-q">' + esc(I.t("on.name")) + '</div>'
        + '<input type="text" id="m0-nom" placeholder="' + esc(I.t("m0.nom")) + '" /></li>'
        + '<li><div class="on-q">' + esc(I.t("on.hardware")) + '</div>'
        + '<div class="on-hw" id="on-hw">' + esc(I.t("on.hardwareDetecting")) + '</div>'
        + '<label class="on-hw-ok"><input type="checkbox" id="on-hw-ok" checked /> ' + esc(I.t("on.hardwareConfirm")) + '</label>'
        + '<div class="champ" id="on-hw-fix" hidden><input type="number" id="on-hw-ram" min="1" max="4096" placeholder="' + esc(I.t("on.hardwareCorrect")) + '" /></div></li>'
        + '<li><div class="on-q">' + esc(I.t("on.level")) + '</div>'
        + '<div class="on-opts" id="on-nivel">'
        + '<button type="button" class="on-b" data-v="principiante">' + esc(I.t("level.beginner")) + '</button>'
        + '<button type="button" class="on-b" data-v="intermedio">' + esc(I.t("level.intermediate")) + '</button>'
        + '<button type="button" class="on-b" data-v="avanzado">' + esc(I.t("level.advanced")) + '</button></div></li>'
        + '<li><div class="on-q">' + esc(I.t("on.tone")) + '</div>'
        + '<div class="on-opts" id="on-tono">'
        + '<button type="button" class="on-b" data-v="sereno">' + esc(I.t("tone.serene")) + '</button>'
        + '<button type="button" class="on-b" data-v="directo">' + esc(I.t("tone.direct")) + '</button>'
        + '<button type="button" class="on-b" data-v="didactico">' + esc(I.t("tone.didactic")) + '</button></div>'
        + '<p class="on-nota">' + esc(I.t("on.toneNote")) + '</p></li>'
        + '</ol>'
        + '<ol class="pasos" start="5"><li>' + esc(I.t("m0.step1")) + '</li></ol>'
        + '<div class="prompt-cebado">' + esc(I.t("m0.prompt")) + '</div>'
        + '<ol class="pasos" start="6"><li>' + esc(I.t("m0.step2")) + '</li></ol>'
        + '<div class="champ">'
        + '<input type="file" id="m0-file" accept="image/png,image/jpeg,image/webp" />'
        + '<button class="action" id="m0-btn">' + esc(I.t("m0.btn")) + '</button>'
        + '</div><div class="aviso" id="m0-aviso"></div></div>';
    }
    function cablerM0() {
      var btn = document.getElementById("m0-btn");
      var aviso = document.getElementById("m0-aviso");
      var nivelSel = null, tonoSel = null;
      function cablearGrupo(id, fijar) {
        var bs = document.querySelectorAll("#" + id + " .on-b");
        bs.forEach(function (b) {
          b.addEventListener("click", function () {
            bs.forEach(function (x) { x.setAttribute("data-actif", "non"); });
            b.setAttribute("data-actif", "oui"); fijar(b.getAttribute("data-v"));
          });
        });
      }
      cablearGrupo("on-nivel", function (v) { nivelSel = v; });
      cablearGrupo("on-tono", function (v) { tonoSel = v; });
      // Hardware: NO se pregunta — el Oráculo lo detecta; se muestra y se confirma/corrige.
      var hwOk = document.getElementById("on-hw-ok");
      hwOk.addEventListener("change", function () { document.getElementById("on-hw-fix").hidden = hwOk.checked; });
      // Inventario (RAM real) + manifiesto de modelos: el Oráculo LEE del manifiesto
      // para nombrar tags concretos que caben — no los hardcodea.
      Promise.all([
        fetch(apiUrl(API + "/api/inventario")).then(function (r) { return r.ok ? r.json() : null; }).catch(function () { return null; }),
        fetch("models.json", { cache: "no-store" }).then(function (r) { return r.ok ? r.json() : null; }).catch(function () { return null; }),
      ]).then(function (res) {
        var inv = res[0], manifiesto = res[1];
        var hw = document.getElementById("on-hw");
        var ram = inv && inv.hardware && inv.hardware.hardware ? inv.hardware.hardware.ram_disponible_gb : null;
        if (window.AURELIUS_ORACULO && typeof ram === "number") {
          hw.textContent = window.AURELIUS_ORACULO.resumen(window.AURELIUS_ORACULO.analizar(ram), manifiesto);
        } else {
          hw.textContent = I.t("on.hardwareUnknown"); // honest sensors: no lo estima a ojo
          hwOk.checked = false; document.getElementById("on-hw-fix").hidden = false;
        }
      });

      btn.addEventListener("click", async function () {
        var nom = document.getElementById("m0-nom").value.trim();
        var file = document.getElementById("m0-file").files[0];
        if (nom === "") { aviso.className = "aviso err"; aviso.textContent = I.t("m0.errName"); return; }
        if (!nivelSel || !tonoSel) { aviso.className = "aviso err"; aviso.textContent = I.t("on.errChoose"); return; }
        if (!file) { aviso.className = "aviso err"; aviso.textContent = I.t("m0.errFile"); return; }
        var ext = (file.name.split(".").pop() || "png").toLowerCase();
        btn.disabled = true; aviso.className = "aviso"; aviso.textContent = I.t("m0.sealing");
        try {
          var buf = await file.arrayBuffer();
          var r = await fetch(API + "/api/totem", { method: "POST", headers: { "X-Nombre": nom, "X-Ext": ext }, body: buf });
          var j = await r.json();
          if (!r.ok || !j.ok) throw new Error(j.error || ("HTTP " + r.status));
          fijarSlug(j.slug, nom); // el servidor devuelve el slug: lo recordamos
          // Guarda nivel/tono (+ corrección de RAM si la hubo) en el estado por slug.
          var prefs = { nivel: nivelSel, tono: tonoSel };
          if (!hwOk.checked) {
            var ramFix = parseFloat(document.getElementById("on-hw-ram").value);
            if (isFinite(ramFix) && ramFix > 0) prefs.ram_declarada_gb = ramFix;
          }
          await fetch(apiUrl(API + "/api/preferencia"), {
            method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify(prefs),
          }).catch(function () {});
          // EL TÓTEM DESPIERTA (recompensa de M0): callback directo si estamos en el
          // drawer (sin iframe/postMessage); si no, compat postMessage al padre.
          try {
            if (onTotemCreado) { onTotemCreado(nom); }
            else if (window.parent && window.parent !== window) {
              window.parent.postMessage({ tipo: "aurelius:totem-creado", nombre: nom }, window.location.origin);
            }
          } catch (e) { /* standalone sin padre ni callback: nada */ }
          aviso.className = "aviso ok";
          aviso.textContent = I.t("m0.sealed", { sha: j.sha256.slice(0, 12), name: nom });
          setTimeout(render, 900);
        } catch (e) {
          aviso.className = "aviso err"; aviso.textContent = "— " + e.message;
          btn.disabled = false;
        }
      });
    }

    // ---------- M1 · El Fuego ----------
    function vueM1() {
      var art = VAULT + "/M1_Espejo_Roto/tiempo_perdido.md";
      return '<div class="module"><h2>' + esc(I.t("m1.title")) + '</h2>'
        + '<p class="obj">' + esc(I.t("m1.obj")) + '</p>'
        + '<p class="on-nota">' + esc(I.t("sov.net")) + '</p>'
        + '<ol class="pasos"><li>' + esc(I.t("m1.step1")) + '</li><li>' + esc(I.t("m1.step2")) + '</li></ol>'
        + bloc(I.t("m1.cmd1"), 'mkdir -p ' + VAULT + '/M1_Espejo_Roto\nollama run ' + MODELO + ' "Dame un plan de 3 pasos, simple y seguro, para empezar un pequeno huerto en un balcon." > ' + art)
        + '<ol class="pasos" start="3"><li>' + esc(I.t("m1.step3")) + '</li></ol>'
        + bloc(I.t("m1.cmd2"), 'python3 ' + SCRIPTS + '/firmar_artefacto.py ' + art)
        + '<p class="obj">' + esc(I.t("m1.paste")) + '</p>'
        + '<div class="champ"><input type="text" id="m1-sha" placeholder="' + esc(I.t("m1.sha")) + '" />'
        + '<button class="action" id="m1-btn">' + esc(I.t("m1.btn")) + '</button></div>'
        + '<div class="aviso" id="m1-aviso"></div></div>';
    }

    // ---------- M2 · El Agua ----------
    function vueM2() {
      var gri = VAULT + "/M2_Agua/grimorio.md";
      var man = VAULT + "/M2_Agua/grimorio.manifest.json";
      return '<div class="module"><h2>' + esc(I.t("m2.title")) + '</h2>'
        + '<p class="obj">' + esc(I.t("m2.obj")) + '</p>'
        + '<ol class="pasos"><li>' + esc(I.t("m2.step1")) + '</li></ol>'
        + bloc(I.t("m2.cmd1"), 'mkdir -p ' + VAULT + '/M2_Agua\nnano ' + gri)
        + '<ol class="pasos" start="2"><li>' + esc(I.t("m2.step2")) + '</li></ol>'
        + bloc(I.t("m2.cmd2"), 'python3 ' + SCRIPTS + '/ingerir.py ' + gri)
        + '<ol class="pasos" start="3"><li>' + esc(I.t("m2.step3")) + '</li></ol>'
        + bloc(I.t("m2.cmd3"), 'python3 ' + SCRIPTS + '/ingerir.py ' + gri + ' --buscar "tu pregunta"')
        + '<ol class="pasos" start="4"><li>' + esc(I.t("m2.step4")) + '</li></ol>'
        + bloc(I.t("m2.cmd4"), 'python3 ' + SCRIPTS + '/firmar_artefacto.py ' + man)
        + '<p class="obj">' + esc(I.t("m2.paste")) + '</p>'
        + '<div class="champ"><input type="text" id="m2-sha" placeholder="' + esc(I.t("m1.sha")) + '" />'
        + '<button class="action" id="m2-btn">' + esc(I.t("m2.btn")) + '</button></div>'
        + '<div class="aviso" id="m2-aviso"></div></div>';
    }

    function cablerCompletar(code, btnId, shaId, avisoId) {
      var btn = document.getElementById(btnId);
      var aviso = document.getElementById(avisoId);
      btn.addEventListener("click", async function () {
        var sha = (document.getElementById(shaId).value || "").trim().toLowerCase();
        if (!/^[0-9a-f]{64}$/.test(sha)) {
          aviso.className = "aviso err"; aviso.textContent = I.t("seal.badSha");
          return;
        }
        btn.disabled = true; aviso.className = "aviso"; aviso.textContent = I.t("seal.sealing");
        try {
          var r = await fetch(apiUrl(API + "/api/modulo/completar"), {
            method: "POST", headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ modulo: code, prueba: sha }),
          });
          var j = await r.json();
          if (!r.ok || !j.ok) throw new Error(j.error || ("HTTP " + r.status));
          aviso.className = "aviso ok"; aviso.textContent = I.t("seal.ok", { code: code });
          setTimeout(render, 900);
        } catch (e) {
          aviso.className = "aviso err"; aviso.textContent = "— " + e.message;
          btn.disabled = false;
        }
      });
    }

    function vueFinal() {
      return '<div class="module"><h2>' + esc(I.t("final.title")) + '</h2>'
        + '<p class="obj">' + esc(I.t("final.body")) + '</p></div>';
    }

    async function render() {
      if (!zone) return;
      var estado;
      try { estado = await getEstado(); }
      catch (e) {
        zone.innerHTML = '<div class="module"><h2>' + esc(I.t("path.serverDown.title")) + '</h2>'
          + '<p class="obj">' + esc(I.t("path.serverDown.body")) + '</p></div>';
        return;
      }
      if (salut) salut.textContent = estado.nombre ? (I.t("path.greet") + estado.nombre) : "";
      pintarRail(estado);
      var act = estado.modulo_actual;
      var html;
      if (act === "M0") { html = vueM0(); }
      else if (act === "M1") { html = vueM1(); }
      else if (act === "M2") { html = vueM2(); }
      else { html = vueFinal(); }
      zone.innerHTML = html;
      cablerCopieurs(zone);
      if (act === "M0") cablerM0();
      else if (act === "M1") cablerCompletar("M1", "m1-btn", "m1-sha", "m1-aviso");
      else if (act === "M2") cablerCompletar("M2", "m2-btn", "m2-sha", "m2-aviso");
    }

    // Resuelve el tag del modelo SIN hardcodearlo en la lógica: el modelo real
    // declarado por el operador (config.json, fuera de git) manda; si no, el
    // recomendado por defecto del manifiesto versionado (models.json); si ambos
    // fallan, se queda el literal de último recurso. Footgun de tags: el manifiesto
    // solo lista variantes instruct explícitas (ver models.json).
    function tagPorDefecto(man) {
      if (!man || !Array.isArray(man.models)) return null;
      var d = man.models.filter(function (x) { return x && x.id === man.default; })[0] || man.models[0];
      return d && typeof d.tag === "string" && d.tag ? d.tag : null;
    }
    async function resolverModelo() {
      var fuentes = ["config.json", "config.example.json"];
      for (var i = 0; i < fuentes.length; i++) {
        try {
          var r = await fetch(fuentes[i], { cache: "no-store" });
          if (r.ok) { var c = await r.json(); if (c && typeof c.model === "string" && c.model) { MODELO = c.model; return; } }
        } catch (e) { /* siguiente fuente */ }
      }
      try {
        var rm = await fetch("models.json", { cache: "no-store" });
        if (rm.ok) { var t = tagPorDefecto(await rm.json()); if (t) { MODELO = t; return; } }
      } catch (e) { /* offline → literal de último recurso */ }
    }

    aplicarIdioma();
    resolverModelo().then(render);

    // Permite al host refrescar el estado al reabrir el panel (sin re-montar → DOM
    // estable: el componente se monta EXACTAMENTE una vez).
    return { refrescar: render };
  }

  return { montar: montar };
})();
