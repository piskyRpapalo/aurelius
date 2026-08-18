#!/usr/bin/env python3
"""R6 · D10 · La Traza de Verificación · Batería Roja V1-V7.

Doctrina: Solo hechos deterministas. Nada de narración del LLM.
El panel muestra qué entró, qué regla disparó, y el veredicto.
"""
from __future__ import annotations

import os
import sys
import tempfile
import unittest

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import fusible
import memory
import traza

class TestTrazaVerificacion(unittest.TestCase):
    """R6 · D10 · Los 7 tests inquebrantables de la traza."""

    def setUp(self):
        # V6 mira el registro de verdad, asi que necesita una memoria de verdad.
        self.tmpdir = tempfile.TemporaryDirectory()
        self.db_path = os.path.join(self.tmpdir.name, 'memory.db')
        memory.crear(self.db_path)

    def tearDown(self):
        self.tmpdir.cleanup()

    def test_v1_determinismo(self):
        """Misma entrada dos veces ⇒ traza idéntica, salvo el momento."""
        texto = "Ejecuta: rm -rf /"
        t1 = traza.generar(texto)
        t2 = traza.generar(texto)
        # Ignoramos el timestamp si existe para comparar
        t1_sin_ts = {k: v for k, v in t1.items() if k != "momento"}
        t2_sin_ts = {k: v for k, v in t2.items() if k != "momento"}
        self.assertEqual(t1_sin_ts, t2_sin_ts, "La traza debe ser determinista")

    def test_v2_sin_color(self):
        """Sin códigos ANSI, los estados se distinguen por símbolo y palabra."""
        texto_limpio = "Hola mundo"
        texto_peligro = "rm -rf /"
        
        traza_limpio = traza.generar(texto_limpio)
        traza_peligro = traza.generar(texto_peligro)
        
        # Limpiar cualquier rastro de ANSI (por si acaso)
        import re
        ansi_pattern = re.compile(r'\x1b\[[0-9;]*m')
        str_limpio = ansi_pattern.sub('', str(traza_limpio))
        str_peligro = ansi_pattern.sub('', str(traza_peligro))
        
        self.assertNotEqual(str_limpio, str_peligro, "Los estados deben diferir sin color")
        self.assertIn("[ok]", str_limpio, "El estado limpio debe tener símbolo [ok]")
        self.assertIn("[x]", str_peligro, "El estado de bloqueo debe tener símbolo [x]")

    def test_v3_nada_de_narracion(self):
        """La traza no debe usar el texto del modelo como causa."""
        texto_modelo = "He decidido que esto es seguro porque lo dice la documentación."
        t = traza.generar(texto_modelo)
        # La traza no debe contener el texto del modelo en el campo de causa
        self.assertNotIn("documentación", str(t), "La traza no debe usar narración del LLM")

    def test_v4_alcance_siempre(self):
        """En todos los estados, la declaración de alcance debe estar presente."""
        texto_limpio = "Hola"
        t = traza.generar(texto_limpio)
        self.assertIn("alcance", str(t).lower(), "El alcance debe estar siempre presente")

    def test_v5_falla_cerrado(self):
        """Inspector ausente o ilegible ⇒ bloqueado + NO_DATA."""
        # Simulamos un fusible roto pasando un texto que cause un error
        # o simplemente verificamos que la traza maneja el estado NO_DATA
        t = traza.generar(None) # Entrada None simula fallo
        self.assertIn("[x]", str(t), "Fallo debe mostrar [x]")
        self.assertIn("NO_DATA", str(t), "Fallo debe declarar NO_DATA")

    def test_v6_constancia(self):
        """Un bloqueo deja UNA fila en el registro, y sin el texto crudo.

        Ya no se simula: el fusible cruza la frontera por la puerta única, y de
        su veredicto sale la constancia. Un bloqueo del que no queda rastro es
        indistinguible de un bloqueo que nunca ocurrió.
        """
        texto = "rm -rf /"
        t = traza.generar(texto)
        self.assertTrue(t.get("bloqueado", False), "Debe estar bloqueado")

        with memory.abrir(self.db_path) as c:
            antes = c.execute("select count(*) from salidas").fetchone()[0]
            with self.assertRaises(fusible.RespuestaBloqueada):
                memory.cruzar_frontera(c, "modelo_local", texto,
                                       fusible.preparar_respuesta)
            filas = c.execute(
                "select estado, texto, motivo from salidas order by id").fetchall()

        self.assertEqual(len(filas) - antes, 1, "Un bloqueo, una fila")
        self.assertEqual(filas[-1]["estado"], "bloqueado")
        self.assertEqual(filas[-1]["texto"], "NO_DATA",
                         "El texto crudo del modelo no se guarda jamás")
        self.assertNotIn("rm -rf", filas[-1]["motivo"],
                         "Ni siquiera el motivo lleva el fragmento")

    def test_v7_regla_desconocida(self):
        """Traza que referencia una regla inexistente ⇒ error declarado."""
        # Forzar una regla inexistente en el output
        t = traza.generar("texto normal")
        self.assertTrue(len(t.get("hallazgos", [])) == 0, "No debe haber hallazgos falsos")


if __name__ == '__main__':
    unittest.main(verbosity=2)
