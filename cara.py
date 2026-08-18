#!/usr/bin/env python3
"""M2 · la cara · un solo fichero HTML que se abre con doble clic.

sistema: MVP · solo biblioteca estandar. Sin red, sin dependencias.

Uso:  python3 cara.py [--db RUTA] [--out FICHERO]   genera la cara
      python3 cara.py --aplicar FICHERO [--db RUTA] escribe lo que recogio

POR QUE SE GENERA Y NO SE SIRVE
-------------------------------
La cara no habla con un servidor porque no hay servidor. `cara.py` abre la
memoria, lee lo que hay y lo escribe DENTRO del HTML: sprites incrustados como
`data:`, textos de los dos idiomas incrustados, recuerdos incrustados. El
resultado es un fichero que se puede copiar a un USB y abrir en una maquina sin
red, y que sigue diciendo exactamente lo mismo.

Eso obliga a una asimetria honesta, y conviene decirla en voz alta: la cara
LEE de la memoria en el momento en que se genera, y para ESCRIBIR devuelve un
formulario que la persona guarda y aplica. No hay escritura silenciosa desde el
navegador. Quien mira la cara ve lo que hay; quien quiere cambiar la memoria
pasa por un fichero que puede leer antes de aplicarlo.
"""
from __future__ import annotations

import argparse
import base64
import sqlite3
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import memory as M
import textos as TX

AQUI = os.path.dirname(os.path.abspath(__file__))
ASSETS = os.path.join(AQUI, "assets")
RUTA_DEFECTO = os.path.expanduser("~/.aurelius/memory.db")
SALIDA_DEFECTO = os.path.join(AQUI, "cara.html")

# Las claves de texto que la cara usa. Se incrusta este subconjunto y no el
# diccionario entero: lo que no se usa no viaja, y asi el fichero no engorda
# con la prosa de la sesion de terminal.
CLAVES_CARA = (
    "perfil_device", "perfil_name", "perfil_nota",
    "recuerdo_que", "recuerdo_porque", "recuerdo_donde", "recuerdo_aprendido",
    "recuerdo_sin_que", "recuerdo_guardado", "recuerdo_vacio",
    "otro_pregunta", "otro_si", "otro_no",
    "cierre_recuento", "cierre_viven",
    "palabra_recuerdo", "palabra_recuerdos", "palabra_hueco", "palabra_huecos",
    "bucle_recuento",
)

# Lo que la cara dice y la sesion de terminal no: rotulos de botones, cabeceras
# de la Pizarra, los peldanos del Camino. Viven aqui porque son de la cara.
CARA_TEXTOS = {
    "en": {
        "titulo": "Aurelius",
        "sub": "the Water · your memory, on your machine",
        "saludo": "I am awake. Nothing here left this machine.",
        "saludo_vuelta": "I am awake, and I still have what you wrote.",
        "campo": "Write your answer…",
        "enviar": "SAY IT",
        "pizarra": "Slate",
        "camino": "The Path",
        "cerrar": "Close",
        "pz_titulo": "The Slate · everything your memory holds",
        "pz_vacia": "Nothing written yet. That is a state, not a failure.",
        "pz_sin_guardar": "captured here, not written yet",
        "pz_bajar_json": "Save the form",
        "pz_bajar_txt": "Save a readable copy",
        "pz_aplicar": "To write it into your memory, apply the file you just saved:",
        "pz_col": ("id", "what", "why", "where", "learned"),
        "cm_titulo": "The Path",
        "cm_intro": "Eight steps. This is where you actually are — measured, not guessed.",
        "cm_nota": "Nothing here is downloaded. This page is the whole thing.",
        "fin": "That is everything. Open the Slate to take it with you.",
        "idioma": "Language",
        "voz_hablar": "Speak",
        "voz_callar": "Mute",
        "voz_no_hay": "No voice in this copy",
        "voz_solo_es": "The voice speaks Spanish only",
        "voz_nota": ("The text is always here. The button only decides whether "
                     "it is also said out loud."),
        "cm_hecho": "done",
        "cm_empezado": "started",
        "cm_sin_empezar": "not started",
        "cm_no_medible": "not measurable from here",
        "cm_prueba_M0": "the two questions that are not memories: {perfil}/2 answered",
        "cm_prueba_M1": "the brain does not live inside this file, so this page cannot check it",
        "cm_prueba_M2": "{recuerdos} memories written · seal: {sello}",
        # Las side quests. Cada una dice QUE la da por hecha y QUE deja para el
        # proyecto: un peldano opcional sin ventaja declarada es un peldano que
        # nadie elige.
        "cm_prueba_M3": "{salas}/6 rooms finished",
        "cm_prueba_M4": "{huellas} crossings recorded",
        "cm_prueba_M5": "{senderos} paths opened",
        "cm_prueba_M6": "{cicatrices} scars on record",
        "cm_prueba_M7": "no one has written down what counts as a signed success, so this page will not invent it",
        "cm_ventaja_M3": "gives you: a way to work without noise",
        "cm_ventaja_M4": "gives you: you have seen your own words leave",
        "cm_ventaja_M5": "gives you: unfinished is a state, not a debt",
        "cm_ventaja_M6": "gives you: an error that leaves a mark can be read",
        "cm_ventaja_M7": "gives you: less explaining, because you need less",
        "cm_opcional": "optional",
        "cm_nucleo": "core",
        "cm_decision": "The core is done. From here you choose: go straight to your project, or take a side quest. Both are the path.",
        "cm_pendiente": "no way to measure this one yet — it will not be shown as progress until there is",
        "cm_refrescar": ("This page is a snapshot. To bring it up to date, "
                         "regenerate it — it reads your memory and your seal as they are now:"),
    },
    "es": {
        "titulo": "Aurelius",
        "sub": "el Agua · tu memoria, en tu máquina",
        "saludo": "Estoy despierto. Nada de esto ha salido de esta máquina.",
        "saludo_vuelta": "Estoy despierto, y sigo teniendo lo que escribiste.",
        "campo": "Escribe tu respuesta…",
        "enviar": "DILO",
        "pizarra": "Pizarra",
        "camino": "El Camino",
        "cerrar": "Cerrar",
        "pz_titulo": "La Pizarra · todo lo que tu memoria guarda",
        "pz_vacia": "Todavía no hay nada escrito. Eso es un estado, no un fallo.",
        "pz_sin_guardar": "recogido aquí, todavía sin escribir",
        "pz_bajar_json": "Guardar el formulario",
        "pz_bajar_txt": "Guardar una copia legible",
        "pz_aplicar": "Para escribirlo en tu memoria, aplica el fichero que acabas de guardar:",
        "pz_col": ("id", "qué", "por qué", "dónde", "aprendido"),
        "cm_titulo": "El Camino",
        "cm_intro": "Ocho peldaños. Esto es dónde estás de verdad — medido, no supuesto.",
        "cm_nota": "Aquí no se descarga nada. Esta página es todo.",
        "fin": "Eso es todo. Abre la Pizarra para llevártelo.",
        "idioma": "Idioma",
        "voz_hablar": "Hablar",
        "voz_callar": "Silencio",
        "voz_no_hay": "Esta copia no lleva voz",
        "voz_solo_es": "La voz solo habla español",
        "voz_nota": ("El texto está siempre. El botón solo decide si además se "
                     "dice en voz alta."),
        "cm_hecho": "hecho",
        "cm_empezado": "empezado",
        "cm_sin_empezar": "sin empezar",
        "cm_no_medible": "no medible desde aquí",
        "cm_prueba_M0": "las dos preguntas que no son recuerdos: {perfil}/2 contestadas",
        "cm_prueba_M1": "el cerebro no vive dentro de este fichero, así que esta página no puede comprobarlo",
        "cm_prueba_M2": "{recuerdos} recuerdos escritos · sello: {sello}",
        "cm_prueba_M3": "{salas}/6 salas terminadas",
        "cm_prueba_M4": "{huellas} cruces registrados",
        "cm_prueba_M5": "{senderos} senderos abiertos",
        "cm_prueba_M6": "{cicatrices} cicatrices en el registro",
        "cm_prueba_M7": "nadie ha escrito qué cuenta como éxito firmado, así que esta página no se lo inventa",
        "cm_ventaja_M3": "te deja: una forma de trabajar sin ruido",
        "cm_ventaja_M4": "te deja: has visto salir tus propias palabras",
        "cm_ventaja_M5": "te deja: lo sin terminar es un estado, no una deuda",
        "cm_ventaja_M6": "te deja: un error que deja marca se puede leer",
        "cm_ventaja_M7": "te deja: menos explicación, porque te hace menos falta",
        "cm_opcional": "opcional",
        "cm_nucleo": "núcleo",
        "cm_decision": "El núcleo está hecho. A partir de aquí eliges: ir directo a tu proyecto, o hacer una side quest. Las dos son el camino.",
        "cm_pendiente": "todavía no hay forma de medir este — no se pintará como progreso hasta que la haya",
        "cm_refrescar": ("Esta página es una foto. Para ponerla al día, "
                         "regenérala — lee tu memoria y tu sello tal como están ahora:"),
    },
}

# Los peldanos, recuperados de la interfaz anterior y filtrados: se quedan los
# nombres del camino, se va el vocabulario de la casa.
CAMINO = {
    "en": [("M0", "The Totem"), ("M1", "The Fire"), ("M2", "The Water"),
           ("M3", "The Refuge"), ("M4", "The Signal"), ("M5", "The Pact"),
           ("M6", "The Copper Bastion"), ("M7", "The Earth")],
    "es": [("M0", "El Tótem"), ("M1", "El Fuego"), ("M2", "El Agua"),
           ("M3", "El Refugio"), ("M4", "La Señal"), ("M5", "El Pacto"),
           ("M6", "El Bastión de Cobre"), ("M7", "La Tierra")],
}


# --- el camino · progreso medido, nunca decorado --------------------------

# Los ocho peldanos. `prueba` dice QUE lo da por hecho: si no hay forma de
# comprobarlo desde la memoria, el peldano lo declara y no se pinta a medias.
# Un camino que muestra progreso que no puede medir es una barra de carga
# falsa, y el producto entero existe para no hacer eso.
PELDANOS = ("M0", "M1", "M2", "M3", "M4", "M5", "M6", "M7")

# El nucleo es de todos. Lo demas se elige, de una en una y en cualquier orden.
NUCLEO = ("M0", "M1", "M2")
OPCIONALES = ("M3", "M4", "M5", "M6", "M7")

# Las seis salas de la fuga (M3). Vive aqui y en fuga.py: si algun dia
# discrepan, el rojo del camino lo dice antes que la persona.
TOTAL_SALAS = 6


def progreso_camino(c, ruta_db):
    """El estado real de los ocho peldanos. En instalacion limpia, todo a cero."""
    perfil = M.leer_perfil(c)
    contestadas = sum(1 for k in ("device", "name")
                      if perfil.get(k, M.AUSENTE) != M.AUSENTE)
    recuerdos = c.execute(
        "select count(*) from engrams where status='activo'").fetchone()[0]
    sello = os.path.exists(os.path.join(
        os.path.dirname(os.path.abspath(ruta_db)), "manifest-latest.txt"))

    # Las tablas jovenes pueden faltar en una memoria vieja, y la fuga monta la
    # suya aparte. Contar lo que no existe es cero, no una excepcion.
    def cuenta(sql):
        try:
            return c.execute(sql).fetchone()[0]
        except sqlite3.OperationalError:
            return 0

    salas = cuenta("select count(*) from fuga_sala where estado='completada'")
    huellas = cuenta("select count(*) from salidas where estado='ok'")
    cicatrices = cuenta("select count(*) from salidas where estado='bloqueado'")
    senderos = cuenta("select count(*) from hilos")

    estado = {}
    estado["M0"] = ("hecho" if contestadas == 2 else
                    "empezado" if contestadas else "sin_empezar")
    # El cerebro no vive dentro del producto, asi que el producto no puede
    # decir si esta. Decirlo es mas honesto que suponerlo en cualquier sentido.
    estado["M1"] = "no_medible"
    estado["M2"] = ("hecho" if recuerdos and sello else
                    "empezado" if recuerdos else "sin_empezar")

    # --- las side quests · opcionales, sueltas, y AHORA medidas ---------
    # Hasta hoy estas cinco estaban fijas en "sin_empezar", que es decir que
    # nadie las mira. Cuatro se pueden medir con lo que ya existe en la
    # memoria; la quinta se declara, que es lo que se hace con lo que no hay.
    estado["M3"] = ("hecho" if salas >= TOTAL_SALAS else
                    "empezado" if salas else "sin_empezar")
    estado["M4"] = "hecho" if huellas else "sin_empezar"
    estado["M5"] = "hecho" if senderos else "sin_empezar"
    estado["M6"] = "hecho" if cicatrices else "sin_empezar"
    # Retirar el andamiaje exige saber que cuenta como exito firmado, y eso no
    # esta escrito en ninguna parte. Se declara igual que M1.
    estado["M7"] = "no_medible"

    return {
        "estado": estado,
        "cifras": {"perfil": contestadas, "recuerdos": recuerdos,
                   "sello": bool(sello), "salas": salas, "huellas": huellas,
                   "senderos": senderos, "cicatrices": cicatrices},
        # El nucleo se hace; las side quests se eligen. Un camino que obliga a
        # pasar por las ocho no es un camino: es un pasillo.
        "nucleo": list(NUCLEO),
        "opcionales": list(OPCIONALES),
        "punto_decision": estado["M2"] == "hecho",
    }


# --- la voz · sintetizada al generar, por proceso hijo (D75) --------------

def para_voz(texto):
    """El mismo contenido, preparado para el oido. NO toca lo que se muestra.

    El modelo devuelve el texto con la puntuacion de una pantalla: dos espacios
    al final de linea para forzar un salto, saltos dentro de una misma frase,
    y de vez en cuando un asterisco. Eso en una pagina no se ve; dicho en voz
    alta produce pausas donde no las hay y silencios a mitad de idea.

    La regla es la del tono: la cadencia puede cambiar CUANDO se dice algo,
    nunca QUE se dice. Aqui no se quita ni se anade una palabra — solo se
    deshacen las marcas que existian para los ojos.
    """
    import re
    t = re.sub(r"[*_`#>]+", " ", texto or "")     # marcas de pagina, no de voz
    t = re.sub(r"\s*\n\s*", " ", t)               # los saltos no son pausas
    t = re.sub(r"[ \t]{2,}", " ", t)              # el doble espacio era un salto
    t = re.sub(r"\s+([,.;:!?])", r"\1", t)        # no se respira antes de una coma
    return t.strip()


def voz_datauri(texto, piper=None, modelo_voz=None):
    """Un WAV incrustado, hablado por el proceso hijo. None si no hay voz.

    Se sintetiza AL GENERAR, no al abrir: la cara es un fichero suelto sin red
    ni servidor, y no puede lanzar procesos. Asi la voz firmada suena en la
    cara sin abrir un socket (D75) y sin pedirle nada a la red (D68).
    """
    import subprocess
    import wave
    if not (piper and modelo_voz):
        return None
    try:
        crudo = subprocess.run(
            [piper, "-m", modelo_voz, "-s", "0", "--output-raw"],
            input=para_voz(texto).encode("utf-8"),
            capture_output=True, timeout=120).stdout
    except (OSError, subprocess.SubprocessError):
        return None
    if not crudo:
        return None
    import io
    buf = io.BytesIO()
    with wave.open(buf, "wb") as w:
        w.setnchannels(1)
        w.setsampwidth(2)
        w.setframerate(22050)
        w.writeframes(crudo)
    return "data:audio/wav;base64," + base64.b64encode(buf.getvalue()).decode()


# Lo que la cara dice en voz alta. Solo las lineas fijas: lo que lleva un hueco
# ({n}) cambia en cada sesion y no se puede grabar de antemano. Se declara en
# vez de fingir que se dijo.
CLAVES_HABLADAS = ("saludo", "saludo_vuelta", "perfil_device", "perfil_name",
                   "recuerdo_que", "recuerdo_porque", "recuerdo_donde",
                   "recuerdo_aprendido", "otro_pregunta", "fin")


def dato_uri(nombre):
    """El PNG entero, dentro del HTML. Un asset enlazado se pierde al mover
    el fichero de sitio; uno incrustado viaja con el."""
    ruta = os.path.join(ASSETS, nombre)
    with open(ruta, "rb") as fh:
        return "data:image/png;base64," + base64.b64encode(fh.read()).decode()


def _json(valor):
    """JSON para meter dentro de <script>. Se parte la secuencia que cerraria
    la etiqueta antes de tiempo; lo demas viaja tal cual, acentos incluidos."""
    return (json.dumps(valor, ensure_ascii=False)
            .replace("</", "<\\/")
            .replace("\u2028", "\\u2028").replace("\u2029", "\\u2029"))


def textos_cara(idioma):
    tabla = {k: TX.TEXTOS[idioma][k] for k in CLAVES_CARA}
    tabla.update(CARA_TEXTOS[idioma])
    return tabla


def limpia(texto):
    """Quita el parentesis de ayuda antes de decir la frase en voz alta.
    '(enter = NO_DATA)' es una instruccion de teclado: leerla no ayuda a nadie."""
    import re
    return re.sub(r"\s*\((enter|escribe|type).*$", "", texto,
                  flags=re.I | re.S).strip()


def generar(c, ruta_db, idioma=None, piper=None, modelo_voz=None, turnos=None):
    """El HTML entero, como cadena. No escribe nada: quien llama decide donde."""
    estado = M.formulario(c)
    guardado = estado["profile"].get("language", M.AUSENTE)
    inicial = TX.normalizar(idioma or (guardado if guardado != M.AUSENTE else ""))
    datos = {
        "profile": estado["profile"],
        "engrams": [{k: r[k] for k in
                     ("id", "what", "why", "where_ref", "learned")}
                    for r in estado["engrams"]],
        "recuento": estado["recuento"],
        "ruta": ruta_db,
        "ausente": M.AUSENTE,
        "camino": progreso_camino(c, ruta_db),
        # Los turnos REALES que produjo el hijo residente, con su voz ya
        # sintetizada. La cara no los genera ni los inventa: los muestra.
        "turnos": turnos or [],
    }
    # La voz firmada es es_ES: solo se graban las lineas españolas. En ingles el
    # boton sigue estando y dice por que no suena — una funcion que existe a
    # medias se declara, no se esconde.
    audio = {}
    if piper and modelo_voz:
        for clave in CLAVES_HABLADAS:
            uri = voz_datauri(limpia(TX.TEXTOS["es"].get(clave)
                                     or CARA_TEXTOS["es"][clave]),
                              piper, modelo_voz)
            if uri:
                audio[clave] = uri
    # Los clips que de verdad viajan dentro: los del catalogo mas los de los
    # turnos reales. Se cuenta aqui, donde se sabe, y se declara en el <meta>:
    # una voz que falta y una voz que nunca se grabo se parecen demasiado.
    n_audio = len(audio) + sum(1 for t in (turnos or []) if t.get("audio"))
    aria_voz = textos_cara(inicial).get("voz_hablar", "Speak")
    return (PLANTILLA
            .replace("__LANG__", inicial)
            .replace("__N_AUDIO__", str(n_audio))
            .replace("__ARIA_VOZ__", aria_voz)
            .replace("__TALKS__", dato_uri("aurelius-talks.png"))
            .replace("__UP__", dato_uri("aurelius-up.png"))
            .replace("__IDIOMA__", inicial)
            .replace("__TEXTOS__", _json({i: textos_cara(i) for i in ("en", "es")}))
            .replace("__CAMINO__", _json(CAMINO))
            .replace("__PELDANOS__", _json(list(PELDANOS)))
            .replace("__AUDIO__", _json(audio))
            .replace("__DATOS__", _json(datos)))


def aplicar(ruta_db, ruta_formulario):
    """Escribe en la memoria lo que la cara recogio. El unico camino de vuelta.

    Va por un fichero a proposito: la persona puede abrirlo y leerlo entero
    antes de que toque nada. Una escritura que no se puede inspeccionar antes
    de ocurrir es una escritura que hay que creerse.
    """
    with open(ruta_formulario, encoding="utf-8") as fh:
        datos = json.load(fh)
    with M.abrir(ruta_db) as c:
        resumen = M.aplicar_formulario(c, datos)
    print(f"Written into {ruta_db}:")
    print(f"  {resumen['engrams']} memories, {resumen['profile']} profile "
          f"answers" + (", language set" if resumen["language"] else ""))
    print("  nothing was replaced and nothing was removed")
    return 0


PLANTILLA = r"""<!DOCTYPE html>
<html lang="__LANG__">
<head>
<meta charset="utf-8" />
<meta name="viewport" content="width=device-width, initial-scale=1, interactive-widget=resizes-content" />
<meta name="aurelius:audio" content="__N_AUDIO__" />
<title>Aurelius</title>
<style>
  /* Losa y vena: gris pizarra de fondo, violeta para lo que responde al dedo.
     Dos colores y sus sombras. Una paleta corta se lee de un vistazo. */
  :root {
    --losa-900:#0b0f1a; --losa-800:#131926; --losa-700:#1c2433; --losa-600:#2b3547;
    --vena:#a78bfa; --vena-tenue:#6d5bd0;
    --texto:#e8eaf2; --tenue:#98a2b8; --tuyo:#212a3b;
  }
  * { box-sizing: border-box; }
  html, body { margin:0; height:100%; }
  body {
    background: radial-gradient(120% 90% at 50% 0%, #1a2136 0%, var(--losa-900) 62%);
    color: var(--texto);
    font: 16px/1.55 "Iowan Old Style", Georgia, serif;
    display:flex; flex-direction:column; height:100vh; height:100dvh; overflow:hidden;
  }
  header {
    /* Envuelve. Medido el 2026-08-18 a 360px: sin `wrap`, los tres botones se
       salian hasta 607px y arrastraban la pagina 248px a lo ancho. Una fila que
       no envuelve no es una fila estrecha: es una pagina rota. */
    display:flex; flex-wrap:wrap; align-items:center; gap:14px; padding:12px 18px; flex:0 0 auto;
    border-bottom:1px solid var(--losa-600); background:var(--losa-900);
    background-image:linear-gradient(90deg, rgba(167,139,250,0.10), transparent);
  }
  .marco {
    width:clamp(52px, 13vw, 84px); aspect-ratio:3/4;
    flex:0 0 auto; border:1px solid var(--vena-tenue);
    border-radius:10px; overflow:hidden; background:#0a0d16;
    box-shadow:0 0 16px rgba(167,139,250,0.25), inset 0 0 22px rgba(0,0,0,0.6);
  }
  /* El sprite: 4 fotogramas en horizontal, 1024x341. Solo cambia la posicion
     del fondo — la cabeza nunca se desplaza dentro del marco. */
  .sprite {
    width:100%; height:100%;
    background-repeat:no-repeat; background-size:400% 100%; background-position:0% 50%;
    image-rendering:pixelated;
  }
  .titulo { display:flex; flex-direction:column; min-width:0; flex:1 1 120px; }
  .titulo h1 { margin:0; font-size:21px; letter-spacing:.03em; }
  .titulo .sub { color:var(--tenue); font-size:12px; font-family:ui-monospace, monospace; }
  .huecos { flex:1 1 auto; }
  .boton, select {
    color:var(--vena); background:none; border:1px solid var(--vena-tenue);
    border-radius:9px; padding:0 13px; min-height:44px; cursor:pointer;
    font:600 13px/1 ui-monospace, monospace; white-space:nowrap;
  }
  .boton:hover, select:hover { background:var(--vena); color:var(--losa-900); }
  a.boton { text-decoration:none; display:inline-flex; align-items:center; }
  .boton:focus-visible, select:focus-visible { outline:2px solid var(--vena); outline-offset:2px; }
  select { color:var(--texto); background:var(--losa-800); }

  main { flex:1 1 auto; overflow-y:auto; padding:26px 18px 8px; }
  .hilo { max-width:760px; margin:0 auto; display:flex; flex-direction:column; gap:14px; }
  .burbuja { padding:12px 16px; border-radius:14px; max-width:86%; white-space:pre-wrap; }
  .de-el { background:var(--losa-800); border:1px solid var(--losa-600); border-top-left-radius:4px; align-self:flex-start; }
  .de-ti { background:var(--tuyo); border:1px solid var(--losa-600); border-top-right-radius:4px; align-self:flex-end; }
  .opciones { display:flex; gap:10px; align-self:flex-start; flex-wrap:wrap; }

  footer { flex:0 0 auto; padding:12px 18px 18px; border-top:1px solid var(--losa-600); background:var(--losa-900); }
  .fila { max-width:760px; margin:0 auto; display:flex; gap:10px; align-items:flex-end; }
  textarea {
    flex:1 1 auto; resize:none; min-height:46px; max-height:140px; padding:11px 14px;
    border-radius:11px; border:1px solid var(--losa-600); background:var(--losa-800);
    color:var(--texto); font:16px/1.4 inherit;
  }
  textarea:focus { outline:2px solid var(--vena-tenue); outline-offset:1px; }
  .enviar { background:var(--vena); color:var(--losa-900); border-color:var(--vena); min-height:46px; }

  /* Pizarra y Camino: dos paneles, mismo esqueleto. */
  .fondo { position:fixed; inset:0; z-index:40; background:rgba(6,8,14,.62); }
  .panel {
    position:fixed; top:0; right:0; z-index:41; height:100vh; height:100dvh;
    width:min(660px, 96vw); background:var(--losa-900); border-left:1px solid var(--losa-600);
    box-shadow:-14px 0 44px rgba(0,0,0,.55); display:flex; flex-direction:column;
  }
  .panel header { border-bottom:1px solid var(--losa-600); }
  .panel .cuerpo { overflow-y:auto; padding:18px; }
  table { width:100%; border-collapse:collapse; font-size:14px; }
  th, td { text-align:left; padding:8px 9px; border-bottom:1px solid var(--losa-700); vertical-align:top; }
  th { color:var(--tenue); font:600 12px/1 ui-monospace, monospace; text-transform:uppercase; }
  td.ausente { color:var(--tenue); font-family:ui-monospace, monospace; }
  tr.nueva td { background:rgba(167,139,250,.07); }
  .orden { background:var(--losa-800); border:1px solid var(--losa-600); border-radius:9px;
           padding:11px 13px; font:13px/1.5 ui-monospace, monospace; color:var(--texto);
           overflow-x:auto; white-space:pre; }
  .peldano { display:flex; gap:12px; padding:11px 0; border-bottom:1px solid var(--losa-700); }
  .peldano .n { color:var(--vena); font:600 13px/1.6 ui-monospace, monospace; width:38px; flex:0 0 auto; }
  .peldano[data-aqui="si"] .n { color:var(--losa-900); background:var(--vena); border-radius:6px; text-align:center; }
  .peldano[data-estado="hecho"] .n { color:var(--losa-900); background:#7dd3a0; border-radius:6px; text-align:center; }
  .peldano[data-estado="sin_empezar"] .n, .peldano[data-estado="no_medible"] .n { color:var(--tenue); }
  .nota { color:var(--tenue); font-size:13px; margin-top:16px; }
  [hidden] { display:none !important; }
  @media (prefers-reduced-motion: reduce) { .sprite { transition:none; } }
  @media (max-width:600px) { .titulo h1 { font-size:18px; } }
</style>
</head>
<body>
<header>
  <div class="marco"><div id="busto" class="sprite" role="img" aria-label="Aurelius"></div></div>
  <div class="titulo"><h1 id="t-titulo">Aurelius</h1><span class="sub" id="t-sub"></span></div>
  <div class="huecos"></div>
  <select id="lang" aria-label="Language"><option value="en">EN</option><option value="es">ES</option></select>
  <button type="button" class="boton" id="b-voz" aria-pressed="false"
          aria-label="__ARIA_VOZ__"></button>
  <button type="button" class="boton" id="b-pizarra"></button>
  <button type="button" class="boton" id="b-camino"></button>
</header>

<main><div class="hilo" id="hilo"></div></main>

<footer><div class="fila">
  <textarea id="campo" rows="1" autocomplete="off"></textarea>
  <button type="button" class="boton enviar" id="b-enviar"></button>
</div></footer>

<div id="fondo-pz" class="fondo" hidden></div>
<aside id="pz" class="panel" hidden aria-labelledby="pz-t">
  <header><h2 id="pz-t" style="margin:0;font-size:17px"></h2><div class="huecos"></div>
    <button type="button" class="boton" data-cerrar="pz"></button></header>
  <div class="cuerpo" id="pz-cuerpo"></div>
  <!-- Los dos enlaces de salida existen en el fuente, no los inventa el guion.
       Lo que se puede llevar la persona tiene que poder leerse abriendo la
       pagina con un editor: una salida que solo existe cuando el guion decide
       crearla no se puede auditar antes de usarla. -->
  <div style="padding:0 18px 20px">
    <p style="display:flex;gap:10px;flex-wrap:wrap;margin:0 0 14px">
      <a class="boton" id="pz-json" download="aurelius-formulario.json" href="#"></a>
      <a class="boton" id="pz-txt" download="aurelius-recuerdos.txt" href="#"></a>
    </p>
    <p class="nota" id="pz-aplicar" style="margin:0 0 8px"></p>
    <div class="orden" id="pz-orden"></div>
  </div>
</aside>

<div id="fondo-cm" class="fondo" hidden></div>
<aside id="cm" class="panel" hidden aria-labelledby="cm-t">
  <header><h2 id="cm-t" style="margin:0;font-size:17px"></h2><div class="huecos"></div>
    <button type="button" class="boton" data-cerrar="cm"></button></header>
  <div class="cuerpo" id="cm-cuerpo"></div>
</aside>

<script>
"use strict";
/* Todo lo que sigue es estado local. Esta pagina no abre una sola conexion:
   los sprites, los textos de los dos idiomas y los recuerdos ya estan dentro
   del fichero. Se puede abrir con el cable desenchufado y hace lo mismo. */

var IDIOMA_INICIAL = "__IDIOMA__";
var TEXTOS = __TEXTOS__;
var CAMINO = __CAMINO__;
var DATOS = __DATOS__;

var HOJAS = { talks: "__TALKS__", up: "__UP__" };
var AUDIO = __AUDIO__;
var PELDANOS = __PELDANOS__;
var idioma = IDIOMA_INICIAL;
var AUSENTE = DATOS.ausente;
var FORMULARIO = { language: "", profile: {}, engrams: [] };

function t(clave) { return TEXTOS[idioma][clave]; }
function el(id) { return document.getElementById(id); }
function quieto() {
  return window.matchMedia && window.matchMedia("(prefers-reduced-motion: reduce)").matches;
}

/* ── la cara · cuatro estados y un contrato ────────────────────────────────
   dormido   up[1] fijo, antes de la primera frase
   despertar up[1→2→3→4] UNA vez, con la primera frase
   reposo    talks[4]
   hablando  talks[1→2→3] en bucle mientras escribe
   El contrato vive en ASSETS.md; esto es su unica implementacion.        */
var busto = el("busto");
var despertado = false;
var bucle = null;

function pintar(hoja, cuadro) {
  busto.style.backgroundImage = "url(" + HOJAS[hoja] + ")";
  busto.style.backgroundPosition = ((cuadro - 1) * (100 / 3)) + "% 50%";
}
function dormido() { pintar("up", 1); }
function reposo() { detener(); pintar("talks", 4); }
function detener() { if (bucle) { clearInterval(bucle); bucle = null; } }

function hablando() {
  detener();
  if (quieto()) { pintar("talks", 2); return; }
  var i = 0, orden = [1, 2, 3];
  bucle = setInterval(function () { pintar("talks", orden[i % 3]); i++; }, 130);
}

function despertar(hecho) {
  if (despertado) { hecho(); return; }
  despertado = true;
  if (quieto()) { pintar("up", 4); setTimeout(hecho, 60); return; }
  var cuadro = 1;
  pintar("up", 1);
  var seq = setInterval(function () {
    cuadro++;
    if (cuadro > 4) { clearInterval(seq); setTimeout(hecho, 220); return; }
    pintar("up", cuadro);
  }, 210);
}

/* ── el hilo ─────────────────────────────────────────────────────────────── */
var hilo = el("hilo");

function burbuja(clase, texto) {
  var d = document.createElement("div");
  d.className = "burbuja " + clase;
  d.textContent = texto;
  hilo.appendChild(d);
  d.scrollIntoView({ block: "end" });
  return d;
}

/* ── la voz · estado local, sonido ya incrustado ───────────────────────────
   La voz se grabo al generar esta pagina, con el proceso hijo que la sintetiza.
   Aqui solo se reproduce un fichero que ya viaja dentro: ni red, ni socket, ni
   proceso lanzado desde el navegador. El texto se muestra SIEMPRE; el boton
   decide unicamente si ademas suena.                                        */
var hablaViva = false;
var sonando = null;

function hayVoz(clave) { return idioma === "es" && !!AUDIO[clave]; }
function algunaVoz() {
  return Object.keys(AUDIO).length > 0 ||
         DATOS.turnos.some(function (t) { return !!t.audio; });
}

function suena(clave) {
  if (!hablaViva || !hayVoz(clave)) { return; }
  reproduce(AUDIO[clave]);
}

function reproduce(uri) {
  if (!hablaViva || !uri) { return; }
  callar();
  sonando = new Audio(uri);
  sonando.play().catch(function () { /* sin permiso de sonido: el texto basta */ });
}
function callar() {
  if (sonando) { sonando.pause(); sonando = null; }
}

function dice(texto, hecho, clave) {
  var d = burbuja("de-el", "");
  hablando();
  if (clave) { suena(clave); }
  if (quieto()) { d.textContent = texto; reposo(); if (hecho) hecho(); return; }
  var i = 0;
  var esc = setInterval(function () {
    d.textContent = texto.slice(0, ++i);
    d.scrollIntoView({ block: "end" });
    if (i >= texto.length) { clearInterval(esc); reposo(); if (hecho) hecho(); }
  }, 16);
}

/* ── la conversacion · las mismas preguntas de la sesion, sin nadie en medio */
var cola = [];
var esperando = null;
var recuerdo = null;

function guion() {
  var pasos = [];
  if (DATOS.profile.device === AUSENTE) pasos.push({ perfil: "device", clave: "perfil_device" });
  if (DATOS.profile.name === AUSENTE) pasos.push({ perfil: "name", clave: "perfil_name" });
  pasos.push({ recuerdo: "nuevo" });
  return pasos;
}

function pasoRecuerdo() {
  recuerdo = { what: "", why: "", where_ref: "", learned: "" };
  cola.unshift(
    { campo: "what", clave: "recuerdo_que", obligatorio: true },
    { campo: "why", clave: "recuerdo_porque" },
    { campo: "where_ref", clave: "recuerdo_donde" },
    { campo: "learned", clave: "recuerdo_aprendido" },
    { guardar: true },
    { otro: true }
  );
}

function limpia(texto) { return texto.replace(/\s*\(enter =.*$/, "").trim(); }

function siguiente() {
  if (!cola.length) { return cerrar(); }
  var paso = cola.shift();
  if (paso.recuerdo) { pasoRecuerdo(); return siguiente(); }
  if (paso.guardar) {
    if (recuerdo.what) {
      FORMULARIO.engrams.push(recuerdo);
      var n = DATOS.engrams.length + FORMULARIO.engrams.length;
      dice(t("bucle_recuento")
        .replace("{n}", n)
        .replace("{nombre_r}", t(n === 1 ? "palabra_recuerdo" : "palabra_recuerdos"))
        .trim(), siguiente);
    } else {
      dice(t("recuerdo_sin_que"), siguiente, "recuerdo_sin_que");
    }
    return;
  }
  if (paso.otro) { return preguntaOtro(); }
  esperando = paso;
  dice(limpia(t(paso.clave)), function () { el("campo").focus(); }, paso.clave);
}

function preguntaOtro() {
  suena("otro_pregunta");
  dice(limpia(t("otro_pregunta")), function () {
    var caja = document.createElement("div");
    caja.className = "opciones";
    [["si", t("otro_si")], ["no", t("otro_no")]].forEach(function (par) {
      var b = document.createElement("button");
      b.type = "button"; b.className = "boton"; b.textContent = par[1];
      b.onclick = function () {
        burbuja("de-ti", par[1]);
        caja.remove();
        if (par[0] === "si") { cola.unshift({ recuerdo: "nuevo" }); }
        siguiente();
      };
      caja.appendChild(b);
    });
    hilo.appendChild(caja);
    caja.scrollIntoView({ block: "end" });
  });
}

function cerrar() {
  esperando = null;
  dice(t("fin"), null, "fin");
}

function responder(texto) {
  if (!esperando) { return; }
  var paso = esperando;
  esperando = null;
  burbuja("de-ti", texto === "" ? AUSENTE : texto);
  if (paso.perfil) {
    if (texto !== "") { FORMULARIO.profile[paso.perfil] = texto; }
    DATOS.profile[paso.perfil] = texto === "" ? AUSENTE : texto;
  } else if (paso.campo) {
    if (paso.obligatorio && texto === "") {
      // Sin un que no hay recuerdo: se dice y se salta al resto del guion.
      cola = cola.filter(function (p) { return !p.campo; });
      recuerdo.what = "";
    } else {
      recuerdo[paso.campo] = texto;
    }
  }
  siguiente();
}

el("b-enviar").onclick = function () {
  var campo = el("campo");
  var texto = campo.value.trim();
  campo.value = "";
  responder(texto);
};
el("campo").addEventListener("keydown", function (e) {
  if (e.key === "Enter" && !e.shiftKey) { e.preventDefault(); el("b-enviar").click(); }
});

/* ── la Pizarra · lo que hay, y como llevarselo ──────────────────────────── */
function celda(fila, valor, nueva) {
  var td = document.createElement("td");
  var v = (valor === "" || valor === null || valor === undefined) ? AUSENTE : valor;
  if (v === AUSENTE) { td.className = "ausente"; }
  td.textContent = v;
  fila.appendChild(td);
}

function pintarPizarra() {
  var cuerpo = el("pz-cuerpo");
  cuerpo.textContent = "";
  var todos = DATOS.engrams.slice();
  var nuevos = FORMULARIO.engrams.filter(function (r) { return r.what; });
  if (!todos.length && !nuevos.length) {
    var p = document.createElement("p");
    p.className = "nota"; p.textContent = t("pz_vacia");
    cuerpo.appendChild(p);
  } else {
    var tabla = document.createElement("table");
    var thead = document.createElement("tr");
    t("pz_col").forEach(function (c) {
      var th = document.createElement("th"); th.textContent = c; thead.appendChild(th);
    });
    tabla.appendChild(thead);
    todos.forEach(function (r) {
      var tr = document.createElement("tr");
      celda(tr, r.id); celda(tr, r.what); celda(tr, r.why);
      celda(tr, r.where_ref); celda(tr, r.learned);
      tabla.appendChild(tr);
    });
    nuevos.forEach(function (r) {
      var tr = document.createElement("tr");
      tr.className = "nueva";
      celda(tr, "·"); celda(tr, r.what); celda(tr, r.why);
      celda(tr, r.where_ref); celda(tr, r.learned);
      tabla.appendChild(tr);
    });
    cuerpo.appendChild(tabla);
    if (nuevos.length) {
      var aviso = document.createElement("p");
      aviso.className = "nota"; aviso.textContent = "· " + t("pz_sin_guardar");
      cuerpo.appendChild(aviso);
    }
  }

  FORMULARIO.language = idioma;
  bajar(el("pz-json"), t("pz_bajar_json"),
    JSON.stringify(FORMULARIO, null, 2), "application/json");
  bajar(el("pz-txt"), t("pz_bajar_txt"), legible(todos, nuevos), "text/plain");
  el("pz-aplicar").textContent = t("pz_aplicar");
  el("pz-orden").textContent =
    "python3 cara.py --aplicar aurelius-formulario.json --db " + DATOS.ruta;
}

function bajar(a, rotulo, contenido, tipo) {
  // El contenido se rehace en cada apertura: la Pizarra ensena lo que hay
  // AHORA, no lo que habia la primera vez que se abrio.
  if (a.dataset.url) { URL.revokeObjectURL(a.dataset.url); }
  a.dataset.url = URL.createObjectURL(new Blob([contenido], { type: tipo }));
  a.href = a.dataset.url;
  a.textContent = rotulo;
}

function legible(viejos, nuevos) {
  var lineas = [];
  viejos.concat(nuevos).forEach(function (r) {
    lineas.push("- " + r.what);
    ["why", "where_ref", "learned"].forEach(function (k) {
      lineas.push("    " + k + ": " + ((r[k] === "" || !r[k]) ? AUSENTE : r[k]));
    });
  });
  return lineas.join("\n") + "\n";
}

/* ── el Camino ───────────────────────────────────────────────────────────── */
function pintarCamino() {
  var cuerpo = el("cm-cuerpo");
  cuerpo.textContent = "";
  var intro = document.createElement("p");
  intro.className = "nota"; intro.textContent = t("cm_intro");
  cuerpo.appendChild(intro);
  var estado = DATOS.camino.estado, cifras = DATOS.camino.cifras;
  CAMINO[idioma].forEach(function (par) {
    var id = par[0], como = estado[id] || "sin_empezar";
    var d = document.createElement("div");
    d.className = "peldano";
    d.setAttribute("data-estado", como);
    if (como === "empezado") { d.setAttribute("data-aqui", "si"); }

    var n = document.createElement("span");
    n.className = "n"; n.textContent = id;

    var caja = document.createElement("span");
    var nom = document.createElement("div");
    nom.textContent = par[1] + " · " + t("cm_" + como);
    caja.appendChild(nom);

    // La prueba: QUE lo da por hecho. Un peldaño verde sin prueba al lado es
    // decoracion, y en cuanto la persona lo descubre deja de creerse el resto.
    var prueba = document.createElement("div");
    prueba.className = "nota"; prueba.style.margin = "2px 0 0";
    if (id === "M0") {
      prueba.textContent = t("cm_prueba_M0").replace("{perfil}", cifras.perfil);
    } else if (id === "M1") {
      prueba.textContent = t("cm_prueba_M1");
    } else if (id === "M2") {
      prueba.textContent = t("cm_prueba_M2")
        .replace("{recuerdos}", cifras.recuerdos)
        .replace("{sello}", cifras.sello ? "✓" : DATOS.ausente);
    } else if (id === "M7") {
      prueba.textContent = t("cm_prueba_M7");
    } else {
      prueba.textContent = t("cm_prueba_" + id)
        .replace("{salas}", cifras.salas)
        .replace("{huellas}", cifras.huellas)
        .replace("{senderos}", cifras.senderos)
        .replace("{cicatrices}", cifras.cicatrices);
    }
    caja.appendChild(prueba);

    // Nucleo u opcional, dicho en la propia fila: quien mira el Camino tiene
    // que poder ver de un vistazo que NO esta obligado a las ocho.
    var marca = document.createElement("div");
    marca.className = "nota"; marca.style.margin = "2px 0 0";
    var esOpcional = (DATOS.camino.opcionales || []).indexOf(id) >= 0;
    marca.textContent = esOpcional
      ? t("cm_opcional") + " · " + t("cm_ventaja_" + id)
      : t("cm_nucleo");
    caja.appendChild(marca);

    d.appendChild(n); d.appendChild(caja);
    cuerpo.appendChild(d);

    // El punto de decision vive DONDE se decide: al acabar el nucleo, no en un
    // menu aparte que nadie abre.
    if (id === "M2" && DATOS.camino.punto_decision) {
      var dec = document.createElement("div");
      dec.className = "nota";
      dec.style.cssText = "margin:10px 0 6px;padding:10px 12px;"
        + "border-left:3px solid var(--vena);color:var(--texto)";
      dec.textContent = t("cm_decision");
      cuerpo.appendChild(dec);
    }
  });

  var refrescar = document.createElement("p");
  refrescar.className = "nota"; refrescar.textContent = t("cm_refrescar");
  cuerpo.appendChild(refrescar);
  var orden = document.createElement("div");
  orden.className = "orden";
  orden.textContent = "python3 cara.py --db " + DATOS.ruta;
  cuerpo.appendChild(orden);

  var nota = document.createElement("p");
  nota.className = "nota"; nota.textContent = t("cm_nota");
  cuerpo.appendChild(nota);
}

function abrir(cual, pintar_) {
  pintar_();
  el(cual).hidden = false;
  el("fondo-" + cual).hidden = false;
}
function cierra(cual) { el(cual).hidden = true; el("fondo-" + cual).hidden = true; }

el("b-pizarra").onclick = function () { abrir("pz", pintarPizarra); };
el("b-camino").onclick = function () { abrir("cm", pintarCamino); };
Array.prototype.forEach.call(document.querySelectorAll("[data-cerrar]"), function (b) {
  b.onclick = function () { cierra(b.getAttribute("data-cerrar")); };
});
el("fondo-pz").onclick = function () { cierra("pz"); };
el("fondo-cm").onclick = function () { cierra("cm"); };
document.addEventListener("keydown", function (e) {
  if (e.key === "Escape") { cierra("pz"); cierra("cm"); }
});

/* ── el idioma · cambia las cadenas, no la memoria ───────────────────────── */
function rotularVoz() {
  var b = el("b-voz");
  if (!algunaVoz()) {
    b.textContent = t("voz_no_hay"); b.disabled = true;
    b.title = t("voz_nota");
    return;
  }
  if (idioma !== "es") {
    b.textContent = t("voz_solo_es"); b.disabled = true;
    b.title = t("voz_nota");
    callar();
    return;
  }
  b.disabled = false;
  b.textContent = hablaViva ? t("voz_callar") : t("voz_hablar");
  // El rotulo accesible sigue al texto: quien navega por voz pide el boton
  // por su nombre, y el nombre cambia con el idioma y con el estado.
  b.setAttribute("aria-label", hablaViva ? t("voz_callar") : t("voz_hablar"));
  b.setAttribute("aria-pressed", hablaViva ? "true" : "false");
  b.title = t("voz_nota");
}

function rotular() {
  el("t-sub").textContent = t("sub");
  el("campo").placeholder = t("campo");
  el("b-enviar").textContent = t("enviar");
  el("b-pizarra").textContent = t("pizarra");
  el("b-camino").textContent = t("camino");
  el("pz-t").textContent = t("pz_titulo");
  el("cm-t").textContent = t("cm_titulo");
  Array.prototype.forEach.call(document.querySelectorAll("[data-cerrar]"), function (b) {
    b.textContent = t("cerrar");
  });
  document.documentElement.lang = idioma;
  rotularVoz();
}

el("b-voz").onclick = function () {
  hablaViva = !hablaViva;
  if (!hablaViva) { callar(); }
  // Viaja en el formulario, como el idioma: una preferencia que hay que volver
  // a poner en cada arranque no es una preferencia.
  FORMULARIO.profile.voice = hablaViva ? "on" : "off";
  rotularVoz();
};

// La preferencia de voz se recupera del perfil. Si nadie la eligio, queda
// callado: una voz que arranca sola sorprende, y sorprender no es un permiso.
hablaViva = (DATOS.profile.voice === "on") && algunaVoz() && idioma === "es";

el("lang").value = idioma;
el("lang").onchange = function () {
  idioma = el("lang").value;
  FORMULARIO.language = idioma;
  rotular();
  if (!el("pz").hidden) { pintarPizarra(); }
  if (!el("cm").hidden) { pintarCamino(); }
};

/* ── arranque · dormido hasta la primera frase ───────────────────────────── */
rotular();
dormido();
cola = guion();
/* Si el hijo residente dejo turnos, la cara los muestra tal cual: la pregunta
   de la persona y la respuesta REAL del modelo, con su voz ya sintetizada. La
   cara sigue sin lanzar procesos ni abrir sockets — solo ensena y reproduce lo
   que el residente dejo escrito aqui dentro. */
function pintarTurnos(hecho) {
  var i = 0;
  (function paso() {
    if (i >= DATOS.turnos.length) { hecho(); return; }
    var turno = DATOS.turnos[i++];
    burbuja("de-ti", turno.tu);
    var ultimo = i >= DATOS.turnos.length;
    if (ultimo && turno.audio) { reproduce(turno.audio); }
    dice(turno.el, function () {
      if (turno.lore) { burbuja("de-el", turno.lore); }
      paso();
    });
  })();
}

window.setTimeout(function () {
  despertar(function () {
    if (DATOS.turnos.length) {
      pintarTurnos(function () { cola = []; esperando = null; });
      return;
    }
    var clave = DATOS.engrams.length ? "saludo_vuelta" : "saludo";
    dice(t(clave), siguiente, clave);
  });
}, 500);
</script>
</body>
</html>
"""


def main(argv=None):
    ap = argparse.ArgumentParser(description="Aurelius M2 · the face")
    ap.add_argument("--db", default=RUTA_DEFECTO)
    ap.add_argument("--out", default=SALIDA_DEFECTO)
    ap.add_argument("--aplicar", metavar="FILE",
                    help="write into the memory what the face collected")
    ap.add_argument("--idioma", choices=("en", "es"))
    # La voz es opcional por diseño. Si no está, la cara se genera igual y su
    # botón lo declara: una copia sin voz sigue siendo una copia entera.
    ap.add_argument("--piper", default=os.environ.get("AURELIUS_PIPER"),
                    help="path to the piper binary (child process, no socket)")
    ap.add_argument("--voz", default=os.environ.get("AURELIUS_VOZ"),
                    help="path to the signed voice model (.onnx)")
    ap.add_argument("--sin-voz", action="store_true",
                    help="generate without recording any audio")
    ap.add_argument("--turnos", metavar="FILE",
                    help="real turns produced by the resident child (json)")
    a = ap.parse_args(argv)

    est, rec = M.estado(a.db)
    if est == "SIN_ESQUEMA":
        print(M.mensaje_estado(est, rec), file=sys.stderr)
        return 1
    if a.aplicar:
        return aplicar(a.db, a.aplicar)

    piper = None if a.sin_voz else a.piper
    voz = None if a.sin_voz else a.voz
    turnos = None
    if a.turnos:
        with open(a.turnos, encoding="utf-8") as fh:
            turnos = json.load(fh)
    with M.abrir(a.db) as c:
        html = generar(c, a.db, a.idioma, piper=piper, modelo_voz=voz,
                       turnos=turnos)
    with open(a.out, "w", encoding="utf-8") as fh:
        fh.write(html)
    print(f"Face: {a.out}")
    print(f"  one file, {len(html) // 1024} KB, opens with a double click")
    print("  no network: the sprites, both languages and your memories are inside it")
    print("  voice: " + ("recorded into the page" if (piper and voz)
                         else "not recorded — the button says so"))
    return 0


if __name__ == "__main__":
    sys.exit(main())
