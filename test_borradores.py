#!/usr/bin/env python3
"""D69 · La capa de BORRADORES · Batería Roja B-a…B-e.

Rojo B-a: lo que propone Aurelius NUNCA entra en engrams.
Rojo B-b: promover sin acto de la persona ⇒ excepción, y cero engramas nuevos.
Rojo B-c: descartar no borra la fila.
Rojo B-d: promovido con acto ⇒ el engrama existe y el borrador apunta a él.
Rojo B-e: una memoria anterior a D69 abre y gana la tabla sin tocar engramas.

IronClaw, dicho en tres funciones: la máquina propone, la persona firma. Estos
rojos existen porque esa frase es fácil de escribir en un documento y fácil de
romper en un `insert`.

sistema: MVP · solo biblioteca estándar. Sin red, sin dependencias.
"""
from __future__ import annotations

import os
import sqlite3
import sys
import tempfile
import unittest

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import memory


class TestBorradores(unittest.TestCase):
    """D69 · los rojos de la capa que separa proponer de firmar."""

    def setUp(self):
        self.tmpdir = tempfile.TemporaryDirectory()
        self.db_path = os.path.join(self.tmpdir.name, 'memory.db')
        memory.crear(self.db_path)

    def tearDown(self):
        self.tmpdir.cleanup()

    def _engramas(self, c):
        return c.execute("select count(*) from engrams").fetchone()[0]

    # ------------------------------------------------------------------
    # Rojo B-a: proponer no es escribir
    # ------------------------------------------------------------------
    def test_rojo_ba_proponer_no_toca_engrams(self):
        """Lo que propone Aurelius no entra en la memoria firmada."""
        with memory.abrir(self.db_path) as c:
            antes = self._engramas(c)
            memory.proponer_borrador(c, "creo que aprendiste algo del cable")
            memory.proponer_borrador(c, "y otra cosa mas")
            despues = self._engramas(c)
            pendientes = memory.leer_borradores(c, "pendiente")

        self.assertEqual(despues, antes,
                         "una propuesta NO puede crear memoria firmada")
        self.assertEqual(len(pendientes), 2, "las dos propuestas esperan")

    # ------------------------------------------------------------------
    # Rojo B-b: sin acto de la persona no hay promoción
    # ------------------------------------------------------------------
    def test_rojo_bb_promover_sin_persona_bloquea(self):
        """Ascender sin firma humana levanta excepción y no escribe nada."""
        with memory.abrir(self.db_path) as c:
            bid = memory.proponer_borrador(c, "propuesta de la maquina")
            antes = self._engramas(c)

            with self.assertRaises(memory.PromocionSinPersona):
                memory.promover_a_engrama(c, bid)          # defecto: sin acto

            with self.assertRaises(memory.PromocionSinPersona):
                memory.promover_a_engrama(c, bid, acto_persona=False)

            self.assertEqual(self._engramas(c), antes,
                             "un intento fallido no deja memoria a medias")
            self.assertEqual(memory.leer_borradores(c)[0]["estado"], "pendiente",
                             "el borrador sigue esperando")

    # ------------------------------------------------------------------
    # Rojo B-c: descartar no borra
    # ------------------------------------------------------------------
    def test_rojo_bc_descartar_conserva_la_fila(self):
        """Descartar es un estado, no una papelera. Cero DELETE."""
        with memory.abrir(self.db_path) as c:
            bid = memory.proponer_borrador(c, "propuesta que no convence")
            memory.descartar_borrador(c, bid, motivo="no es lo que quise decir")

            todas = memory.leer_borradores(c)
            fila = todas[0]

        self.assertEqual(len(todas), 1, "la fila se queda: descartar no borra")
        self.assertEqual(fila["estado"], "descartado")
        self.assertEqual(fila["motivo"], "no es lo que quise decir",
                         "y queda por que se descarto")
        self.assertEqual(fila["texto"], "propuesta que no convence",
                         "el texto de la propuesta no se pierde")

    # ------------------------------------------------------------------
    # Rojo B-d: con acto, asciende y deja rastro de su origen
    # ------------------------------------------------------------------
    def test_rojo_bd_promovido_apunta_a_su_engrama(self):
        """Promovido: el engrama existe, y el borrador dice en qué se convirtió.

        El engrama nace `origin='persona'` porque la promoción es su acto y
        porque el CHECK de origin no se migra. La prueba de que lo propuso la
        máquina vive en la fila del borrador, no en el engrama.
        """
        with memory.abrir(self.db_path) as c:
            bid = memory.proponer_borrador(c, "la impresora fallaba por el cable")
            eng = memory.promover_a_engrama(
                c, bid, acto_persona=True, why="lo comprobamos cambiandolo")

            fila = memory.leer_borradores(c)[0]

        self.assertEqual(fila["estado"], "promovido")
        self.assertEqual(fila["engrama_id"], eng["id"],
                         "el borrador debe apuntar al engrama en que se convirtio")
        self.assertEqual(eng["what"], "la impresora fallaba por el cable")
        self.assertEqual(eng["origin"], "persona",
                         "lo firma la persona: la promocion es su acto")

    def test_rojo_bd_no_se_promueve_dos_veces(self):
        """Una promoción no se repite: el segundo intento no duplica memoria."""
        with memory.abrir(self.db_path) as c:
            bid = memory.proponer_borrador(c, "una sola vez")
            memory.promover_a_engrama(c, bid, acto_persona=True)
            antes = self._engramas(c)

            with self.assertRaises(memory.PromocionSinPersona):
                memory.promover_a_engrama(c, bid, acto_persona=True)

            self.assertEqual(self._engramas(c), antes,
                             "promover dos veces no puede duplicar el recuerdo")

    # ------------------------------------------------------------------
    # Rojo B-e: una memoria anterior a D69 no revienta
    # ------------------------------------------------------------------
    def test_rojo_be_memoria_vieja_gana_la_tabla(self):
        """Una memoria nacida antes de D69 abre, migra y no pierde nada."""
        vieja = os.path.join(self.tmpdir.name, "vieja.db")
        con = sqlite3.connect(vieja)
        con.executescript(memory.ESQUEMA)      # solo engrams y links
        con.execute("insert into engrams (what) values ('recuerdo de antes')")
        con.commit()
        con.close()

        with memory.abrir(vieja) as c:
            antes = self._engramas(c)
            memory.asegurar_tablas(c)
            bid = memory.proponer_borrador(c, "propuesta nueva sobre memoria vieja")
            despues = self._engramas(c)
            pendientes = memory.leer_borradores(c, "pendiente")

        self.assertEqual(antes, 1, "el recuerdo viejo estaba")
        self.assertEqual(despues, 1, "y sigue estando, intacto")
        self.assertEqual(len(pendientes), 1)
        self.assertIsInstance(bid, int)


if __name__ == '__main__':
    unittest.main(verbosity=2)
