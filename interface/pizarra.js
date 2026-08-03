"use strict";
/* La Pizarra — terminal SIMULADO, 100% cliente-side, CERO ejecución real (§BLOQUE 4).
 *
 * Enseña los comandos base con un filesystem ficticio en memoria. JAMÁS toca el
 * backend (no existe endpoint de ejecución) ni la máquina real. El modelo no tiene
 * manos: eso es el suelo de IronClaw, no una capa.
 *
 * Honest sensors en la simulación: un comando no implementado dice "not on the slate
 * yet" — NUNCA inventa una salida plausible. Una salida falsa se la llevaría el usuario
 * a su terminal real y enseñaría algo falso; ese fallo es tan grave como una shell real.
 *
 * El puente es el punto: cada comando lleva COPIAR → "do it for real in your terminal".
 * Scaffolding fading (Códice §IV): cuando el usuario DEMUESTRA un comando (lo ejecuta
 * bien aquí), la Pizarra deja de EXPLICARLO y pasa a solo PROPONERLO. El andamio cae
 * por comando, medido en localStorage — no por sensación.
 *
 * API: window.AURELIUS_PIZARRA.montar(raiz) → { demostrados(), reset() }.
 */
window.AURELIUS_PIZARRA = (function () {
  var COMANDOS = ["ls", "cd", "pwd", "cat", "mkdir", "touch", "echo", "grep", "head", "tail", "wc", "tree"];
  var EXPLICA = {
    ls: "list a directory", cd: "change directory", pwd: "print working directory",
    cat: "print a file", mkdir: "make a directory", touch: "create an empty file",
    echo: "print text — or write it: echo hi > f", grep: "find lines matching a pattern",
    head: "first lines of a file", tail: "last lines of a file",
    wc: "count lines/words/chars", tree: "show the tree",
  };
  var CLAVE_DEM = "aurelius.pizarra.demostrados";

  function fsInicial() {
    return { type: "dir", children: {
      "notas.txt": { type: "file", content: "The silicon proposes.\nThe carbon signs.\n" },
      proyectos: { type: "dir", children: {
        "leeme.md": { type: "file", content: "# Projects\n- garden\n- node\n- slate\n" },
        huerto: { type: "dir", children: {} },
      } },
      diario: { type: "dir", children: {
        "dia1.txt": { type: "file", content: "today i learned ls\nand also pwd\nand cat\n" },
      } },
    } };
  }

  function cargarDem() {
    try { return JSON.parse(localStorage.getItem(CLAVE_DEM) || "[]"); }
    catch (e) { return []; }
  }
  function guardarDem(lista) {
    try { localStorage.setItem(CLAVE_DEM, JSON.stringify(lista)); } catch (e) { /* memoria */ }
  }

  // ---- filesystem ficticio (en memoria) --------------------------------------
  function nodoEn(fs, segs) {
    var n = fs;
    for (var i = 0; i < segs.length; i++) {
      if (n.type !== "dir" || !n.children[segs[i]]) return null;
      n = n.children[segs[i]];
    }
    return n;
  }
  function normaliza(cwd, arg) {
    // Devuelve array de segmentos desde la raíz, resolviendo . y ..
    var base = (arg && arg.charAt(0) === "/") ? [] : cwd.slice();
    var partes = (arg || "").split("/");
    for (var i = 0; i < partes.length; i++) {
      var p = partes[i];
      if (p === "" || p === ".") continue;
      if (p === "..") { base.pop(); continue; }
      base.push(p);
    }
    return base;
  }

  // ---- tokenizador (comillas dobles + redirección > / >>) --------------------
  function tokeniza(linea) {
    var toks = [], redir = null, i = 0;
    while (i < linea.length) {
      var c = linea.charAt(i);
      if (c === " ") { i++; continue; }
      if (c === ">") {
        redir = (linea.charAt(i + 1) === ">") ? ">>" : ">";
        i += (redir === ">>") ? 2 : 1;
        continue;
      }
      var t = "";
      if (c === '"') {
        i++;
        while (i < linea.length && linea.charAt(i) !== '"') { t += linea.charAt(i); i++; }
        i++;
      } else {
        while (i < linea.length && linea.charAt(i) !== " " && linea.charAt(i) !== ">") { t += linea.charAt(i); i++; }
      }
      toks.push({ t: t, trasRedir: redir !== null });
    }
    var args = toks.filter(function (x) { return !x.trasRedir; }).map(function (x) { return x.t; });
    var destino = toks.filter(function (x) { return x.trasRedir; }).map(function (x) { return x.t; })[0] || null;
    return { args: args, redir: redir, destino: destino };
  }

  // ---- ejecución (devuelve {out, err}) ---------------------------------------
  function ejecutar(fs, cwd, linea) {
    var tk = tokeniza(linea);
    var args = tk.args;
    var cmd = args.shift();
    if (!cmd) return { out: "", err: false };
    if (COMANDOS.indexOf(cmd) < 0) {
      // Honest sensors: NO se inventa salida. Se declara la ausencia y se guía.
      return { out: cmd + ": not on the slate yet — try: " + COMANDOS.join(" "), err: true, noImpl: true };
    }
    var r = { out: "", err: false };
    var arg = args[0];
    switch (cmd) {
      case "pwd": r.out = "/" + cwd.join("/"); break;
      case "ls": {
        var segs = arg ? normaliza(cwd, arg) : cwd.slice();
        var n = nodoEn(fs, segs);
        if (!n) { r = { out: "ls: cannot access '" + arg + "': No such file or directory", err: true }; break; }
        if (n.type === "file") { r.out = arg; break; }
        r.out = Object.keys(n.children).sort().join("  ");
        break;
      }
      case "cd": {
        if (!arg) { cwd.length = 0; break; } // cd → raíz
        var segs2 = normaliza(cwd, arg);
        var n2 = nodoEn(fs, segs2);
        if (!n2) { r = { out: "cd: " + arg + ": No such file or directory", err: true }; break; }
        if (n2.type !== "dir") { r = { out: "cd: " + arg + ": Not a directory", err: true }; break; }
        cwd.length = 0; Array.prototype.push.apply(cwd, segs2);
        break;
      }
      case "cat": {
        if (!arg) { r = { out: "cat: missing file operand", err: true }; break; }
        var nf = nodoEn(fs, normaliza(cwd, arg));
        if (!nf) { r = { out: "cat: " + arg + ": No such file or directory", err: true }; break; }
        if (nf.type === "dir") { r = { out: "cat: " + arg + ": Is a directory", err: true }; break; }
        r.out = nf.content.replace(/\n$/, "");
        break;
      }
      case "mkdir": case "touch": {
        if (!arg) { r = { out: cmd + ": missing operand", err: true }; break; }
        var segsN = normaliza(cwd, arg);
        var nombre = segsN.pop();
        var padre = nodoEn(fs, segsN);
        if (!padre || padre.type !== "dir") { r = { out: cmd + ": cannot create '" + arg + "': No such file or directory", err: true }; break; }
        if (padre.children[nombre]) {
          if (cmd === "mkdir") { r = { out: "mkdir: cannot create directory '" + arg + "': File exists", err: true }; }
          break; // touch sobre existente: no-op (como bash)
        }
        padre.children[nombre] = cmd === "mkdir" ? { type: "dir", children: {} } : { type: "file", content: "" };
        break;
      }
      case "echo": {
        var texto = args.join(" ");
        if (tk.redir && tk.destino) {
          var segsE = normaliza(cwd, tk.destino);
          var nom = segsE.pop();
          var pad = nodoEn(fs, segsE);
          if (!pad || pad.type !== "dir") { r = { out: "echo: " + tk.destino + ": No such file or directory", err: true }; break; }
          var prev = (pad.children[nom] && pad.children[nom].type === "file" && tk.redir === ">>") ? pad.children[nom].content : "";
          pad.children[nom] = { type: "file", content: prev + texto + "\n" };
        } else { r.out = texto; }
        break;
      }
      case "grep": case "head": case "tail": case "wc": {
        var esGrep = cmd === "grep";
        var patron = esGrep ? args.shift() : null;
        var nlineas = 10;
        if ((cmd === "head" || cmd === "tail") && args[0] === "-n") { args.shift(); nlineas = parseInt(args.shift(), 10) || 10; }
        var af = args[0];
        if (esGrep && (patron === undefined || af === undefined)) { r = { out: "usage: grep <pattern> <file>", err: true }; break; }
        if (!af) { r = { out: cmd + ": missing file operand", err: true }; break; }
        var ng = nodoEn(fs, normaliza(cwd, af));
        if (!ng) { r = { out: cmd + ": " + af + ": No such file or directory", err: true }; break; }
        if (ng.type === "dir") { r = { out: cmd + ": " + af + ": Is a directory", err: true }; break; }
        var lineas = ng.content.replace(/\n$/, "").split("\n");
        if (cmd === "grep") r.out = lineas.filter(function (l) { return l.indexOf(patron) >= 0; }).join("\n");
        else if (cmd === "head") r.out = lineas.slice(0, nlineas).join("\n");
        else if (cmd === "tail") r.out = lineas.slice(-nlineas).join("\n");
        else { // wc
          var chars = ng.content.length;
          var words = ng.content.split(/\s+/).filter(Boolean).length;
          var nl = (ng.content.match(/\n/g) || []).length;
          r.out = nl + " " + words + " " + chars + " " + af;
        }
        break;
      }
      case "tree": {
        var raizSegs = arg ? normaliza(cwd, arg) : cwd.slice();
        var nr = nodoEn(fs, raizSegs);
        if (!nr) { r = { out: "tree: " + arg + ": No such file or directory", err: true }; break; }
        var lin = [arg || "."];
        (function rec(n, pre) {
          if (n.type !== "dir") return;
          var ks = Object.keys(n.children).sort();
          ks.forEach(function (k, idx) {
            var ultimo = idx === ks.length - 1;
            lin.push(pre + (ultimo ? "└── " : "├── ") + k);
            rec(n.children[k], pre + (ultimo ? "    " : "│   "));
          });
        })(nr, "");
        r.out = lin.join("\n");
        break;
      }
    }
    return r;
  }

  // ---- copia robusta (mismo motivo que camino.js: http tailnet ≠ secure) ------
  function copiar(txt, btn) {
    function marca(t) { var v = btn.textContent; btn.textContent = t; setTimeout(function () { btn.textContent = v; }, 1200); }
    if (window.isSecureContext && navigator.clipboard) {
      navigator.clipboard.writeText(txt).then(function () { marca("copied ✓"); }).catch(function () { marca("select+copy"); });
      return;
    }
    var ta = document.createElement("textarea"); ta.value = txt; ta.style.position = "fixed"; ta.style.top = "-1000px";
    document.body.appendChild(ta); ta.focus(); ta.select();
    var ok = false; try { ok = document.execCommand("copy"); } catch (e) { ok = false; }
    document.body.removeChild(ta); marca(ok ? "copied ✓" : "select+copy");
  }

  function esc(s) { var d = document.createElement("div"); d.textContent = s; return d.innerHTML; }

  // ---- montaje ----------------------------------------------------------------
  function montar(raiz) {
    if (!raiz || raiz.dataset.pzMontado === "1") return apiDe(raiz);
    raiz.dataset.pzMontado = "1";
    var fs = fsInicial();
    var cwd = [];
    var demostrados = cargarDem();

    raiz.innerHTML =
      '<div class="pz">' +
      '  <div class="pz-badge" role="status">PIZARRA · SIMULATION · RUNS NOTHING</div>' +
      '  <div class="pz-hint">A fake slate to practice on. It executes <b>nothing</b> real — the point is to <b>copy</b> a command and run it for real in your own terminal.</div>' +
      '  <div class="pz-board" id="pz-board" aria-live="polite"></div>' +
      '  <form class="pz-fila" id="pz-fila"><span class="pz-prompt" id="pz-prompt">/ $</span>' +
      '    <input class="pz-in" id="pz-in" type="text" autocomplete="off" autocapitalize="off" spellcheck="false" aria-label="slate command" /></form>' +
      '  <div class="pz-fade"><span class="pz-fade-lbl">commands</span><span class="pz-chips" id="pz-chips"></span></div>' +
      '</div>';

    var board = raiz.querySelector("#pz-board");
    var input = raiz.querySelector("#pz-in");
    var prompt = raiz.querySelector("#pz-prompt");
    var chips = raiz.querySelector("#pz-chips");

    function pintaPrompt() { prompt.textContent = "/" + cwd.join("/") + " $"; }

    function pintaChips() {
      // Scaffolding fading VISIBLE: no demostrado → se EXPLICA; demostrado → solo se PROPONE.
      chips.innerHTML = "";
      COMANDOS.forEach(function (c) {
        var hecho = demostrados.indexOf(c) >= 0;
        var b = document.createElement("button");
        b.type = "button";
        b.className = "pz-chip" + (hecho ? " pz-chip-hecho" : "");
        b.setAttribute("data-cmd", c);
        b.title = hecho ? "demonstrated — copy to run for real" : EXPLICA[c];
        b.innerHTML = hecho
          ? '<span class="pz-chip-cmd">' + c + '</span>'
          : '<span class="pz-chip-cmd">' + c + '</span> <span class="pz-chip-exp">' + esc(EXPLICA[c]) + "</span>";
        b.addEventListener("click", function () { input.value = c + " "; input.focus(); copiar(c, b); });
        chips.appendChild(b);
      });
    }

    function fila(linea, res) {
      var div = document.createElement("div");
      div.className = "pz-linea";
      var cab = document.createElement("div");
      cab.className = "pz-eco";
      cab.innerHTML = '<span class="pz-eco-p">' + esc("/" + cwd.join("/") + " $") + '</span> <span class="pz-eco-cmd">' + esc(linea) + "</span>";
      var cop = document.createElement("button");
      cop.type = "button"; cop.className = "pz-copiar"; cop.textContent = "⧉ copy";
      cop.title = "copy this command and run it for real in your terminal";
      cop.addEventListener("click", function () { copiar(linea, cop); });
      cab.appendChild(cop);
      div.appendChild(cab);
      if (res.out !== "") {
        var pre = document.createElement("pre");
        pre.className = "pz-salida" + (res.err ? " pz-err" : "");
        pre.textContent = res.out;
        div.appendChild(pre);
      }
      board.appendChild(div);
      board.scrollTop = board.scrollHeight;
    }

    raiz.querySelector("#pz-fila").addEventListener("submit", function (e) {
      e.preventDefault();
      var linea = input.value.trim();
      input.value = "";
      if (!linea) return;
      var cmd = linea.split(/\s+/)[0];
      var res = ejecutar(fs, cwd, linea);
      fila(linea, res);
      pintaPrompt();
      // Se DEMUESTRA solo si es un comando real y NO dio error (aprendizaje medido).
      if (COMANDOS.indexOf(cmd) >= 0 && !res.err && demostrados.indexOf(cmd) < 0) {
        demostrados.push(cmd); guardarDem(demostrados); pintaChips();
      }
    });

    pintaPrompt();
    pintaChips();
    return apiDe(raiz);
  }

  function apiDe(raiz) {
    return {
      demostrados: function () { return cargarDem(); },
      reset: function () { try { localStorage.removeItem(CLAVE_DEM); } catch (e) {} },
      _raiz: raiz,
    };
  }

  return { montar: montar };
})();
