#!/usr/bin/env python3
"""El puente · el camino de vuelta sin terminal · Batería Roja Pu-a…Pu-e.

Rojo Pu-a: la cara por defecto no lleva red; solo con `--puente` la lleva.
Rojo Pu-b: el puente escribe EXACTAMENTE lo que escribiría el comando.
Rojo Pu-c: no escucha fuera de esta máquina salvo que se le diga.
Rojo Pu-d: un cuerpo que no es un formulario se bloquea y no escribe nada.
Rojo Pu-e: el puente no borra: aplicar dos veces añade, nunca reemplaza.

Por qué existe el puente, en una línea: una página abierta desde el disco no
puede escribir en tu base de datos — ningún navegador lo permite —, así que sin
algo que escuche en la propia máquina el único camino de vuelta es un comando,
y en un teléfono un comando es un callejón sin salida.

Y por qué es opcional: la cara que recibe cualquiera que clone el repositorio
sigue sin una sola línea de red. Pu-a es el rojo que lo sostiene.

sistema: MVP · solo biblioteca estándar. Sin dependencias.
"""
from __future__ import annotations

import importlib.util
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
import threading
import unittest
import urllib.error
import urllib.request
from http.server import ThreadingHTTPServer

AQUI = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, AQUI)

import memory as M                                          # noqa: E402


def _cargar_puente():
    """`bin/aurelius-puente` no lleva extensión: se carga por ruta."""
    ruta = os.path.join(AQUI, "bin", "aurelius-puente")
    spec = importlib.util.spec_from_loader(
        "aurelius_puente",
        importlib.machinery.SourceFileLoader("aurelius_puente", ruta))
    modulo = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(modulo)
    return modulo


P = _cargar_puente()

FORMULARIO = {
    "engrams": [
        {"what": "la impresora funcionó al cambiar un cable",
         "why": "llevaba un mes sin imprimir", "where_ref": "el taller",
         "learned": "mirar el cable antes que el driver"},
        {"what": "recuperé la base de una copia", "why": "", "where_ref": "",
         "learned": ""},
    ],
    "profile": {"device": "el portátil de la cocina"},
    "language": "es",
}


class TestPuente(unittest.TestCase):

    def setUp(self):
        self.tmpdir = tempfile.TemporaryDirectory()
        self.db = os.path.join(self.tmpdir.name, "memory.db")
        M.crear(self.db)

    def tearDown(self):
        self.tmpdir.cleanup()

    # ------------------------------------------------------------------
    def _servir(self, db):
        """Un puente de verdad, en un puerto efímero de loopback."""
        # Callado: una tanda que escupe una linea por peticion deja de leerse.
        class Mudo(P.Puente):
            def log_message(self, formato, *args):
                pass

        servidor = ThreadingHTTPServer(("127.0.0.1", 0), Mudo)
        servidor.ruta_db = db
        servidor.ruta_cara = getattr(self, "ruta_cara", os.path.join(
            self.tmpdir.name, "cara.html"))
        hilo = threading.Thread(target=servidor.serve_forever, daemon=True)
        hilo.start()
        self.addCleanup(servidor.shutdown)
        self.addCleanup(servidor.server_close)
        return "http://127.0.0.1:%d" % servidor.server_address[1]

    def _postear(self, origen, cuerpo, ruta="/aplicar"):
        datos = cuerpo if isinstance(cuerpo, bytes) else \
            json.dumps(cuerpo).encode("utf-8")
        pet = urllib.request.Request(
            origen + ruta, data=datos, method="POST",
            headers={"Content-Type": "application/json"})
        try:
            with urllib.request.urlopen(pet, timeout=10) as r:
                return r.status, json.loads(r.read().decode("utf-8"))
        except urllib.error.HTTPError as e:
            with e:
                return e.code, json.loads(e.read().decode("utf-8"))

    def _memoria(self, db):
        """Lo que hay escrito, en una forma comparable."""
        with M.abrir(db) as c:
            engramas = [(f["what"], f["why"], f["where_ref"], f["learned"])
                        for f in c.execute(
                            "select * from engrams order by id")]
            perfil = M.leer_perfil(c)
        return engramas, perfil

    # ------------------------------------------------------------------
    # Rojo Pu-a: la red es opcional, y por defecto no está
    # ------------------------------------------------------------------
    def test_rojo_pua_la_cara_por_defecto_no_lleva_red(self):
        """Quien clona el repositorio recibe una cara que no habla con nadie."""
        salida = os.path.join(self.tmpdir.name, "cara.html")
        orden = [sys.executable, "cara.py", "--db", self.db, "--out", salida,
                 "--sin-voz"]
        subprocess.run(orden, cwd=AQUI, capture_output=True, text=True,
                       timeout=120, check=True)
        html = open(salida, encoding="utf-8").read()
        for patron in (r"fetch\s*\(", r"XMLHttpRequest", r"https?://"):
            self.assertFalse(re.search(patron, html, re.I),
                             f"la cara por defecto lleva red: {patron}")
        self.assertNotIn("pz-auto", html, "y tampoco el botón que la usaría")

        # Con la bandera, y solo con ella, aparecen las dos cosas.
        subprocess.run(orden + ["--puente", "http://127.0.0.1:8734"],
                       cwd=AQUI, capture_output=True, text=True,
                       timeout=120, check=True)
        html = open(salida, encoding="utf-8").read()
        self.assertIn("pz-auto", html, "con --puente el botón tiene que existir")
        self.assertTrue(re.search(r"fetch\s*\(", html),
                        "y tiene que poder hablar con el puente")

    # ------------------------------------------------------------------
    # Rojo Pu-b: el botón hace lo mismo que el comando
    # ------------------------------------------------------------------
    def test_rojo_pub_el_puente_escribe_lo_mismo_que_el_comando(self):
        """Dos memorias, dos caminos, un resultado idéntico.

        Si algún día divergen, este rojo lo dice antes que la persona: un botón
        que hace *casi* lo mismo que el comando es peor que no tenerlo.
        """
        por_comando = os.path.join(self.tmpdir.name, "comando.db")
        M.crear(por_comando)
        ruta_json = os.path.join(self.tmpdir.name, "formulario.json")
        with open(ruta_json, "w", encoding="utf-8") as fh:
            json.dump(FORMULARIO, fh)
        subprocess.run([sys.executable, "cara.py", "--aplicar", ruta_json,
                        "--db", por_comando], cwd=AQUI, capture_output=True,
                       text=True, timeout=120, check=True)

        origen = self._servir(self.db)
        codigo, respuesta = self._postear(origen, FORMULARIO)

        self.assertEqual(codigo, 200, respuesta)
        self.assertEqual(respuesta["estado"], "ok")
        self.assertEqual(self._memoria(self.db), self._memoria(por_comando),
                         "el puente y el comando han escrito cosas distintas")

    # ------------------------------------------------------------------
    # Rojo Pu-c: no escucha fuera de esta máquina
    # ------------------------------------------------------------------
    def test_rojo_puc_loopback_por_defecto(self):
        """Sin variable de entorno, loopback. Un puerto abierto es una puerta."""
        self.assertEqual(P.BIND, "127.0.0.1",
                         "el puente no puede nacer escuchando fuera")
        fuente = open(os.path.join(AQUI, "bin", "aurelius-puente"),
                      encoding="utf-8").read()
        self.assertNotIn('"0.0.0.0"', fuente,
                         "ninguna dirección abierta escrita en el repo")
        self.assertIn("AURELIUS_PUENTE_BIND", fuente,
                      "la dirección se declara por entorno, no en el árbol")

    # ------------------------------------------------------------------
    # Rojo Pu-d: lo que no es un formulario no entra
    # ------------------------------------------------------------------
    def test_rojo_pud_basura_no_escribe_nada(self):
        """Un cuerpo ilegible se bloquea, y la memoria queda como estaba."""
        origen = self._servir(self.db)
        antes = self._memoria(self.db)

        codigo, respuesta = self._postear(origen, b"{esto no es json")
        self.assertEqual(codigo, 400)
        self.assertEqual(respuesta["estado"], "bloqueado")
        self.assertNotIn("json", respuesta["motivo"].lower().replace("jsondecodeerror", ""),
                         "el motivo va por tipo, no arrastra el cuerpo")

        codigo, _ = self._postear(origen, FORMULARIO, ruta="/otra-cosa")
        self.assertEqual(codigo, 404, "solo se atiende /aplicar")

        self.assertEqual(self._memoria(self.db), antes,
                         "nada de esto pudo escribir en la memoria")

    # ------------------------------------------------------------------
    # Rojo Pu-e: el puente añade; nunca reemplaza
    # ------------------------------------------------------------------
    def test_rojo_pue_aplicar_dos_veces_anade(self):
        """El contrato de aplicar_formulario se conserva a través del puente."""
        origen = self._servir(self.db)
        self._postear(origen, FORMULARIO)
        engramas_1, _ = self._memoria(self.db)
        self._postear(origen, FORMULARIO)
        engramas_2, _ = self._memoria(self.db)

        self.assertEqual(len(engramas_2), len(engramas_1) * 2,
                         "aplicar dos veces añade dos veces: nada se reemplaza")
        self.assertEqual(engramas_2[:len(engramas_1)], engramas_1,
                         "y lo primero que se escribió sigue igual")


    # ------------------------------------------------------------------
    # Rojo Pu-f: sirve la cara, y NADA mas
    # ------------------------------------------------------------------
    def test_rojo_puf_sirve_la_cara_y_solo_la_cara(self):
        """Un servidor que sirve un directorio sirve la memoria de alguien."""
        self.ruta_cara = os.path.join(self.tmpdir.name, "cara.html")
        with open(self.ruta_cara, "w", encoding="utf-8") as fh:
            fh.write("<html>la cara</html>")
        origen = self._servir(self.db)

        with urllib.request.urlopen(origen + "/", timeout=10) as r:
            self.assertEqual(r.status, 200)
            self.assertIn("la cara", r.read().decode("utf-8"))

        for ruta in ("/memory.db", "/../memory.db", "/policies.json", "/bin/"):
            try:
                with urllib.request.urlopen(origen + ruta, timeout=10) as r:
                    self.fail(f"el puente sirvio {ruta}")
            except urllib.error.HTTPError as e:
                with e:
                    self.assertEqual(e.code, 404, f"{ruta} no dio 404")

if __name__ == '__main__':
    unittest.main(verbosity=2)
