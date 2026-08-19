"""Con qué Python se está corriendo esto, y si está dentro de lo probado.

Un solo módulo lo decide, y lo consumen el producto (`aurelius.py`) y la tanda
de pruebas (`bin/pruebas`). Si cada uno llevara su propio rango, el día que se
pruebe una versión nueva habría que acertar en dos sitios, y bastaría fallar en
uno para que el README prometiera un rango y el programa declarara otro.

Regla: **declara, no bloquea.** Una versión fuera del rango probado no es una
versión rota — es una versión sobre la que no hay dato. Negarse a arrancar
convertiría una ausencia de medida en un veredicto, que es justo lo que este
árbol no hace con `NO_DATA` en ningún otro sitio.
"""
from __future__ import annotations

import sys

# Los CINCO puntos corridos enteros, no un intervalo elegido a ojo. Los dos
# extremos son los que definen el rango; los tres de en medio ya no se infieren
# -- se midieron con `uv` el 2026-08-16 y están en la tabla del README:
#   3.10.12 · 3.11.16 · 3.12.13 · 3.13.15 · 3.14.4
# `PROBADAS` sigue siendo el par de EXTREMOS y no la lista de cinco, porque es
# lo que se compara: el aviso nombra el rango, no el censo. `test_interprete`
# exige que ese par y MINIMA/MAXIMA no se separen nunca.
PROBADAS = ("3.10.12", "3.14.4")
MINIMA = (3, 10, 12)
MAXIMA = (3, 14, 4)


def actual():
    """La versión en curso como tupla de tres. Sin adivinar nada."""
    return tuple(sys.version_info[:3])


def dentro_del_rango(v=None):
    """¿Cae dentro de los extremos probados? Los extremos cuentan como dentro."""
    v = tuple(v) if v is not None else actual()
    return MINIMA <= v <= MAXIMA


def texto(v=None):
    """Las dos versiones probadas, escritas igual en todas partes."""
    return " / ".join(PROBADAS)


def _linea(idioma, puesta):
    if idioma == "es":
        return (f"NOTA · Python {puesta}. La tanda de pruebas se ha corrido en "
                f"{texto()}, no en esta.")
    return (f"NOTE · Python {puesta}. The test run has been done on "
            f"{texto()}, not on this one.")


def aviso(v=None, idioma=None):
    """La declaración, o `None` si no hay nada que declarar.

    Sin `idioma`, sale en los dos: esto ocurre ANTES de que nadie haya elegido,
    y elegir uno por la persona sería suponer — el mismo motivo por el que la
    primera pregunta de la sesión se hace en los dos a la vez.

    Con `idioma`, sale solo en ese. Quien ya firmó su idioma en el perfil no
    tiene por qué leer dos veces la misma frase, y en la pantalla de un teléfono
    esa cortesía se nota: son dos líneas de las primeras cuatro que ve.
    """
    if dentro_del_rango(v):
        return None
    v = tuple(v) if v is not None else actual()
    puesta = ".".join(str(n) for n in v)
    if idioma in ("es", "en"):
        return _linea(idioma, puesta)
    return _linea("es", puesta) + "\n" + _linea("en", puesta)
