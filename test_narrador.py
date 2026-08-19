#!/usr/bin/env python3
"""La capa de alias · Batería Roja N-a…N-e.

Rojo N-a: nada de lo que el Narrador emite lleva un nombre técnico crudo.
Rojo N-b: el glosario del prompt tampoco — ni siquiera como equivalencia.
Rojo N-c: una clave sin firmar sale NO_DATA, jamás el nombre interno.
Rojo N-d: un idioma sin nombres firmados sale NO_DATA, y el glosario vacío.
Rojo N-e: no se inventan claves — cada una resuelve a algo real del árbol.

El corazón de los dos primeros: la cocina no se enseña en el comedor. Un
producto que llama «cruzar_frontera» a lo que la persona vive como la Cicatriz
puede tener el mejor lore del mundo y lo rompe en la primera frase.

sistema: MVP · solo biblioteca estándar. Sin red, sin dependencias.
"""
from __future__ import annotations

import os
import re
import sys
import unittest

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import narrador as N


# Los nombres que jamás pueden asomar: los de las funciones, los de las tablas
# y los identificadores de los rojos. Se derivan de la propia tabla, así que
# añadir una clave nueva amplía la vigilancia sola.
def _crudos():
    """Lo que es INEQUÍVOCAMENTE un identificador, y nada más.

    La primera versión de este test prohibía también la parte suelta de cada
    función, y se puso roja con «abrir un Sendero»: `abrir` es a la vez
    `hilos.abrir` y un verbo corriente. Prohibir los verbos comunes no protege
    nada y deja el lore sin español.

    La línea correcta: un identificador se reconoce por su forma —lleva punto o
    guion bajo— o por ser una palabra que en castellano no diría nadie
    (`engrams`, `profile`). `hilos`, `salidas` y `borradores` son nombres de
    tabla Y palabras normales: que el lore prefiera «Sagas», «Huellas» y
    «Cuaderno» es estilo, no fuga, y un test no debe confundir las dos cosas.
    """
    crudos = set()
    for tabla in N.ALIAS.values():
        for clave in tabla:
            if "." in clave or "_" in clave:
                crudos.add(clave)
            if "." in clave:
                modulo, funcion = clave.split(".", 1)
                if "_" in funcion:
                    crudos.add(funcion)
                crudos.add(modulo + ".py")
    # Identificadores que ninguna frase castellana produciría por accidente.
    crudos.update({"engrams", "profile", "links", "hilos_eventos", "fuga_sala",
                   "sqlite", "SELECT", "insert into", "def ", "self."})
    return crudos


CRUDOS = _crudos()

# Claves que no son funciones ni tablas: leyes y piezas de pedagogía. Van
# declaradas a mano a propósito — si alguien añade una, este test le obliga a
# decir que la ha añadido.
CONCEPTOS = {
    "V6", "U7", "P-a", "P-f", "B-b", "B-c", "D67", "D69",
    "cero_delete", "NO_DATA", "dry_run", "fallo_ramificacion",
    "objetivo_macro", "scaffolding_fading", "retrieval",
}

MODULOS = ("memory", "hilos", "cara", "fusible", "traza", "guardrails", "andamio")


def _asoma(texto, crudo):
    """¿Aparece ese identificador como palabra suelta en el texto?"""
    return re.search(r"(?<![\w.])" + re.escape(crudo) + r"(?![\w])", texto) is not None


class TestCapaDeAlias(unittest.TestCase):

    # ------------------------------------------------------------------
    # Rojo N-a: lo que se dice no lleva cocina
    # ------------------------------------------------------------------
    def test_rojo_na_nada_emitido_lleva_nombre_crudo(self):
        """Ni el alias ni la frase pueden contener un nombre técnico."""
        for idioma, tabla in N.ALIAS.items():
            for clave in tabla:
                for salida in (N.narrar(clave, idioma), N.decir(clave, idioma)):
                    for crudo in CRUDOS:
                        self.assertFalse(
                            _asoma(salida, crudo),
                            f"[{idioma}] {clave} emite el nombre técnico "
                            f"{crudo!r}: {salida!r}")

    # ------------------------------------------------------------------
    # Rojo N-b: el glosario enseña vocabulario, no equivalencias
    # ------------------------------------------------------------------
    def test_rojo_nb_el_glosario_no_lleva_los_internos(self):
        """Enseñarle al modelo la equivalencia es enseñarle la palabra prohibida.

        Si el prompt dice «cruzar_frontera se llama la Cicatriz», el modelo
        conoce las dos y tarde o temprano dice la primera.
        """
        for idioma in N.ALIAS:
            texto = N.glosario(idioma)
            for crudo in CRUDOS:
                self.assertFalse(
                    _asoma(texto, crudo),
                    f"[{idioma}] el glosario del prompt lleva {crudo!r}")

    def test_rojo_nb_el_glosario_si_lleva_los_alias(self):
        """Y sirve para algo: el vocabulario firmado está dentro."""
        texto = N.glosario("es")
        self.assertTrue(texto, "con nombres firmados el glosario no puede ir vacío")
        for clave in ("memory.cruzar_frontera", "M0", "engrams"):
            self.assertIn(N.narrar(clave, "es"), texto,
                          f"el glosario no enseña el nombre de {clave}")

    # ------------------------------------------------------------------
    # Rojo N-c: lo no firmado se declara
    # ------------------------------------------------------------------
    def test_rojo_nc_clave_sin_firmar_es_no_data(self):
        """Una mecánica sin nombre de juego se declara; no se traduce a pelo."""
        for inventada in ("memory.borrar_todo", "hilos.fusionar", "M9", "XYZ"):
            self.assertEqual(N.narrar(inventada, "es"), N.AUSENTE)
            self.assertEqual(N.decir(inventada, "es"), N.AUSENTE)
            self.assertFalse(_asoma(N.narrar(inventada, "es"), inventada),
                             "ni siquiera al fallar se dice el nombre interno")

    # ------------------------------------------------------------------
    # Rojo N-d: un idioma sin firmar no improvisa
    # ------------------------------------------------------------------
    def test_rojo_nd_idioma_sin_nombres_declara_ausencia(self):
        """Sin vocabulario firmado, NO_DATA y glosario vacío.

        Hoy el inglés está en esa situación y se ve. Preferimos un modelo sin
        glosario a un modelo con vocabulario inventado.
        """
        for idioma in ("en", "fr", ""):
            self.assertEqual(N.narrar("memory.cruzar_frontera", idioma), N.AUSENTE)
            self.assertEqual(N.glosario(idioma), "",
                             f"[{idioma}] sin nombres firmados no hay glosario")

    # ------------------------------------------------------------------
    # Rojo N-e: no se inventan claves
    # ------------------------------------------------------------------
    def test_rojo_ne_cada_clave_resuelve_a_algo_real(self):
        """Una clave que no existe en el árbol es un alias sin mecánica debajo."""
        import importlib
        cargados = {m: importlib.import_module(m) for m in MODULOS}
        aqui = os.path.dirname(os.path.abspath(__file__))
        esquema = ""
        for fichero in ("memory.py", "fuga.py"):
            with open(os.path.join(aqui, fichero), encoding="utf-8") as fh:
                esquema += fh.read()
        tablas = set(re.findall(r"(?i)create table if not exists (\w+)", esquema))
        peldanos = set(cargados["cara"].PELDANOS)

        for clave in N.conocidos("es"):
            if "." in clave:
                modulo, funcion = clave.split(".", 1)
                self.assertIn(modulo, cargados, f"{clave}: módulo desconocido")
                self.assertTrue(
                    callable(getattr(cargados[modulo], funcion, None)),
                    f"{clave} no existe en el árbol: alias sin mecánica debajo")
            elif clave in peldanos or clave in CONCEPTOS:
                continue
            else:
                self.assertIn(clave, tablas,
                              f"{clave} no es función, ni tabla, ni peldaño, ni "
                              f"concepto declarado")

    def test_rojo_ne_los_ocho_peldanos_tienen_nombre(self):
        """El Camino se narra entero: ocho peldaños, ocho nombres firmados."""
        import cara
        for peldano in cara.PELDANOS:
            self.assertNotEqual(
                N.narrar(peldano, "es"), N.AUSENTE,
                f"{peldano} no tiene nombre de juego y el Camino se narra entero")


if __name__ == '__main__':
    unittest.main(verbosity=2)
