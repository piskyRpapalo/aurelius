#!/usr/bin/env python3
"""Lanzador · doble clic, y Aurelius abre. Solo biblioteca estándar.

Esto NO es una capa nueva sobre el producto: es la puerta para quien no abre
una terminal. Arranca el mismo servidor de `bin/aurelius-pwa`, en el mismo
puerto, contra la misma memoria. Si algo falla, lo dice en una ventana del
navegador en vez de en una consola que esta persona no va a mirar.

LO QUE VA DENTRO Y LO QUE NO
----------------------------
Dentro va el producto entero, y cabe porque es biblioteca estándar: sin esa
disciplina no habría un fichero único que empaquetar. Fuera se quedan las dos
piezas grandes, y el lanzador **lo dice en vez de fingir**:

* el motor (`llama-completion`), que es código ejecutable de terceros;
* el cerebro (2,3 GiB), que se descarga con su licencia y su huella delante,
  y lo acepta la persona.

Sin ellos, Aurelius **pregunta y recuerda pero no conversa**. Es exactamente la
descripción honesta que ya está en el README, y esta puerta no promete más.
"""
from __future__ import annotations

import os
import socket
import sys
import threading
import time
import webbrowser

PUERTO = int(os.environ.get("AURELIUS_PWA_PUERTO", "8740"))

# PIEZAS DECLARADAS PARA EL EMPAQUETADOR, Y NO ES CEREMONIA.
# El servidor se carga desde un fichero de datos, asi que el analizador
# estatico de PyInstaller no ve NINGUNO de sus imports: construia un binario
# de 13 MB que moria con "No module named 'json'". Nombrarlas aqui es lo que
# hace que entren en el paquete, y de paso deja escrito de que depende esta
# puerta -- que es una lista corta, y esa es la gracia.
if False:                                    # nunca se ejecuta; se analiza
    import argparse, contextlib, hashlib, json, re, shutil, sqlite3   # noqa
    import subprocess, unicodedata, urllib.request, uuid, datetime    # noqa
    import http.server, socketserver, sqlite3, base64, difflib        # noqa


def raiz_empaquetada():
    """Donde vive el producto: dentro del paquete, o al lado del guion."""
    if getattr(sys, "frozen", False):
        return getattr(sys, "_MEIPASS", os.path.dirname(sys.executable))
    return os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def puerto_ocupado(puerto):
    with socket.socket() as s:
        s.settimeout(0.4)
        return s.connect_ex(("127.0.0.1", puerto)) == 0


def main():
    raiz = raiz_empaquetada()
    sys.path.insert(0, raiz)

    # Ya hay uno: se abre el navegador y no se arranca un segundo. Dos
    # servidores sobre la misma memoria es la forma mas rapida de que la
    # persona vea una cosa y el fichero diga otra.
    if puerto_ocupado(PUERTO):
        webbrowser.open(f"http://127.0.0.1:{PUERTO}/")
        print("Aurelius ya estaba abierto.")
        return 0

    os.chdir(raiz)
    try:
        import importlib.util
        from importlib.machinery import SourceFileLoader
        ruta = os.path.join(raiz, "bin", "aurelius-pwa")
        spec = importlib.util.spec_from_loader(
            "aurelius_pwa", SourceFileLoader("aurelius_pwa", ruta))
        modulo = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(modulo)
    except Exception as e:
        print(f"No pude arrancar Aurelius: {type(e).__name__}: {e}",
              file=sys.stderr)
        input("Pulsa Enter para cerrar. ")
        return 1

    hilo = threading.Thread(target=lambda: modulo.main([]), daemon=True)
    hilo.start()

    # Se espera a que RESPONDA antes de abrir el navegador. Abrirlo antes
    # ensena un error de conexion a quien no sabe que eso es normal, y la
    # primera impresion del producto pasa a ser una pagina rota.
    for _ in range(40):
        time.sleep(0.25)
        if puerto_ocupado(PUERTO):
            break
    else:
        print("El servidor no llegó a responder.", file=sys.stderr)
        input("Pulsa Enter para cerrar. ")
        return 1

    webbrowser.open(f"http://127.0.0.1:{PUERTO}/")
    print(f"Aurelius está abierto en http://127.0.0.1:{PUERTO}")
    print("Cierra esta ventana para apagarlo.")
    try:
        while hilo.is_alive():
            hilo.join(timeout=1)
    except KeyboardInterrupt:
        pass
    return 0


if __name__ == "__main__":
    sys.exit(main())
