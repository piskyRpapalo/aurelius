#!/usr/bin/env python3
"""Servidor de la cara de Aurelius (Misión 2.3) + API de ESTADO del Camino.

Sirve `interface/` en el puerto 8050 (0.0.0.0 → alcanzable en la red local).
Además de ficheros estáticos, expone una API mínima para que el Camino del
Soberano sea RECORRIBLE con estado persistente REAL en disco (el system prompt NO
escribe ficheros — esta API sí):

    GET  /api/estado             → estado_del_soberano.json
    POST /api/totem              → M0·El Tótem: guarda el avatar subido, calcula su
                                    SHA-256, fija nombre/totem_hash/creado, avanza a M1.
                                    Cabeceras: X-Nombre, X-Ext (png|jpg|webp). Cuerpo = bytes de la imagen.
    POST /api/modulo/completar   → M1/M2: {modulo:"M1"|"M2", prueba:"<sha256>"} — el
                                    usuario firmó en SU terminal (IronClaw); aquí se registra.
    GET  /api/anclaje            → El Anclaje (Método v1 §3): las dos listas + el
                                    contenido CRUDO de sus dos ficheros de texto plano.
    POST /api/anclaje/declaracion→ {modulo, confianza:1-5, sin_ayuda:bool} ANTES del módulo.
    POST /api/anclaje/resultado  → {modulo, resultado:"completo"|"parcial"|"no"} DESPUÉS.
    POST /api/anclaje/borrar     → borrado total del registro de calibración, sin fricción.

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
import os
import re
import shutil
import signal
import socket
import socketserver
import subprocess
import sys
import urllib.parse
import urllib.request
from pathlib import Path
from types import FrameType
from typing import Any, NoReturn

# La raíz servida: el hermano `interface/` junto a `scripts/`.
RAIZ_INTERFAZ: Path = (Path(__file__).resolve().parent.parent / "interface").resolve()
VAULT: Path = (Path(__file__).resolve().parent.parent / "sovereign_vault").resolve()
# MULTIUSUARIO (misión hermanos, 2026-07-27): el estado ya NO es un único fichero
# — vive por soberano en sovereign_vault/estado/<slug>.json. El fichero legado
# (monousuario) se migra a estado/soberano.json al arrancar y se conserva como
# respaldo. LÍMITE HONESTO: esto es SEPARACIÓN DE ESTADO para hermanos de
# confianza en un tailnet privado, NO autenticación — cualquiera con el enlace
# puede escribir el nombre de otro. Auth real es feature futura.
ESTADO_DIR: Path = VAULT / "estado"
ESTADO_LEGADO: Path = VAULT / "estado_del_soberano.json"
SLUG_MAX: int = 40
SLUG_RE = re.compile(r"^[a-z0-9][a-z0-9-]{0,39}$")  # lista blanca estricta
M0_DIR: Path = VAULT / "M0_Totem"
# EL ANCLAJE (Metodo v1 §3): dos ficheros de TEXTO PLANO por soberano — uno de
# declaraciones previas, uno de resultados observados. Separados a proposito: la
# declaracion se firma ANTES del modulo y el resultado se anota DESPUES, y tenerlos
# en el mismo fichero invitaria a editar la prediccion sabiendo ya como acabo.
# Son de anexion: una correccion es una linea nueva, no una linea reescrita.
ANCLAJE_DIR: Path = VAULT / "anclaje"
# Auditoría de hardware honesta: se INVOCA (no se toca) un script externo si el
# operador lo configura por env. Sin él, el inventario rinde "desconocido"
# (honest sensors). Sin ruta del núcleo hardcodeada — portable.
_GENESIS_ENV: str = os.environ.get("AURELIUS_GENESIS_PY", "")
GENESIS_PY: Path = Path(_GENESIS_ENV) if _GENESIS_ENV else Path("/nonexistent/hw-audit")
OLLAMA_TAGS: str = "http://127.0.0.1:11434/api/tags"
HERRAMIENTAS: tuple[str, ...] = ("python3", "git", "ollama", "docker", "ffmpeg", "node", "uv", "whisper", "yt-dlp")
VERBOSIDADES: frozenset[str] = frozenset({"breve", "normal", "detallado"})
LOCALES: frozenset[str] = frozenset({"en", "es", "fr", "pt", "de", "el", "ru"})
# Onboarding guiado del Tótem (M0): nivel condiciona la PROFUNDIDAD de las
# explicaciones (Scaffolding Fading); tono ajusta el ESTILO — JAMÁS las reglas.
NIVELES: frozenset[str] = frozenset({"principiante", "intermedio", "avanzado"})
TONOS: frozenset[str] = frozenset({"sereno", "directo", "didactico"})
PUERTO_DEFECTO: int = 8050
HOST_DEFECTO: str = "0.0.0.0"  # tailnet, no solo loopback

# Orden canónico del Camino (system prompt: M0 Tótem · M1 Fuego · M2 Agua · …).
ORDEN: tuple[str, ...] = ("M0", "M1", "M2", "M3", "M4", "M5")
EXT_PERMITIDAS: frozenset[str] = frozenset({"png", "jpg", "jpeg", "webp"})
MAX_TOTEM_BYTES: int = 8 * 1024 * 1024  # 8 MB — un avatar, no un vídeo
SHA256_RE = re.compile(r"^[0-9a-f]{64}$")
# Identificador de modulo del Anclaje: misma lista blanca estricta que el slug de
# soberano. Opaco a proposito — el Anclaje no sabe ni le importa que modulos
# existen, asi que la abolicion de la numeracion (arsenal 1.3) no le afecta.
MODULO_RE = re.compile(r"^[a-z0-9][a-z0-9-]{0,39}$")
RESULTADOS: tuple[str, ...] = ("completo", "parcial", "no")
CONFIANZA_MIN: int = 1
CONFIANZA_MAX: int = 5

# Cabeceras de los dos ficheros. Llevan la formula IMPRESA (Metodo §3.3) para que
# el fichero se pueda recalcular a mano sin abrir la interfaz ni este codigo.
CABECERA_DECLARACIONES: str = (
    "# ANCLAJE · DECLARACIONES PREVIAS. Una linea por modulo, firmada ANTES de empezarlo.\n"
    "# Separado por tabuladores.  fecha\tmodulo\tconfianza(1-5)\tespera_sin_ayuda(si|no)\n"
    "# confianza_normalizada = (confianza - 1) / 4      -> valor entre 0 y 1\n"
    "# Este fichero es TUYO: texto plano, local, exportable y borrable cuando quieras.\n"
    "# Solo se anota la FECHA, jamas la hora ni cuanto tardaste: el tiempo empleado\n"
    "# no mide nada sobre ti y no se recoge (Metodo §3.4 y §4.5).\n"
)
CABECERA_RESULTADOS: str = (
    "# ANCLAJE · RESULTADOS OBSERVADOS. Una linea por modulo, anotada DESPUES de terminarlo.\n"
    "# Separado por tabuladores.  fecha\tmodulo\tresultado(completo|parcial|no)\n"
    "# resultado_normalizado:  completo = 1.0   parcial = 0.5   no = 0.0\n"
    "# delta = confianza_normalizada - resultado_normalizado\n"
    "# delta positivo -> sobreestimacion · negativo -> infraestimacion · ~0 -> calibrado\n"
    "# El indicador es la MEDIA MOVIL de los ultimos 5 modulos, nunca un modulo suelto.\n"
)

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
    "nivel": None,  # onboarding M0: principiante|intermedio|avanzado (profundidad)
    "tono": None,  # onboarding M0: sereno|directo|didactico (ESTILO, no reglas)
    "ram_declarada_gb": None,  # corrección opcional del usuario al hardware detectado
}


def _ahora_iso() -> str:
    return _dt.datetime.now(_dt.timezone.utc).isoformat()


def _slug(texto: str) -> str:
    """Slug SANEADO desde entrada de usuario → nombre de fichero seguro.
    Minúsculas, lista blanca [a-z0-9-], sin espacios ni rutas ni `..`, cap 40.
    Cualquier carácter fuera de la lista blanca colapsa a '-'; vacío → 'soberano'."""
    limpio = re.sub(r"[^a-z0-9]+", "-", texto.lower()).strip("-")[:SLUG_MAX].strip("-")
    return limpio or "soberano"


def _slug_valido(slug: str | None) -> str | None:
    """Valida un slug ya formado (viene del cliente): estricto o None. Defensa
    contra path traversal — solo [a-z0-9-], jamás `/`, `.`, `..` ni longitud loca."""
    if slug is None:
        return None
    slug = slug.strip()
    return slug if SLUG_RE.match(slug) else None


def _ruta_estado(slug: str) -> Path:
    """Ruta del estado de un soberano, ANCLADA a ESTADO_DIR (defensa en
    profundidad: aunque el slug burlara la validación, jamás sale del directorio)."""
    p = (ESTADO_DIR / f"{slug}.json").resolve()
    if not str(p).startswith(str(ESTADO_DIR.resolve()) + "/"):
        raise ValueError(f"slug fuera del directorio de estado: {slug!r}")
    return p


def _migrar_legado() -> None:
    """Migra el estado monousuario legado → estado/soberano.json UNA vez.
    Idempotente: si el destino ya existe, no toca nada. El legado se conserva."""
    ESTADO_DIR.mkdir(parents=True, exist_ok=True)
    destino = ESTADO_DIR / "soberano.json"
    if destino.exists() or not ESTADO_LEGADO.exists():
        return
    try:
        shutil.copy2(ESTADO_LEGADO, destino)
        sys.stderr.write(f"[aurelius-8050] migrado estado legado → {destino.name}\n")
    except OSError as e:
        sys.stderr.write(f"[aurelius-8050] AVISO: no se pudo migrar el legado ({e})\n")


def _base_estado() -> dict[str, Any]:
    """Estado base limpio (usuario nuevo o sin nombre todavía — solo en memoria)."""
    base = dict(_ESTADO_BASE)
    base["modulos_completados"] = []
    base["pruebas"] = {}
    return base


def _leer_estado(slug: str | None) -> dict[str, Any]:
    """Lee el estado del soberano `slug` del disco, defensivo. Sin slug (usuario
    nuevo, aún sin nombre) → base limpia EN MEMORIA, no se escribe nada. Slug
    válido sin fichero → base (empieza su Camino en M0)."""
    base = _base_estado()
    if slug is None:
        return base
    ruta = _ruta_estado(slug)
    if not ruta.exists():
        return base
    try:
        crudo = json.loads(ruta.read_text(encoding="utf-8"))
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


def _escribir_estado(slug: str, estado: dict[str, Any]) -> None:
    """Persiste el estado del soberano `slug`. Requiere identidad — sin nombre no
    se escribe (el usuario nuevo vive en memoria hasta que se nombra en M0)."""
    ruta = _ruta_estado(slug)
    ruta.parent.mkdir(parents=True, exist_ok=True)
    ruta.write_text(json.dumps(estado, ensure_ascii=False, indent=2), encoding="utf-8")


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


# ─────────────────────────── EL ANCLAJE (Metodo v1 §3) ───────────────────────
# Mide la distancia entre lo que el usuario CREE que sabe y lo que demuestra. No
# mide capacidad. No emite juicio. Registra trayectoria.
#
# PROHIBICIONES QUE ESTE CODIGO DEBE SEGUIR CUMPLIENDO (Metodo §3.4, son suelo):
#   · CERO BIOMETRIA. Aqui no entra latencia entre pulsaciones, ritmo de escritura,
#     tiempo de pausa, camara ni microfono. Por eso se guarda la FECHA y no la hora:
#     con hora de declaracion y hora de resultado se podria derivar cuanto tardo el
#     usuario, y ese numero no mide nada sobre el.
#   · CERO OPACIDAD. No hay ningun ajuste que no este escrito en la cabecera del
#     propio fichero. Nada se corrige "por detras" para detectar trampas.
#   · CERO JUICIO. Este modulo no produce ni una cadena de texto sobre la persona.
#   · CERO USO EXTERNO. Estos ficheros no se exportan ni se comparan con nadie.
#   · BORRADO TOTAL sin friccion, ver _borrar_anclaje().


def _hoy_iso() -> str:
    """Fecha (no instante) en UTC. Deliberadamente sin hora: ver §3.4 arriba."""
    return _dt.datetime.now(_dt.timezone.utc).date().isoformat()


def _ruta_anclaje(slug: str, tipo: str) -> Path:
    """Ruta de un fichero del Anclaje, ANCLADA a ANCLAJE_DIR (misma defensa en
    profundidad que _ruta_estado: aunque el slug burlara la validacion, jamas
    sale del directorio). `tipo` es 'declaraciones' o 'resultados'."""
    if tipo not in ("declaraciones", "resultados"):
        raise ValueError(f"tipo de fichero del anclaje desconocido: {tipo!r}")
    p = (ANCLAJE_DIR / f"{slug}.{tipo}.tsv").resolve()
    if not str(p).startswith(str(ANCLAJE_DIR.resolve()) + "/"):
        raise ValueError(f"slug fuera del directorio del anclaje: {slug!r}")
    return p


def _leer_tsv(ruta: Path, campos: tuple[str, ...]) -> list[dict[str, str]]:
    """Lee un TSV del Anclaje, defensivo. Ignora comentarios, lineas vacias y
    lineas con un numero de columnas que no cuadra — un fichero editado a mano y
    mal cerrado degrada perdiendo esa linea, jamas reventando el registro entero
    (es el diario del usuario: tiene derecho a abrirlo con un editor)."""
    if not ruta.exists():
        return []
    try:
        crudo = ruta.read_text(encoding="utf-8")
    except OSError:
        return []
    filas: list[dict[str, str]] = []
    for linea in crudo.splitlines():
        if not linea.strip() or linea.lstrip().startswith("#"):
            continue
        partes = linea.split("\t")
        if len(partes) != len(campos):
            continue
        filas.append({c: partes[i].strip() for i, c in enumerate(campos)})
    return filas


def _leer_crudo(ruta: Path) -> str:
    """Contenido literal del fichero, para que la interfaz pueda ENSENARLO. La
    doctrina exige que el usuario pueda recalcular la media a mano con sus propios
    registros; para eso tiene que poder verlos tal cual estan en disco."""
    if not ruta.exists():
        return ""
    try:
        return ruta.read_text(encoding="utf-8")
    except OSError:
        return ""


def _anexar_anclaje(slug: str, tipo: str, cabecera: str, campos: list[str]) -> None:
    """Anexa una linea. Solo de anexion: una correccion es una linea nueva. Si el
    fichero no existe todavia, nace con su cabecera (que lleva la formula impresa)."""
    ruta = _ruta_anclaje(slug, tipo)
    ruta.parent.mkdir(parents=True, exist_ok=True)
    nuevo = not ruta.exists()
    with ruta.open("a", encoding="utf-8") as f:
        if nuevo:
            f.write(cabecera)
        f.write("\t".join(campos) + "\n")


def _leer_anclaje(slug: str | None) -> dict[str, Any]:
    """Registro completo del Anclaje de un soberano. Sin identidad → registro
    vacio EN MEMORIA (la pagina se pinta igual, con NO DATA honesto)."""
    if slug is None:
        return {"declaraciones": [], "resultados": [], "crudo": {"declaraciones": "", "resultados": ""}}
    d = _ruta_anclaje(slug, "declaraciones")
    r = _ruta_anclaje(slug, "resultados")
    return {
        "declaraciones": _leer_tsv(d, ("fecha", "modulo", "confianza", "sin_ayuda")),
        "resultados": _leer_tsv(r, ("fecha", "modulo", "resultado")),
        "crudo": {"declaraciones": _leer_crudo(d), "resultados": _leer_crudo(r)},
    }


def _borrar_anclaje(slug: str) -> None:
    """Borrado TOTAL del registro de calibracion, sin friccion (Metodo §3.4: el
    usuario puede borrarlo entero en cualquier momento, sin preguntas de
    confirmacion culpabilizadoras).

    Borra los dos ficheros del Anclaje y NADA MAS. El estado del Camino, el Totem
    y las pruebas del usuario no se tocan: borrar tu diario de calibracion no te
    cuesta tu progreso."""
    for tipo in ("declaraciones", "resultados"):
        with contextlib.suppress(OSError):
            _ruta_anclaje(slug, tipo).unlink(missing_ok=True)


def _genesis_hw() -> dict[str, Any]:
    """Invoca el script externo de auditoría de hardware (AURELIUS_GENESIS_PY) por
    subprocess — NO lo toca (su guardia isinstance es inviolable). Si falla o no
    está configurado, hardware desconocido, jamás inventado."""
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

    def _slug_peticion(self) -> str | None:
        """Slug del soberano de esta petición: header X-Soberano o query ?soberano=.
        Validado estricto (path traversal/basura → None). SEPARACIÓN DE ESTADO, NO
        AUTH: cualquiera con el enlace puede poner el nombre de otro (hermanos de
        confianza en tailnet privado). Auth real = feature futura."""
        crudo = self.headers.get("X-Soberano")
        if not crudo:
            consulta = urllib.parse.urlsplit(self.path).query
            vals = urllib.parse.parse_qs(consulta).get("soberano")
            crudo = vals[0] if vals else None
        return _slug_valido(crudo)

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
            self._json(_leer_estado(self._slug_peticion()))
            return
        if ruta == "/api/anclaje":
            self._json(_leer_anclaje(self._slug_peticion()))
            return
        if ruta == "/api/inventario":
            inv = _inventario()
            slug = self._slug_peticion()
            if slug is not None:  # solo se cachea en el estado de un soberano nombrado
                estado = _leer_estado(slug)
                estado["inventario"] = inv
                _escribir_estado(slug, estado)
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
            elif ruta == "/api/anclaje/declaracion":
                self._post_anclaje_declaracion()
            elif ruta == "/api/anclaje/resultado":
                self._post_anclaje_resultado()
            elif ruta == "/api/anclaje/borrar":
                self._post_anclaje_borrar()
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
            "prueba": "integridad (no autoria; la firma con clave Ed25519 llega en M5)",
        }
        destino.with_name(destino.name + ".sig.json").write_text(
            json.dumps(sig, ensure_ascii=False, indent=2), encoding="utf-8"
        )

        # El nombre DEFINE la identidad: su slug es el fichero de estado. El
        # cliente guardará este slug para sus siguientes peticiones.
        slug = _slug(nombre)
        estado = _leer_estado(slug)
        estado["nombre"] = nombre
        estado["totem_hash"] = sha
        if estado["creado"] is None:
            estado["creado"] = _ahora_iso()
        estado["pruebas"]["M0"] = sha
        _avanzar(estado, "M0")
        _escribir_estado(slug, estado)
        self._json({"ok": True, "sha256": sha, "slug": slug, "totem": str(destino), "estado": estado})

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
        slug = self._slug_peticion()
        if slug is None:
            self._json({"error": "sin identidad: forja tu Tótem (M0) para tener un Camino"}, 409)
            return
        estado = _leer_estado(slug)
        if estado["nombre"] is None:
            self._json({"error": "primero forja tu Tótem (M0)"}, 409)
            return
        estado["pruebas"][modulo] = prueba
        _avanzar(estado, modulo)
        _escribir_estado(slug, estado)
        self._json({"ok": True, "estado": estado})

    def _post_preferencia(self) -> None:
        """§verbosidad + idioma: persiste la preferencia del usuario en el estado."""
        try:
            cuerpo = json.loads(self._leer_cuerpo() or b"{}")
        except json.JSONDecodeError:
            self._json({"error": "JSON inválido"}, 400)
            return
        slug = self._slug_peticion()
        estado = _leer_estado(slug)
        cambiado = False
        verb = str(cuerpo.get("verbosidad", "")).strip().lower()
        if verb in VERBOSIDADES:
            estado["verbosidad"] = verb
            cambiado = True
        loc = str(cuerpo.get("locale", "")).strip().lower()
        if loc in LOCALES:
            estado["locale"] = loc
            cambiado = True
        niv = str(cuerpo.get("nivel", "")).strip().lower()
        if niv in NIVELES:
            estado["nivel"] = niv
            cambiado = True
        ton = str(cuerpo.get("tono", "")).strip().lower()
        if ton in TONOS:
            estado["tono"] = ton
            cambiado = True
        ram = cuerpo.get("ram_declarada_gb")
        if isinstance(ram, (int, float)) and 0 < ram <= 4096:  # defensivo: rango sano
            estado["ram_declarada_gb"] = float(ram)
            cambiado = True
        if not cambiado:
            self._json({"error": "nada válido (verbosidad/locale/nivel/tono/ram_declarada_gb)"}, 400)
            return
        # Solo se persiste con identidad; usuario nuevo (sin nombre) → en memoria.
        if slug is not None:
            _escribir_estado(slug, estado)
        self._json({"ok": True, "persistido": slug is not None, "estado": estado})

    # ---- El Anclaje (Metodo v1 §3) ----
    def _cuerpo_json(self) -> dict[str, Any] | None:
        """Cuerpo JSON de la peticion, o None si no parsea (ya respondido 400)."""
        try:
            cuerpo = json.loads(self._leer_cuerpo() or b"{}")
        except json.JSONDecodeError:
            self._json({"error": "JSON inválido"}, 400)
            return None
        if not isinstance(cuerpo, dict):
            self._json({"error": "el cuerpo debe ser un objeto JSON"}, 400)
            return None
        return cuerpo

    def _slug_o_409(self) -> str | None:
        """Identidad requerida para ESCRIBIR en el registro (el registro vive por
        soberano). La lectura sin identidad rinde registro vacio, no un error."""
        slug = self._slug_peticion()
        if slug is None:
            self._json({"error": "sin identidad: forja tu Tótem (M0) para tener registro"}, 409)
            return None
        return slug

    def _post_anclaje_declaracion(self) -> None:
        """Declaracion PREVIA: confianza 1-5 y si espera completarlo sin ayuda.
        Se firma ANTES del modulo — es la prediccion, y por eso el Anclaje cumple
        la Regla Unica. El servidor no comprueba que sea "antes": no puede, y
        fingir que puede seria opacidad. La honestidad del orden es del usuario."""
        cuerpo = self._cuerpo_json()
        if cuerpo is None:
            return
        modulo = str(cuerpo.get("modulo", "")).strip().lower()
        if not MODULO_RE.match(modulo):
            self._json({"error": "modulo inválido (minúsculas, [a-z0-9-], máx. 40)"}, 400)
            return
        conf = cuerpo.get("confianza")
        if not isinstance(conf, int) or isinstance(conf, bool) or not (CONFIANZA_MIN <= conf <= CONFIANZA_MAX):
            self._json({"error": f"confianza debe ser un entero de {CONFIANZA_MIN} a {CONFIANZA_MAX}"}, 400)
            return
        sin_ayuda = cuerpo.get("sin_ayuda")
        if not isinstance(sin_ayuda, bool):
            self._json({"error": "sin_ayuda debe ser true o false"}, 400)
            return
        slug = self._slug_o_409()
        if slug is None:
            return
        _anexar_anclaje(
            slug, "declaraciones", CABECERA_DECLARACIONES,
            [_hoy_iso(), modulo, str(conf), "si" if sin_ayuda else "no"],
        )
        self._json({"ok": True, "anclaje": _leer_anclaje(slug)})

    def _post_anclaje_resultado(self) -> None:
        """Resultado OBSERVADO tras el modulo: completo / parcial / no completado.
        Tres valores y ninguno mas: el Metodo fija la escala y el codigo no la
        amplia por su cuenta, porque cada valor nuevo cambia la formula."""
        cuerpo = self._cuerpo_json()
        if cuerpo is None:
            return
        modulo = str(cuerpo.get("modulo", "")).strip().lower()
        if not MODULO_RE.match(modulo):
            self._json({"error": "modulo inválido (minúsculas, [a-z0-9-], máx. 40)"}, 400)
            return
        resultado = str(cuerpo.get("resultado", "")).strip().lower()
        if resultado not in RESULTADOS:
            self._json({"error": f"resultado debe ser uno de: {', '.join(RESULTADOS)}"}, 400)
            return
        slug = self._slug_o_409()
        if slug is None:
            return
        _anexar_anclaje(slug, "resultados", CABECERA_RESULTADOS, [_hoy_iso(), modulo, resultado])
        self._json({"ok": True, "anclaje": _leer_anclaje(slug)})

    def _post_anclaje_borrar(self) -> None:
        """Borrado total, sin friccion y sin preguntas (Metodo §3.4). Borra los dos
        ficheros del Anclaje y nada mas: el Camino del usuario queda intacto."""
        slug = self._slug_o_409()
        if slug is None:
            return
        _borrar_anclaje(slug)
        self._json({"ok": True, "anclaje": _leer_anclaje(slug)})


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
    _migrar_legado()  # monousuario → estado/soberano.json (idempotente)
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
    # La IP se calcula en runtime (no hay hostname en el código): el endpoint del
    # modelo vive en interface/config.json (fuera de git). Barrido de reconocimiento.
    if ip is not None:
        sys.stderr.write(f"[aurelius-8050]   → LAN/tailnet: http://{ip}:{puerto}/aurelius_face.html\n")

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
