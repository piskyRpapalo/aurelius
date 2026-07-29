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
   más las razones de memoria estándar por cuantización. Se etiqueta como estimada. */

window.AURELIUS_ORACULO = (function () {
  // Ancla medida (este proyecto): 18.56 GB / 30.5 B ≈ 0.61 → 0.6 GB por B a Q4.
  var GB_POR_B = { q4: 0.6, q8: 1.1, f16: 2.0 };
  var OVERHEAD_GB = 3.0; // SO + servicios + margen base
  var KV_GB = 1.5; // caché de contexto aproximada (crece con la ventana)
  var CLASES_B = [1, 3, 8, 14, 32, 70]; // tamaños comunes en mil millones de parámetros

  function footprint(paramsB, quant) {
    var por = GB_POR_B[quant] || GB_POR_B.q4;
    return paramsB * por + KV_GB;
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
      .map(function (m) { return { tag: m.tag, class_b: m.class_b, verificado: m.hardware_verified === true }; });
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
    var recs = recomendarTags(a, manifiesto);
    if (recs.length) {
      var etq = recs.slice(0, 3).map(function (r) { return r.tag + (r.verificado ? "" : " (sin verificar)"); });
      partes.push("Del manifiesto, te caben: " + etq.join(", ") + ".");
    }
    return partes.join(" ");
  }

  return { analizar: analizar, resumen: resumen, footprint: footprint, recomendarTags: recomendarTags };
})();
