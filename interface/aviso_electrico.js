"use strict";
/* ADVERTENCIA ELÉCTRICA — Método v1 §2.3. Obligatoria, no negociable.

   «Esta advertencia aparece al inicio del tema, no en un pie de página, y no se
   puede desactivar. Si un módulo futuro necesita saltársela, no entra.»

   ─── QUÉ SIGNIFICA AQUÍ "NO SE PUEDE DESACTIVAR" ──────────────────────────────
   Se cumple por ARQUITECTURA, no por vigilancia:

     1. `montar()` no acepta ninguna opción para ocultarla, atenuarla o diferirla.
        No hay flag que poner a false. Si mañana alguien necesita uno, tendrá que
        añadirlo a este fichero, y eso es exactamente la decisión que §2.3 quiere
        que sea visible en un diff en vez de ocurrir en silencio.
     2. Se inserta como PRIMER hijo del contenedor del tema, siempre. No al final,
        no en un desplegable, no detrás de un "leer más".
     3. `TEMAS_ELECTRICOS` está congelado: en tiempo de ejecución nadie puede
        sacar un tema de la lista. Añadir uno se hace aquí, en el código.
     4. `verificar()` permite a quien pinte un tema comprobar que la advertencia
        sigue puesta después de un re-render, y volver a montarla si no.

   Lo que NO se promete, porque sería mentira: en su propia máquina el usuario
   puede borrar cualquier nodo con las herramientas del navegador. Ningún código
   servido en un cliente evita eso. Lo que se garantiza es que AURELIUS nunca se
   la salta ni le ofrece un interruptor para hacerlo.

   ─── ALCANCE (§2.3, literal) ──────────────────────────────────────────────────
   Corriente continua de 24 V o menos. En la práctica 3.3 V, 5 V, 12 V y pilas.
   JAMÁS red eléctrica doméstica (110/230 V CA), baterías de alta capacidad ni
   condensadores de alta tensión.

   API: window.AURELIUS_AVISO_ELECTRICO
     TEMAS_ELECTRICOS   lista congelada de identificadores de tema eléctricos.
     esElectrico(tema)  → bool
     montar({raiz, tema}) → bool (true si se ha renderizado)
     verificar(raiz)    → bool (¿sigue la advertencia dentro de este contenedor?)
   Requiere que i18n.js esté cargado antes. */

window.AURELIUS_AVISO_ELECTRICO = (function () {
  /* Registro ÚNICO de temas eléctricos. Se declara en el código y se congela: un
     tema sale de esta lista con un commit, jamás en tiempo de ejecución.

     Los identificadores salen del Método §2.4 y del arsenal, pestaña 4:
       tema-2    ELECTRICIDAD CONTINUA (<= 24 V CC) — §2.3 declarada activa
       tema-3    COMPONENTES — multímetro sobre componentes físicos
       mision-2  EL CIRCUITO — «ADVERTENCIA: 24 V de corriente continua como
                 máximo. Jamás red doméstica.»
     Ninguno de los tres existe todavía como módulo: la Fase 1 no autoriza
     construir temas. El registro y el punto de montaje quedan listos para cuando
     se construyan, que es lo que pide la tarea 3 de la Fase 1. */
  var TEMAS_ELECTRICOS = Object.freeze(["tema-2", "tema-3", "mision-2"]);

  var MARCA = "data-aviso-electrico";

  function esElectrico(tema) {
    return typeof tema === "string" && TEMAS_ELECTRICOS.indexOf(tema.trim().toLowerCase()) >= 0;
  }

  function esc(s) { var d = document.createElement("div"); d.textContent = String(s); return d.innerHTML; }

  /** ¿Sigue la advertencia dentro de este contenedor? Para que quien re-pinte un
      tema pueda comprobarlo y volver a montarla sin tener que acordarse de cómo. */
  function verificar(raiz) {
    var r = raiz || document;
    return !!(r.querySelector && r.querySelector("[" + MARCA + "]"));
  }

  /** Monta la advertencia como PRIMER hijo de `raiz` si `tema` es eléctrico.
      No hay parámetro para desactivarla: ver la cabecera de este fichero.
      Idempotente — si ya está puesta, no la duplica. */
  function montar(opts) {
    opts = opts || {};
    var raiz = opts.raiz;
    var tema = opts.tema;
    if (!raiz || !raiz.insertBefore) return false;
    if (!esElectrico(tema)) return false;
    if (verificar(raiz)) return true;

    var I = window.AURELIUS_I18N;

    /* Aviso de traducción DENTRO del propio recuadro, no solo en la cabecera de
       la página. Para prosa larga, caer a inglés es lo correcto (mejor que
       doctrina mal traducida). Para una advertencia de SEGURIDAD, el usuario
       merece saber, ahí mismo, que la está leyendo en un idioma que no es el que
       eligió porque nadie ha revisado la traducción. */
    var sinRevisar = I && typeof I.esVerificado === "function" && !I.esVerificado();

    var caja = document.createElement("aside");
    caja.setAttribute(MARCA, "obligatorio");
    caja.className = "ae-aviso";
    caja.setAttribute("role", "note");
    caja.setAttribute("aria-label", I.t("elec.title"));
    caja.innerHTML =
      '<div class="ae-cabecera">' + esc(I.t("elec.title")) + "</div>"
      + '<p class="ae-limite">' + esc(I.t("elec.limit")) + "</p>"
      + '<p class="ae-jamas">' + esc(I.t("elec.never")) + "</p>"
      + '<p class="ae-medida">' + esc(I.t("elec.measure")) + "</p>"
      + (sinRevisar ? '<p class="ae-idioma">' + esc(I.t("elec.unreviewed")) + "</p>" : "");

    raiz.insertBefore(caja, raiz.firstChild);
    return true;
  }

  return {
    TEMAS_ELECTRICOS: TEMAS_ELECTRICOS,
    esElectrico: esElectrico,
    verificar: verificar,
    montar: montar,
  };
})();
