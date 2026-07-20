/* Diccionario bilingüe de Aurelius (EN/ES) — CADENAS DE UI (chrome).
 *
 * OJO — LEY DE ALCANCE: este toggle EN/ES es de AURELIUS (la app de aprendizaje,
 * la biblioteca del emperador que aprende). NO es del dashboard Hexelion, cuya ley
 * de idiomas es dura: El Nexo es EN, Le Jardin es FR, interno ES. Aurelius es su
 * propio organismo; su bilingüismo vive aquí y solo aquí.
 *
 * El contenido largo de cada misión (título, objetivo, pasos, skill) vive tipado
 * en missions.ts como objetos {en, es} — no en este diccionario plano. */

export type Locale = "en" | "es";

export const LOCALES: readonly Locale[] = ["en", "es"] as const;

/** Bloque de texto por idioma (para contenido que no es chrome). */
export type Bilingue = Record<Locale, string>;

/** Todas las claves de chrome conocidas por Aurelius. */
export type MessageKey =
  | "app.name"
  | "app.tagline"
  | "hero.eyebrow"
  | "hero.subtitle"
  | "lang.toggle"
  | "missions.title"
  | "missions.phase"
  | "mission.objective"
  | "mission.steps"
  | "mission.skill"
  | "mission.start"
  | "mission.active"
  | "mission.done"
  | "mission.locked"
  | "tier.local"
  | "tier.movil"
  | "tier.red"
  | "mascot.title"
  | "mascot.hint"
  | "mascot.state.normal"
  | "mascot.state.pensando"
  | "mascot.state.ayudando"
  | "mascot.state.desconectado"
  | "m1.upload"
  | "m1.hint"
  | "m1.save"
  | "m1.created"
  | "m1.reset"
  | "footer.scope";

type Messages = Record<MessageKey, string>;

export const dictionary: Record<Locale, Messages> = {
  en: {
    "app.name": "Aurelius",
    "app.tagline": "The emperor's library that learns.",
    "hero.eyebrow": "Technical sovereignty, one mission at a time",
    "hero.subtitle":
      "Meditations were notes to oneself. Aurelius is your Codex: play the missions, earn the skills, build your own node.",
    "lang.toggle": "Español",
    "missions.title": "The Hexelion Path",
    "missions.phase": "Phase 1 · local rites",
    "mission.objective": "Objective",
    "mission.steps": "Steps",
    "mission.skill": "Skill earned",
    "mission.start": "Begin",
    "mission.active": "In progress",
    "mission.done": "Completed",
    "mission.locked": "Locked",
    "tier.local": "local",
    "tier.movil": "mobile",
    "tier.red": "network",
    "mascot.title": "Your companion",
    "mascot.hint": "Create it in the First Mirror. One character, two homes — it also lives in the Garden.",
    "mascot.state.normal": "at rest",
    "mascot.state.pensando": "thinking",
    "mascot.state.ayudando": "helping",
    "mascot.state.desconectado": "offline",
    "m1.upload": "Upload your avatar",
    "m1.hint": "Generate it with a free AI (Leonardo.ai, Bing) using the Solar-punk prompt, then upload it. It stays on your node.",
    "m1.save": "Set as companion",
    "m1.created": "Your companion is born — the personification of your Hexelion.",
    "m1.reset": "Choose another",
    "footer.scope":
      "Aurelius is the emperor's library. Hexelion is its physical workshop. P0X is the whole empire. Don't confuse them.",
  },
  es: {
    "app.name": "Aurelius",
    "app.tagline": "La biblioteca del emperador que aprende.",
    "hero.eyebrow": "Soberanía técnica, una misión a la vez",
    "hero.subtitle":
      "Las Meditaciones eran notas a uno mismo. Aurelius es tu Códice: juega las misiones, gana las skills, construye tu propio nodo.",
    "lang.toggle": "English",
    "missions.title": "El Camino Hexelion",
    "missions.phase": "Fase 1 · ritos locales",
    "mission.objective": "Objetivo",
    "mission.steps": "Pasos",
    "mission.skill": "Skill que ganas",
    "mission.start": "Empezar",
    "mission.active": "En curso",
    "mission.done": "Completada",
    "mission.locked": "Bloqueada",
    "tier.local": "local",
    "tier.movil": "móvil",
    "tier.red": "red",
    "mascot.title": "Tu compañero",
    "mascot.hint": "Créalo en el Primer Espejo. Un personaje, dos hogares — también vive en el Jardín.",
    "mascot.state.normal": "en reposo",
    "mascot.state.pensando": "pensando",
    "mascot.state.ayudando": "ayudando",
    "mascot.state.desconectado": "desconectado",
    "m1.upload": "Sube tu avatar",
    "m1.hint": "Genéralo con una IA gratis (Leonardo.ai, Bing) usando el prompt Solar-punk, y súbelo. Se queda en tu nodo.",
    "m1.save": "Fijar como compañero",
    "m1.created": "Tu compañero ha nacido — la personificación de tu Hexelion.",
    "m1.reset": "Elegir otro",
    "footer.scope":
      "Aurelius es la biblioteca del emperador. Hexelion es su taller físico. P0X es el imperio entero. No los confundas.",
  },
};
