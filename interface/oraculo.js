"use strict";
/* Oráculo de recursos de Aurelius — un GUARDIÁN que evita frustración: antes de
   que el usuario descargue un modelo, estima qué CLASE cabe en su máquina y le
   ENSEÑA el porqué. No prohíbe (es su máquina, su soberanía); informa.

   Fuente del dato: el inventario local de Aurelius (/api/inventario → estado del
   soberano). Campo clave: `ram_disponible_gb`. NO hay campo de VRAM/GPU en el
   inventario → se DECLARA "no reportada", jamás se estima a ojo (honest sensors).

   La math NO es una métrica medida por modelo: es una ESTIMACIÓN de viabilidad,
   anclada en un punto REAL medido en este proyecto (un modelo de 30.5B mil
   millones a cuantización Q4_K_M ocupa ≈18.56 GB → ≈0.6 GB por mil millones a Q4)
   más las razones de memoria estándar por cuantización. Se etiqueta como estimada.

   DOS FÍSICAS DISTINTAS (corrección 2026-07-29):
   - RAM (footprint) = f(parámetros TOTALES): todos los pesos deben residir en memoria.
   - Velocidad (tok/s) = f(parámetros ACTIVOS): en un MoE solo computan los expertos
     enrutados por token. El ancla medida (35 tok/s) es de un MoE con ~3.3B ACTIVOS;
     NO se extrapola a un modelo DENSO de tamaño total parecido (un denso de 30B es
     mucho más lento). La velocidad se etiqueta [MEDIDO] / [ESTIMADO] / [NO APLICABLE]. */

window.AURELIUS_ORACULO = (function () {
  // Ancla medida (este proyecto): 18.56 GB / 30.5 B ≈ 0.61 → 0.6 GB por B a Q4.
  var GB_POR_B = { q4: 0.6, q8: 1.1, f16: 2.0 };
  var OVERHEAD_GB = 3.0; // SO + servicios + margen base
  var KV_GB = 1.5; // caché de contexto aproximada (crece con la ventana)
  var CLASES_B = [1, 3, 8, 14, 32, 70]; // tamaños comunes en mil millones de parámetros

  // Ancla de VELOCIDAD medida en este proyecto: es un MoE, no un denso. Los 35 tok/s
  // corresponden a ~3.3B ACTIVOS. No se transfieren a arquitecturas densas.
  var ANCLA_VELOCIDAD = { arch: "moe", activos_b: 3.3, tok_s: 35 };

  // Roofline para DENSOS (§5.1): el decode es memory-bound → cada token lee TODOS
  // los pesos una vez → tok/s ≈ ancho_banda ÷ peso × η. Es DERIVACIÓN, no medición.
  var BW_MEM_GBS = 80;     // ancho de banda de memoria ASUMIDO (Beelink DDR5 dual-ch ~80–90 GB/s)
  var ETA_ROOFLINE = 0.75; // eficiencia típica del roofline (0.7–0.8)

  // footprint = RAM = f(parámetros TOTALES). Correcto para denso Y MoE: todos los
  // pesos residen en memoria aunque en un MoE solo una fracción compute por token.
  function footprint(paramsB, quant) {
    var por = GB_POR_B[quant] || GB_POR_B.q4;
    return paramsB * por + KV_GB;
  }

  /** Etiqueta la VELOCIDAD de un modelo del manifiesto separando denso de MoE. La
      medición (35 tok/s) SOLO aplica al ancla MoE; a un denso NO se extrapola. Devuelve
      { etiqueta: "MEDIDO"|"ESTIMADO"|"NO APLICABLE", texto }. Defensivo ante la forma. */
  function velocidadDe(model) {
    if (!model || typeof model !== "object") {
      return { etiqueta: "NO APLICABLE", texto: "velocidad desconocida" };
    }
    if (model.throughput_provenance === "measured" && typeof model.throughput_tok_s === "number") {
      var act = typeof model.active_b === "number" ? model.active_b : null;
      return {
        etiqueta: "MEDIDO",
        texto: "~" + model.throughput_tok_s + " tok/s [MEDIDO]" + (act ? " (MoE, ~" + act + "B activos)" : ""),
      };
    }
    if (model.arch === "moe") {
      return { etiqueta: "ESTIMADO", texto: "velocidad [ESTIMADA] — MoE sin medir en este HW" };
    }
    // Denso: NO se mide, pero SÍ se DERIVA por roofline (memory-bound). NO DATA es
    // para lo que no sabes; esto se sabe por deducción → se etiqueta [DERIVADO] con
    // la fórmula y el ancho de banda asumido, no se esconde ni se finge medido.
    var q = "q4";
    var qs = ("" + (model.quant || "")).toLowerCase();
    if (qs.indexOf("q8") >= 0) q = "q8";
    else if (qs.indexOf("f16") >= 0 || qs.indexOf("fp16") >= 0) q = "f16";
    var pB = typeof model.active_b === "number" ? model.active_b : null; // denso: active = total
    if (pB === null) {
      return { etiqueta: "NO APLICABLE", texto: "velocidad [NO APLICABLE] — falta el tamaño para derivarla" };
    }
    var pesoGB = pB * (GB_POR_B[q] || GB_POR_B.q4);
    var toks = Math.round((BW_MEM_GBS / pesoGB) * ETA_ROOFLINE);
    return {
      etiqueta: "DERIVADO",
      texto: "~" + toks + " tok/s [DERIVADO] — roofline BW÷peso×η (BW≈" + BW_MEM_GBS +
        " GB/s asumido · η≈" + ETA_ROOFLINE + " · peso≈" + pesoGB.toFixed(1) + " GB)",
    };
  }

  /** Analiza la RAM disponible (GB) → clases que caben, recomendado, y VRAM
      declarada como no disponible si no viene en el inventario. Defensivo. */
  function analizar(ramGb, vramGb) {
    if (typeof ramGb !== "number" || !isFinite(ramGb) || ramGb <= 0) {
      return { disponible: false, motivo: "RAM no reportada en el inventario" };
    }
    var usable = ramGb - OVERHEAD_GB;
    var clases = CLASES_B.map(function (p) {
      var mem = footprint(p, "q4");
      return {
        params_b: p,
        mem_est_gb: Math.round(mem * 10) / 10,
        cabe: mem <= ramGb, // entra pero puede ir justo
        comodo: mem <= usable * 0.9, // entra con margen para SO + contexto
      };
    });
    var comodos = clases.filter(function (c) { return c.comodo; });
    return {
      disponible: true,
      ramGb: Math.round(ramGb * 10) / 10,
      vramGb: typeof vramGb === "number" && isFinite(vramGb) ? vramGb : null, // null = no reportada
      clases: clases,
      recomendadoMaxB: comodos.length ? comodos[comodos.length - 1].params_b : null,
      // El porqué, para ENSEÑAR (no solo obedecer):
      regla: "memoria ≈ (parámetros en miles de millones) × (bytes por peso, que fija la cuantización) + caché de contexto. Q4 ≈ 0.6 GB por mil millones; Q8 el doble; F16 más del triple.",
      aviso_swap: "si el modelo supera tu RAM, el sistema tira de disco (swap): funciona, pero MUCHO más lento — segundos por palabra en vez de tiempo real.",
      nota_estimacion: "cifras ESTIMADAS (ancladas en un punto real medido), no medidas por modelo. Con GPU y suficiente VRAM podrías correr más de lo que dice esta estimación por RAM.",
      nota_velocidad: "que un modelo QUEPA en RAM (params totales) no dice cómo de RÁPIDO irá: la velocidad la fijan los params ACTIVOS. La única medición (35 tok/s) es de un MoE de ~3.3B activos y NO se extrapola a modelos densos.",
    };
  }

  /** Cruza el análisis de RAM con el manifiesto versionado (models.json) y devuelve
      los modelos concretos que caben cómodos, del más grande al más pequeño. El
      Oráculo NO hardcodea tags: los LEE del manifiesto. Defensivo ante la forma del
      objeto (que puede venir null si el fetch falló). */
  function recomendarTags(a, manifiesto) {
    if (!a || a.disponible === false) return [];
    if (!manifiesto || !Array.isArray(manifiesto.models)) return [];
    var tope = typeof a.recomendadoMaxB === "number" ? a.recomendadoMaxB : 0;
    return manifiesto.models
      .filter(function (m) {
        return m && typeof m.tag === "string" && typeof m.class_b === "number" && m.class_b <= tope;
      })
      .sort(function (x, y) { return y.class_b - x.class_b; })
      .map(function (m) {
        return {
          tag: m.tag,
          class_b: m.class_b,
          arch: m.arch === "moe" ? "moe" : "dense",
          active_b: typeof m.active_b === "number" ? m.active_b : m.class_b,
          verificado: m.hardware_verified === true,
          velocidad: velocidadDe(m), // { etiqueta, texto } — MEDIDO / ESTIMADO / NO APLICABLE
        };
      });
  }

  /** Resumen en texto llano para inyectar al mentor / mostrar al usuario. Si se le
      pasa el manifiesto (models.json ya parseado), nombra los tags concretos que
      caben — leídos del manifiesto, jamás hardcodeados. */
  function resumen(a, manifiesto) {
    if (!a || a.disponible === false) {
      return "Recursos: RAM no reportada por el inventario — no estimo a ojo. Revisa el proveedor de inventario de hardware.";
    }
    var caben = a.clases.filter(function (c) { return c.comodo; }).map(function (c) { return c.params_b + "B"; });
    var justos = a.clases.filter(function (c) { return c.cabe && !c.comodo; }).map(function (c) { return c.params_b + "B"; });
    var noCaben = a.clases.filter(function (c) { return !c.cabe; }).map(function (c) { return c.params_b + "B"; });
    var partes = [];
    partes.push("RAM disponible: " + a.ramGb + " GB. VRAM: " + (a.vramGb === null ? "no reportada" : a.vramGb + " GB") + ".");
    partes.push("A cuantización Q4: caben con holgura " + (caben.join(", ") || "—") + (justos.length ? "; van justos " + justos.join(", ") : "") + (noCaben.length ? "; NO caben (swap a disco) " + noCaben.join(", ") : "") + ".");
    if (a.recomendadoMaxB !== null) partes.push("Recomendado máximo cómodo: ~" + a.recomendadoMaxB + "B a Q4.");
    partes.push("La RAM decide qué CABE (params totales); la velocidad depende de los params ACTIVOS — no son lo mismo.");
    var recs = recomendarTags(a, manifiesto);
    if (recs.length) {
      var etq = recs.slice(0, 3).map(function (r) {
        return r.tag + (r.verificado ? "" : " (sin verificar)") + " · " + r.velocidad.texto;
      });
      partes.push("Del manifiesto, te caben: " + etq.join("; ") + ".");
    }
    return partes.join(" ");
  }

  return { analizar: analizar, resumen: resumen, footprint: footprint, recomendarTags: recomendarTags, velocidadDe: velocidadDe };
})();
