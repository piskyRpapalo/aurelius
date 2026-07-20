/* i18n de Aurelius — motor mínimo, sin dependencias, framework-agnóstico.
 *
 * Diseño: un store diminuto con `locale` actual, `t(key)` para traducir, un
 * `toggle()` EN⇄ES y un `subscribe()` para que cualquier UI (vanilla, React,
 * lo que sea) se re-pinte al cambiar de idioma. Persiste la elección en
 * localStorage si existe (navegador); si no, vive en memoria (tests, SSR).
 *
 * Este es el ANDAMIAJE PREPARADO que pidió la misión: objeto de traducciones
 * en/es + toggle. La app Aurelius se construye encima cuando David lo decida. */

import {
  dictionary,
  LOCALES,
  type Locale,
  type MessageKey,
} from "./dictionary";

const CLAVE_ALMACEN = "aurelius.locale";

function esLocale(x: string | null): x is Locale {
  return x !== null && (LOCALES as readonly string[]).includes(x);
}

function leerInicial(): Locale {
  try {
    const guardado = globalThis.localStorage?.getItem(CLAVE_ALMACEN) ?? null;
    if (esLocale(guardado)) return guardado;
    // Sin preferencia guardada: respeta el idioma del navegador si es ES.
    const nav = globalThis.navigator?.language ?? "";
    if (nav.toLowerCase().startsWith("es")) return "es";
  } catch {
    /* sin localStorage/navigator (tests, SSR): cae al defecto */
  }
  return "en";
}

type Escucha = (locale: Locale) => void;

export interface I18n {
  /** Idioma actual. */
  readonly locale: Locale;
  /** Traduce una clave al idioma actual. */
  t(key: MessageKey): string;
  /** Fija el idioma explícitamente. */
  set(locale: Locale): void;
  /** Alterna EN⇄ES. */
  toggle(): void;
  /** Se suscribe a cambios de idioma; devuelve la función para desuscribirse. */
  subscribe(fn: Escucha): () => void;
}

export function crearI18n(inicial?: Locale): I18n {
  let locale: Locale = inicial ?? leerInicial();
  const escuchas = new Set<Escucha>();

  const persistir = (l: Locale): void => {
    try {
      globalThis.localStorage?.setItem(CLAVE_ALMACEN, l);
    } catch {
      /* sin almacenamiento: la elección vive en memoria */
    }
  };

  const emitir = (): void => {
    for (const fn of escuchas) fn(locale);
  };

  return {
    get locale(): Locale {
      return locale;
    },
    t(key: MessageKey): string {
      return dictionary[locale][key];
    },
    set(l: Locale): void {
      if (l === locale) return;
      locale = l;
      persistir(l);
      emitir();
    },
    toggle(): void {
      this.set(locale === "en" ? "es" : "en");
    },
    subscribe(fn: Escucha): () => void {
      escuchas.add(fn);
      return () => escuchas.delete(fn);
    },
  };
}

/** Instancia por defecto lista para importar. */
export const i18n: I18n = crearI18n();

export type { Locale, MessageKey } from "./dictionary";
