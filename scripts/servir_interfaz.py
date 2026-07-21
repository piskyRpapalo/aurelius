#!/usr/bin/env python3
"""Servidor estático de la cara de Aurelius (Misión 2.3).

Sirve `~/aurelius/interface/` en el puerto 8050, escuchando en 0.0.0.0 para que
la cara sea alcanzable desde cualquier nodo del tailnet del Soberano
(http://soberano.tailb9e0f7.ts.net:8050/aurelius_face.html) — nunca solo
localhost. Es un servidor de FICHEROS estáticos: no proxya al modelo; la propia
página hace fetch al endpoint de Ollama del Soberano. Cierre limpio con Ctrl-C
o SIGTERM (systemd).

Uso:
    python3 scripts/servir_interfaz.py [--puerto 8050] [--host 0.0.0.0]
"""

from __future__ import annotations

import argparse
import contextlib
import functools
import http.server
import signal
import socket
import socketserver
import sys
from pathlib import Path
from types import FrameType
from typing import NoReturn

# La raíz servida: el hermano `interface/` junto a `scripts/`.
RAIZ_INTERFAZ: Path = (Path(__file__).resolve().parent.parent / "interface").resolve()
PUERTO_DEFECTO: int = 8050
HOST_DEFECTO: str = "0.0.0.0"  # tailnet, no solo loopback


class Manejador(http.server.SimpleHTTPRequestHandler):
    """SimpleHTTPRequestHandler anclado a `interface/`, sin caché y silencioso."""

    def end_headers(self) -> None:
        # La cara es un artefacto vivo en desarrollo: nada de caché agresiva.
        self.send_header("Cache-Control", "no-store, must-revalidate")
        super().end_headers()

    def log_message(self, formato: str, *args: object) -> None:
        # Log compacto a stderr (systemd lo captura); sin ruido de user-agent.
        sys.stderr.write("[aurelius-8050] %s - %s\n" % (self.address_string(), formato % args))


def _construir_servidor(host: str, puerto: int) -> socketserver.TCPServer:
    """Crea el TCPServer con SO_REUSEADDR y el handler anclado a la raíz."""
    if not RAIZ_INTERFAZ.is_dir():
        raise FileNotFoundError(f"no existe el directorio a servir: {RAIZ_INTERFAZ}")
    cara = RAIZ_INTERFAZ / "aurelius_face.html"
    if not cara.is_file():
        # Defensivo: avisar, pero no abortar — el server puede servir otros ficheros.
        sys.stderr.write(f"[aurelius-8050] AVISO: no se encontró {cara}\n")

    manejador = functools.partial(Manejador, directory=str(RAIZ_INTERFAZ))
    socketserver.TCPServer.allow_reuse_address = True
    try:
        return socketserver.ThreadingTCPServer((host, puerto), manejador)
    except OSError as err:
        raise OSError(f"no se pudo abrir {host}:{puerto} ({err})") from err


def _ip_tailnet() -> str | None:
    """Mejor esfuerzo para mostrar la IP con la que salir al tailnet (informativo)."""
    with contextlib.suppress(OSError):
        with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as s:
            s.connect(("100.100.100.100", 80))  # Tailscale MagicDNS anchor, no envía nada
            return str(s.getsockname()[0])
    return None


def servir(host: str, puerto: int) -> int:
    """Levanta el servidor y bloquea hasta señal de cierre. Devuelve exit code."""
    try:
        servidor = _construir_servidor(host, puerto)
    except (FileNotFoundError, OSError) as err:
        sys.stderr.write(f"[aurelius-8050] ERROR: {err}\n")
        return 1

    # serve_forever() corre en el hilo PRINCIPAL; llamar shutdown() desde el
    # handler de señal (mismo hilo) se autobloquea. En su lugar, SIGTERM se
    # convierte en KeyboardInterrupt (SIGINT ya lo es) para romper el select del
    # bucle, y cerramos el socket en el `finally`. Patrón probado y sin deadlock.
    def _apagar(_sig: int, _frame: FrameType | None) -> NoReturn:
        raise KeyboardInterrupt

    signal.signal(signal.SIGTERM, _apagar)

    ip = _ip_tailnet()
    sys.stderr.write(f"[aurelius-8050] sirviendo {RAIZ_INTERFAZ}\n")
    sys.stderr.write(f"[aurelius-8050] escuchando en http://{host}:{puerto}\n")
    if ip is not None:
        sys.stderr.write(f"[aurelius-8050]   → tailnet: http://{ip}:{puerto}/aurelius_face.html\n")
    sys.stderr.write("[aurelius-8050]   → MagicDNS: "
                     f"http://soberano.tailb9e0f7.ts.net:{puerto}/aurelius_face.html\n")

    with servidor:
        try:
            servidor.serve_forever(poll_interval=0.5)
        except KeyboardInterrupt:
            sys.stderr.write("\n[aurelius-8050] señal recibida, cerrando…\n")
        finally:
            servidor.server_close()
    sys.stderr.write("[aurelius-8050] cerrado limpio.\n")
    return 0


def _parsear(argv: list[str]) -> argparse.Namespace:
    p = argparse.ArgumentParser(description="Sirve la cara de Aurelius en :8050 (tailnet).")
    p.add_argument("--puerto", type=int, default=PUERTO_DEFECTO, help=f"puerto (def {PUERTO_DEFECTO})")
    p.add_argument("--host", default=HOST_DEFECTO, help=f"host de escucha (def {HOST_DEFECTO})")
    return p.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = _parsear(argv if argv is not None else sys.argv[1:])
    if not (0 < args.puerto < 65536):
        sys.stderr.write(f"[aurelius-8050] ERROR: puerto inválido {args.puerto}\n")
        return 2
    return servir(args.host, args.puerto)


if __name__ == "__main__":
    raise SystemExit(main())
