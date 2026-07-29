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

/**
 * Last-resort model tag for OFFLINE resilience only. The model name is NOT
 * hardcoded as the source of truth: it lives in the versioned manifest
 * (interface/models.json) and is loaded by `cargarModeloPorDefecto()`. Tag
 * footgun: this is an explicit instruct variant + quantization on purpose —
 * a bare tag can resolve to a Thinking variant with non-disableable reasoning.
 */
export const AURELIUS_AI_MODEL_FALLBACK = "qwen3:30b-a3b-instruct-2507-q4_K_M";

/** One recommended model as it appears in the versioned manifest. */
export interface ModeloManifiesto {
  readonly id: string;
  readonly tag: string;
  readonly class_b: number;
}

/** Shape of interface/models.json (only the fields this module reads). */
export interface Manifiesto {
  readonly default: string;
  readonly models: readonly ModeloManifiesto[];
}

/**
 * Resuelve el tag del modelo por defecto LEYÉNDOLO del manifiesto versionado
 * (models.json), nunca hardcodeándolo. Si el manifiesto no está disponible,
 * cae al fallback offline. Defensivo ante la forma del JSON.
 */
export async function cargarModeloPorDefecto(
  fetchImpl: typeof fetch = fetch,
  ruta = "models.json",
): Promise<string> {
  try {
    const r = await fetchImpl(ruta, { cache: "no-store" });
    if (!r.ok) return AURELIUS_AI_MODEL_FALLBACK;
    const m: unknown = await r.json();
    if (m !== null && typeof m === "object" && "models" in m) {
      const man = m as Manifiesto;
      if (Array.isArray(man.models)) {
        const elegido: ModeloManifiesto | undefined =
          man.models.find((x) => x.id === man.default) ?? man.models[0];
        if (elegido && typeof elegido.tag === "string" && elegido.tag.length > 0) {
          return elegido.tag;
        }
      }
    }
  } catch {
    /* offline → fallback */
  }
  return AURELIUS_AI_MODEL_FALLBACK;
}

export interface RespuestaIA {
  readonly texto: string;
  readonly modelo: string;
  /** ms de pared medidos en el cliente (para vigilar la latencia local). */
  readonly latenciaMs: number;
}

/**
 * Genera una respuesta con el modelo LOCAL (no-stream).
 * Aislado por diseño: solo `localhost`, nunca la red. El tag del modelo se pasa
 * como argumento (resuelto por `cargarModeloPorDefecto()`), jamás se hardcodea.
 */
export async function generarLocal(
  prompt: string,
  opciones: { numPredict?: number; signal?: AbortSignal; modelo?: string } = {},
): Promise<RespuestaIA> {
  const modelo: string = opciones.modelo ?? AURELIUS_AI_MODEL_FALLBACK;
  const t0 = performance.now();
  const r = await fetch(`${AURELIUS_AI_ENDPOINT}/api/generate`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({
      model: modelo,
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
  return { texto, modelo, latenciaMs: performance.now() - t0 };
}
