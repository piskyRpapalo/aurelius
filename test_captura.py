#!/usr/bin/env python3
"""El par completo, y el consentimiento que no se presume.

La que importa es la 4: capturar no es consentir. El dia que un turno entre al
dataset sin que nadie lo haya subido a 1, este producto habra dejado de cumplir
su primera promesa.
"""
from __future__ import annotations

import os
import sys
import tempfile
import unittest

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import captura
import memory


class TestCaptura(unittest.TestCase):

    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.ruta = os.path.join(self.tmp.name, "memory.db")
        memory.crear(self.ruta)

    def tearDown(self):
        self.tmp.cleanup()

    def test_1_guarda_el_par_entero(self):
        """Lo que fallaba antes: la respuesta se guardaba sin su pregunta."""
        with memory.abrir(self.ruta) as c:
            tid = captura.registrar(c, "hola, que es esto?", "Hablas conmigo.",
                                    modelo="qwen3-4b", idioma="es")
            self.assertIsNotNone(tid)
            fila = c.execute("select prompt, respuesta from turnos "
                             "where id = ?", (tid,)).fetchone()
        self.assertEqual(fila[0], "hola, que es esto?")
        self.assertEqual(fila[1], "Hablas conmigo.")

    def test_2_nace_sin_consentimiento(self):
        with memory.abrir(self.ruta) as c:
            tid = captura.registrar(c, "p", "r")
            valor = c.execute("select consent from turnos where id = ?",
                              (tid,)).fetchone()[0]
        self.assertEqual(valor, 0)

    def test_3_solo_el_carbono_lo_sube(self):
        with memory.abrir(self.ruta) as c:
            tid = captura.registrar(c, "p", "r")
            self.assertEqual(captura.pares(c), [])
            captura.consentir(c, tid, True, motivo="firmado")
            self.assertEqual(len(captura.pares(c)), 1)

    def test_4_capturar_no_es_consentir(self):
        """Diez turnos capturados no dan ni un solo par entrenable."""
        with memory.abrir(self.ruta) as c:
            for i in range(10):
                captura.registrar(c, f"p{i}", f"r{i}")
            self.assertEqual(captura.recuento(c)["turnos"], 10)
            self.assertEqual(captura.recuento(c)["consentidos"], 0)
            self.assertEqual(captura.pares(c), [])

    def test_5_el_consentimiento_se_puede_retirar(self):
        with memory.abrir(self.ruta) as c:
            tid = captura.registrar(c, "p", "r")
            captura.consentir(c, tid, True)
            captura.consentir(c, tid, False, motivo="me arrepenti")
            self.assertEqual(captura.pares(c), [])

    def test_6_corregir_conserva_las_dos(self):
        """Borrar el original destruiria el par de preferencia."""
        with memory.abrir(self.ruta) as c:
            tid = captura.registrar(c, "que recuerdas?", "Recuerdo muchas cosas.",
                                    idioma="es")
            captura.corregir(c, tid, "No tengo eso en tu memoria.",
                             motivo="relleno")
            captura.consentir(c, tid, True)
            par = captura.pares(c)[0]
        self.assertEqual(par["clase"], "preferencia")
        self.assertEqual(par["rechazado"], "Recuerdo muchas cosas.")
        self.assertEqual(par["elegido"], "No tengo eso en tu memoria.")
        self.assertEqual(par["motivo"], "relleno")

    def test_7_corregir_no_consiente(self):
        with memory.abrir(self.ruta) as c:
            tid = captura.registrar(c, "p", "r")
            captura.corregir(c, tid, "otra cosa")
            self.assertEqual(captura.pares(c), [])

    def test_8_un_fallo_no_tumba_el_turno(self):
        """Se llama con la respuesta ya entregada: aqui no se puede levantar."""
        class Rota:
            def executescript(self, *a): raise RuntimeError("disco lleno")
            def execute(self, *a): raise RuntimeError("disco lleno")
        self.assertIsNone(captura.registrar(Rota(), "p", "r"))

    def test_9_se_puede_apagar(self):
        self.assertTrue(captura.activa({}))
        self.assertTrue(captura.activa({"captura": "si"}))
        self.assertFalse(captura.activa({"captura": "no"}))

    def test_10_memoria_vieja_recibe_la_tabla(self):
        """Migracion aditiva: una memoria anterior a esto no puede reventar."""
        with memory.abrir(self.ruta) as c:
            c.execute("drop table if exists turnos")
            self.assertIsNotNone(captura.registrar(c, "p", "r"))


if __name__ == "__main__":
    unittest.main(verbosity=2)
