/* IA LOCAL DE AURELIUS — enrutado canónico (§D · crítico de rendimiento).
 *
 * REGLA DURA: Aurelius habla SOLO con el modelo residente del propio nodo
 * `soberano` (el "Beelink" = soberano, la MISMA máquina donde corre Aurelius y
 * donde vive `soberano-coder`). NUNCA a través del proxy que enruta a Fragua
 * (RK3588, CPU, hasta ~30s de latencia). El navegador de David corre en soberano,
 * así que `localhost:11434` = el Ollama local de soberano, con GPU/Vulkan.
 *
 * Verificado 2026-07-20: `ollama ps` muestra `soberano-coder:latest` a 100% GPU
 * en este endpoint (OLLAMA_IGPU_ENABLE=1 / Vulkan). Carga en frío ~6s + 1 tok;
 * en caliente, tiempo real. NO cruza la red del rack hacia otros nodos.
 *
 * Endpoint ANTES (a corregir): proxy → Fragua (batch/CPU, lento).
 * Endpoint AHORA: localhost:11434 (soberano, GPU) — aislado, mínima latencia. */

/** Endpoint del modelo local de soberano. Localhost del propio nodo, jamás la red. */
export const AURELIUS_AI_ENDPOINT = "http://localhost:11434";

/** Modelo residente con aceleración GPU/Vulkan en soberano. */
export const AURELIUS_AI_MODEL = "soberano-coder:latest";

export interface RespuestaIA {
  readonly texto: string;
  readonly modelo: string;
  /** ms de pared medidos en el cliente (para vigilar la latencia local). */
  readonly latenciaMs: number;
}

/**
 * Genera una respuesta con el modelo LOCAL de soberano (no-stream).
 * Aislado por diseño: solo `localhost`, nunca el proxy hacia Fragua.
 */
export async function generarLocal(
  prompt: string,
  opciones: { numPredict?: number; signal?: AbortSignal } = {},
): Promise<RespuestaIA> {
  const t0 = performance.now();
  const r = await fetch(`${AURELIUS_AI_ENDPOINT}/api/generate`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({
      model: AURELIUS_AI_MODEL,
      prompt,
      stream: false,
      options: { num_predict: opciones.numPredict ?? 256 },
    }),
    signal: opciones.signal ?? null,
  });
  if (!r.ok) {
    throw new Error(`IA local no responde (${r.status}) — ¿ollama en soberano vivo?`);
  }
  const carga: unknown = await r.json();
  const texto =
    typeof carga === "object" && carga !== null && "response" in carga
      ? String((carga as { response: unknown }).response)
      : "";
  return { texto, modelo: AURELIUS_AI_MODEL, latenciaMs: performance.now() - t0 };
}
