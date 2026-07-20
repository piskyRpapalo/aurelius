/* Sistema de misiones de Aurelius (§C).
 *
 * Estructura extensible: cada misión declara Objetivo, Tier de hardware, pasos y
 * la SKILL que otorga. Añadir una misión = empujar un objeto a `MISSIONS`. El
 * "Constructor de Misiones" comunitario (usuarios proponen, David firma) es Fase 2
 * / horizonte: esta forma de datos ya lo soporta (una misión es solo datos), pero
 * NO se construye aquí.
 *
 * FASE 1 = ritos LOCALES (M1–M3). Las misiones de red (handshake Tailscale, trueque
 * de cómputo) son horizonte F6 — exponen topología y arrastran puntos vetados; no
 * se implementan. El tier "red" existe en el tipo para cuando llegue su hora. */

import type { Bilingue, Locale } from "./i18n/dictionary";

export type HardwareTier = "local" | "movil" | "red";
export type MissionStatus = "available" | "active" | "done" | "locked";

export interface Mission {
  readonly id: string;
  readonly code: string; // "M1", "M2", …
  readonly tier: HardwareTier;
  readonly title: Bilingue;
  readonly objective: Bilingue;
  readonly steps: Record<Locale, readonly string[]>;
  /** La skill de soberanía que el rito otorga al completarse. */
  readonly skill: Bilingue;
  readonly status: MissionStatus;
  /** Efecto IKEA: la misión produce algo que es TUYO (tu nodo, tu mascota). */
  readonly ikea?: boolean;
}

export const MISSIONS: readonly Mission[] = [
  {
    id: "primer-espejo",
    code: "M1",
    tier: "local",
    ikea: true,
    title: {
      en: "The First Mirror — Rite of Seeding",
      es: "El Primer Espejo — Rito de Siembra",
    },
    objective: {
      en: "Create your companion: the personification of your Hexelion. Effect IKEA — it is YOUR node.",
      es: "Crea tu compañero: la personificación de tu Hexelion. Efecto IKEA — es TU nodo.",
    },
    steps: {
      en: [
        "Generate an avatar with a free AI (Leonardo.ai, Bing) using the primed Solar-punk prompt.",
        "Upload the image — Aurelius cleans the background and scales it nearest-neighbor.",
        "It is saved on your node and becomes your companion, in both homes.",
      ],
      es: [
        "Genera un avatar con una IA gratis (Leonardo.ai, Bing) con el prompt Solar-punk cebado.",
        "Sube la imagen — Aurelius limpia el fondo y la escala nearest-neighbor.",
        "Se guarda en tu nodo y se vuelve tu compañero, en los dos hogares.",
      ],
    },
    skill: {
      en: "Ownership: your node has a face you made.",
      es: "Propiedad: tu nodo tiene una cara que hiciste tú.",
    },
    status: "available",
  },
  {
    id: "scribe-local",
    code: "M2",
    tier: "local",
    title: {
      en: "The Local Scribe",
      es: "El Scribe Local",
    },
    objective: {
      en: "Learn the local memory (RAG): save your first piece of curated knowledge, on-node.",
      es: "Aprende la memoria local (RAG): guarda tu primer conocimiento curado, en el nodo.",
    },
    steps: {
      en: [
        "Write a short note worth remembering.",
        "Curate it: title, source, why it matters.",
        "Store it in the local memory — it never leaves your node.",
      ],
      es: [
        "Escribe una nota corta que valga la pena recordar.",
        "Cúrala: título, fuente, por qué importa.",
        "Guárdala en la memoria local — nunca sale de tu nodo.",
      ],
    },
    skill: {
      en: "Sovereign memory: knowledge you keep, not knowledge you rent.",
      es: "Memoria soberana: conocimiento que guardas, no que alquilas.",
    },
    status: "locked",
  },
  {
    id: "sonda-fisica",
    code: "M3",
    tier: "movil",
    title: {
      en: "The Physical Probe",
      es: "La Sonda Física",
    },
    objective: {
      en: "Your first botanical photo in airplane mode (data sovereignty), signed locally.",
      es: "Tu primera foto botánica en modo avión (soberanía del dato), firmada en local.",
    },
    steps: {
      en: [
        "Enable airplane mode — nothing leaves the device.",
        "Photograph a plant; the probe reads it offline.",
        "The capture is signed locally before anything syncs.",
      ],
      es: [
        "Activa el modo avión — nada sale del dispositivo.",
        "Fotografía una planta; la sonda la lee sin red.",
        "La captura se firma en local antes de sincronizar nada.",
      ],
    },
    skill: {
      en: "Physical proof: the world enters your node on your terms.",
      es: "Prueba física: el mundo entra a tu nodo en tus términos.",
    },
    status: "locked",
  },
];
