#!/usr/bin/env python3
"""Elección de cerebro con hot-swap y rollback. **Solo biblioteca estándar.**

Este módulo es el único de la forja pensado para entrar algún día en el
producto, y por eso no importa nada que no traiga Python. Lo que cruza de la
forja al producto es un fichero GGUF y su huella. Nada más.

EL HALLAZGO QUE ORDENA TODO ESTO
--------------------------------
`descarga.presente()` es literalmente `huella_fichero(ruta) == pieza.sha256`.
Un GGUF afinado es otro fichero con otro sha256. Si la Fase 4 sobrescribiera
`modelos/qwen3-4b-instruct-2507-Q4_K_M.gguf`, el producto diría —con razón—
que su cerebro no está, y ofrecería descargarlo otra vez.

Así que el afinado **no sustituye al cerebro: se pone al lado**, como pieza
propia con su huella medida y firmada. Misma disciplina que el catálogo:
«huellas medidas, no heredadas». El producto lo elige solo si verifica.

Y EL REGALO QUE YA ESTABA AHÍ
-----------------------------
`motor_llama` lanza `llama-completion` como **proceso hijo en cada turno**. Eso
es lo que hace que un turno cueste 5,4-6,3 min en el teléfono... y también lo
que hace que el hot-swap sea trivial: no hay demonio que reiniciar. Cambiar a
qué fichero apunta el siguiente turno **es** el hot-swap. Sin reinicio, sin
señal, sin estado que migrar.

CONTRATO
--------
* Si el afinado no está, o su huella no cuadra, se usa el base. Sin ruido y
  sin fallar: un cerebro afinado ausente no es una avería.
* El rollback no borra nada. Escribe una preferencia, y la preferencia se lee
  en el turno siguiente.
* Nada aquí descarga, ni valida modelos por red, ni abre un socket.
"""
from __future__ import annotations

import hashlib
import json
import os
from pathlib import Path

NOMBRE_REGISTRO = "cerebro.json"
TROZO = 1024 * 1024


class Eleccion:
    """Lo que se eligió y por qué. El porqué viaja: sin él no hay auditoría."""

    __slots__ = ("ruta", "cual", "motivo")

    def __init__(self, ruta, cual, motivo):
        self.ruta, self.cual, self.motivo = ruta, cual, motivo

    def __repr__(self):
        return f"<Eleccion {self.cual} · {self.motivo}>"


def huella_fichero(ruta):
    """sha256 del fichero, por trozos. Un GGUF no cabe en memoria dos veces."""
    h = hashlib.sha256()
    try:
        with open(ruta, "rb") as fh:
            for bloque in iter(lambda: fh.read(TROZO), b""):
                h.update(bloque)
    except OSError:
        return None
    return h.hexdigest()


def _registro(raiz):
    try:
        with open(Path(raiz) / NOMBRE_REGISTRO, encoding="utf-8") as fh:
            datos = json.load(fh)
        return datos if isinstance(datos, dict) else {}
    except (OSError, json.JSONDecodeError):
        return {}


def escribir_registro(raiz, datos):
    """Escritura atómica: se escribe al lado y se renombra.

    Un registro a medio escribir es peor que ninguno -- deja al producto
    eligiendo con un fichero roto, y el rename de POSIX es lo único que
    garantiza que nadie lo lea a mitad.
    """
    raiz = Path(raiz)
    raiz.mkdir(parents=True, exist_ok=True)
    destino = raiz / NOMBRE_REGISTRO
    tmp = raiz / (NOMBRE_REGISTRO + ".parcial")
    with open(tmp, "w", encoding="utf-8") as fh:
        json.dump(datos, fh, ensure_ascii=False, indent=2)
        fh.flush()
        os.fsync(fh.fileno())
    os.replace(tmp, destino)
    return destino


def elegir(raiz, ruta_base):
    """Qué GGUF usa el siguiente turno.

    Devuelve siempre una `Eleccion`: incluso cuando no hay nada que elegir, se
    dice cuál se usa y por qué.
    """
    raiz = Path(raiz)
    reg = _registro(raiz)

    if reg.get("preferencia") == "base":
        return Eleccion(ruta_base, "base", "rollback pedido en el registro")

    afinado = reg.get("afinado") or {}
    destino, sello = afinado.get("destino"), afinado.get("sha256")
    if not (destino and sello):
        return Eleccion(ruta_base, "base", "no hay cerebro afinado declarado")

    ruta = raiz / destino
    if not ruta.is_file():
        return Eleccion(ruta_base, "base", "el afinado está declarado y no está en disco")

    medida = huella_fichero(ruta)
    if medida != sello:
        # El disco manda sobre el registro. Igual que en `descarga.presente`.
        return Eleccion(ruta_base, "base",
                        "la huella del afinado no cuadra: se ignora")
    return Eleccion(str(ruta), "afinado", f"huella verificada · {sello[:12]}…")


def promover(raiz, ruta_gguf, version, notas=""):
    """Declara un afinado como candidato, con su huella MEDIDA aquí y ahora."""
    ruta_gguf = Path(ruta_gguf)
    sello = huella_fichero(ruta_gguf)
    if sello is None:
        raise FileNotFoundError(f"no puedo medir {ruta_gguf}")
    reg = _registro(raiz)
    reg["afinado"] = {
        "destino": os.path.relpath(ruta_gguf, Path(raiz)),
        "sha256": sello,
        "version": version,
        "notas": notas,
        "bytes": ruta_gguf.stat().st_size,
    }
    reg.pop("preferencia", None)
    escribir_registro(raiz, reg)
    return sello


def rollback(raiz, motivo):
    """Vuelve al base. No borra el afinado: un rollback no destruye pruebas."""
    reg = _registro(raiz)
    reg["preferencia"] = "base"
    reg["rollback"] = {"motivo": motivo}
    escribir_registro(raiz, reg)
    return True
