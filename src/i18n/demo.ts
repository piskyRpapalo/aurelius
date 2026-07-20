/* Demo/humo del andamiaje i18n de Aurelius. Ejecuta con `npx tsx src/i18n/demo.ts`.
   No es la app: solo prueba que el toggle EN⇄ES y las traducciones responden. */

import { crearI18n } from "./i18n";

const i18n = crearI18n("en");
const log = (): void =>
  console.log(`[${i18n.locale}] ${i18n.t("app.name")} — ${i18n.t("app.tagline")}`);

const off = i18n.subscribe(() => log());
log(); // [en] Aurelius — The emperor's library that learns.
i18n.toggle(); // [es] Aurelius — La biblioteca del emperador que aprende.
i18n.toggle(); // [en] ...
off();

console.log("toggle-label:", i18n.t("lang.toggle"));
