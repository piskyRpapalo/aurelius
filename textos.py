#!/usr/bin/env python3
"""Todo lo que el producto dice, en los dos idiomas que habla.

sistema: MVP · solo biblioteca estandar. Sin red, sin dependencias.

Un solo diccionario, dos columnas. La alternativa —un `if idioma == "es"`
en cada print— reparte el mismo texto por todo el fichero y garantiza que
manana una de las dos versiones se quede atras sin que nadie lo note. Aqui
una traduccion que falta es una clave que falta, y el caso 10 de
`test_idioma.py` la encuentra antes que la persona.

La pregunta del idioma es la unica que no vive en una columna: se hace antes
de saber en que idioma hablar, asi que se dice en los dos a la vez. Preguntar
"¿en que idioma?" en un idioma ya elegido por nosotros seria haber elegido.
"""
from __future__ import annotations

# El juego se narra en espanol: la base de nombres del lore se firmo en
# espanol el 2026-08-19, y un producto cuyo idioma por defecto no tiene ni un
# nombre de juego arranca mudo. El ingles sigue entero para la sesion -- las
# dos columnas de TEXTOS estan completas -- y los nombres clave del lore se
# mantienen bilingues como marca. Lo que cambia es por donde se empieza.
DEFECTO = "es"

# (clave, como se llama ese idioma en ese idioma). El nombre va en su propia
# lengua a proposito: quien busca "Español" no esta leyendo la palabra
# "Spanish".
IDIOMAS = (("en", "English"), ("es", "Español"))

PREGUNTA_IDIOMA = "Language · Idioma"
AYUDA_IDIOMA = "Type 1 or 2 · Escribe 1 o 2"
# El rechazo de la primera pregunta tambien es bilingue: la persona que se
# equivoca al elegir idioma todavia no ha elegido idioma.
RECHAZO_IDIOMA = ("{entrada!r} · type the number: 1 or 2"
                  " · escribe el número: 1 o 2")


TEXTOS = {
    "en": {
        # --- paso 1 · la declaracion
        "sabe_de_mi": "What I know about myself, without any memory at all:",
        "bullet_campos": "  - a memory has 4 fields: what, why, where, learned",
        "bullet_ausencia": "  - absence is written as {ausente}, never left blank",
        "bullet_vive": "  - my memory would live in: {ruta}",
        "bullet_frontera": "  - nothing leaves this machine unless you export it",
        "crear_pregunta": "Create my memory now?  (type the number: 1 or 2)",
        "crear_si": "Yes, create it",
        "crear_no": "No, not yet",
        "nada_creado": "\nNothing created. I keep no record of this session.",
        "creado": "\nCreated: {ruta}",

        # --- paso 0 · las dos preguntas que no son recuerdos
        "perfil_cabecera": "\n--- first, two questions that are not memories ",
        "perfil_intro": (
            "I keep two things apart: who you are and where I am (this part),\n"
            "and what you remember (everything after). Neither answer is\n"
            "required. Press enter and it stays as {ausente} — which is an\n"
            "answer too: it says nobody told me, instead of me pretending.\n"),
        "perfil_device": "Where am I?  (the machine I'm running on, in your words)  ",
        "perfil_name": "How should I call you?  ",
        "perfil_nota": ("({ausente} is not a blank cell: it is a question nobody\n"
                        " answered. Nothing is lost by leaving it that way.)"),

        # --- paso 2 · el recuerdo
        "recuerdo_cabecera": "\n--- now a memory, one field at a time ",
        "recuerdo_intro": (
            "A memory here is just something that happened to you and that you\n"
            "decided was worth keeping. It does not have to be important.\n"),
        "recuerdo_ejemplos": (
            "  e.g.  the printer finally worked after I changed one cable\n"
            "        I broke the database and got it back from a copy\n"
            "        someone explained DNS to me and this time I got it\n"),
        "recuerdo_que": "So — what happened?  ",

        # --- la charla · el turno con el cerebro
        "cerebro_afinado": "Brain: fine-tuned copy · {motivo}",
        "charla_cabecera": "\n--- talking ",
        "charla_sin_motor": (
            "There is no conversation engine in this copy, so I cannot talk\n"
            "yet. Everything else works: your memory is whole without me.\n"),
        "charla_sin_binario": (
            "The brain is on this machine, but there is nothing here to run it\n"
            "with. Install {motor} and I can talk. Everything else already\n"
            "works without it.\n"),
        "charla_sin_modelo": (
            "I can run a brain, but I cannot find one. It should be at\n"
            "  {ruta}\n"
            "If you downloaded it somewhere else, move it there — I do not go\n"
            "looking around your disk.\n"),
        "charla_donde": "You are at {peldano}. {prueba}",
        "charla_decision": (
            "The core is done. From here you choose: go straight to your own\n"
            "project, or take an optional stop. Both are the path.\n"),
        "charla_como_salir": "(empty line to leave; nothing is lost)",
        "charla_bloqueado": (
            "I stopped that: it had the shape of something that burns. The\n"
            "mark is in the record; what it said is not."),
        "charla_callado": "The engine gave nothing back. That is a fact, not an answer.",
        "charla_tarde": "It did not finish in time. {motivo}",
        "recuerdo_sin_que": ("Without a 'what' there is no memory. Nothing written,\n"
                             "and nothing wrong: come back when there is something."),
        "sin_motor": ("\nThis copy has no conversation engine installed. I can keep\n"
                      "and recall your notes, but I cannot talk yet. Everything\n"
                      "below works without it.\n"
                      "To switch talking on, install the engine listed in\n"
                      "README → Requirements.\n"),
        "recuerdo_opcionales": (
            "\nThe next three can stay empty. Enter leaves them as {ausente},\n"
            "and a memory with declared gaps is still a memory — it is more\n"
            "honest than one where I guessed the parts you did not tell me.\n"),
        "recuerdo_porque": "Why does it matter to you?  (enter = {ausente})  ",
        "recuerdo_donde": "Is there a file, a photo, a note that backs it?  (enter = {ausente})  ",
        "recuerdo_aprendido": "Did you learn anything you'd tell someone else?  (enter = for later)  ",
        "recuerdo_guardado": "\nSaved, exactly as you wrote it:",
        "recuerdo_vacio": "(empty, for later)",

        # --- el bucle
        "palabra_recuerdo": "memory",
        "palabra_recuerdos": "memories",
        "palabra_hueco": "declared gap",
        "palabra_huecos": "declared gaps",
        "bucle_recuento": "\n{n} {nombre_r}. Three is a good start — not a requirement.",
        "otro_pregunta": "Add another memory?  (type the number: 1 or 2)",
        "otro_si": "Yes, one more",
        "otro_no": "No, that's enough for today",

        # --- paso 5 · el enlace
        "enlace_pregunta": "\nAre two of these related?  (type the number: 1 or 2)",
        "enlace_si": "Yes, two of them are",
        "enlace_no": "No, they stand on their own",
        "enlace_desde": "from id:  ",
        "enlace_hasta": "to id:  ",
        "enlace_como": "in your own words, how?  (enter = {ausente})  ",
        "enlace_guardado": "Link saved.",

        # --- paso 6 · las vistas
        "vista_tabla": "\n=== TABLE ",
        "vista_arbol": "\n=== TREE ",
        "vista_recuento": "\n=== COUNT ",

        # --- paso 7 · el cierre honesto
        "cierre_cabecera": "\n--- honest closing ",
        "cierre_recuento": "I have {engrams} {nombre_r} and {huecos} {nombre_h}.",
        "cierre_viven": "They live in {ruta}. You can copy that file and take it with you.",
        "cierre_frontera": "Redaction at the border: ",
        "cierre_frontera_ok": "ready",
        "cierre_frontera_no": "NOT AVAILABLE — export is blocked",
        "cierre_pregunta": "\nWhich piece do you want to understand first?  ",
        "cierre_intencion_why": "the next thing I want to learn",
        "cierre_intencion": "Saved as an intention. It orients the next mission.",

        # --- paso 8 · el sello
        "sello_no_hay": ("Sealing today's state is not available: the manifest "
                         "module is not here."),
        "sello_no_hay_2": "Your memory is safe anyway. Nothing was lost.",
        "sello_intro": "Before you go: I can seal what your memory looks like right now.",
        "sello_intro_2": "A seal proves nothing changed, without saying what it says.",
        "sello_pregunta": "Seal today?  (type the number: 1 or 2)",
        "sello_si": "Yes, seal it",
        "sello_no": "Not now — I can do it any time",
        "sello_sellando": "Sealing.",
        "sello_no_sellado": "Not sealed. The memory keeps growing.",
        "sello_escrito": "Sealed: {destino}",
        "sello_copia": ("Keep a copy somewhere else: a seal next to what it "
                        "certifies is lost with it."),

        # --- cierre de mision
        "final": "\nMission M2 complete: ",
        "final_si": "yes",
        "final_no": "no — nothing was written",

        # --- la oferta de M3 · la Fuga del Museo
        "m3_intro": ("There is a second thing, and it is a game. Six rooms, "
                     "and a bust that wants out of a museum."),
        "m3_reanudar": ("You left a museum halfway through. It is still there, "
                        "exactly where you stopped."),
        "m3_pregunta": "Go into the Escape from the Museum?",
        "m3_si": "yes, let's go",
        "m3_no": "not today",
        "m3_luego": ("It keeps. It is a file, not an appointment: nothing "
                     "there expires."),

        # --- gramatica de las preguntas numeradas
        "rechazo": "{entrada!r} is not one of them. Type the number: {numeros}.",
        "o": "or",

        # --- estados de la memoria (los dice memory.py, se guardan aqui)
        "estado_sin_esquema": ("I have no memory yet. Nothing has been created on "
                               "this machine. I can create it now, if you say so."),
        # La misma ausencia, dicha desde una bandera que NO va a preguntar. La
        # frase de arriba promete crearla, y la sesion cumple esa promesa; una
        # bandera que la repite y se va deja a la persona esperando una
        # pregunta que no llega.
        "sin_memoria_aun": ("There is no memory on this machine yet, so there is\n"
                            "nothing to do here. Run this and we make it together:\n"
                            "  python3 aurelius.py\n"),

        # --- el ritual · primer contacto. Todo lo que se ve, aquí.
        "ritual_saludo": "\nFirst, three things about you. None is required.",
        "ritual_nombre": "How should I call you?  (Enter for {ausente})  ",
        "ritual_ritmo": "Pace of the answers (0-9, Enter for {ausente})  ",
        "ritual_hecho": "Done. What you told me is in your memory, not in a file of mine.",
        "estado_vacia": ("My memory exists and it is empty. 0 memories. "
                         "Nothing is missing: nothing has been written yet."),
        "estado_con_datos": "{n} memories, {l} links",
        "estado_archivados": ", {a} archived",
        "estado_cola": ". Everything shown comes from what you wrote.",
    },

    "es": {
        # --- paso 1 · la declaracion
        "sabe_de_mi": "Lo que sé de mí mismo, sin memoria ninguna:",
        "bullet_campos": "  - un recuerdo tiene 4 campos: qué, por qué, dónde, aprendido",
        "bullet_ausencia": "  - la ausencia se escribe {ausente}, nunca se deja en blanco",
        "bullet_vive": "  - mi memoria viviría en: {ruta}",
        "bullet_frontera": "  - nada sale de esta máquina si tú no lo exportas",
        "crear_pregunta": "¿Creo mi memoria ahora?  (escribe el número: 1 o 2)",
        "crear_si": "Sí, créala",
        "crear_no": "No, todavía no",
        "nada_creado": "\nNo he creado nada. No guardo ningún rastro de esta sesión.",
        "creado": "\nCreada: {ruta}",

        # --- paso 0 · las dos preguntas que no son recuerdos
        "perfil_cabecera": "\n--- primero, dos preguntas que no son recuerdos ",
        "perfil_intro": (
            "Separo dos cosas: quién eres y dónde estoy (esta parte), y lo que\n"
            "tú recuerdas (todo lo demás). Ninguna respuesta es obligatoria.\n"
            "Pulsa enter y se queda en {ausente} — que también es una respuesta:\n"
            "dice que nadie me lo contó, en vez de que yo me lo invente.\n"),
        "perfil_device": "¿Dónde estoy?  (la máquina en la que corro, con tus palabras)  ",
        "perfil_name": "¿Cómo te llamo?  ",
        "perfil_nota": ("({ausente} no es una celda vacía: es una pregunta que nadie\n"
                        " contestó. No se pierde nada por dejarla así.)"),

        # --- paso 2 · el recuerdo
        "recuerdo_cabecera": "\n--- ahora un recuerdo, campo a campo ",
        "recuerdo_intro": (
            "Un recuerdo aquí es algo que te pasó y que decidiste que valía la\n"
            "pena guardar. No hace falta que sea importante.\n"),
        "recuerdo_ejemplos": (
            "  p.ej.  la impresora por fin funcionó al cambiar un cable\n"
            "         rompí la base de datos y la recuperé de una copia\n"
            "         alguien me explicó el DNS y esta vez lo entendí\n"),
        "recuerdo_que": "Entonces — ¿qué pasó?  ",

        # --- la charla · el turno con el cerebro
        "cerebro_afinado": "Cerebro: copia afinada · {motivo}",
        "charla_cabecera": "\n--- hablando ",
        "charla_sin_motor": (
            "Esta copia no tiene motor de conversación, así que todavía no\n"
            "puedo charlar. Lo demás funciona: tu memoria está entera sin mí.\n"),
        "charla_sin_binario": (
            "El cerebro está en esta máquina, pero no hay con qué encenderlo.\n"
            "Instala {motor} y podré hablar. Lo demás ya funciona sin él.\n"),
        "charla_sin_modelo": (
            "Puedo encender un cerebro, pero no encuentro ninguno. Tendría que\n"
            "estar en\n"
            "  {ruta}\n"
            "Si lo bajaste a otro sitio, muévelo ahí — yo no voy a rebuscar por\n"
            "tu disco.\n"),
        "charla_donde": "Estás en {peldano}. {prueba}",
        "charla_decision": (
            "El núcleo está hecho. A partir de aquí eliges: ir directo a tu\n"
            "proyecto, o hacer una parada opcional. Las dos son el camino.\n"),
        "charla_como_salir": "(línea vacía para salir; no se pierde nada)",
        "charla_bloqueado": (
            "Eso lo he parado: tenía forma de algo que quema. La marca queda\n"
            "en el registro; lo que decía, no."),
        "charla_callado": "El motor no devolvió nada. Eso es un hecho, no una respuesta.",
        "charla_tarde": "No le dio tiempo a terminar. {motivo}",
        "recuerdo_sin_que": ("Sin un 'qué' no hay recuerdo. No he escrito nada,\n"
                             "y no pasa nada: vuelve cuando lo haya."),
        "sin_motor": ("\nEsta copia no tiene motor de conversación instalado. Puedo\n"
                      "guardar y recordar tus notas, pero todavía no puedo charlar.\n"
                      "Todo lo de abajo funciona sin él.\n"
                      "Para activar la charla, instala el motor que indica\n"
                      "README → Requirements.\n"),
        "recuerdo_opcionales": (
            "\nLos tres siguientes pueden quedarse vacíos. Enter los deja en\n"
            "{ausente}, y un recuerdo con huecos declarados sigue siendo un\n"
            "recuerdo — es más honesto que uno donde yo adivine lo que no me\n"
            "contaste.\n"),
        "recuerdo_porque": "¿Por qué te importa?  (enter = {ausente})  ",
        "recuerdo_donde": "¿Hay un fichero, una foto, una nota que lo respalde?  (enter = {ausente})  ",
        "recuerdo_aprendido": "¿Aprendiste algo que le contarías a otra persona?  (enter = para luego)  ",
        "recuerdo_guardado": "\nGuardado, exactamente como lo escribiste:",
        "recuerdo_vacio": "(vacío, para luego)",

        # --- el bucle
        "palabra_recuerdo": "recuerdo",
        "palabra_recuerdos": "recuerdos",
        "palabra_hueco": "hueco declarado",
        "palabra_huecos": "huecos declarados",
        "bucle_recuento": "\n{n} {nombre_r}. Tres es un buen comienzo — no una obligación.",
        "otro_pregunta": "¿Añadimos otro recuerdo?  (escribe el número: 1 o 2)",
        "otro_si": "Sí, uno más",
        "otro_no": "No, por hoy está bien",

        # --- paso 5 · el enlace
        "enlace_pregunta": "\n¿Hay dos de estos que estén relacionados?  (escribe el número: 1 o 2)",
        "enlace_si": "Sí, dos de ellos lo están",
        "enlace_no": "No, cada uno va por su lado",
        "enlace_desde": "del id:  ",
        "enlace_hasta": "al id:  ",
        "enlace_como": "con tus palabras, ¿cómo?  (enter = {ausente})  ",
        "enlace_guardado": "Enlace guardado.",

        # --- paso 6 · las vistas
        "vista_tabla": "\n=== TABLA ",
        "vista_arbol": "\n=== ÁRBOL ",
        "vista_recuento": "\n=== RECUENTO ",

        # --- paso 7 · el cierre honesto
        "cierre_cabecera": "\n--- cierre honesto ",
        "cierre_recuento": "Tengo {engrams} {nombre_r} y {huecos} {nombre_h}.",
        "cierre_viven": "Viven en {ruta}. Puedes copiar ese fichero y llevártelo.",
        "cierre_frontera": "Redacción en la frontera: ",
        "cierre_frontera_ok": "lista",
        "cierre_frontera_no": "NO DISPONIBLE — la exportación está bloqueada",
        "cierre_pregunta": "\n¿Qué pieza quieres entender primero?  ",
        "cierre_intencion_why": "lo siguiente que quiero aprender",
        "cierre_intencion": "Guardado como intención. Orienta la próxima misión.",

        # --- paso 8 · el sello
        "sello_no_hay": ("Sellar el estado de hoy no está disponible: el módulo "
                         "del manifiesto no está aquí."),
        "sello_no_hay_2": "Tu memoria está a salvo igualmente. No se ha perdido nada.",
        "sello_intro": "Antes de que te vayas: puedo sellar cómo está tu memoria ahora mismo.",
        "sello_intro_2": "Un sello demuestra que nada cambió, sin decir lo que dice.",
        "sello_pregunta": "¿Sellamos lo de hoy?  (escribe el número: 1 o 2)",
        "sello_si": "Sí, séllalo",
        "sello_no": "Ahora no — puedo hacerlo cuando quiera",
        "sello_sellando": "Sellando.",
        "sello_no_sellado": "Sin sellar. La memoria sigue creciendo.",
        "sello_escrito": "Sellado: {destino}",
        "sello_copia": ("Guarda una copia en otro sitio: un sello al lado de lo "
                        "que certifica se pierde con ello."),

        # --- cierre de mision
        "final": "\nMisión M2 completa: ",
        "final_si": "sí",
        "final_no": "no — no se escribió nada",

        # --- la oferta de M3 · la Fuga del Museo
        "m3_intro": ("Hay una segunda cosa, y es un juego. Seis salas, y un "
                     "busto que quiere salir de un museo."),
        "m3_reanudar": ("Dejaste un museo a medias. Sigue ahí, exactamente "
                        "donde lo dejaste."),
        "m3_pregunta": "¿Entramos en la Fuga del Museo?",
        "m3_si": "sí, vamos",
        "m3_no": "hoy no",
        "m3_luego": ("Se guarda. Es un fichero, no una cita: nada de eso "
                     "caduca."),

        # --- gramatica de las preguntas numeradas
        "rechazo": "{entrada!r} no es ninguna de ellas. Escribe el número: {numeros}.",
        "o": "o",

        # --- estados de la memoria
        "estado_sin_esquema": ("Todavía no tengo memoria. No se ha creado nada en "
                               "esta máquina. Puedo crearla ahora, si tú lo dices."),
        "sin_memoria_aun": ("Todavía no hay memoria en esta máquina, así que aquí\n"
                            "no hay nada que hacer. Ejecuta esto y la creamos juntos:\n"
                            "  python3 aurelius.py\n"),

        # --- el ritual · primer contacto. Todo lo que se ve, aquí.
        "ritual_saludo": "\nPrimero, tres cosas sobre ti. Ninguna es obligatoria.",
        "ritual_nombre": "¿Cómo te llamo?  (Enter para {ausente})  ",
        "ritual_ritmo": "Ritmo de las respuestas (0-9, Enter para {ausente})  ",
        "ritual_hecho": "Hecho. Lo que me has dicho está en tu memoria, no en un fichero mío.",
        "estado_vacia": ("Mi memoria existe y está vacía. 0 recuerdos. "
                         "No falta nada: no se ha escrito nada todavía."),
        "estado_con_datos": "{n} recuerdos, {l} enlaces",
        "estado_archivados": ", {a} archivados",
        "estado_cola": ". Todo lo que se ve viene de lo que tú escribiste.",
    },
}


def normalizar(idioma):
    """Un idioma que no conocemos no rompe la sesion: cae al de por defecto."""
    return idioma if idioma in TEXTOS else DEFECTO


def texto(idioma, clave, **kw):
    """La cadena, ya formateada. Una clave que no existe se dice, no se calla.

    Preferimos reventar aqui, en la primera sesion que toque esa rama, a
    imprimir una cadena vacia que nadie relaciona con una traduccion olvidada.
    """
    tabla = TEXTOS[normalizar(idioma)]
    if clave not in tabla:
        raise KeyError(f"texto sin traducir: {clave!r} en {idioma!r}")
    return tabla[clave].format(**kw) if kw else tabla[clave]


def plural(idioma, n, singular, plural_):
    """La palabra que le toca a ese numero. '1 recuerdos' no lo dice nadie.

    Es una regla, no dos frases: duplicar la oracion entera para cambiar una
    letra garantiza que manana solo se corrija una de las dos copias.
    """
    return texto(idioma, singular if n == 1 else plural_)


def lista_numeros(n, idioma):
    """'1 or 2' · '1, 2 o 3'. El rechazo tiene que decir que numeros valen."""
    numeros = [str(i) for i in range(1, n + 1)]
    if n == 1:
        return numeros[0]
    return ", ".join(numeros[:-1]) + f" {texto(idioma, 'o')} " + numeros[-1]
