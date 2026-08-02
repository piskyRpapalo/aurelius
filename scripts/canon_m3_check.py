#!/usr/bin/env python3
"""Check del canon: **M3 = El Refugio, y sólo M3.**

Falla (exit 1) si:
  R1  una línea nombra M3 junto a un hito que NO es el Refugio
      (Bautismo/Baluarte/Ed25519/Pacto/Pact/Señal/Signal) SIN nombrar también el
      Refugio en esa misma línea.  → "M3 pasó a significar otra cosa".
  R2  una línea nombra el Refugio junto a un slot distinto de M3
      (M0/M1/M2/M4/M5) SIN nombrar también M3 en esa misma línea.
      → "el Refugio se mudó de slot".

Nota: las líneas-resumen que emparejan M3 CON el Refugio (aunque listen también
M4/M5/Pacto/Señal) pasan a propósito — describen el Camino, no lo redefinen.

Excepciones deliberadas: `scripts/canon_m3_allowlist.txt` (una por línea,
`<ruta-relativa>:<subcadena literal de la línea>`). Viven en un commit → auditables.

Escanea sólo ficheros trackeados (`git ls-files`). Excluye: .git/, node_modules/,
docs/, *.sig.json, CHANGELOG.md, PENDIENTES.md, y las propias herramientas del check.
"""
from __future__ import annotations

import re
import subprocess
import sys
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent
ALLOWLIST = RAIZ / "scripts" / "canon_m3_allowlist.txt"
SELF = {"scripts/canon_m3_check.py", "scripts/canon_m3_allowlist.txt"}

FORBIDDEN = re.compile(r"bautismo|baluarte|ed25519|\bpacto\b|\bpact\b|se[ñn]al|\bsignal\b", re.I)
REFUGIO = re.compile(r"refug|refuge|ref[úu]gio|zuflucht|καταφύγιο|убежище", re.I)
M3 = re.compile(r"\bM3\b")
OTRO_SLOT = re.compile(r"\bM[0124-5]\b")  # M0/M1/M2/M4/M5 (nunca M3)

EXCLUIR_NOMBRE = {"CHANGELOG.md", "PENDIENTES.md"}
EXCLUIR_PREFIJO = ("docs/", ".git/", "node_modules/")


def cargar_allowlist() -> list[tuple[str, str]]:
    if not ALLOWLIST.exists():
        return []
    fuera: list[tuple[str, str]] = []
    for ln in ALLOWLIST.read_text(encoding="utf-8").splitlines():
        ln = ln.strip()
        if not ln or ln.startswith("#"):
            continue
        ruta, _, sub = ln.partition(":")
        if ruta.strip() and sub.strip():
            fuera.append((ruta.strip(), sub.strip()))
    return fuera


def permitido(rel: str, linea: str, allow: list[tuple[str, str]]) -> bool:
    return any(rel == r and s in linea for r, s in allow)


def ficheros() -> list[str]:
    res = subprocess.run(["git", "-C", str(RAIZ), "ls-files"], capture_output=True, text=True, check=True)
    salida: list[str] = []
    for rel in res.stdout.splitlines():
        if rel in SELF or Path(rel).name in EXCLUIR_NOMBRE:
            continue
        if rel.endswith(".sig.json"):
            continue
        if any(rel.startswith(p) for p in EXCLUIR_PREFIJO):
            continue
        salida.append(rel)
    return salida


def main() -> int:
    allow = cargar_allowlist()
    fallos: list[str] = []
    for rel in ficheros():
        try:
            texto = (RAIZ / rel).read_text(encoding="utf-8", errors="replace")
        except OSError:
            continue
        for n, linea in enumerate(texto.splitlines(), 1):
            r1 = bool(M3.search(linea) and FORBIDDEN.search(linea) and not REFUGIO.search(linea))
            r2 = bool(REFUGIO.search(linea) and OTRO_SLOT.search(linea) and not M3.search(linea))
            if (r1 or r2) and not permitido(rel, linea, allow):
                regla = "R1(M3≠Refugio)" if r1 else "R2(Refugio≠M3)"
                fallos.append(f"{rel}:{n}: [{regla}] {linea.strip()[:120]}")
    if fallos:
        print("CANON M3 · VIOLACIONES:")
        for f in fallos:
            print("  " + f)
        print(f"\n{len(fallos)} violación(es). Corrige, o registra la excepción en {ALLOWLIST.name}.")
        return 1
    print("CANON M3 · OK — M3 = El Refugio; sin violaciones.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
