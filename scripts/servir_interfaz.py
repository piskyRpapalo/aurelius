#!/usr/bin/env python3
"""Servidor de la cara de Aurelius (Misión 2.3) + API de ESTADO del Camino.

Sirve `~/aurelius/interface/` en el puerto 8050 (0.0.0.0 → tailnet del Soberano).
Además de ficheros estáticos, expone una API mínima para que el Camino del
Soberano sea RECORRIBLE con estado persistente REAL en disco (el system prompt NO
escribe ficheros — esta API sí):

    GET  /api/estado             → estado_del_soberano.json
    POST /api/totem              → M0·El Tótem: guarda el avatar subido, calcula su
                                    SHA-256, fija nombre/totem_hash/creado, avanza a M1.
                                    Cabeceras: X-Nombre, X-Ext (png|jpg|webp). Cuerpo = bytes de la imagen.
    POST /api/modulo/completar   → M1/M2: {modulo:"M1"|"M2", prueba:"<sha256>"} — el
                                    usuario firmó en SU terminal (IronClaw); aquí se registra.

La verdad del estado vive en `sovereign_vault/estado_del_soberano.json`. Cierre
limpio con Ctrl-C o SIGTERM (systemd).

Uso:
    python3 scripts/servir_interfaz.py [--puerto 8050] [--host 0.0.0.0]
"""

from __future__ import annotations

import argparse
import contextlib
import datetime as _dt
import functools
import hashlib
import http.server
import json
import re
import shutil
import signal
import socket
import socketserver
import subprocess
import sys
import urllib.request
from pathlib import Path
from types import FrameType
from typing import Any, NoReturn

# La raíz servida: el hermano `interface/` junto a `scripts/`.
RAIZ_INTERFAZ: Path = (Path(__file__).resolve().parent.parent / "interface").resolve()
VAULT: Path = (Path(__file__).resolve().parent.parent / "sovereign_vault").resolve()
ESTADO_JSON: Path = VAULT / "estado_del_soberano.json"
M0_DIR: Path = VAULT / "M0_Totem"
GENESIS_PY: Path = Path("/home/pisky/p0x/monje/genesis.py")  # auditoría de hardware honesta (se INVOCA, no se toca)
OLLAMA_TAGS: str = "http://127.0.0.1:11434/api/tags"
HERRAMIENTAS: tuple[str, ...] = ("python3", "git", "ollama", "docker", "ffmpeg", "node", "uv", "whisper", "yt-dlp")
VERBOSIDADES: frozenset[str] = frozenset({"breve", "normal", "detallado"})
LOCALES: frozenset[str] = frozenset({"en", "es"})
PUERTO_DEFECTO: int = 8050
HOST_DEFECTO: str = "0.0.0.0"  # tailnet, no solo loopback

# Orden canónico del Camino (system prompt: M0 Tótem · M1 Fuego · M2 Agua · …).
ORDEN: tuple[str, ...] = ("M0", "M1", "M2", "M3", "M4", "M5")
EXT_PERMITIDAS: frozenset[str] = frozenset({"png", "jpg", "jpeg", "webp"})
MAX_TOTEM_BYTES: int = 8 * 1024 * 1024  # 8 MB — un avatar, no un vídeo
SHA256_RE = re.compile(r"^[0-9a-f]{64}$")

_ESTADO_BASE: dict[str, Any] = {
    "nombre": None,
    "totem_hash": None,
    "modulo_actual": "M0",
    "modulos_completados": [],
    "creado": None,
    "pruebas": {},  # campo aditivo declarado: {modulo: sha256 firmado por el usuario}
    "verbosidad": "normal",  # §barra de verbosidad: breve|normal|detallado
    "locale": "en",  # idioma base canon (inglés); el desplegable lo cambia
    "inventario": None,  # snapshot del inventario (hardware genesis + software)
}


def _ahora_iso() -> str:
    return _dt.datetime.now(_dt.timezone.utc).isoformat()


def _slug(texto: str) -> str:
    limpio = re.sub(r"[^a-z0-9]+", "-", texto.lower()).strip("-")
    return limpio or "soberano"


def _leer_estado() -> dict[str, Any]:
    """Lee el estado del disco, defensivo: si falta o está corrupto, base limpia."""
    base = dict(_ESTADO_BASE)
    base["modulos_completados"] = []
    base["pruebas"] = {}
    if not ESTADO_JSON.exists():
        return base
    try:
        crudo = json.loads(ESTADO_JSON.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError):
        return base
    if not isinstance(crudo, dict):
        return base
    for clave, defecto in _ESTADO_BASE.items():
        valor = crudo.get(clave, defecto)
        base[clave] = valor if valor is not None else defecto
    if not isinstance(base["modulos_completados"], list):
        base["modulos_completados"] = []
    if not isinstance(base["pruebas"], dict):
        base["pruebas"] = {}
    return base


def _escribir_estado(estado: dict[str, Any]) -> None:
    ESTADO_JSON.parent.mkdir(parents=True, exist_ok=True)
    ESTADO_JSON.write_text(json.dumps(estado, ensure_ascii=False, indent=2), encoding="utf-8")


def _avanzar(estado: dict[str, Any], modulo: str) -> None:
    """Marca `modulo` como completado y fija modulo_actual al siguiente del Camino."""
    if modulo not in estado["modulos_completados"]:
        estado["modulos_completados"].append(modulo)
    if modulo in ORDEN:
        i = ORDEN.index(modulo)
        estado["modulo_actual"] = ORDEN[i + 1] if i + 1 < len(ORDEN) else modulo


def _sha256_bytes(datos: bytes) -> str:
    h = hashlib.sha256()
    h.update(datos)
    return h.hexdigest()


def _genesis_hw() -> dict[str, Any]:
    """Invoca genesis.py (auditoría de hardware honesta) por subprocess — NO lo toca
    (su guard isinstance es inviolable). Si falla, hardware desconocido, no inventado."""
    if not GENESIS_PY.exists():
        return {"estado": "desconocido", "motivo": f"no existe {GENESIS_PY}"}
    try:
        out = subprocess.run(
            [sys.executable, str(GENESIS_PY)], capture_output=True, text=True, timeout=25,
        )
    except (subprocess.SubprocessError, OSError) as e:
        return {"estado": "desconocido", "motivo": f"{type(e).__name__}: {e}"[:200]}
    if out.returncode != 0:
        return {"estado": "desconocido", "motivo": (out.stderr or "genesis error").strip()[:200]}
    try:
        return json.loads(out.stdout)
    except json.JSONDecodeError:
        return {"estado": "desconocido", "motivo": "genesis no devolvió JSON"}


def _ollama_modelos() -> dict[str, Any]:
    """Software: modelos instalados vía /api/tags. Honesto si Ollama no responde."""
    try:
        with urllib.request.urlopen(OLLAMA_TAGS, timeout=6) as r:
            data = json.loads(r.read().decode("utf-8"))
    except Exception as e:  # noqa: BLE001 — red/parse: degradación honesta
        return {"estado": "desconocido", "motivo": f"ollama no responde ({e})"[:160], "modelos": []}
    modelos = [
        {
            "name": m.get("name"),
            "size_bytes": m.get("size"),
            "familia": (m.get("details") or {}).get("family"),
            "parametros": (m.get("details") or {}).get("parameter_size"),
            "cuantizacion": (m.get("details") or {}).get("quantization_level"),
        }
        for m in data.get("models", [])
    ]
    return {"estado": "vivo", "modelos": modelos}


def _herramientas() -> dict[str, bool]:
    """Presencia de herramientas detectables (which). Ausente = False honesto."""
    return {t: shutil.which(t) is not None for t in HERRAMIENTAS}


def _inventario() -> dict[str, Any]:
    """Inventario del Soberano: hardware (genesis) + software (ollama, herramientas)."""
    ol = _ollama_modelos()
    return {
        "hardware": _genesis_hw(),
        "software": {
            "ollama": ol.get("estado"),
            "modelos_ollama": ol.get("modelos", []),
            "herramientas": _herramientas(),
        },
        "generado": _ahora_iso(),
        "nota": "honest sensors: lo no detectado se marca desconocido, no se inventa",
    }


class Manejador(http.server.SimpleHTTPRequestHandler):
    """Estáticos anclados a `interface/` + API de estado del Camino. Sin caché."""

    # ---- utilidades de respuesta ----
    def _json(self, cuerpo: dict[str, Any], codigo: int = 200) -> None:
        datos = json.dumps(cuerpo, ensure_ascii=False).encode("utf-8")
        self.send_response(codigo)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(datos)))
        self.end_headers()
        self.wfile.write(datos)

    def _leer_cuerpo(self) -> bytes:
        try:
            n = int(self.headers.get("Content-Length", "0"))
        except ValueError:
            return b""
        return self.rfile.read(n) if n > 0 else b""

    def end_headers(self) -> None:
        # La cara es un artefacto vivo en desarrollo: nada de caché agresiva.
        self.send_header("Cache-Control", "no-store, must-revalidate")
        super().end_headers()

    def log_message(self, formato: str, *args: object) -> None:
        sys.stderr.write("[aurelius-8050] %s - %s\n" % (self.address_string(), formato % args))

    # ---- API ----
    def do_GET(self) -> None:  # noqa: N802 (firma de la stdlib)
        ruta = self.path.split("?", 1)[0]
        if ruta == "/api/estado":
            self._json(_leer_estado())
            return
        if ruta == "/api/inventario":
            inv = _inventario()
            estado = _leer_estado()
            estado["inventario"] = inv  # snapshot en el estado del Soberano
            _escribir_estado(estado)
            self._json(inv)
            return
        super().do_GET()

    def do_POST(self) -> None:  # noqa: N802
        ruta = self.path.split("?", 1)[0]
        try:
            if ruta == "/api/totem":
                self._post_totem()
            elif ruta == "/api/modulo/completar":
                self._post_completar()
            elif ruta == "/api/preferencia":
                self._post_preferencia()
            else:
                self._json({"error": "ruta desconocida"}, 404)
        except Exception as e:  # degradación honesta, nunca 500 opaco sin cuerpo
            self._json({"error": f"{type(e).__name__}: {e}"}, 500)

    def _post_totem(self) -> None:
        """M0·El Tótem: guarda el avatar, lo sella por hash, fija identidad, avanza a M1."""
        nombre = (self.headers.get("X-Nombre", "") or "").strip()
        ext = (self.headers.get("X-Ext", "png") or "png").strip().lower()
        if nombre == "":
            self._json({"error": "falta X-Nombre (¿cómo te llamas, soberano?)"}, 400)
            return
        if ext not in EXT_PERMITIDAS:
            self._json({"error": f"extensión no permitida: {ext}"}, 400)
            return
        datos = self._leer_cuerpo()
        if len(datos) == 0:
            self._json({"error": "cuerpo vacío: sube la imagen del Tótem"}, 400)
            return
        if len(datos) > MAX_TOTEM_BYTES:
            self._json({"error": "el Tótem supera 8 MB (es un avatar, no un vídeo)"}, 400)
            return

        M0_DIR.mkdir(parents=True, exist_ok=True)
        destino = M0_DIR / f"totem-{_slug(nombre)}.{ext}"
        destino.write_bytes(datos)
        sha = _sha256_bytes(datos)
        # Log de validación por hash (mismo formato que firmar_artefacto.py).
        sig = {
            "nombre": destino.name,
            "sha256": sha,
            "timestamp_iso": _ahora_iso(),
            "tamano_bytes": len(datos),
            "fase": "hash-M0-M2",
            "prueba": "integridad (no autoria; la firma con clave Ed25519 llega en M3)",
        }
        destino.with_name(destino.name + ".sig.json").write_text(
            json.dumps(sig, ensure_ascii=False, indent=2), encoding="utf-8"
        )

        estado = _leer_estado()
        estado["nombre"] = nombre
        estado["totem_hash"] = sha
        if estado["creado"] is None:
            estado["creado"] = _ahora_iso()
        estado["pruebas"]["M0"] = sha
        _avanzar(estado, "M0")
        _escribir_estado(estado)
        self._json({"ok": True, "sha256": sha, "totem": str(destino), "estado": estado})

    def _post_completar(self) -> None:
        """M1/M2: registra la firma que el usuario hizo en SU terminal (IronClaw)."""
        try:
            cuerpo = json.loads(self._leer_cuerpo() or b"{}")
        except json.JSONDecodeError:
            self._json({"error": "JSON inválido"}, 400)
            return
        modulo = str(cuerpo.get("modulo", "")).strip().upper()
        prueba = str(cuerpo.get("prueba", "")).strip().lower()
        if modulo not in ("M1", "M2"):
            self._json({"error": "modulo debe ser M1 o M2"}, 400)
            return
        if not SHA256_RE.match(prueba):
            self._json({"error": "prueba debe ser un SHA-256 (64 hex) — fírmalo en tu terminal primero"}, 400)
            return
        estado = _leer_estado()
        if estado["nombre"] is None:
            self._json({"error": "primero forja tu Tótem (M0)"}, 409)
            return
        estado["pruebas"][modulo] = prueba
        _avanzar(estado, modulo)
        _escribir_estado(estado)
        self._json({"ok": True, "estado": estado})

    def _post_preferencia(self) -> None:
        """§verbosidad + idioma: persiste la preferencia del usuario en el estado."""
        try:
            cuerpo = json.loads(self._leer_cuerpo() or b"{}")
        except json.JSONDecodeError:
            self._json({"error": "JSON inválido"}, 400)
            return
        estado = _leer_estado()
        cambiado = False
        verb = str(cuerpo.get("verbosidad", "")).strip().lower()
        if verb in VERBOSIDADES:
            estado["verbosidad"] = verb
            cambiado = True
        loc = str(cuerpo.get("locale", "")).strip().lower()
        if loc in LOCALES:
            estado["locale"] = loc
            cambiado = True
        if not cambiado:
            self._json({"error": "nada válido (verbosidad: breve|normal|detallado; locale: en|es)"}, 400)
            return
        _escribir_estado(estado)
        self._json({"ok": True, "estado": estado})


def _construir_servidor(host: str, puerto: int) -> socketserver.TCPServer:
    """Crea el TCPServer con SO_REUSEADDR y el handler anclado a la raíz."""
    if not RAIZ_INTERFAZ.is_dir():
        raise FileNotFoundError(f"no existe el directorio a servir: {RAIZ_INTERFAZ}")
    cara = RAIZ_INTERFAZ / "aurelius_face.html"
    if not cara.is_file():
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
