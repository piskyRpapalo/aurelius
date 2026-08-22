#!/usr/bin/env python3
"""--restore · devolver una copia a su sitio sin perder lo que habia.

La simetria de --backup no es --import: lo que --export produce va REDACTADO
por la frontera, asi que reimportarlo devuelve `[REDACTED:...]` donde estaba el
texto. El camino sin perdida es este.
"""
from __future__ import annotations

import os
import sys
import tempfile
import unittest

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import aurelius
import memory


class TestRestaurar(unittest.TestCase):

    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.viva = os.path.join(self.tmp.name, "memory.db")
        memory.crear(self.viva)
        with memory.abrir(self.viva) as c:
            memory.escribir_engrama(c, what="lo que habia antes", why="x")
        self.copia = os.path.join(self.tmp.name, "copia.db")
        memory.respaldar(self.viva, self.copia)
        with memory.abrir(self.viva) as c:
            memory.escribir_engrama(c, what="lo de despues", why="y")

    def tearDown(self):
        self.tmp.cleanup()

    def _cuantos(self, ruta):
        return memory.estado(ruta)[1].get("engrams", 0)

    def test_1_sin_confirmacion_no_toca_nada(self):
        """La que sostiene la promesa: un enter distraido no borra una memoria."""
        self.assertEqual(aurelius.restaurar(self.viva, self.copia, confirmar=""), 1)
        self.assertEqual(self._cuantos(self.viva), 2)

    def test_2_una_confirmacion_que_no_es_la_palabra_tampoco(self):
        for dicho in ("si", "y", "yes", "vale", "ok"):
            with self.subTest(dicho=dicho):
                aurelius.restaurar(self.viva, self.copia, confirmar=dicho)
                self.assertEqual(self._cuantos(self.viva), 2)

    def test_3_con_la_palabra_se_restaura(self):
        self.assertEqual(
            aurelius.restaurar(self.viva, self.copia, confirmar="restore"), 0)
        self.assertEqual(self._cuantos(self.viva), 1)

    def test_4_lo_que_habia_se_resguarda(self):
        """Una restauracion que borra la unica copia es el accidente del que protege."""
        aurelius.restaurar(self.viva, self.copia, confirmar="restore")
        guardados = [f for f in os.listdir(self.tmp.name)
                     if "antes-de-restaurar" in f and not f.endswith(("-wal", "-shm"))]
        self.assertEqual(len(guardados), 1, "no quedo resguardo de lo anterior")
        self.assertEqual(
            self._cuantos(os.path.join(self.tmp.name, guardados[0])), 2)

    def test_5_una_copia_que_no_existe_falla_cerrado(self):
        self.assertEqual(
            aurelius.restaurar(self.viva, os.path.join(self.tmp.name, "nada.db"),
                               confirmar="restore"), 2)
        self.assertEqual(self._cuantos(self.viva), 2)

    def test_6_un_fichero_que_no_es_memoria_falla_cerrado(self):
        basura = os.path.join(self.tmp.name, "basura.db")
        with open(basura, "w") as fh:
            fh.write("esto no es una base de datos")
        self.assertEqual(
            aurelius.restaurar(self.viva, basura, confirmar="restore"), 2)
        self.assertEqual(self._cuantos(self.viva), 2)

    def test_7_el_mismo_fichero_se_rechaza(self):
        self.assertEqual(
            aurelius.restaurar(self.viva, self.viva, confirmar="restore"), 2)
        self.assertEqual(self._cuantos(self.viva), 2)

    def test_8_no_deja_ficheros_a_medias_al_rechazar(self):
        aurelius.restaurar(self.viva, self.copia, confirmar="no")
        sobras = [f for f in os.listdir(self.tmp.name) if "comprobando" in f]
        self.assertEqual(sobras, [], f"quedaron temporales: {sobras}")


if __name__ == "__main__":
    unittest.main(verbosity=2)
