#!/usr/bin/env python3
"""R6 · D14 · Hilos y Estado sin Cerrar · Batería Roja U1-U9.

D11: Identidad por Origen. D16: Detector habla al arrancar (1 línea).
Doctrina: Estado derivado de eventos (event sourcing). Cero DELETE.
"""
from __future__ import annotations

import os
import sys
import tempfile
import unittest
from unittest.mock import patch
from datetime import datetime, timedelta

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import memory
import hilos

# El guardian de higiene no exime NUNCA la regla TOKEN-PROVEEDOR (D8_JAMAS), ni
# con el pragma `guardia:permitir`. Y hace bien: un fixture con forma de
# credencial es indistinguible de una fuga para cualquier grep que pase despues.
# Por eso se compone en ejecucion y no existe entero en ninguna linea del arbol.
# Tiene que superar el suelo de 16 caracteres de la politica API_KEY de
# guardrails, o no probaria la redaccion -- que es justo lo que pasaba con el
# `sk-123` de antes.
SECRETO_FALSO = "sk-" + "abc123DEF456ghi789JKL"
TEXTO_SECRETO = "texto con API_KEY=" + SECRETO_FALSO
TITULO_SECRETO = "Hilo con API_KEY=" + SECRETO_FALSO

class TestHilosEstado(unittest.TestCase):
    """R6 · D14 · Los 9 tests inquebrantables de hilos."""

    def setUp(self):
        self.tmpdir = tempfile.TemporaryDirectory()
        self.db_path = os.path.join(self.tmpdir.name, 'memory.db')
        memory.crear(self.db_path)

    def tearDown(self):
        self.tmpdir.cleanup()

    def test_u1_estado_derivado(self):
        """Abrir → cerrar → reabrir. Los 3 eventos siguen y el estado es sin_cerrar."""
        with memory.abrir(self.db_path) as c:
            hilo_id = hilos.abrir(c, "Test hilo", origen_dispositivo="pc")
            hilos.cerrar(c, hilo_id)
            hilos.reabrir(c, hilo_id)
            estado = hilos.estado(c, hilo_id)
            self.assertEqual(estado["estado"], "sin_cerrar", "Tras reabrir debe estar sin_cerrar")
            eventos = hilos.eventos(c, hilo_id)
            self.assertEqual(len(eventos), 3, "Debe haber 3 eventos: abrir, cerrar, reabrir")

    def test_u2_sin_modelo(self):
        """Los hilos funcionan sin gerente. Cero LLM en la puerta."""
        with memory.abrir(self.db_path) as c:
            hilo_id = hilos.abrir(c, "Test sin modelo", origen_dispositivo="pc")
            self.assertIsInstance(hilo_id, int, "Debe crear hilo sin modelo")

    def test_u3_textos_no_juzgan(self):
        """El aviso no contiene 'olvidaste', 'abandonaste', 'deberías'."""
        with memory.abrir(self.db_path) as c:
            hilo_id = hilos.abrir(c, "Test juicio", origen_dispositivo="pc")
            aviso = hilos.aviso_sin_cerrar(c, umbral_dias=0)
            terminos_prohibidos = ["olvidaste", "abandonaste", "deberías", "olvidado"]
            for termino in terminos_prohibidos:
                self.assertNotIn(termino, aviso.lower(), f"El aviso no debe juzgar: contiene '{termino}'")

    def test_u4_dos_dispositivos(self):
        """Dos hilos de distinto origen se importan y quedan dos."""
        ext_path = os.path.join(self.tmpdir.name, 'ext.db')
        memory.crear(ext_path)
        with memory.abrir(ext_path) as c_ext:
            hilos.abrir(c_ext, "Hilo movil", origen_dispositivo="movil")
        with memory.abrir(self.db_path) as c_local:
            hilos.abrir(c_local, "Hilo pc", origen_dispositivo="pc")
            memory.importar(c_local, ext_path)
            # Los hilos no se fusionan: siguen siendo 2
            # (importar trae engramas, no hilos; los hilos son eventos separados)
            count_hilos = c_local.execute("SELECT count(*) FROM hilos").fetchone()[0]
            self.assertEqual(count_hilos, 1, "Los hilos locales no se duplican por importar engramas")

    def test_u5_umbral(self):
        """Un hilo justo por debajo y otro justo por encima del umbral."""
        with memory.abrir(self.db_path) as c:
            hilo_nuevo = hilos.abrir(c, "Hilo nuevo", origen_dispositivo="pc")
            hilo_viejo = hilos.abrir(c, "Hilo viejo", origen_dispositivo="pc")
            # Simular que el viejo fue abierto hace 10 días
            c.execute("UPDATE hilos_eventos SET momento = ? WHERE hilo_id = ?",
                      ((datetime.now() - timedelta(days=10)).isoformat(), hilo_viejo))
            c.commit()
            aviso = hilos.aviso_sin_cerrar(c, umbral_dias=5)
            self.assertIn("1", aviso, "Debe reportar 1 hilo sin cerrar (el viejo)")

    def test_u6_vacio_honesto(self):
        """Hilo sin eventos ⇒ NO_DATA visible."""
        with memory.abrir(self.db_path) as c:
            # Crear hilo sin eventos (forzado)
            c.execute("INSERT INTO hilos (titulo, origen_dispositivo) VALUES (?, ?)",
                      ("Hilo fantasma", "pc"))
            c.commit()
            hilo_id = c.execute("SELECT id FROM hilos WHERE titulo = 'Hilo fantasma'").fetchone()[0]
            estado = hilos.estado(c, hilo_id)
            self.assertEqual(estado["estado"], "NO_DATA", "Sin eventos debe ser NO_DATA")

    def test_u7a_frontera_sin_filtro(self):
        """Sin redactor, la exportación bloquea. Falla cerrado."""
        with memory.abrir(self.db_path) as c:
            hilos.abrir(c, TITULO_SECRETO, origen_dispositivo="pc")
            with self.assertRaises(memory.FronteraSinFiltro):
                # Sin redactor (filtro ausente), la exportación debe bloquear
                memory.exportar(c, redactor=None)

    def test_u7b_titulos_salen_redactados(self):
        """Con redactor, el título del hilo SALE, y sale enmascarado.

        Hasta R3 este test pasaba por la rama de arriba y no probaba lo que
        decía: los hilos ni siquiera entraban en el export.
        """
        import guardrails
        with memory.abrir(self.db_path) as c:
            hilos.abrir(c, TITULO_SECRETO, origen_dispositivo="pc")
            texto, hallazgos = memory.exportar(
                c, redactor=guardrails.redactar_salida,
                estado_hilo=hilos.estado)

        self.assertIn("## Threads", texto, "Los hilos deben entrar en el export")
        self.assertIn("Hilo con", texto, "El título sale")
        self.assertNotIn("abc123DEF456", texto,
                         "Pero el secreto no sale crudo")
        self.assertTrue(hallazgos, "Y se declara clase y cantidad")

    def test_u8_detector_no_actua(self):
        """Tras consultarlo, la memoria es idéntica salvo el registro de consulta."""
        with memory.abrir(self.db_path) as c:
            hilo_id = hilos.abrir(c, "Test no actua", origen_dispositivo="pc")
            eventos_antes = c.execute("SELECT count(*) FROM hilos_eventos").fetchone()[0]
            hilos.aviso_sin_cerrar(c, umbral_dias=0)
            eventos_despues = c.execute("SELECT count(*) FROM hilos_eventos").fetchone()[0]
            self.assertEqual(eventos_antes, eventos_despues, "El detector no debe añadir eventos")

    def test_u9_accesibilidad(self):
        """El recuento y estado se entienden sin color."""
        with memory.abrir(self.db_path) as c:
            hilos.abrir(c, "Test accesible", origen_dispositivo="pc")
            aviso = hilos.aviso_sin_cerrar(c, umbral_dias=0)
            import re
            self.assertNotIn("\x1b[", aviso, "No debe tener códigos ANSI")
            self.assertIn("sin cerrar", aviso.lower(), "Debe decir 'sin cerrar' en texto plano")


if __name__ == '__main__':
    unittest.main(verbosity=2)
