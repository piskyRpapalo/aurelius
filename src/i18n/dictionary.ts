/* Diccionario bilingüe de Aurelius (EN/ES).
 *
 * OJO — LEY DE ALCANCE: este toggle EN/ES es de AURELIUS (la app de aprendizaje,
 * mascota de David para probar el producto). NO es del dashboard Hexelion, cuya
 * ley de idiomas es dura e inmutable: El Nexo es EN, Le Jardin es FR, interno ES.
 * Aurelius es su propio organismo; su bilingüismo vive aquí y solo aquí.
 *
 * Cada clave existe en los dos idiomas. Añadir un idioma = añadir su columna en
 * `Locale` y su bloque en `dictionary`; el tipo `MessageKey` obliga a cubrir
 * todas las claves (no hay traducción a medias silenciosa). */

export type Locale = "en" | "es";

export const LOCALES: readonly Locale[] = ["en", "es"] as const;

/** Todas las claves de mensaje conocidas por Aurelius. */
export type MessageKey =
  | "app.name"
  | "app.tagline"
  | "nav.learn"
  | "nav.review"
  | "nav.progress"
  | "action.start"
  | "action.next"
  | "action.check"
  | "feedback.correct"
  | "feedback.tryAgain"
  | "lang.toggle";

type Messages = Record<MessageKey, string>;

export const dictionary: Record<Locale, Messages> = {
  en: {
    "app.name": "Aurelius",
    "app.tagline": "Learn by playing, one card at a time.",
    "nav.learn": "Learn",
    "nav.review": "Review",
    "nav.progress": "Progress",
    "action.start": "Start",
    "action.next": "Next",
    "action.check": "Check",
    "feedback.correct": "Correct!",
    "feedback.tryAgain": "Not quite — try again.",
    "lang.toggle": "Español",
  },
  es: {
    "app.name": "Aurelius",
    "app.tagline": "Aprende jugando, una carta a la vez.",
    "nav.learn": "Aprender",
    "nav.review": "Repasar",
    "nav.progress": "Progreso",
    "action.start": "Empezar",
    "action.next": "Siguiente",
    "action.check": "Comprobar",
    "feedback.correct": "¡Correcto!",
    "feedback.tryAgain": "Casi — inténtalo de nuevo.",
    "lang.toggle": "English",
  },
};
