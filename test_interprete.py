#!/usr/bin/env python3
"""test_interprete.py · el rango probado se declara y NO bloquea.

sistema: MVP · solo biblioteca estandar.

Lo que hay que saber de este modulo son dos cosas y las dos se pueden romper
en silencio: que una version de fuera se DECLARE (si no, el rango del README
es una promesa que el programa no cumple), y que declararla no impida arrancar
(si bloqueara, una ausencia de medida se habria convertido en un veredicto).
"""
from __future__ import annotations

import os
import subprocess
import sys
import unittest
from pathlib import Path

AQUI = Path(__file__).resolve().parent
sys.path.insert(0, str(AQUI))

import interprete as I     # noqa: E402


class TestRango(unittest.TestCase):

    def test_01_los_extremos_probados_estan_dentro(self):
        """Un extremo fuera de su propio rango declararia contra si mismo."""
        self.assertTrue(I.dentro_del_rango(I.MINIMA), "la minima probada cae fuera")
        self.assertTrue(I.dentro_del_rango(I.MAXIMA), "la maxima probada cae fuera")
        self.assertIsNone(I.aviso(I.MINIMA), "la minima probada genera aviso")
        self.assertIsNone(I.aviso(I.MAXIMA), "la maxima probada genera aviso")

    def test_02_las_probadas_del_texto_son_las_del_rango(self):
        """El numero que se ensena y el que se compara tienen que ser el mismo.

        Si se separan, el aviso puede decir "probado en 3.10.12" mientras la
        comparacion usa otro minimo, y nadie lo notaria: las dos mitades
        seguirian pareciendo correctas por separado.
        """
        self.assertEqual(
            I.PROBADAS,
            (".".join(str(n) for n in I.MINIMA), ".".join(str(n) for n in I.MAXIMA)),
            "PROBADAS y MINIMA/MAXIMA se han separado")

    def test_03_por_debajo_y_por_encima_se_declaran(self):
        for v in ((3, 9, 7), (3, 10, 11), (3, 15, 0), (4, 0, 0)):
            with self.subTest(v=v):
                self.assertFalse(I.dentro_del_rango(v))
                aviso = I.aviso(v)
                self.assertIsNotNone(aviso, f"{v} no se declaro")
                # La version puesta sale literal: un aviso que no dice CUAL es
                # la version obliga a ir a buscarla, y entonces no es un aviso.
                self.assertIn(".".join(str(n) for n in v), aviso)
                # Y en los dos idiomas, porque esto pasa antes de que nadie
                # haya elegido uno.
                self.assertIn("NOTA ·", aviso)
                self.assertIn("NOTE ·", aviso)

    def test_04_dentro_del_rango_no_dice_nada(self):
        """Un aviso que sale siempre deja de leerse."""
        for v in ((3, 10, 12), (3, 11, 0), (3, 12, 8), (3, 14, 4)):
            with self.subTest(v=v):
                self.assertIsNone(I.aviso(v), f"{v} esta dentro y aun asi declaro")

    def test_05_declarar_no_es_bloquear(self):
        """El caso que de verdad importa: el programa ARRANCA fuera de rango.

        No se comprueba leyendo el codigo -- se arranca `aurelius.py` de
        verdad, con el rango movido por debajo de la version en curso, y se
        exige que la nota salga Y que el proceso termine en 0. Un modulo que
        solo se probara a si mismo no notaria que `aurelius.py` decidio
        `sys.exit(1)` al ver la nota.
        """
        v = ".".join(str(n) for n in I.actual())
        guion = (
            "import interprete, sys;"
            # El rango se mueve entero por DEBAJO de la version en curso, asi
            # que la de esta maquina queda fuera pase lo que pase.
            "interprete.MINIMA=(3,0,0); interprete.MAXIMA=(3,0,1);"
            "interprete.PROBADAS=('3.0.0','3.0.1');"
            "sys.argv=['aurelius.py','--view','--db',DB];"
            "import aurelius; sys.exit(aurelius.main())"
        )
        entorno = dict(os.environ, AURELIUS_TEST="1", AURELIUS_RITMO="0",
                       AURELIUS_SIN_HARDWARE="1")
        import tempfile
        with tempfile.TemporaryDirectory() as tmp:
            db = os.path.join(tmp, "memoria.db")
            import memory
            memory.crear(db)
            r = subprocess.run(
                [sys.executable, "-c", f"DB={db!r}\n" + guion],
                cwd=str(AQUI), env=entorno, capture_output=True, text=True, timeout=120)

        salida = r.stdout + r.stderr
        self.assertIn("NOTA ·", salida, f"fuera de rango y no se declaro:\n{salida}")
        self.assertIn(v, salida, "la nota no dice que version se esta usando")
        self.assertEqual(r.returncode, 0,
                         f"declarar bloqueo el arranque (codigo {r.returncode}):\n{salida}")

    def test_06_dentro_de_rango_el_arranque_no_dice_nada(self):
        """Y al reves: con el rango de verdad, la nota no aparece."""
        entorno = dict(os.environ, AURELIUS_TEST="1", AURELIUS_RITMO="0",
                       AURELIUS_SIN_HARDWARE="1")
        import tempfile
        with tempfile.TemporaryDirectory() as tmp:
            db = os.path.join(tmp, "memoria.db")
            import memory
            memory.crear(db)
            r = subprocess.run(
                [sys.executable, "aurelius.py", "--view", "--db", db],
                cwd=str(AQUI), env=entorno, capture_output=True, text=True, timeout=120)
        salida = r.stdout + r.stderr
        if I.dentro_del_rango():
            self.assertNotIn("NOTA ·", salida,
                             f"esta version esta dentro del rango y aun asi declaro:\n{salida}")
        self.assertEqual(r.returncode, 0, f"--view no cerro limpio:\n{salida}")


class TestAvisoSigueAlIdioma(unittest.TestCase):
    """La nota del intérprete respeta lo que la persona ya firmó.

    Medido en un teléfono: en una pantalla estrecha, la nota bilingüe se come
    dos de las primeras cuatro líneas que alguien ve. Quien ya eligió idioma no
    tiene por qué leer dos veces la misma frase — y quien no lo ha elegido sí,
    porque suponérselo sería exactamente lo que la primera pregunta evita.
    """

    FUERA = (3, 99, 0)      # una versión que nadie ha probado, seguro

    def test_sin_idioma_firmado_salen_los_dos(self):
        salida = I.aviso(self.FUERA)
        self.assertIn("NOTA ·", salida, "falta el castellano")
        self.assertIn("NOTE ·", salida, "falta el inglés")

    def test_con_idioma_firmado_sale_solo_ese(self):
        es = I.aviso(self.FUERA, idioma="es")
        self.assertIn("NOTA ·", es)
        self.assertNotIn("NOTE ·", es, "el español no tiene que leer inglés")

        en = I.aviso(self.FUERA, idioma="en")
        self.assertIn("NOTE ·", en)
        self.assertNotIn("NOTA ·", en, "el inglés no tiene que leer español")

    def test_un_idioma_que_no_hablamos_no_elige_por_nadie(self):
        """`fr` no es una firma válida: se cae a los dos, no a uno inventado."""
        salida = I.aviso(self.FUERA, idioma="fr")
        self.assertIn("NOTA ·", salida)
        self.assertIn("NOTE ·", salida)

    def test_dentro_del_rango_no_dice_nada_en_ningun_idioma(self):
        for idioma in (None, "es", "en"):
            self.assertIsNone(I.aviso((3, 10, 12), idioma=idioma))



if __name__ == "__main__":
    unittest.main()
