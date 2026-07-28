"use strict";
/* i18n compartido de Aurelius — una sola fuente para la cara (aurelius_face.html)
   y el Camino (camino.html). Base INGLÉS (canon del Soberano). El idioma vive en
   localStorage("aurelius.locale") y viaja entre ambas páginas + sobrevive a la
   recarga. Añadir un idioma = añadir su bloque al diccionario, sin refactor.

   HONESTIDAD DE TRADUCCIÓN (regla dura): `verified[loc]` marca qué idioma revisó
   un HUMANO. en/es/fr = verificados (David los habla). pt/de/el/ru = traducción
   automática pendiente de revisión: las claves que NO estén traducidas caen a
   INGLÉS (base) — jamás doctrina mal traducida al griego o al ruso. La cara
   muestra un aviso cuando el idioma activo no está verificado. */

window.AURELIUS_I18N = (function () {
  var LOCALES = ["en", "es", "fr", "pt", "de", "el", "ru"];
  var NOMBRE = { en: "EN", es: "ES", fr: "FR", pt: "PT", de: "DE", el: "EL", ru: "RU" };
  var VERIFIED = { en: true, es: true, fr: true, pt: false, de: false, el: false, ru: false };
  var CLAVE = "aurelius.locale";

  // ── Diccionario. en completo (base); es/fr completos (verificados); pt/de/el/ru
  //    traducen lo corto y caen a en en la prosa técnica larga (honesto). ──────
  var D = {
    en: {
      "face.sub": "the Preceptor · IronClaw",
      "face.vacio": "Greet him to wake the Preceptor.",
      "face.campo": "Speak with Aurelius…",
      "face.hablar": "SPEAK",
      "face.chemin": "The Path ▸",
      "face.verboLbl": "Aurelius:",
      "face.vBreve": "brief", "face.vNormal": "normal", "face.vDet": "detailed",
      "face.localAI": "Local AI · your node",
      "face.techDetail": "technical detail",
      "face.configWarn": "⚠ point Aurelius at your model: copy config.example.json → config.json",
      "id.ask": "Who are you, sovereign?",
      "id.placeholder": "Your name…",
      "id.enter": "Enter",
      "id.change": "change",
      "id.greet": "Sovereign: ",
      "path.title": "The Sovereign's Path",
      "path.back": "← Aurelius",
      "path.greet": "Hi, ", "wake.greet": "Welcome, {name}. Your Totem is awake — I see you now.",
      "path.serverDown.title": "The server isn't answering",
      "path.serverDown.body": "Can't reach the state (8050). Is the Aurelius service alive?",
      "step.M0": "The Totem", "step.M1": "The Fire", "step.M2": "The Water",
      "step.M3": "The Refuge", "step.M4": "The Signal", "step.M5": "The Pact",
      "m0.title": "M0 · The Totem",
      "m0.obj": "Create your companion: the face you made. IKEA effect — it's YOUR node.",
      "m0.step1": "Generate an avatar with a free image AI (Leonardo.ai, Bing) using this Solar-punk primer prompt:",
      "m0.prompt": "Portrait avatar, solar-punk, bust of a serene philosopher-emperor, pale marble veined with copper and warm circuits, amber light eyes, organic luminous background, soft pixel-art, hopeful, no text.",
      "m0.step2": "Download the image and upload it below with your name. It is sealed by hash and becomes your Totem.",
      "m0.nom": "Your name, sovereign…",
      "m0.btn": "Forge the Totem",
      "m0.errName": "Tell me your name first.",
      "m0.errFile": "Upload your Totem's image.",
      "m0.sealing": "Sealing your Totem…",
      "m0.sealed": "✓ Totem sealed (SHA-256 {sha}…). Welcome, {name}.",
      "m1.title": "M1 · The Fire",
      "m1.obj": "Light the Silicon Fire: run a model on YOUR machine, off the cloud.",
      "m1.step1": "Disconnect the network (wifi or cable off) — nothing leaves the node.",
      "m1.step2": "Ask the LOCAL model for something useful and safe: a plan, a recipe, a translation. Save its answer:",
      "m1.cmd1": "run the model offline and save the answer",
      "m1.step3": "Sign the result with your own hand (SHA-256 integrity):",
      "m1.cmd2": "sign it (IronClaw: you run it)",
      "m1.paste": "Paste below the SHA-256 the signer printed to seal M1.",
      "m1.sha": "SHA-256 (64 hex)…",
      "m1.btn": "Seal M1",
      "m2.title": "M2 · The Water",
      "m2.obj": "Local memory (RAG): store your first curated knowledge, in the node — it never leaves.",
      "m2.step1": "Create your grimoire and paste text from a PHYSICAL source of yours (a book, a note). Curate it: title, source, why it matters.",
      "m2.cmd1": "create the grimoire",
      "m2.step2": "Ingest it into your LOCAL vector memory (offline, no model, no network):",
      "m2.cmd2": "ingest (you run it)",
      "m2.step3": "Check it: retrieve something from the local vector with a question of yours:",
      "m2.cmd3": "search your local memory",
      "m2.step4": "Sign the manifest with your own hand:",
      "m2.cmd4": "sign the manifest",
      "m2.paste": "Paste below the manifest's SHA-256 to seal M2.",
      "m2.btn": "Seal M2",
      "seal.badSha": "That's not a SHA-256 (64 hex). Sign it in your terminal first.",
      "seal.sealing": "Sealing…",
      "seal.ok": "✓ {code} sealed. The Path continues.",
      "final.title": "The Path continues…",
      "final.body": "You walked M0→M2: the Totem, the Fire and the Water. M3 (the Refuge) and beyond are horizon — the scaffold retires as you climb. Aurelius awaits you for what's next.",
      "copy": "COPY", "copyOk": "OK", "copyManual": "⌘/Ctrl+C",
    },
    es: {
      "face.sub": "el Preceptor · IronClaw",
      "face.vacio": "Salúdalo para despertar al Preceptor.",
      "face.campo": "Habla con Aurelius…",
      "face.hablar": "HABLAR",
      "face.chemin": "El Camino ▸",
      "face.verboLbl": "Aurelius:",
      "face.vBreve": "breve", "face.vNormal": "normal", "face.vDet": "detallado",
      "face.localAI": "IA local · tu nodo",
      "face.techDetail": "detalle técnico",
      "face.configWarn": "⚠ apunta Aurelius a tu modelo: copia config.example.json → config.json",
      "id.ask": "¿Quién eres, soberano?",
      "id.placeholder": "Tu nombre…",
      "id.enter": "Entrar",
      "id.change": "cambiar",
      "id.greet": "Soberano: ",
      "path.title": "El Camino del Soberano",
      "path.back": "← Aurelius",
      "path.greet": "Hola, ", "wake.greet": "Bienvenido, {name}. Tu Tótem despertó — ahora te veo.",
      "path.serverDown.title": "El servidor no responde",
      "path.serverDown.body": "No alcanzo el estado (8050). ¿Está vivo el servicio de Aurelius?",
      "step.M0": "El Tótem", "step.M1": "El Fuego", "step.M2": "El Agua",
      "step.M3": "El Refugio", "step.M4": "La Señal", "step.M5": "El Pacto",
      "m0.title": "M0 · El Tótem",
      "m0.obj": "Crea tu compañero: la cara que hiciste tú. Efecto IKEA — es TU nodo.",
      "m0.step1": "Genera un avatar con una IA de imágenes gratis (Leonardo.ai, Bing) usando este prompt cebado Solar-punk:",
      "m0.prompt": "Retrato avatar, solar-punk, busto de un emperador-filósofo sereno, mármol claro veteado de cobre y circuitos cálidos, ojos de luz ámbar, fondo orgánico y luminoso, pixel-art suave, esperanzado, sin texto.",
      "m0.step2": "Descarga la imagen y súbela aquí abajo con tu nombre. Se sella por hash y se vuelve tu Tótem.",
      "m0.nom": "Tu nombre, soberano…",
      "m0.btn": "Forjar el Tótem",
      "m0.errName": "Dime tu nombre primero.",
      "m0.errFile": "Sube la imagen de tu Tótem.",
      "m0.sealing": "Sellando tu Tótem…",
      "m0.sealed": "✓ Tótem sellado (SHA-256 {sha}…). Bienvenido, {name}.",
      "m1.title": "M1 · El Fuego",
      "m1.obj": "Enciende el Fuego del Silicio: corre un modelo en TU máquina, sin la nube.",
      "m1.step1": "Desconecta la red (apaga el wifi o el cable) — nada debe salir del nodo.",
      "m1.step2": "Pídele al modelo LOCAL algo útil y seguro: un plan, una receta, una traducción. Guarda su respuesta:",
      "m1.cmd1": "correr el modelo offline y guardar la respuesta",
      "m1.step3": "Firma el resultado con tu mano (integridad SHA-256):",
      "m1.cmd2": "firmar (IronClaw: lo ejecutas tú)",
      "m1.paste": "Pega abajo el SHA-256 que imprimió el firmador para sellar M1.",
      "m1.sha": "SHA-256 (64 hex)…",
      "m1.btn": "Sellar M1",
      "m2.title": "M2 · El Agua",
      "m2.obj": "La memoria local (RAG): guarda tu primer conocimiento curado, en el nodo — nunca sale.",
      "m2.step1": "Crea tu grimorio y pega texto de una fuente FÍSICA tuya (un libro, una nota). Cúralo: título, fuente, por qué importa.",
      "m2.cmd1": "crear el grimorio",
      "m2.step2": "Ingiérelo en tu memoria vectorial LOCAL (offline, sin modelo, sin red):",
      "m2.cmd2": "ingerir (lo ejecutas tú)",
      "m2.step3": "Compruébalo: recupera algo del vector local con una pregunta tuya:",
      "m2.cmd3": "buscar en tu memoria local",
      "m2.step4": "Firma el manifiesto con tu mano:",
      "m2.cmd4": "firmar el manifiesto",
      "m2.paste": "Pega abajo el SHA-256 del manifiesto para sellar M2.",
      "m2.btn": "Sellar M2",
      "seal.badSha": "Eso no es un SHA-256 (64 hex). Fírmalo en tu terminal primero.",
      "seal.sealing": "Sellando…",
      "seal.ok": "✓ {code} sellado. El Camino continúa.",
      "final.title": "El Camino continúa…",
      "final.body": "Has recorrido M0→M2: el Tótem, el Fuego y el Agua. M3 (el Refugio) y más allá son horizonte — el andamio se retira a medida que subes. Aurelius te espera para lo que sigue.",
      "copy": "COPIAR", "copyOk": "OK", "copyManual": "⌘/Ctrl+C",
    },
    fr: {
      "face.sub": "le Précepteur · IronClaw",
      "face.vacio": "Salue-le pour éveiller le Précepteur.",
      "face.campo": "Parle avec Aurelius…",
      "face.hablar": "PARLER",
      "face.chemin": "Le Chemin ▸",
      "face.verboLbl": "Aurelius :",
      "face.vBreve": "bref", "face.vNormal": "normal", "face.vDet": "détaillé",
      "face.localAI": "IA locale · ton nœud",
      "face.techDetail": "détail technique",
      "face.configWarn": "⚠ pointe Aurelius vers ton modèle : copie config.example.json → config.json",
      "id.ask": "Qui es-tu, souverain ?",
      "id.placeholder": "Ton nom…",
      "id.enter": "Entrer",
      "id.change": "changer",
      "id.greet": "Souverain : ",
      "path.title": "Le Chemin du Souverain",
      "path.back": "← Aurelius",
      "path.greet": "Salut, ", "wake.greet": "Bienvenue, {name}. Ton Totem s'est éveillé — je te vois.",
      "path.serverDown.title": "Le serveur ne répond pas",
      "path.serverDown.body": "Je n'atteins pas l'état (8050). Le service d'Aurelius est-il vivant ?",
      "step.M0": "Le Totem", "step.M1": "Le Feu", "step.M2": "L'Eau",
      "step.M3": "Le Refuge", "step.M4": "Le Signal", "step.M5": "Le Pacte",
      "m0.title": "M0 · Le Totem",
      "m0.obj": "Crée ton compagnon : le visage que tu as fait. Effet IKEA — c'est TON nœud.",
      "m0.step1": "Génère un avatar avec une IA d'images gratuite (Leonardo.ai, Bing) avec ce prompt amorce Solar-punk :",
      "m0.prompt": "Portrait avatar, solar-punk, buste d'un empereur-philosophe serein, marbre clair veiné de cuivre et de circuits chauds, yeux de lumière ambrée, fond organique et lumineux, pixel-art doux, plein d'espoir, sans texte.",
      "m0.step2": "Télécharge l'image et dépose-la ci-dessous avec ton nom. Elle est scellée par hash et devient ton Totem.",
      "m0.nom": "Ton nom, souverain…",
      "m0.btn": "Forger le Totem",
      "m0.errName": "Dis-moi ton nom d'abord.",
      "m0.errFile": "Dépose l'image de ton Totem.",
      "m0.sealing": "Scellement de ton Totem…",
      "m0.sealed": "✓ Totem scellé (SHA-256 {sha}…). Bienvenue, {name}.",
      "m1.title": "M1 · Le Feu",
      "m1.obj": "Allume le Feu du Silicium : fais tourner un modèle sur TA machine, hors du nuage.",
      "m1.step1": "Déconnecte le réseau (wifi ou câble coupé) — rien ne sort du nœud.",
      "m1.step2": "Demande au modèle LOCAL quelque chose d'utile et sûr : un plan, une recette, une traduction. Garde sa réponse :",
      "m1.cmd1": "lancer le modèle hors ligne et garder la réponse",
      "m1.step3": "Signe le résultat de ta main (intégrité SHA-256) :",
      "m1.cmd2": "signer (IronClaw : c'est toi qui l'exécutes)",
      "m1.paste": "Colle ci-dessous le SHA-256 que le signeur a imprimé pour sceller M1.",
      "m1.sha": "SHA-256 (64 hex)…",
      "m1.btn": "Sceller M1",
      "m2.title": "M2 · L'Eau",
      "m2.obj": "La mémoire locale (RAG) : garde ton premier savoir curé, dans le nœud — il ne sort jamais.",
      "m2.step1": "Crée ton grimoire et colle le texte d'une source PHYSIQUE à toi (un livre, une note). Cure-le : titre, source, pourquoi ça compte.",
      "m2.cmd1": "créer le grimoire",
      "m2.step2": "Ingère-le dans ta mémoire vectorielle LOCALE (hors ligne, sans modèle, sans réseau) :",
      "m2.cmd2": "ingérer (c'est toi qui l'exécutes)",
      "m2.step3": "Vérifie : récupère quelque chose du vecteur local avec une question à toi :",
      "m2.cmd3": "chercher dans ta mémoire locale",
      "m2.step4": "Signe le manifeste de ta main :",
      "m2.cmd4": "signer le manifeste",
      "m2.paste": "Colle ci-dessous le SHA-256 du manifeste pour sceller M2.",
      "m2.btn": "Sceller M2",
      "seal.badSha": "Ce n'est pas un SHA-256 (64 hex). Signe-le dans ton terminal d'abord.",
      "seal.sealing": "Scellement…",
      "seal.ok": "✓ {code} scellé. Le Chemin continue.",
      "final.title": "Le Chemin continue…",
      "final.body": "Tu as parcouru M0→M2 : le Totem, le Feu et l'Eau. M3 (le Refuge) et au-delà sont l'horizon — l'échafaudage se retire à mesure que tu montes. Aurelius t'attend pour la suite.",
      "copy": "COPIER", "copyOk": "OK", "copyManual": "⌘/Ctrl+C",
    },
    // ── pt/de/el/ru: SIN revisar humano (verified:false). Se traducen las claves
    //    cortas de UI; la prosa técnica larga cae a INGLÉS (mejor que doctrina mal
    //    traducida). David revisará y completará las que hable. ──────────────────
    pt: {
      "face.hablar": "FALAR", "face.chemin": "O Caminho ▸", "face.campo": "Fala com Aurelius…",
      "face.vBreve": "breve", "face.vNormal": "normal", "face.vDet": "detalhado",
      "face.localAI": "IA local · o teu nó", "face.vacio": "Cumprimenta-o para acordar o Precetor.",
      "id.ask": "Quem és, soberano?", "id.placeholder": "O teu nome…", "id.enter": "Entrar", "id.change": "mudar", "id.greet": "Soberano: ",
      "path.title": "O Caminho do Soberano", "path.back": "← Aurelius", "path.greet": "Olá, ",
      "step.M0": "O Totem", "step.M1": "O Fogo", "step.M2": "A Água",
      "step.M3": "O Refúgio", "step.M4": "O Sinal", "step.M5": "O Pacto",
      "m0.nom": "O teu nome, soberano…", "m0.btn": "Forjar o Totem",
      "m1.btn": "Selar M1", "m2.btn": "Selar M2", "copy": "COPIAR", "copyOk": "OK",
    },
    de: {
      "face.hablar": "SPRECHEN", "face.chemin": "Der Weg ▸", "face.campo": "Sprich mit Aurelius…",
      "face.vBreve": "kurz", "face.vNormal": "normal", "face.vDet": "ausführlich",
      "face.localAI": "Lokale KI · dein Knoten", "face.vacio": "Begrüße ihn, um den Präzeptor zu wecken.",
      "id.ask": "Wer bist du, Souverän?", "id.placeholder": "Dein Name…", "id.enter": "Los", "id.change": "ändern", "id.greet": "Souverän: ",
      "path.title": "Der Weg des Souveräns", "path.back": "← Aurelius", "path.greet": "Hallo, ",
      "step.M0": "Der Totem", "step.M1": "Das Feuer", "step.M2": "Das Wasser",
      "step.M3": "Die Zuflucht", "step.M4": "Das Signal", "step.M5": "Der Pakt",
      "m0.nom": "Dein Name, Souverän…", "m0.btn": "Den Totem schmieden",
      "m1.btn": "M1 besiegeln", "m2.btn": "M2 besiegeln", "copy": "KOPIEREN", "copyOk": "OK",
    },
    el: {
      "face.hablar": "ΜΙΛΑ", "face.chemin": "Ο Δρόμος ▸", "face.campo": "Μίλα με τον Αυρήλιο…",
      "face.vBreve": "σύντομο", "face.vNormal": "κανονικό", "face.vDet": "αναλυτικό",
      "face.localAI": "Τοπική ΤΝ · ο κόμβος σου", "face.vacio": "Χαιρέτησέ τον για να ξυπνήσει ο Παιδαγωγός.",
      "id.ask": "Ποιος είσαι, κυρίαρχε;", "id.placeholder": "Το όνομά σου…", "id.enter": "Είσοδος", "id.change": "αλλαγή", "id.greet": "Κυρίαρχος: ",
      "path.title": "Ο Δρόμος του Κυρίαρχου", "path.back": "← Aurelius", "path.greet": "Γεια, ",
      "step.M0": "Το Τοτέμ", "step.M1": "Η Φωτιά", "step.M2": "Το Νερό",
      "step.M3": "Το Καταφύγιο", "step.M4": "Το Σήμα", "step.M5": "Το Σύμφωνο",
      "m0.nom": "Το όνομά σου, κυρίαρχε…", "m0.btn": "Σφυρηλάτησε το Τοτέμ",
      "m1.btn": "Σφράγισε το M1", "m2.btn": "Σφράγισε το M2", "copy": "ΑΝΤΙΓΡΑΦΗ", "copyOk": "OK",
    },
    ru: {
      "face.hablar": "ГОВОРИТЬ", "face.chemin": "Путь ▸", "face.campo": "Говори с Аврелием…",
      "face.vBreve": "кратко", "face.vNormal": "обычно", "face.vDet": "подробно",
      "face.localAI": "Локальный ИИ · твой узел", "face.vacio": "Поприветствуй его, чтобы разбудить Наставника.",
      "id.ask": "Кто ты, государь?", "id.placeholder": "Твоё имя…", "id.enter": "Войти", "id.change": "сменить", "id.greet": "Государь: ",
      "path.title": "Путь Государя", "path.back": "← Aurelius", "path.greet": "Привет, ",
      "step.M0": "Тотем", "step.M1": "Огонь", "step.M2": "Вода",
      "step.M3": "Убежище", "step.M4": "Сигнал", "step.M5": "Пакт",
      "m0.nom": "Твоё имя, государь…", "m0.btn": "Выковать Тотем",
      "m1.btn": "Запечатать M1", "m2.btn": "Запечатать M2", "copy": "КОПИЯ", "copyOk": "OK",
    },
  };

  function normaliza(loc) { return LOCALES.indexOf(loc) >= 0 ? loc : "en"; }

  function leer() {
    // INGLÉS POR DEFECTO (canon del Soberano): base en; solo una elección
    // previa guardada la cambia. No autodetectamos el idioma del navegador —
    // el selector es la vía explícita.
    try {
      var g = localStorage.getItem(CLAVE);
      if (LOCALES.indexOf(g) >= 0) return g;
    } catch (e) { /* sin localStorage */ }
    return "en";
  }

  var actual = leer();

  function fijar(loc) {
    actual = normaliza(loc);
    try { localStorage.setItem(CLAVE, actual); } catch (e) { /* memoria */ }
    return actual;
  }

  // t(key, vars): traduce con fallback a INGLÉS (base) → nunca doctrina en un
  // idioma sin traducir; interpola {name}/{sha}/{code}.
  function t(key, vars) {
    var loc = D[actual] || {};
    var s = (key in loc) ? loc[key] : (key in D.en ? D.en[key] : key);
    if (vars) {
      for (var k in vars) {
        if (Object.prototype.hasOwnProperty.call(vars, k)) {
          s = s.split("{" + k + "}").join(String(vars[k]));
        }
      }
    }
    return s;
  }

  return {
    locales: LOCALES,
    nombre: NOMBRE,
    verified: VERIFIED,
    get locale() { return actual; },
    set: fijar,
    t: t,
    esVerificado: function () { return VERIFIED[actual] === true; },
  };
})();
