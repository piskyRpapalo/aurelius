#!/usr/bin/env python3
"""narrador.py · el puente entre lo que el código hace y lo que se dice.

sistema: MVP · solo biblioteca estándar. Sin red, sin dependencias.

QUÉ ES, Y QUÉ NO ES
-------------------
No es un diccionario de traducción y no cambia una sola llamada: el código
sigue invocando `cruzar_frontera`, y lo que la persona lee es «la Cicatriz».
Es microcopía, y vive en su propio módulo porque `textos.py` gobierna las
cadenas de la sesión — mezclarlos haría que cambiar una palabra del juego
tocase el fichero de la interfaz.

Sirve a los dos estados del producto, y de la misma tabla:

* **Cerebro apagado** — la interfaz llama a `narrar()` y usa el alias directo.
* **Cerebro encendido** — el prompt del sistema lleva `glosario()`, para que el
  modelo adopte este vocabulario en vez de inventarse otro. Nótese que el
  glosario **no lleva los nombres internos**: enseñarle a un modelo que
  `cruzar_frontera` se llama «la Cicatriz» es enseñarle la palabra
  `cruzar_frontera`, y tarde o temprano la dice.

DE DÓNDE SALEN ESTOS NOMBRES
----------------------------
De `Cuarentena/salida/LORE_EVOLUTIVO_BASE_NOMBRES.md`, firmada como dirección
el 2026-08-19 (commit `31222dc` del repositorio interno). Esa base **no viaja
con el producto**: es doctrina, y el producto es un clon público que se abre
solo. Por eso la tabla se copia aquí, declarando su origen. Si la base cambia,
esto se actualiza a mano y a propósito — un alias que aparece sin haber sido
firmado es exactamente lo que este módulo existe para impedir.

EN QUÉ IDIOMA HABLA
-------------------
En español, y solo en español. La interfaz es bilingüe y lo seguirá siendo; la
voz del juego no. Los nombres del lore nacieron en español en la base firmada,
y traducir un nombre propio es cambiarlo. Fuera del español, `narrar()`
devuelve `NO_DATA` — no como hueco, sino como declaración.

LA REGLA QUE NO SE NEGOCIA
--------------------------
Un nombre que no está en la base firmada **no se inventa**: sale `NO_DATA`.
Nunca el nombre técnico crudo. Que a una mecánica le falte su nombre de juego
es un dato; enseñarle `promover_a_engrama` a quien está jugando es una fuga de
la cocina al comedor.
"""
from __future__ import annotations

AUSENTE = "NO_DATA"
DEFECTO = "es"

# Cada entrada: interno -> (alias, qué se dice cuando esa mecánica se dispara).
# La segunda mitad no es adorno: es lo que hace que el glosario enseñe el
# vocabulario SIN enseñar la función que hay debajo.
_ES = {
    # --- mecánicas ---------------------------------------------------------
    "memory.cruzar_frontera":      ("la Cicatriz",
                             "Algo quiso salir. Lo miré, y queda escrito qué lo paró."),
    "memory.escribir_engrama":     ("inscribir una Piedra",
                             "Queda inscrito con tus palabras. No las he tocado."),
    "memory.leer_engrama":         ("recordar",
                             "Esto lo escribiste tú."),
    "memory.proponer_borrador":    ("el Cuaderno se abre",
                             "Te propongo esto. No es tuyo hasta que lo firmes."),
    "memory.promover_a_engrama":   ("firmar la Piedra",
                             "Lo has firmado. Ahora es memoria."),
    "memory.descartar_borrador":   ("tachar",
                             "Tachado. La hoja se queda: tachar no es arrancar."),
    "memory.leer_borradores":      ("leer el Cuaderno",
                             "Esto es lo que te he propuesto y sigue esperando."),
    "memory.registrar_salida":     ("dejar Huella",
                             "Queda la huella de lo que salió."),
    "memory.resumen_salidas":      ("el Registro de Huellas",
                             "Esto salió, y esto se paró. Puedes enseñarlo entero."),
    "memory.exportar":             ("llevarse la Piedra",
                             "Aquí está, cubierto. Es tuyo y se va contigo."),
    "memory.importar":             ("Piedra de otro sitio",
                             "Viene de otra máquina. Conserva de dónde vino."),
    "memory.archivar":             ("guardar",
                             "No se borra. Se guarda, y vuelve cuando la llames."),
    "memory.desarchivar":          ("devolver a la luz",
                             "Vuelve a estar a la vista."),
    "memory.vista_arbol":          ("el Árbol de Piedras",
                             "Así se sostiene lo que llevas."),
    "memory.vista_recuento":       ("la Cuenta",
                             "Tantas piedras, tantos huecos declarados."),
    "memory.recuento_huecos":      ("los Huecos",
                             "Esto sigue sin contestar. No es un fallo: es una pregunta abierta."),
    "memory.escribir_enlace":      ("tender un Sendero",
                             "Estas dos se tocan, y ya lo dice el mapa."),
    "memory.respaldar":            ("la Copia Lejana",
                             "Una copia al lado del original no es una copia."),
    "memory.restaurar":            ("traer la Copia",
                             "Vuelve entera, o no vuelve."),
    "memory.asegurar_tablas":      ("ensanchar la Casa",
                             "Tu memoria es más vieja que esto. Le he hecho sitio sin tocar nada."),
    "memory.mision_completa":      ("el Sello",
                             "Está sellado."),
    "hilos.abrir":           ("abrir un Sendero",
                             "Queda abierto. No hace falta cerrarlo hoy."),
    "hilos.cerrar":          ("cerrar un Sendero",
                             "Cerrado."),
    "hilos.reabrir":         ("volver al Sendero",
                             "Vuelve a estar abierto. Nadie te ha quitado el sitio."),
    "hilos.aviso_sin_cerrar":     ("el Sendero espera",
                             "Hay senderos abiertos. El más viejo lleva un tiempo."),
    "cara.progreso_camino":      ("el Peldaño",
                             "Estás aquí, y esto es lo que se puede medir de aquí."),
    "fusible.inspeccionar":         ("el Fusible",
                             "Eso tiene forma de algo que quema."),
    "fusible.preparar_respuesta":   ("el Fusible salta",
                             "No paso eso. La forma es peligrosa."),
    "traza.generar":        ("la Traza",
                             "Qué entró, qué regla saltó, y qué decidí. Nada más."),
    "guardrails.redactar_salida":      ("el Velo",
                             "Va cubierto. Digo la clase y cuántas veces, nunca el trozo."),
    "andamio.ensamblar":            ("levantar el Andamio",
                             "Te monto la pregunta. Léela antes de usarla."),
    "andamio.marcar_inspeccionado": ("mirar el Andamio",
                             "Lo has mirado. Ahora puede salir."),

    # --- entidades ---------------------------------------------------------
    "engrams":              ("las Piedras", "Lo que has inscrito."),
    "borradores":           ("el Cuaderno del Game Master",
                             "Lo que te he propuesto. Ninguna es tuya hasta que la firmes."),
    "links":                ("los Senderos entre Piedras",
                             "Lo que has decidido que se toca."),
    "hilos":                ("las Sagas abiertas", "Lo que empezaste y sigue vivo."),
    "hilos_eventos":        ("la Crónica del Sendero",
                             "Abierto, cerrado, reabierto. Los tres siguen ahí."),
    "salidas":              ("las Huellas", "Todo lo que cruzó, y todo lo que no."),
    "profile":              ("el Espejo del Aprendiz",
                             "Esto es lo que me has dicho de ti. Lo demás está en blanco, y se ve."),
    "fuga_sala":            ("las Salas del Refugio", "Seis, y ninguna te pide prisa."),

    # --- leyes del mundo ---------------------------------------------------
    "V6":                   ("la Cicatriz no miente",
                             "Lo que se paró deja marca. Lo que se paró no se guarda."),
    "U7":                   ("el Nombre Protegido",
                             "Tu sendero sale, pero su secreto va cubierto."),
    "P-a":                  ("no hay puerta trasera",
                             "Solo hay una salida, y pasa por delante de ti."),
    "P-f":                  ("tu «no» no se anota",
                             "Has dicho que no. Eso es tuyo, y no queda escrito."),
    "B-b":                  ("solo el Aprendiz firma la Piedra",
                             "Yo no puedo firmarla. Para eso estás tú."),
    "B-c":                  ("tachar no es arrancar", "La hoja tachada se queda."),
    "D67":                  ("lo que sale, sale cubierto",
                             "Nombro lo que voy a descubrir, y decides tú, una por una."),
    "D69":                  ("el Cuaderno y la firma",
                             "Yo propongo. Tú firmas. En ese orden."),
    "cero_delete":          ("nada se arranca", "Aquí no se borra. Se archiva."),
    "NO_DATA":              ("el Silencio Honesto", "No lo sé. Eso también es un dato."),

    # --- pedagogía ---------------------------------------------------------
    "dry_run":              ("el Ensayo en Seco",
                             "Antes de que pase de verdad, mira lo que va a pasar."),
    "fallo_ramificacion":   ("el Fallo abre camino", "No ha salido. Y por aquí se sigue."),
    "objetivo_macro":       ("la Estrella Fija", "Esto es a lo que ibas. Sigue ahí."),
    "scaffolding_fading":   ("el Andamio que se retira",
                             "Ya no hace falta que te lo explique."),
    "retrieval":            ("recordar en voz alta",
                             "Dímelo tú antes de que te lo diga yo."),

    # --- los peldaños ------------------------------------------------------
    "M0": ("el Tótem",             "Le has puesto tu nombre."),
    "M1": ("el Fuego",             "Desde aquí no puedo saber si está encendido. No lo voy a suponer."),
    "M2": ("el Agua",              "La primera piedra está tallada."),
    "M3": ("el Refugio",           "Seis salas, y ninguna te pide prisa."),
    "M4": ("la Señal",             "Algo tuyo cruzó, y lo viste salir."),
    "M5": ("el Pacto",             "Dejaste un sendero abierto. Abierto es un estado, no una deuda."),
    "M6": ("el Bastión de Cobre",  "Algo se paró. Queda la marca; lo parado, no."),
    "M7": ("la Tierra",            "A partir de aquí explico menos, porque te hace menos falta."),
}

# EL JUEGO SE NARRA EN ESPAÑOL. Decisión del Soberano, 2026-08-19, y no un
# hueco pendiente de rellenar: el Narrador habla español y solo español.
#
# La interfaz sigue bilingüe entera —las dos columnas de `TEXTOS` están
# completas, y `test_idioma` lo vigila—, así que quien elige inglés recorre el
# producto en inglés. Lo que no cambia de idioma es la voz del juego: sus
# nombres nacieron en español en la base firmada, y traducir un nombre propio
# es cambiarlo.
#
# Por eso esta tabla no tiene columna inglesa y `narrar()` devuelve NO_DATA
# fuera del español. No es una ausencia por hacer: es la forma que tiene el
# código de decir que aquí no va nada más.
_EN: dict[str, tuple[str, str]] = {}

ALIAS = {"es": _ES, "en": _EN}


def _tabla(idioma):
    return ALIAS.get(idioma or "", ALIAS[DEFECTO] if idioma is None else {})


def narrar(interno, idioma=DEFECTO):
    """El nombre de juego de una mecánica, o `NO_DATA`. Jamás el nombre técnico.

    `interno` es la clave del árbol (`cruzar_frontera`, `engrams`, `M4`…). Un
    idioma que no conocemos y una clave que no está firmada acaban en el mismo
    sitio, y es el correcto: se declara la ausencia.
    """
    entrada = ALIAS.get(idioma, {}).get(interno)
    return entrada[0] if entrada else AUSENTE


def decir(interno, idioma=DEFECTO):
    """Lo que el Narrador dice cuando esa mecánica se dispara, o `NO_DATA`."""
    entrada = ALIAS.get(idioma, {}).get(interno)
    return entrada[1] if entrada else AUSENTE


def conocidos(idioma=DEFECTO):
    """Las claves con nombre firmado en ese idioma. Vacío es una respuesta."""
    return tuple(sorted(ALIAS.get(idioma, {})))


def glosario(idioma=DEFECTO):
    """El bloque que se pega al prompt del sistema cuando hay cerebro.

    Lleva el vocabulario y lo que significa; **no lleva los nombres internos**.
    Un modelo al que se le enseña la equivalencia aprende las dos palabras, y
    la que no debe decir la dice antes o después.

    Sin nombres firmados para ese idioma devuelve cadena vacía: es preferible
    un modelo sin glosario a un modelo con vocabulario inventado.
    """
    tabla = ALIAS.get(idioma, {})
    if not tabla:
        return ""
    lineas = ["Habla siempre con este vocabulario. No uses otro y no lo expliques:"]
    for clave in sorted(tabla):
        alias, dicho = tabla[clave]
        lineas.append(f"- {alias}: {dicho}")
    return "\n".join(lineas)
