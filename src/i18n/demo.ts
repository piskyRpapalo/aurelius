/* Demo/humo del andamiaje i18n de Aurelius. Ejecuta con `npx tsx src/i18n/demo.ts`
   (o cualquier runner TS). No es la app: solo prueba que el toggle EN⇄ES y las
   traducciones responden. */

import { crearI18n } from "./i18n";

const i18n = crearI18n("en");
const log = (): void =>
  console.log(`[${i18n.locale}] ${i18n.t("app.name")} — ${i18n.t("app.tagline")}`);

const off = i18n.subscribe(() => log());
log(); // [en] Aurelius — Learn by playing, one card at a time.
i18n.toggle(); // [es] Aurelius — Aprende jugando, una carta a la vez.
i18n.toggle(); // [en] ...
off();

console.log("check:", i18n.t("feedback.correct"), "/", (i18n.set("es"), i18n.t("feedback.correct")));
