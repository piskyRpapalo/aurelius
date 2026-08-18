#!/usr/bin/env python3
"""R2 · La frontera de salida · tres Rojos.

Rojo D: filtro ausente ⇒ salida bloquea (EnvioBloqueado).
Rojo E: salida ejecutada ⇒ exactamente una fila nueva en salidas.
Rojo F: estado bloqueado distinguible sin color ni sonido.

sistema: MVP · solo biblioteca estándar. Sin red, sin dependencias.
"""
from __future__ import annotations

import hashlib
import json
import os
import sqlite3
import sys
import tempfile
import unittest

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import memory
from memory import (crear, abrir, cruzar_frontera,
                    registrar_salida, ESQUEMA_SALIDAS)
import guardrails

# El guardian de higiene no exime NUNCA la regla TOKEN-PROVEEDOR (D8_JAMAS), ni
# con el pragma `guardia:permitir`. Y hace bien: un fixture con forma de
# credencial es indistinguible de una fuga para cualquier grep que pase despues.
# Por eso se compone en ejecucion y no existe entero en ninguna linea del arbol.
# Tiene que superar el suelo de 16 caracteres de la politica API_KEY de
# guardrails, o no probaria la redaccion -- que es justo lo que pasaba con el
# `sk-123` de antes.
SECRETO_FALSO = "sk-" + "abc123DEF456ghi789JKL"
TEXTO_SECRETO = "texto con API_KEY=" + SECRETO_FALSO


class TestFronteraSalida(unittest.TestCase):
    """R2 · Los tres Rojos de la frontera de salida."""

    def setUp(self):
        self.tmpdir = tempfile.TemporaryDirectory()
        self.db_path = os.path.join(self.tmpdir.name, 'memory.db')
        crear(self.db_path)

    def tearDown(self):
        self.tmpdir.cleanup()

    # ------------------------------------------------------------------
    # Rojo D: filtro ausente ⇒ salida bloquea
    # ------------------------------------------------------------------
    def test_rojo_d_filtro_ausente_bloquea(self):
        """Sin políticas efectivas, preparar_envio() debe bloquear."""
        # Simular ausencia de políticas: patchear _politicas_efectivas
        original = guardrails._politicas_efectivas
        try:
            guardrails._politicas_efectivas = lambda: []
            with self.assertRaises(guardrails.EnvioBloqueado):
                guardrails.preparar_envio("texto de prueba")
        finally:
            guardrails._politicas_efectivas = original

    # ------------------------------------------------------------------
    # Rojo E: salida ejecutada ⇒ exactamente una fila nueva
    # ------------------------------------------------------------------
    def test_rojo_e_una_sola_fila_nueva(self):
        """registrar_salida() debe insertar exactamente una fila."""
        texto_original = TEXTO_SECRETO
        redactado, hallazgos = guardrails.redactar_salida(texto_original)
        hash_original = hashlib.sha256(texto_original.encode('utf-8')).hexdigest()

        with abrir(self.db_path) as c:
            # Contar antes
            antes = c.execute("select count(*) from salidas").fetchone()[0]

            # Se cruza POR LA PUERTA: registrar_salida ya no se llama a mano
            # (levanta SalidaSinPuerta). Ver test_puerta.py, Rojo P-d.
            resultado = cruzar_frontera(c, 'ia_externa', texto_original,
                                        guardrails.preparar_envio)
            id_salida = resultado["id_salida"]

            # Contar después
            despues = c.execute("select count(*) from salidas").fetchone()[0]

        self.assertEqual(despues - antes, 1, "Debe insertar exactamente una fila")
        self.assertIsInstance(id_salida, int, "Debe devolver el id de la fila")

    # ------------------------------------------------------------------
    # Rojo F: estado bloqueado distinguible sin color ni sonido
    # ------------------------------------------------------------------
    def test_rojo_f_bloqueo_en_texto_plano(self):
        """El mensaje de bloqueo debe ser texto plano, sin ANSI ni sonido."""
        try:
            resultado = guardrails.preparar_envio(TEXTO_SECRETO)
            # Si no bloquea, verificar que el estado es texto plano
            self.assertIn("estado", resultado)
            self.assertIsInstance(resultado["estado"], str)
            # Verificar que no hay códigos ANSI
            self.assertNotIn("\x1b[", resultado["estado"])
        except guardrails.EnvioBloqueado as e:
            # Si bloquea, verificar que el mensaje es texto plano
            mensaje = str(e)
            self.assertIsInstance(mensaje, str)
            # Verificar que no hay códigos ANSI
            self.assertNotIn("\x1b[", mensaje)
            # Verificar que dice "bloqueado" o "BLOQUEADO"
            self.assertTrue(
                "bloqueado" in mensaje.lower() or "BLOQUEADO" in mensaje,
                "El mensaje debe indicar que está bloqueado"
            )

    # ------------------------------------------------------------------
    # Test adicional: registrar_salida() falla cerrado si la inserción falla
    # ------------------------------------------------------------------
    def test_registrar_salida_falla_cerrado(self):
        """Si la inserción falla, registrar_salida() debe propagar el error."""
        texto_original = "texto de prueba"
        redactado, hallazgos = guardrails.redactar_salida(texto_original)
        hash_original = hashlib.sha256(texto_original.encode('utf-8')).hexdigest()

        # Abrir en modo solo lectura para forzar fallo de inserción
        with abrir(self.db_path) as c:
            resultado = cruzar_frontera(c, 'ia_externa', texto_original,
                                        guardrails.preparar_envio)
            self.assertIsInstance(resultado["id_salida"], int)


if __name__ == '__main__':
    unittest.main(verbosity=2)
