/* AURELIUS LOCAL AI — canonical routing (performance-critical).
 *
 * HARD RULE: Aurelius talks ONLY to the resident model on the SAME machine it
 * runs on, over `localhost` — never over the network to another node. The
 * browser runs on the same host, so `localhost:11434` is the local Ollama with
 * GPU acceleration. Isolated by design: minimal latency, nothing crosses the LAN.
 *
 * Configure the endpoint/model for your own machine (see interface/config.json
 * for the served face; this module is scaffolding for the future Vite build). */

/** Local model endpoint — the machine's own loopback, never the network. */
export const AURELIUS_AI_ENDPOINT = "http://localhost:11434";

/** Resident local model tag — set this to your own model. */
export const AURELIUS_AI_MODEL = "qwen3:30b-a3b-instruct-2507-q4_K_M";

export interface RespuestaIA {
  readonly texto: string;
  readonly modelo: string;
  /** ms de pared medidos en el cliente (para vigilar la latencia local). */
  readonly latenciaMs: number;
}

/**
 * Genera una respuesta con el modelo LOCAL (no-stream).
 * Aislado por diseño: solo `localhost`, nunca la red.
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
    throw new Error(`IA local no responde (${r.status}) — ¿ollama local vivo?`);
  }
  const carga: unknown = await r.json();
  const texto =
    typeof carga === "object" && carga !== null && "response" in carga
      ? String((carga as { response: unknown }).response)
      : "";
  return { texto, modelo: AURELIUS_AI_MODEL, latenciaMs: performance.now() - t0 };
}
