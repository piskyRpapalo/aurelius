#!/usr/bin/env python3
"""R2 · La puerta única · tres Rojos.

Rojo P-a: toda salida pasa por la puerta — no hay ruta alternativa.
Rojo P-b: filtro ausente ⇒ bloqueo.
Rojo P-c: una salida ⇒ exactamente una entrada en el registro.

sistema: MVP · solo biblioteca estándar. Sin red, sin dependencias.
"""
from __future__ import annotations

import hashlib
import os
import sqlite3
import sys
import tempfile
import unittest

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from memory import crear, abrir, cruzar_frontera, registrar_salida
import andamio
import guardrails


class TestPuertaUnica(unittest.TestCase):
    """R2 · Los tres Rojos de la puerta única."""

    def setUp(self):
        self.tmpdir = tempfile.TemporaryDirectory()
        self.db_path = os.path.join(self.tmpdir.name, 'memory.db')
        crear(self.db_path)

    def tearDown(self):
        self.tmpdir.cleanup()

    # ------------------------------------------------------------------
    # Rojo P-a: toda salida pasa por la puerta
    # ------------------------------------------------------------------
    def test_rojo_pa_toda_salida_pasa_por_la_puerta(self):
        """cruzar_frontera() es la única forma de registrar una salida."""
        texto_original = "texto de prueba"

        # Preparar con andamio (requiere inspección)
        andamio.ensamblar("conversar", {}, {})
        andamio.marcar_inspeccionado()

        with abrir(self.db_path) as c:
            resultado = cruzar_frontera(c, "andamio", texto_original, andamio.preparar_salida_andamio)

        self.assertEqual(resultado["estado"], "ok")
        self.assertIn("id_salida", resultado)
        self.assertIsInstance(resultado["id_salida"], int)

    # ------------------------------------------------------------------
    # Rojo P-b: filtro ausente ⇒ bloqueo
    # ------------------------------------------------------------------
    def test_rojo_pb_filtro_ausente_bloquea(self):
        """Sin políticas efectivas, cruzar_frontera() debe bloquear."""
        texto_original = "texto con API_KEY=sk-123"

        # Simular ausencia de políticas
        original = guardrails._politicas_efectivas
        try:
            guardrails._politicas_efectivas = lambda: []

            with abrir(self.db_path) as c:
                with self.assertRaises(guardrails.EnvioBloqueado):
                    cruzar_frontera(c, "ia_externa", texto_original, guardrails.preparar_envio)
        finally:
            guardrails._politicas_efectivas = original

    # ------------------------------------------------------------------
    # Rojo P-c: una salida ⇒ exactamente una entrada en el registro
    # ------------------------------------------------------------------
    def test_rojo_pc_una_salida_una_entrada(self):
        """cruzar_frontera() debe registrar exactamente una entrada."""
        texto_original = "texto de prueba con API_KEY=sk-123"

        with abrir(self.db_path) as c:
            # Contar antes
            antes = c.execute("select count(*) from salidas").fetchone()[0]

            # Cruzar la frontera con guardrails
            resultado = cruzar_frontera(c, "ia_externa", texto_original, guardrails.preparar_envio)

            # Contar después
            despues = c.execute("select count(*) from salidas").fetchone()[0]

        self.assertEqual(despues - antes, 1, "Debe registrar exactamente una entrada")
        self.assertEqual(resultado["estado"], "ok")


if __name__ == '__main__':
    unittest.main(verbosity=2)
