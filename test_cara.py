#!/usr/bin/env python3
"""M2 · la cara · lo que tiene que ser verdad de una interfaz sin red.

sistema: MVP · solo biblioteca estandar.

La cara se GENERA: `cara.py` lee la memoria y escribe un HTML autocontenido.
Por eso casi todos estos casos son sobre el fichero generado y no sobre el
codigo que lo genera — lo que le llega a la persona es el HTML, y es ahi
donde una llamada de red o una palabra de la casa harian dano.

Ninguna prueba toca la memoria real: todas pasan --db a una base temporal.
"""
from __future__ import annotations

import os
import json
import re
import shutil
import subprocess
import sys
import tempfile

AQUI = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, AQUI)
import memory as M                          # noqa: E402
import textos as TX                         # noqa: E402

CASOS = []
TEMPORALES = []


def caso(nombre):
    def envoltorio(fn):
        CASOS.append((nombre, fn))
        return fn
    return envoltorio


# --- lo que no puede aparecer en la cara ----------------------------------

# El vocabulario de la casa. Vive en los comentarios del codigo interno, que
# lee el equipo; no puede vivir en la cara, que lee cualquiera (D67).
LEXICO_PRIVADO = ("soberano", "preceptor", "ironclaw", "hexelion")

# Todo lo que abre un socket. La cara se abre con doble clic desde el disco y
# tiene que funcionar entera sin una sola conexion (D68).
RED = (r"fetch\s*\(", r"XMLHttpRequest", r"WebSocket", r"EventSource",
       r"navigator\.sendBeacon", r"import\s*\(", r"https?://")

ASSETS = ("aurelius-talks.png", "aurelius-up.png")


def tmp_dir():
    d = tempfile.mkdtemp(prefix="aurelius_cara_")
    TEMPORALES.append(d)
    return d


def base_con_recuerdos(idioma=None):
    """Una memoria pequena pero con las dos cosas que importan: texto real y
    un hueco declarado."""
    ruta = os.path.join(tmp_dir(), "memory.db")
    M.crear(ruta)
    with M.abrir(ruta) as c:
        M.escribir_engrama(c, what="la impresora funciono al cambiar un cable",
                           why="llevaba un mes sin imprimir")
        M.escribir_engrama(c, what="recupere la base de datos de una copia")
        M.escribir_perfil(c, "device", "el portatil de la cocina")
        if idioma:
            M.escribir_perfil(c, "language", idioma)
    return ruta


def generar(ruta, extra=()):
    salida = os.path.join(tmp_dir(), "cara.html")
    proc = subprocess.run(
        [sys.executable, "cara.py", "--db", ruta, "--out", salida, *extra],
        cwd=AQUI, capture_output=True, text=True, timeout=120)
    assert proc.returncode == 0, \
        f"cara.py fallo ({proc.returncode}): {proc.stderr[-500:]}"
    return open(salida, encoding="utf-8").read(), salida


# --- los cinco que pidio la mision ----------------------------------------

@caso("1 · la cara no lleva ni una palabra del vocabulario de la casa")
def t1():
    html, _ = generar(base_con_recuerdos())
    bajo = html.lower()
    encontradas = [p for p in LEXICO_PRIVADO if p in bajo]
    assert not encontradas, f"la cara publica dice {encontradas}"


@caso("2 · la cara no hace ni una llamada de red, ni carga nada de fuera")
def t2():
    html, _ = generar(base_con_recuerdos())
    for patron in RED:
        hallado = re.findall(patron, html, re.I)
        assert not hallado, f"la cara llama a la red: {patron} -> {hallado[:3]}"
    # Y nada se carga de fuera del fichero: ni script, ni hoja, ni imagen.
    for etiqueta, atributo in (("script", "src"), ("link", "href"),
                               ("img", "src")):
        for valor in re.findall(rf'<{etiqueta}[^>]*\s{atributo}="([^"]*)"',
                                html, re.I):
            assert valor.startswith("data:"), \
                f"<{etiqueta}> carga algo de fuera: {valor[:60]}"


@caso("3 · la Pizarra lleva los recuerdos y se los puede llevar la persona")
def t3():
    ruta = base_con_recuerdos()
    html, _ = generar(ruta)
    with M.abrir(ruta) as c:
        filas = [dict(r) for r in c.execute("select what, why from engrams")]
    for fila in filas:
        assert fila["what"] in html, f"la Pizarra no lleva el recuerdo {fila['what']!r}"
    # El hueco declarado se ve declarado, no como celda vacia.
    assert M.AUSENTE in html, "la Pizarra esconde los huecos en vez de decirlos"
    # Y exportar es del navegador, sin servidor: un enlace con download.
    assert re.search(r'download\s*=', html, re.I), \
        "no hay forma de llevarse los recuerdos sin pedirselos a un servidor"


@caso("4 · el selector cambia las cadenas, y arranca en el idioma del perfil")
def t4():
    html, _ = generar(base_con_recuerdos(idioma="es"))
    # Las dos columnas viajan dentro del fichero: cambiar de idioma no puede
    # depender de ir a buscar la traduccion a ningun sitio.
    assert TX.TEXTOS["es"]["recuerdo_que"] in html, "el español no viaja en la cara"
    assert TX.TEXTOS["en"]["recuerdo_que"] in html, "el ingles no viaja en la cara"
    # Y arranca en lo que dice el perfil, no en lo que le apetezca a la cara.
    assert re.search(r'IDIOMA_INICIAL\s*=\s*"es"', html), \
        "la cara ignora el idioma que la persona ya eligio"
    en, _ = generar(base_con_recuerdos(idioma="en"))
    assert re.search(r'IDIOMA_INICIAL\s*=\s*"en"', en), \
        "la cara no respeta el ingles del perfil"


@caso("5 · ASSETS.md declara el mapa de fotogramas y el contrato de animacion")
def t5():
    ruta = os.path.join(AQUI, "ASSETS.md")
    assert os.path.exists(ruta), "no hay ASSETS.md"
    doc = open(ruta, encoding="utf-8").read()
    for nombre in ASSETS:
        assert nombre in doc, f"ASSETS.md no declara {nombre}"
    # Los cuatro fotogramas de cada hoja, descritos uno a uno.
    for trozo in ("boca abierta", "boca en \"o\"", "sonrisa",
                  "sin romper", "trozos volando"):
        assert trozo in doc, f"el mapa de fotogramas no describe: {trozo}"
    # El contrato, en el mismo sitio que el mapa.
    for trozo in ("up[1]", "up[1→2→3→4]", "talks[4]", "talks[1→2→3]"):
        assert trozo in doc, f"el contrato de animacion no menciona {trozo}"
    assert "local" in doc.lower(), "el contrato no dice que la animacion es local"


# --- lo que la mision implica y conviene fijar ----------------------------

@caso("6 · los dos assets existen con su nombre canonico y son PNG")
def t6():
    for nombre in ASSETS:
        ruta = os.path.join(AQUI, "assets", nombre)
        assert os.path.exists(ruta), f"falta assets/{nombre}"
        with open(ruta, "rb") as fh:
            assert fh.read(8) == b"\x89PNG\r\n\x1a\n", f"{nombre} no es un PNG"


@caso("7 · la cara respeta el contrato de animacion, y lo hace sin red")
def t7():
    html, _ = generar(base_con_recuerdos())
    # Los dos sprites viajan incrustados, no enlazados.
    assert html.count("data:image/png;base64,") >= 2, \
        "los sprites no viajan dentro del fichero"
    # El contrato, tal como se escribio: dormido, despertar una vez, reposo,
    # bucle al hablar. Se comprueba que el codigo nombra los cuatro estados.
    for estado in ("dormido", "despertar", "reposo", "hablando"):
        assert estado in html, f"la cara no implementa el estado {estado!r}"
    # Despertar ocurre UNA vez: el codigo tiene que apagar su propia bandera.
    assert re.search(r"despertado\s*=\s*true", html, re.I), \
        "nada impide que el despertar se repita en cada frase"


@caso("8 · la cara se genera sin tocar la memoria real de la persona")
def t8():
    import inspect
    assert '"--db", ruta' in inspect.getsource(generar), \
        "generar() dejo de fijar la base: una prueba podria ir a la memoria real"
    real = os.path.expanduser("~/.aurelius")

    def foto():
        if not os.path.isdir(real):
            return None
        return sorted((n, os.stat(os.path.join(real, n)).st_mtime_ns)
                      for n in os.listdir(real))

    antes = foto()
    generar(base_con_recuerdos())
    assert foto() == antes, "generar la cara toco la memoria real"


@caso("9 · el modo formulario escribe lo que la cara recogio, sin borrar nada")
def t9():
    ruta = base_con_recuerdos()
    with M.abrir(ruta) as c:
        antes = c.execute("select count(*) from engrams").fetchone()[0]
        resumen = M.aplicar_formulario(c, {
            "language": "es",
            "profile": {"name": "David"},
            "engrams": [{"what": "un recuerdo que llego por el formulario",
                         "why": "", "where_ref": "", "learned": ""}],
        })
        despues = c.execute("select count(*) from engrams").fetchone()[0]
        assert despues == antes + 1, f"el formulario escribio {despues - antes} filas"
        assert M.leer_perfil(c, "language") == "es", "el idioma no llego al perfil"
        assert M.leer_perfil(c, "name") == "David", "el perfil no recogio el nombre"
        assert resumen["engrams"] == 1, f"el resumen miente: {resumen}"
        # Lo que ya estaba sigue estando: un formulario no es un reemplazo.
        primeros = [r[0] for r in c.execute("select what from engrams order by id")]
        assert primeros[0] == "la impresora funciono al cambiar un cable", \
            "el formulario piso lo que ya habia"


@caso("10 · el formulario no borra ni archiva, pase lo que pase")
def t10():
    import inspect
    fuente = inspect.getsource(M.aplicar_formulario)
    for prohibido in ("delete", "drop", "truncate"):
        assert prohibido not in fuente.lower(), \
            f"el modo formulario contiene {prohibido!r}"
    # Un formulario vacio no es una orden de vaciar: no escribe nada y lo dice.
    ruta = base_con_recuerdos()
    with M.abrir(ruta) as c:
        antes = c.execute("select count(*) from engrams").fetchone()[0]
        resumen = M.aplicar_formulario(c, {})
        despues = c.execute("select count(*) from engrams").fetchone()[0]
    assert antes == despues, "un formulario vacio cambio la memoria"
    assert resumen["engrams"] == 0, f"el resumen miente: {resumen}"


@caso("11 · la cara no inventa recuerdos: sin memoria, lo dice y no rellena")
def t11():
    ruta = os.path.join(tmp_dir(), "memory.db")
    M.crear(ruta)
    html, _ = generar(ruta)
    assert "0" in html, "una memoria vacia no declara su recuento"
    for inventado in ("la impresora", "lorem ipsum", "example memory"):
        assert inventado not in html.lower(), \
            f"la cara trae un recuerdo de ejemplo: {inventado!r}"


@caso("12 · el botón de audio está desde el primer arranque, con voz o sin ella")
def t12():
    # Sin voz grabada: el botón EXISTE igual y declara que esta copia no habla.
    # Un control que aparece solo cuando la función está disponible enseña a la
    # persona que el producto cambia de forma, y deja de poder confiarse de él.
    html, _ = generar(base_con_recuerdos())
    assert 'id="b-voz"' in html, "no hay botón de audio en la cara"
    for idioma in ("en", "es"):
        assert TX.TEXTOS.get(idioma) is not None
    for clave in ("voz_hablar", "voz_callar", "voz_no_hay"):
        assert clave in html, f"el botón no trae el rótulo {clave}"
    assert 'aria-pressed' in html, "el botón no dice si está pulsado"


@caso("13 · el texto se ve siempre; el botón solo decide si además suena")
def t13():
    html, _ = generar(base_con_recuerdos())
    # La función que escribe la burbuja no puede depender del estado de la voz.
    cuerpo = re.search(r"function dice\(texto, hecho, clave\) \{(.*?)\n\}",
                       html, re.S)
    assert cuerpo, "no se encuentra la función que escribe lo que se dice"
    assert "hablaViva" not in cuerpo.group(1), \
        "escribir el texto depende del botón de voz: el texto debe estar siempre"
    assert "suena(clave)" in cuerpo.group(1), "el sonido no está enganchado"


@caso("14 · en instalación limpia el Camino está a cero y no finge progreso")
def t14():
    ruta = os.path.join(tmp_dir(), "memory.db")
    M.crear(ruta)                       # base recién hecha: nadie ha contestado
    html, _ = generar(ruta)
    estado = json.loads(re.search(r"var DATOS = (\{.*?\});\n", html, re.S).group(1))
    camino = estado["camino"]
    # Se comprueban los VALORES, no la forma del dict: añadir un contador nuevo
    # es legítimo; que un contador mienta en limpio, no.
    for clave, valor in camino["cifras"].items():
        assert valor in (0, False), \
            f"una instalación limpia declara {clave}={valor}"
    hechos = [p for p, e in camino["estado"].items() if e == "hecho"]
    assert not hechos, f"en limpio ya hay peldaños dados por hechos: {hechos}"
    # Los dos que no se pueden medir lo DICEN. M1 porque el cerebro no vive
    # dentro del fichero; M7 porque nadie ha escrito qué cuenta como éxito
    # firmado. Declararlos es más honesto que pintarlos sin empezar.
    for p in ("M1", "M7"):
        assert camino["estado"][p] == "no_medible", \
            f"{p} no se puede medir y no se declara como tal"
    assert all(camino["estado"][p] == "sin_empezar"
               for p in ("M3", "M4", "M5", "M6")), \
        "hay peldaños con estado inventado"
    # Y el camino es modular: núcleo y opcionales, sin solaparse.
    assert camino["nucleo"] == ["M0", "M1", "M2"], \
        f"el núcleo cambió sin decirlo: {camino['nucleo']}"
    assert camino["opcionales"] == ["M3", "M4", "M5", "M6", "M7"], \
        f"las side quests cambiaron sin decirlo: {camino['opcionales']}"
    assert not set(camino["nucleo"]) & set(camino["opcionales"]), \
        "un peldaño no puede ser obligatorio y opcional a la vez"
    assert camino["punto_decision"] is False, \
        "en limpio no hay nada que decidir: el núcleo no está hecho"


@caso("15 · cada peldaño enseña QUÉ lo da por hecho, y cómo refrescar")
def t15():
    html, _ = generar(base_con_recuerdos())
    for clave in ("cm_prueba_M0", "cm_prueba_M1", "cm_prueba_M2",
                  "cm_pendiente", "cm_refrescar"):
        assert clave in html, f"el Camino no trae {clave}"
    # Y el progreso se mueve con la memoria, no con el calendario.
    estado = json.loads(re.search(r"var DATOS = (\{.*?\});\n", html, re.S).group(1))
    assert estado["camino"]["cifras"]["recuerdos"] == 2, \
        "el Camino no cuenta los recuerdos que hay"
    assert estado["camino"]["estado"]["M2"] == "empezado", \
        "con recuerdos y sin sello, el Agua debería estar empezada, no hecha"


@caso("16 · la voz viaja incrustada y sigue sin abrir un socket")
def t16():
    import shutil as _sh
    piper = os.path.expanduser("~/aurelius-m1/venv/bin/piper")
    voz = os.path.expanduser("~/aurelius-m1/voces/es_ES-sharvard-medium.onnx")
    if not (os.path.exists(piper) and os.path.exists(voz)):
        return          # sin voz instalada no hay nada que comprobar aquí
    ruta = base_con_recuerdos()
    salida = os.path.join(tmp_dir(), "cara.html")
    proc = subprocess.run(
        [sys.executable, "cara.py", "--db", ruta, "--out", salida,
         "--piper", piper, "--voz", voz],
        cwd=AQUI, capture_output=True, text=True, timeout=600)
    assert proc.returncode == 0, f"cara.py con voz falló: {proc.stderr[-400:]}"
    html = open(salida, encoding="utf-8").read()
    assert "data:audio/wav;base64," in html, "la voz no viajó dentro del fichero"
    for patron in RED:
        assert not re.findall(patron, html, re.I), \
            f"la cara con voz llama a la red: {patron}"


@caso("17 · los dos filtros existen y el lore pasa los dos guardianes")
def t17():
    arq = open(os.path.join(AQUI, "ARQUETIPO.md"), encoding="utf-8").read()
    for filtro in ("`rapido`", "`lector`"):
        assert filtro in arq, f"el arquetipo no declara el filtro {filtro}"
    assert "read aloud" in arq and "en voz alta" in arq, \
        "el arquetipo no dice que lo leen en voz alta"
    lore = open(os.path.join(AQUI, "LORE.md"), encoding="utf-8").read()
    for doc, nombre in ((arq, "ARQUETIPO.md"), (lore, "LORE.md")):
        bajo = doc.lower()
        assert not [p for p in LEXICO_PRIVADO if p in bajo], \
            f"{nombre} lleva vocabulario de la casa"
        for termino in ("temple", "ollama", "gguf"):
            assert termino not in bajo, f"{nombre} nombra {termino!r}"


@caso("18 · toda clave del lore apunta a una pieza que existe de verdad")
def t18():
    import lore as L
    disponibles = L.piezas()
    assert len(disponibles) >= 8, f"solo se leyeron {len(disponibles)} piezas"
    faltan = [t for t in L.CLAVES if t not in disponibles]
    # Esta errata ya ocurrio: un titulo sin tilde no casaba con LORE.md y esa
    # pieza no salia nunca, en silencio. El silencio es el problema.
    assert not faltan, f"claves que no apuntan a ninguna pieza: {faltan}"
    for titulo, textos in disponibles.items():
        for idioma in ("en", "es"):
            assert textos.get(idioma), f"{titulo} no tiene version {idioma}"


@caso("19 · el lore no se fuerza, no se repite, y sale literal del fichero")
def t19():
    import lore as L
    assert L.elegir("háblame de gatos", "es") is None, \
        "se forzo una pieza donde no venia a cuento"
    primera = L.elegir("¿por qué guardar una copia en otro sitio?", "es")
    assert primera, "no eligio pieza para un tema que si esta cubierto"
    titulo, texto = primera
    # Literal: lo que lee la persona es lo que alguien reviso, sin pasar por
    # ningun modelo. Esa es toda la razon de que este modulo exista.
    assert texto == L.piezas()[titulo]["es"], "la pieza salio alterada"
    otra = L.elegir("¿por qué guardar una copia en otro sitio?", "es",
                    usadas={titulo})
    assert otra is None or otra[0] != titulo, "repitio la pieza ya usada"


@caso("20 · la cara acepta turnos reales del residente, con su voz y sin red")
def t20():
    ruta = base_con_recuerdos()
    turnos = [{"tu": "¿y si se me rompe el disco?",
               "el": "Entonces no la tendrías ahí. Pero sí en otro sitio.",
               "audio": "data:audio/wav;base64,UklGRiQAAABXQVZF",
               "lore": "El banco de semillas de Svalbard existe porque…"}]
    ruta_turnos = os.path.join(tmp_dir(), "turnos.json")
    with open(ruta_turnos, "w", encoding="utf-8") as fh:
        json.dump(turnos, fh, ensure_ascii=False)
    html, _ = generar(ruta, extra=("--turnos", ruta_turnos, "--sin-voz"))
    assert turnos[0]["el"] in html, "la cara no muestra la respuesta real"
    assert turnos[0]["lore"] in html, "la cara pierde el párrafo del lector"
    assert "reproduce(turno.audio)" in html, \
        "el botón no reproduce el audio del turno real"
    for patron in RED:
        assert not re.findall(patron, html, re.I), \
            f"la cara con turnos llama a la red: {patron}"


@caso("21 · lo que se oye se limpia; lo que se muestra no se toca")
def t21():
    import cara as C
    crudo = "Por si se borra.  \n  Por si la pierdes.  \n\n  *Por si* la quieres."
    dicho = C.para_voz(crudo)
    assert "\n" not in dicho and "*" not in dicho, f"quedan marcas de página: {dicho!r}"
    assert "  " not in dicho, "quedan dobles espacios, que la voz lee como pausa"
    # Y no se pierde ni se añade una palabra: la limpieza es de marcas, no de
    # contenido. Un filtro de voz que edita lo dicho deja de ser un filtro.
    palabras = lambda t: [w for w in re.sub(r"[*_`#>]", " ", t).split() if w]
    assert palabras(dicho) == palabras(crudo), \
        f"la limpieza cambió las palabras: {palabras(crudo)} -> {palabras(dicho)}"
    # Lo mostrado sale del texto original, no del limpiado.
    html, _ = generar(base_con_recuerdos())
    assert "para_voz" not in re.search(r"function dice\(.*?\n\}", html, re.S).group(0), \
        "la burbuja pasa por la limpieza de voz: el texto mostrado debe ser el original"


# --- calidad de la cara en un telefono · R1-R6 -----------------------------
# Android primero: la cara se abre con doble clic, pero se LEE en la mano. Lo
# que sigue es lo que tiene que ser verdad del HTML generado antes de que nadie
# la juzgue en una pantalla de 360 px.

ANCHO_MINIMO = 360          # el estrecho que hay que aguantar sin scroll lateral
TACTIL_MINIMO = 44          # px de lado; por debajo, el dedo falla y la culpa es nuestra


def _estilo(html):
    """El bloque <style> entero, que es donde vive la culpa de la maquetacion."""
    m = re.search(r"<style>(.*?)</style>", html, re.S | re.I)
    assert m, "la cara no lleva hoja de estilo"
    return m.group(1)


def _reglas(css):
    """[(selector, cuerpo)] de la hoja, sin entrar en las media queries."""
    return re.findall(r"([^{}@]+)\{([^{}]*)\}", css)


@caso("22 · R1 · la cara declara el viewport, o el telefono la dibuja a 980 px")
def t22():
    html, _ = generar(base_con_recuerdos())
    m = re.search(r'<meta\s+name="viewport"\s+content="([^"]*)"', html, re.I)
    assert m, "sin <meta viewport> el movil finge ser un escritorio y encoge todo"
    contenido = m.group(1).replace(" ", "")
    assert "width=device-width" in contenido, f"viewport sin device-width: {m.group(1)}"
    assert "initial-scale=1" in contenido, f"viewport sin initial-scale=1: {m.group(1)}"


@caso("23 · R2 · el cabeceo no lleva anchos fijos, y nada obliga a pasar de 360 px")
def t23():
    html, _ = generar(base_con_recuerdos())
    css = _estilo(html)

    # El marco del busto es lo unico del cabeceo con medida propia. Si la lleva
    # en px, el cabeceo deja de caber antes que el resto y arrastra la pagina.
    for selector, cuerpo in _reglas(css):
        if ".marco" not in selector:
            continue
        fijos = re.findall(r"\b(width|height)\s*:\s*(\d+)px", cuerpo)
        assert not fijos, \
            f"el cabeceo lleva medida fija ({selector.strip()}): {fijos}"

    # El cabeceo tiene que ENVOLVER. Esta es la guarda que faltaba: la primera
    # version de este rojo miraba solo `.marco` y los min-width, paso en verde,
    # y el navegador midio 248px de scroll lateral a 360px porque la fila de
    # botones no envolvia. Un test que puede estar verde con la pagina rota no
    # es un test: es un adorno.
    cabeceo = [c for sel, c in _reglas(css) if sel.strip() == "header"]
    assert cabeceo, "no hay regla para <header>"
    assert re.search(r"flex-wrap\s*:\s*wrap", cabeceo[0]), \
        "el cabeceo no envuelve: en un telefono estrecho arrastra la pagina a lo ancho"

    # Y ninguna regla puede EXIGIR mas ancho del que hay.
    for prop, valor in re.findall(r"\bmin-width\s*:\s*(\d+)px", css) and \
            [("min-width", v) for v in re.findall(r"\bmin-width\s*:\s*(\d+)px", css)] or []:
        assert int(valor) <= ANCHO_MINIMO, \
            f"{prop}:{valor}px obliga a scroll lateral en un telefono de {ANCHO_MINIMO}px"


@caso("24 · R3 · lo que la cara recoge se lo lleva un fichero, no un comando")
def t24():
    html, _ = generar(base_con_recuerdos())

    # El JSON se descarga desde la propia pagina, sin red y sin ayuda.
    assert re.search(r'download="[^"]*\.json"', html, re.I), \
        "no hay enlace de descarga con nombre .json"
    assert "createObjectURL" in html, \
        "el fichero no se fabrica en la pagina: sin createObjectURL no hay descarga local"

    # Y no se le manda a nadie a abrir una terminal. Quien llega a la cara desde
    # un telefono no tiene una, y decirselo convierte el producto en un requisito.
    assert "terminal" not in html.lower(), \
        "la cara manda abrir una terminal: en un telefono eso es un callejon sin salida"


@caso("25 · R4 · ni un src ni un href que salga de este fichero")
def t25():
    html, _ = generar(base_con_recuerdos())
    for etiqueta, atributo in (("script", "src"), ("link", "href"),
                               ("img", "src"), ("a", "href"),
                               ("source", "src"), ("iframe", "src")):
        for valor in re.findall(rf'<{etiqueta}[^>]*\s{atributo}="([^"]*)"', html, re.I):
            assert not re.match(r"(?i)\s*(https?:)?//", valor), \
                f"<{etiqueta} {atributo}> apunta fuera: {valor[:60]}"


@caso("26 · R5 · idioma declarado, el boton dice su nombre, y el dedo acierta")
def t26():
    html, _ = generar(base_con_recuerdos("es"))

    # El idioma del documento es el de la sesion, no el que se quedo escrito.
    # Un lector de pantalla lee en el idioma que diga aqui, no en el que vea.
    m = re.search(r'<html\s+lang="([^"]*)"', html, re.I)
    assert m, "el <html> no declara lang"
    assert m.group(1).lower().startswith("es"), \
        f'sesion en espanol y el documento declara lang="{m.group(1)}"'

    # Hablar tiene rotulo accesible propio: su texto cambia (Hablar/Callar) y
    # aria-pressed dice el estado, pero sin nombre no se puede pedir por voz.
    boton = re.search(r'<button[^>]*id="b-voz"[^>]*>', html, re.I)
    assert boton, "no existe el boton de voz"
    assert "aria-label" in boton.group(0), \
        f"el boton Hablar no tiene aria-label: {boton.group(0)}"

    # Nada que se toque con el dedo por debajo del minimo.
    css = _estilo(html)
    for selector, cuerpo in _reglas(css):
        if not re.search(r"\.boton|\.enviar|select", selector):
            continue
        for alto in re.findall(r"\bmin-height\s*:\s*(\d+)px", cuerpo):
            assert int(alto) >= TACTIL_MINIMO, \
                f"{selector.strip()} mide {alto}px de alto; el minimo tactil es {TACTIL_MINIMO}"


@caso("27 · R6 · la cara declara cuanta voz lleva dentro, y el numero cuadra")
def t27():
    html, _ = generar(base_con_recuerdos())
    m = re.search(r'<meta\s+name="aurelius:audio"\s+content="(\d+)"', html, re.I)
    assert m, ("la cara no declara cuantos clips lleva; sin numero declarado, "
               "una voz que falta no se distingue de una voz que no se grabo")
    declarados = int(m.group(1))
    reales = len(re.findall(r"data:audio/wav;base64,", html))
    assert declarados == reales, \
        f"declara {declarados} clips de voz y lleva {reales}"


# --- el camino modular · nucleo, decision, side quests --------------------

def _camino(html):
    return json.loads(re.search(r"var DATOS = (\{.*?\});\n", html, re.S).group(1))["camino"]


@caso("28 · cada side quest se enciende con lo que la mide, y solo con eso")
def t28():
    """Hasta hoy M3-M7 estaban fijas en sin_empezar: nadie las miraba.

    Cada una tiene ahora su medida en la memoria. Este caso enciende una sola y
    comprueba que las hermanas NO se contagian — un peldaño que se enciende por
    lo que hizo otro es una barra de carga con pasos.
    """
    import guardrails
    import hilos as H

    # M5 · un sendero abierto, y nada mas
    ruta = base_con_recuerdos()
    with M.abrir(ruta) as c:
        H.abrir(c, "trabajo en progreso", origen_dispositivo="pc")
    camino = _camino(generar(ruta)[0])
    assert camino["estado"]["M5"] == "hecho", "abrir un hilo debe encender M5"
    for otro in ("M3", "M4", "M6"):
        assert camino["estado"][otro] == "sin_empezar", \
            f"{otro} se encendio sin que nadie lo hiciera"

    # M4 · una salida que cruzo de verdad
    ruta = base_con_recuerdos()
    with M.abrir(ruta) as c:
        M.cruzar_frontera(c, "cli_export", "texto que cruza",
                          guardrails.preparar_envio)
    camino = _camino(generar(ruta)[0])
    assert camino["estado"]["M4"] == "hecho", "una salida real debe encender M4"
    assert camino["estado"]["M6"] == "sin_empezar", \
        "una salida limpia no es una cicatriz"

    # M6 · una cicatriz: el filtro paro algo y quedo constancia
    ruta = base_con_recuerdos()
    original = guardrails._politicas_efectivas
    try:
        guardrails._politicas_efectivas = lambda: []
        with M.abrir(ruta) as c:
            try:
                M.cruzar_frontera(c, "ia_externa", "algo con secreto",
                                  guardrails.preparar_envio)
            except guardrails.EnvioBloqueado:
                pass
    finally:
        guardrails._politicas_efectivas = original
    camino = _camino(generar(ruta)[0])
    assert camino["estado"]["M6"] == "hecho", "un bloqueo debe encender M6"
    assert camino["estado"]["M4"] == "sin_empezar", \
        "lo que se paro no salio: M4 no puede darse por hecho"

    # M3 · las seis salas de la fuga
    ruta = base_con_recuerdos()
    with M.abrir(ruta) as c:
        c.executescript("""
            create table if not exists fuga_sala (
                sala integer primary key, nombre text not null default 'NO_DATA',
                entrado_en text not null default (datetime('now')),
                salido_en text not null default 'NO_DATA',
                minutos integer not null default -1,
                estado text not null default 'entrada',
                concepto text not null default 'NO_DATA');""")
        for i in range(1, 4):
            c.execute("insert into fuga_sala (sala, estado) values (?, 'completada')", (i,))
        c.commit()
    camino = _camino(generar(ruta)[0])
    assert camino["estado"]["M3"] == "empezado", \
        f"tres salas de seis es empezado, no {camino['estado']['M3']}"
    assert camino["cifras"]["salas"] == 3


@caso("29 · el nucleo abre la decision, y las side quests siguen sin hacerse")
def t29():
    """Terminar el nucleo no arrastra a nadie por las cinco opcionales."""
    ruta = base_con_recuerdos()
    # El sello de M2 es un fichero al lado de la memoria.
    open(os.path.join(os.path.dirname(ruta), "manifest-latest.txt"), "w").close()

    camino = _camino(generar(ruta)[0])
    assert camino["estado"]["M2"] == "hecho", "con recuerdos y sello, M2 esta hecho"
    assert camino["punto_decision"] is True, \
        "acabado el nucleo, la decision tiene que estar abierta"
    sin_hacer = [p for p in camino["opcionales"]
                 if camino["estado"][p] in ("sin_empezar", "no_medible")]
    assert len(sin_hacer) == 5, \
        f"las cinco side quests siguen sin hacerse; estan {sin_hacer}"


@caso("30 · la cara dice cual es nucleo, cual opcional, y que deja cada una")
def t30():
    """Un peldano opcional sin ventaja declarada es un peldano que nadie elige."""
    html, _ = generar(base_con_recuerdos("es"))
    for clave in ("cm_opcional", "cm_nucleo", "cm_decision"):
        assert clave in html, f"falta el rotulo {clave}"
    for p in ("M3", "M4", "M5", "M6", "M7"):
        assert f"cm_ventaja_{p}" in html, f"{p} no declara que deja para el proyecto"
        assert f"cm_prueba_{p}" in html, f"{p} no dice que lo da por hecho"


def main():
    fallos = 0
    print("── M2 · LA CARA " + "─" * 50)
    for nombre, fn in CASOS:
        try:
            fn()
            print(f"  ok    · {nombre}")
        except AssertionError as e:
            fallos += 1
            print(f"  FALLO · {nombre}\n          -> {e}")
        except Exception as e:
            fallos += 1
            print(f"  ERROR · {nombre}\n          -> {type(e).__name__}: {e}")
    for d in TEMPORALES:
        shutil.rmtree(d, ignore_errors=True)
    total = len(CASOS)
    print(f"\nRESULTADO: {total - fallos}/{total} correctos, {fallos} fallo(s)")
    return 1 if fallos else 0


if __name__ == "__main__":
    sys.exit(main())
