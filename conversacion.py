#!/usr/bin/env python3
"""conversacion.py · el turno. Donde el producto por fin habla.

sistema: MVP · solo biblioteca estándar. Sin red, sin dependencias.

QUÉ ES UN TURNO
---------------
Una función: entra lo que dijo la persona, sale lo que se le dice. Por el
camino se mira en qué peldaño está, se decide qué toca, y —si hay cerebro— se
le pregunta al modelo. Nada más, y en ese orden.

EL MOTOR SE INYECTA, NO SE IMPORTA
----------------------------------
`turno()` recibe `motor`: una función `texto -> texto`. El adaptador real
(`motor_llama`) lanza el binario de completacion como proceso hijo; una
prueba puede pasar un
motor sintético de tres líneas. Es el mismo criterio que el `redactor` de la
frontera, y resuelve algo que llevaba tiempo declarado como pendiente: probar
el núcleo de la conversación **sin modelo**. Un gerente sintético que cumple el
contrato es la única forma de mantener rojo-antes-verde cuando la pieza es un
modelo externo.

SIN CEREBRO EL BUCLE SIGUE VIVO
-------------------------------
Sin motor no hay charla, y se dice. Lo que no se hace es fabricar una respuesta
plausible: eso es el fallo que ninguna prueba automática detecta y todas las
personas notan. La memoria funciona entera sin modelo, y el turno lo declara.

LO QUE EL MODELO CONTESTA CRUZA LA FRONTERA
-------------------------------------------
Toda respuesta pasa por `memory.cruzar_frontera` con el fusible como
preparación. Si el fusible salta, queda la cicatriz y no pasa nada. Si no,
queda la huella. Un modelo que habla sin dejar constancia es un modelo del que
no se puede auditar nada.
"""
from __future__ import annotations

import os
import shutil
import subprocess

import memory as M
import fusible
import narrador as N
import textos as TX

# POR QUÉ `llama-completion` Y NO `llama-cli`.
# Medido el 2026-08-19, contra el mismo modelo y el mismo prompt:
#
#   llama-cli         · stdout 1075 B — cargador, arte ASCII, cabecera del
#                       binario y la lista de comandos. stderr: 0.
#   llama-completion  · stdout 46 B — la respuesta y nada más.
#                       stderr: 2353 B, todo el ruido.
#
# `llama-cli` es una interfaz de chat y escribe su interfaz por la salida
# estándar. Lo descubrió el primer turno real: la fila del registro guardaba
# 1489 caracteres de los que casi todos eran el banner. Las quince pruebas
# unitarias no podían verlo — un motor sintético devuelve lo que se le dice que
# devuelva —, y solo aparece cuando habla el binario de verdad.
#
# La alternativa era recortar el banner con expresiones regulares. Se descartó:
# sería el primer trozo de este árbol que depende de la FORMA de la salida de un
# programa ajeno, y esa dependencia se rompe sola en la siguiente versión sin
# que nadie se entere. Cambiar de binario es una constante; parsear una interfaz
# es una deuda.
#
# Las banderas, cada una con su cicatriz:
#   · `-c` explícito SIEMPRE. El modelo trae 262144 de contexto y con el
#     defecto la máquina se arrodilla reservando caché (2026-08-18).
#   · `--no-display-prompt`, o la respuesta llega con el prompt pegado delante.
#   · `--no-warmup`, porque el arranque en frío ya es bastante lento.
#   · `-st` NO se pasa: era la bandera que `llama-cli` necesitaba para no
#     entrar en modo interactivo y reimprimir el prompt en bucle — 427 millones
#     de líneas y 1,4 GB de basura en cinco minutos. `llama-completion` no tiene
#     ese modo, así que la bandera sobra. La cicatriz se conserva escrita
#     porque el binario puede volver a cambiar.
# Los dos marcadores que el binario añade al final. Medidos el 2026-08-19 sobre
# la build b10488: con `-st` cierra con `[end of text]`; sin ella espera más
# entrada y cierra con `> EOF by user` al encontrarse el flujo cerrado.
#
# Recortar esto ES depender de la forma de una salida ajena, y conviene decirlo
# en vez de disimularlo. La diferencia con parsear el banner entero es de
# grado y de riesgo: son dos tokens fijos y con nombre, el recorte vive en una
# función con su propio rojo, y si mañana cambian, ese rojo se pone rojo aquí
# en vez de aparecer como basura en el registro de una persona.
MARCADORES_FINAL = ("[end of text]", "> EOF by user")

CONTEXTO = 4096
TOPE_TOKENS = int(os.environ.get("AURELIUS_TOPE_TOKENS", "320"))
MOTOR = "llama-completion"

# Cuánto se espera a que el modelo conteste. Medido el 2026-08-19 en dos
# máquinas, con el mismo modelo de 4B:
#
#   Beelink (Ryzen 7, x86_64) · 14,5 tok/s de generación
#   Doogee S110 (aarch64)     ·  1,81 tok/s de generación · 3,38 de prompt
#
# Ocho veces más lento. Con TOPE_TOKENS=320 eso es un turno de más de seis
# minutos en el teléfono, y el defecto de 180 s cortaba SIEMPRE — el producto
# decía "el motor no devolvió nada", que era cierto y no era la verdad: el
# motor estaba trabajando.
#
# Se sube el defecto y se deja gobernar por el entorno. Lo que NO se hace es
# esconder el corte: un turno que se pasó del tiempo se dice distinto de un
# motor que falló, porque son cosas distintas y se arreglan distinto.
ESPERA = int(os.environ.get("AURELIUS_ESPERA", "420"))

FASES = ("nucleo", "decision", "side_quest", "proyecto")


def motor_disponible():
    """La ruta del motor, o None. Nunca el PATH implícito de un servicio."""
    declarado = os.environ.get("AURELIUS_MOTOR", "").strip()
    if declarado:
        return declarado if os.path.isfile(declarado) else None
    return shutil.which(MOTOR)


def motor_llama(modelo, hilos=8, tiempo=None):
    """Devuelve un motor real: una función `prompt -> texto`.

    Proceso hijo por entrada y salida estándar. Ni un socket: un puerto local
    es indistinguible de un túnel, y esa es la razón por la que el gerente no
    puede ser un servidor (D68).
    """
    binario = motor_disponible()
    if not (binario and modelo and os.path.isfile(modelo)):
        return None
    tiempo = ESPERA if tiempo is None else tiempo

    def hablar(prompt):
        orden = [binario, "-m", modelo, "-c", str(CONTEXTO),
                 "-n", str(TOPE_TOKENS), "-st", "--no-warmup",
                 "--no-display-prompt", "-t", str(hilos), "-p", prompt]
        try:
            r = subprocess.run(orden, capture_output=True, text=True,
                               timeout=tiempo, stdin=subprocess.DEVNULL)
        except subprocess.TimeoutExpired:
            # No es lo mismo que fallar: estaba trabajando y no le dio tiempo.
            raise SeAgotoElTiempo(
                f"el modelo tardó más de {tiempo} segundos. En esta máquina "
                f"puede ser lo normal: prueba con menos tokens "
                f"(AURELIUS_TOPE_TOKENS) o más espera (AURELIUS_ESPERA).")
        except Exception:
            return None
        if r.returncode != 0:
            return None
        return limpiar(r.stdout, prompt)

    return hablar


# Las tres ausencias posibles. Se separan porque "no hay motor" a secas manda a
# la persona a buscar lo que ya tiene: quien descargo el cerebro y no instalo el
# binario, y quien instalo el binario y no bajo el cerebro, necesitan
# instrucciones distintas. Un mensaje que sirve para los dos casos no sirve para
# ninguno.
SIN_NADA = "sin_nada"
SIN_BINARIO = "sin_binario"
SIN_MODELO = "sin_modelo"
LISTO = "listo"


def diagnostico(modelo):
    """(motor, motivo). El motivo dice QUE falta, no que algo falta.

    `modelo` es la ruta donde el producto espera el cerebro. Se comprueba en el
    DISCO: una bandera en un fichero de estado dice lo que era verdad cuando se
    escribio.
    """
    binario = motor_disponible()
    hay_modelo = bool(modelo) and os.path.isfile(modelo)
    if binario and hay_modelo:
        return motor_llama(modelo), LISTO
    if not binario and not hay_modelo:
        return None, SIN_NADA
    return (None, SIN_MODELO) if binario else (None, SIN_BINARIO)


def limpiar(crudo, prompt=""):
    """Lo que dijo el modelo, sin lo que dijimos nosotros ni lo que dice el binario.

    Tres cosas se van, en este orden:

    1. El eco del prompt, si la bandera `--no-display-prompt` faltase.
    2. Los marcadores de cierre del binario.
    3. Los espacios de los bordes.

    Lo que queda se registra tal cual. El registro promete poder enseñarse, y
    un registro lleno de marcadores de una herramienta no se enseña: se explica.
    """
    dicho = crudo or ""
    if prompt and dicho.startswith(prompt):
        dicho = dicho[len(prompt):]
    dicho = dicho.strip()
    # En bucle: un cierre puede traer los dos, uno detrás de otro.
    cambiado = True
    while cambiado:
        cambiado = False
        for marca in MARCADORES_FINAL:
            if dicho.endswith(marca):
                dicho = dicho[:-len(marca)].rstrip()
                cambiado = True
    return dicho


# --- dónde está la persona -------------------------------------------------

def fase(camino, perfil=None):
    """En qué punto de la campaña estamos, según lo que el código MIDE.

    No hay adivinanza: el núcleo se deriva de `progreso_camino`, y la única
    pieza que no se puede medir —haber elegido ir al proyecto— se lee del
    perfil, donde la persona la dejó escrita.
    """
    perfil = perfil or {}
    if perfil.get("modo") == "proyecto":
        return "proyecto"
    if not camino.get("punto_decision"):
        return "nucleo"
    hechas = [p for p in camino["opcionales"]
              if camino["estado"].get(p) == "hecho"]
    return "side_quest" if hechas else "decision"


def elegir_modo(c, modo):
    """La persona decide si sigue el Camino o abre su proyecto. Se guarda."""
    if modo not in ("camino", "proyecto"):
        raise ValueError("el modo es 'camino' o 'proyecto'")
    M.escribir_perfil(c, "modo", modo)
    return modo


# --- el prompt del sistema -------------------------------------------------

def _arquetipo(idioma):
    """El carácter, entero y al principio. Un idioma por sesión (ARQUETIPO §5)."""
    ruta = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                        "ARQUETIPO.md")
    if not os.path.isfile(ruta):
        return ""
    with open(ruta, encoding="utf-8") as fh:
        texto = fh.read()
    # Los dos bloques del arquetipo van entre vallas de código; se toma el que
    # toca y nunca los dos: dos caracteres a la vez producen uno confuso.
    bloques = [b for b in texto.split("```") if "Aurelius" in b]
    if not bloques:
        return ""
    if idioma == "es":
        for b in bloques:
            if "Eres Aurelius" in b:
                return b.strip()
    for b in bloques:
        if "You are Aurelius" in b:
            return b.strip()
    return bloques[0].strip()


GUIA = {
    "es": {
        "nucleo": "Estás acompañando el núcleo. Pregunta una cosa cada vez.",
        "decision": ("El núcleo está hecho. Recuérdale que puede ir a su "
                     "proyecto o hacer una parada opcional, y que las dos son "
                     "el camino. No elijas por él."),
        "side_quest": "Está en una parada opcional. Acompaña, no adelantes.",
        "proyecto": ("Está construyendo lo suyo. NUNCA propongas el tema ni el "
                     "dominio: no es tuyo. Narra lo que acaba de pasar y "
                     "devuélvele el turno."),
    },
    "en": {
        "nucleo": "You are walking the core with them. One question at a time.",
        "decision": ("The core is done. Remind them they can go to their own "
                     "project or take an optional stop, and that both are the "
                     "path. Do not choose for them."),
        "side_quest": "They are on an optional stop. Keep pace; do not run ahead.",
        "proyecto": ("They are building their own thing. NEVER propose the "
                     "subject or the domain: it is not yours. Say what just "
                     "happened and hand the turn back."),
    },
}


def prompt_sistema(fase_actual, idioma=None):
    """Carácter + vocabulario + qué toca ahora. En ese orden y entero.

    El glosario lleva los nombres del juego y lo que significan, **jamás la
    equivalencia con el nombre interno**: enseñarle a un modelo que
    `cruzar_frontera` se llama la Cicatriz es enseñarle la palabra que no debe
    decir. Ver `narrador.glosario`.
    """
    idioma = TX.normalizar(idioma)
    partes = [_arquetipo(idioma)]
    glosario = N.glosario(idioma)
    if glosario:
        partes.append(glosario)
    partes.append(GUIA.get(idioma, GUIA["es"]).get(fase_actual, ""))
    return "\n\n".join(p for p in partes if p).strip()


# --- el turno --------------------------------------------------------------

class SinCerebro(Exception):
    """No hay motor. No es un fallo: es una ausencia, y se declara."""


class SeAgotoElTiempo(Exception):
    """El modelo no llegó a tiempo. Estaba trabajando; no es lo mismo que fallar."""


def turno(c, texto_persona, camino, motor=None, idioma=None, canal="modelo_local"):
    """Un turno completo. Devuelve un dict; no imprime nada.

    Sin `motor`, levanta SinCerebro: quien llama decide qué decir, y el
    producto sigue funcionando entero por memoria y formulario. Lo que no se
    hace es inventar una respuesta que parezca del modelo.

    Con `motor`, la respuesta **cruza la frontera** antes de volver. Si el
    fusible salta queda la cicatriz y no se devuelve texto.
    """
    idioma = TX.normalizar(idioma)
    perfil = M.leer_perfil(c)
    donde = fase(camino, perfil)
    sistema = prompt_sistema(donde, idioma)

    if motor is None:
        raise SinCerebro("no hay motor de conversación en esta copia")

    cruda = motor(sistema + "\n\n" + (texto_persona or ""))
    if not cruda:
        raise SinCerebro("el motor no devolvió nada")

    # La puerta única. El fusible mira la forma de lo que el modelo propone; si
    # salta, `cruzar_frontera` deja la fila del bloqueo y relanza.
    salida = M.cruzar_frontera(c, canal, cruda.strip(),
                               fusible.preparar_respuesta)
    return {
        "fase": donde,
        "texto": salida["texto"],
        "hallazgos": salida["hallazgos"],
        "id_salida": salida["id_salida"],
        "sistema": sistema,
    }


def proponer(c, texto, origen="aurelius"):
    """Lo que el game master apunta va al Cuaderno, nunca a la memoria firmada.

    D69 en una línea: la máquina propone, la persona firma. El turno puede
    sugerir un recuerdo; ascenderlo es acto de quien vive en esta máquina.
    """
    return M.proponer_borrador(c, texto, origen=origen)
