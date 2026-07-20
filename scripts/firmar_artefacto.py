#!/usr/bin/env python3
"""El Acto de Firmar — FASE HASH (M0–M2 del Camino Hexelion).

Calcula el SHA-256 de un archivo y escribe un LOG DE VALIDACIÓN junto a él
(`<archivo>.sig.json`: nombre, hash SHA-256, timestamp ISO, tamaño en bytes).

En M0–M2 el usuario AÚN NO TIENE claves criptográficas — las genera en M3 («El
Bautismo»). Por eso este script prueba **INTEGRIDAD** (la huella inmutable del
archivo), NO **AUTORÍA**. La firma con clave Ed25519 (que prueba presencia humana)
llega en M3, en un script APARTE: `firmar_con_clave.py` (aún no creado — ver el
stub/TODO al final). Esta progresión hash → clave es Scaffolding Fading aplicado a
la criptografía (§5 del canon): el andamio se retira a medida que sube la competencia.

Uso:
    python3 firmar_artefacto.py <archivo>
    python3 firmar_artefacto.py ~/aurelius/sovereign_vault/M1_Espejo_Roto/tiempo_perdido.md

Salida: escribe `<archivo>.sig.json` y confirma en texto legible. Código de salida
0 si firmó, 1 si el archivo no existe o hubo error.
"""
from __future__ import annotations

import datetime as dt
import hashlib
import json
import sys
from pathlib import Path
from typing import TypedDict


class RegistroFirma(TypedDict):
    """Log de validación por hash (fase M0–M2). No es una firma con clave."""

    nombre: str
    sha256: str
    timestamp_iso: str
    tamano_bytes: int
    fase: str
    prueba: str


def calcular_sha256(ruta: Path) -> str:
    """Devuelve el SHA-256 hex del archivo, leído en bloques (no carga todo en RAM)."""
    h = hashlib.sha256()
    with ruta.open("rb") as f:
        for bloque in iter(lambda: f.read(65536), b""):
            h.update(bloque)
    return h.hexdigest()


def firmar(ruta: Path) -> RegistroFirma:
    """Calcula el hash y construye el registro de validación. Defensivo ante ausencia."""
    if not ruta.exists():
        raise FileNotFoundError(f"no existe el archivo a firmar: {ruta}")
    if not ruta.is_file():
        raise ValueError(f"no es un archivo regular: {ruta}")
    return {
        "nombre": ruta.name,
        "sha256": calcular_sha256(ruta),
        "timestamp_iso": dt.datetime.now(dt.timezone.utc).isoformat(),
        "tamano_bytes": ruta.stat().st_size,
        "fase": "hash-M0-M2",
        "prueba": "integridad (no autoria; la firma con clave Ed25519 llega en M3)",
    }


def main(argv: list[str]) -> int:
    if len(argv) != 2:
        print("uso: python3 firmar_artefacto.py <archivo>", file=sys.stderr)
        return 1
    ruta = Path(argv[1]).expanduser()
    try:
        registro = firmar(ruta)
    except (FileNotFoundError, ValueError) as e:
        print(f"ERROR: {e}", file=sys.stderr)
        return 1

    destino = ruta.with_name(ruta.name + ".sig.json")
    destino.write_text(json.dumps(registro, ensure_ascii=False, indent=2), encoding="utf-8")

    print(f"✓ Sellado por hash (fase M0-M2): {ruta.name}")
    print(f"  SHA-256 : {registro['sha256']}")
    print(f"  tamaño  : {registro['tamano_bytes']} bytes")
    print(f"  log     : {destino}")
    print("  prueba integridad, no autoria — la firma con clave llega en M3.")
    return 0


# ─────────────────────────────────────────────────────────────────────────────
# TODO · M3 «El Bautismo» — firma con CLAVE (progresión hash → clave, §5 del canon).
#
# Cuando el usuario llegue a M3 generará su par Ed25519 (privada JAMÁS sale del
# dispositivo). Entonces vivirá un script APARTE, `firmar_con_clave.py`, que:
#   1. Carga la clave privada Ed25519 del usuario (p.ej. ~/.aurelius/keys/, 0600).
#   2. Firma el archivo (o su hash) → `<archivo>.sig` (firma cruda) + `.sig.json`
#      que ahora incluye `pubkey` y `signature`, probando AUTORÍA/presencia humana.
#   3. Verifica con la pública. Dependencia: `cryptography` (Ed25519) — se añade en M3.
# Este script (hash) NO se toca: los dos coexisten; el hash prueba integridad, la
# clave prueba autoría. El andamio (hash) sigue disponible aunque suba la competencia.
# ─────────────────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
