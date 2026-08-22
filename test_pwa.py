#!/usr/bin/env python3
"""La cara premium · los cuatro estados y el fail-closed.

El estado 4 se prueba inyectando el fallo en la costura, no rompiendo la
configuracion. Motivo medido el 2026-08-22: una configuracion invalida NO
bloquea -- cae a las politicas core, que no se pueden apagar, y el filtro sigue
corriendo. Eso es correcto por diseno, y significa que el estado 4 solo lo
alcanza un fallo del propio filtro. Se prueba lo que puede pasar, no lo que
seria comodo que pasara.
"""
from __future__ import annotations

import importlib.util
import json
import os
import sys
import tempfile
import unittest
from unittest import mock

AQUI = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, AQUI)

import guardrails as G

# El guardian de higiene no exime NUNCA la regla TOKEN-PROVEEDOR, ni con el
# pragma `guardia:permitir`, y hace bien: un fixture con forma de credencial es
# indistinguible de una fuga para cualquier grep que pase despues. Se compone en
# ejecucion, como en test_frontera.py, para que no exista entero en ninguna
# linea del arbol. Y pasa del suelo de 16 caracteres de la politica API_KEY, o
# no probaria la redaccion.
SECRETO_FALSO = "sk-" + "abc123DEF456ghi789JKL"
import memory
import captura

# `bin/aurelius-pwa` no lleva extension .py -- es un ejecutable, no un modulo --
# asi que se le da un cargador explicito en vez de dejar que se adivine por el
# nombre. Probar el fichero que se ejecuta de verdad vale mas que probar una
# copia con otra extension.
from importlib.machinery import SourceFileLoader          # noqa: E402
_ruta = os.path.join(AQUI, "bin", "aurelius-pwa")
_spec = importlib.util.spec_from_loader(
    "aurelius_pwa", SourceFileLoader("aurelius_pwa", _ruta))
PWA = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(PWA)


class Fingida:
    """Un manejador sin socket: se le llama el metodo y se mira que respondio."""

    def __init__(self, db):
        self.server = mock.Mock(ruta_db=db, modelo=None)
        self.codigo = None
        self.cuerpo = None

    def _json(self, codigo, cuerpo):
        self.codigo, self.cuerpo = codigo, cuerpo


class TestFrontera(unittest.TestCase):

    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.db = os.path.join(self.tmp.name, "memory.db")
        memory.crear(self.db)
        self.h = Fingida(self.db)

    def tearDown(self):
        self.tmp.cleanup()

    def _frontera(self, texto):
        PWA.PWA._frontera(self.h, {"texto": texto})
        return self.h.codigo, self.h.cuerpo

    def test_1_con_hallazgos_los_cuenta_el_servidor(self):
        """Estado 1. El contador viaja en el payload; la interfaz no cuenta."""
        cod, cuerpo = self._frontera(f"clave {SECRETO_FALSO} aqui")
        self.assertEqual(cod, 200)
        self.assertTrue(cuerpo["hallazgos"])
        for h in cuerpo["hallazgos"]:
            self.assertIn("policy", h)
            self.assertIn("count", h)
        # El fragmento encontrado NUNCA viaja: clase y cantidad, nada mas.
        self.assertNotIn(SECRETO_FALSO, json.dumps(cuerpo))

    def test_2_limpio_declara_lista_vacia(self):
        """Estado 3. Lista vacia declarada, distinta de no haber mirado."""
        cod, cuerpo = self._frontera("hola, aqui no hay nada")
        self.assertEqual(cod, 200)
        self.assertEqual(cuerpo["hallazgos"], [])

    def test_3_fail_closed_devuelve_409(self):
        """Estado 4. Si el filtro no termina, 409 y NINGUN texto de vuelta."""
        with mock.patch.object(
                PWA.G, "preparar_envio",
                side_effect=G.EnvioBloqueado("el filtro no pudo completarse")):
            cod, cuerpo = self._frontera("lo que sea")
        self.assertEqual(cod, 409)
        self.assertEqual(cuerpo["estado"], "bloqueado")
        # La que sostiene la promesa: no hay campo por el que colar el texto.
        self.assertNotIn("texto", cuerpo)

    def test_4_texto_que_no_es_texto(self):
        PWA.PWA._frontera(self.h, {"texto": {"no": "soy texto"}})
        self.assertEqual(self.h.codigo, 400)


class TestCaptura(unittest.TestCase):

    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.db = os.path.join(self.tmp.name, "memory.db")
        memory.crear(self.db)
        with memory.abrir(self.db) as c:
            self.tid = captura.registrar(c, "una pregunta", "una respuesta")
        self.h = Fingida(self.db)

    def tearDown(self):
        self.tmp.cleanup()

    def test_5_listar_no_consiente_por_nadie(self):
        PWA.PWA._captura_listar(self.h)
        self.assertEqual(self.h.codigo, 200)
        self.assertEqual(self.h.cuerpo["recuento"]["consentidos"], 0)
        self.assertFalse(self.h.cuerpo["turnos"][0]["consent"])

    def test_6_consentir_es_uno_por_peticion(self):
        PWA.PWA._captura_marcar(self.h, {"id": self.tid, "consent": True})
        self.assertEqual(self.h.cuerpo["recuento"]["consentidos"], 1)
        PWA.PWA._captura_marcar(self.h, {"id": self.tid, "consent": False})
        self.assertEqual(self.h.cuerpo["recuento"]["consentidos"], 0)

    def test_7_id_que_no_es_id(self):
        PWA.PWA._captura_marcar(self.h, {"id": "todos", "consent": True})
        self.assertEqual(self.h.codigo, 400)


if __name__ == "__main__":
    unittest.main(verbosity=2)
