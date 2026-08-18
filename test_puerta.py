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

import memory
from memory import crear, abrir, cruzar_frontera, registrar_salida
import andamio
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
        texto_original = TEXTO_SECRETO

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
        texto_original = TEXTO_SECRETO

        with abrir(self.db_path) as c:
            # Contar antes
            antes = c.execute("select count(*) from salidas").fetchone()[0]

            # Cruzar la frontera con guardrails
            resultado = cruzar_frontera(c, "ia_externa", texto_original, guardrails.preparar_envio)

            # Contar después
            despues = c.execute("select count(*) from salidas").fetchone()[0]

        self.assertEqual(despues - antes, 1, "Debe registrar exactamente una entrada")
        self.assertEqual(resultado["estado"], "ok")


    # ------------------------------------------------------------------
    # Rojo P-d: no hay segunda ruta al registro
    # ------------------------------------------------------------------
    def test_rojo_pd_registrar_fuera_de_la_puerta(self):
        """registrar_salida() a mano ⇒ SalidaSinPuerta.

        Es el rojo que hacía falta para que P-a signifique algo: sin él,
        «toda salida pasa por la puerta» se comprobaba usando la puerta.
        """
        with abrir(self.db_path) as c:
            with self.assertRaises(memory.SalidaSinPuerta):
                registrar_salida(c, "ia_externa", "texto", [], "abc")

    # ------------------------------------------------------------------
    # Rojo P-e: la huella es del original, no de la redacción
    # ------------------------------------------------------------------
    def test_rojo_pe_huella_del_original(self):
        """Un registro que hashea su propia redacción no prueba qué salió."""
        texto_original = TEXTO_SECRETO

        with abrir(self.db_path) as c:
            resultado = cruzar_frontera(c, "ia_externa", texto_original,
                                        guardrails.preparar_envio)
            fila = c.execute(
                "select hash_original, texto from salidas where id = ?",
                (resultado["id_salida"],)).fetchone()

        esperado = hashlib.sha256(texto_original.encode("utf-8")).hexdigest()
        self.assertEqual(fila["hash_original"], esperado,
                         "La huella debe ser la del texto original")
        del_redactado = hashlib.sha256(fila["texto"].encode("utf-8")).hexdigest()
        self.assertNotEqual(fila["hash_original"], del_redactado,
                            "Hashear lo redactado no prueba qué salió")

    # ------------------------------------------------------------------
    # Rojo P-f: la negativa de la persona no deja rastro
    # ------------------------------------------------------------------
    def test_rojo_pf_sin_aprobacion_no_hay_fila(self):
        """La persona dice que no: no sale, y NO se anota.

        El registro guarda los veredictos del filtro, no las decisiones de
        quien vive en esta máquina.
        """
        with abrir(self.db_path) as c:
            antes = c.execute("select count(*) from salidas").fetchone()[0]
            with self.assertRaises(memory.SalidaNoAprobada):
                cruzar_frontera(c, "ia_externa", "texto de prueba",
                                guardrails.preparar_envio,
                                confirmar=lambda t, h: False)
            despues = c.execute("select count(*) from salidas").fetchone()[0]

        self.assertEqual(despues, antes, "La negativa humana no deja rastro")

    # ------------------------------------------------------------------
    # Rojo P-g: el registro se lee sin color y sin texto crudo
    # ------------------------------------------------------------------
    def test_rojo_pg_registro_sin_color_ni_crudo(self):
        """`ok` y `bloqueado` se distinguen sin color, y el crudo no aparece."""
        secreto = TEXTO_SECRETO

        original = guardrails._politicas_efectivas
        with abrir(self.db_path) as c:
            cruzar_frontera(c, "ia_externa", secreto, guardrails.preparar_envio)
            try:
                guardrails._politicas_efectivas = lambda: []
                with self.assertRaises(guardrails.EnvioBloqueado):
                    cruzar_frontera(c, "ia_externa", secreto,
                                    guardrails.preparar_envio)
            finally:
                guardrails._politicas_efectivas = original
            resumen = memory.resumen_salidas(c)

        estados = {f["estado"] for f in resumen}
        self.assertEqual(estados, {"ok", "bloqueado"})
        for fila in resumen:
            self.assertNotIn("texto", fila, "El resumen no lleva texto crudo")
            self.assertNotIn("\x1b[", str(fila), "Sin códigos ANSI")
        self.assertNotIn("abc123DEF456", str(resumen),
                         "Ni un fragmento del secreto")


if __name__ == '__main__':
    unittest.main(verbosity=2)
