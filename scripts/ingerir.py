#!/usr/bin/env python3
"""M2 · El Agua — memoria local (RAG) que NUNCA sale del nodo.

El usuario ejecuta ESTE script en SU propia terminal (IronClaw: la máquina guía,
el carbono ejecuta y firma con su mano). Ingiere un `grimorio.md` en una base
vectorial LOCAL y permite buscar en ella — 100% offline, sin modelo ni red.

Uso:
    python3 ingerir.py grimorio.md                       # ingiere → .vec.json + .manifest.json
    python3 ingerir.py grimorio.md --buscar "pregunta"   # recupera del vector local

LÍMITE DECLARADO (honestidad antes que magia): es un vectorizador LIGERO — bolsa
de palabras con hashing, NO embeddings neuronales. Demuestra la memoria soberana
local (fragmentar → vectorizar → recuperar por coseno) sin depender de ningún
modelo. Nada aquí toca la red; el dato es tuyo, local y borrable.
"""
from __future__ import annotations

import argparse
import datetime as dt
import hashlib
import json
import math
import re
import sys
from pathlib import Path
from typing import TypedDict

DIM = 512  # dimensiones del vector (bolsa de palabras con hashing)


class Fragmento(TypedDict):
    idx: int
    texto: str
    vector: list[float]  # normalizado (norma 1)


def _tokens(texto: str) -> list[str]:
    return re.findall(r"[a-zà-ÿ0-9]{2,}", texto.lower())


def _vectorizar(texto: str) -> list[float]:
    """Vector normalizado por hashing de tokens (determinista, offline)."""
    v = [0.0] * DIM
    for t in _tokens(texto):
        idx = int(hashlib.sha1(t.encode("utf-8")).hexdigest(), 16) % DIM
        v[idx] += 1.0
    norma = math.sqrt(sum(x * x for x in v))
    return [x / norma for x in v] if norma > 0 else v


def _coseno(a: list[float], b: list[float]) -> float:
    return sum(x * y for x, y in zip(a, b))


def _fragmentar(md: str) -> list[str]:
    """Por párrafos (líneas en blanco). Descarta vacíos y cabeceras solas."""
    crudos = re.split(r"\n\s*\n", md)
    return [p.strip() for p in crudos if p.strip()]


def _rutas(grimorio: Path) -> tuple[Path, Path]:
    return (
        grimorio.with_name(grimorio.stem + ".vec.json"),
        grimorio.with_name(grimorio.stem + ".manifest.json"),
    )


def ingerir(grimorio: Path) -> dict[str, object]:
    if not grimorio.exists():
        raise FileNotFoundError(f"no existe el grimorio: {grimorio}")
    if not grimorio.is_file():
        raise ValueError(f"no es un archivo regular: {grimorio}")
    md = grimorio.read_text(encoding="utf-8")
    fragmentos: list[Fragmento] = [
        {"idx": i, "texto": texto, "vector": _vectorizar(texto)}
        for i, texto in enumerate(_fragmentar(md))
    ]
    if not fragmentos:
        raise ValueError("el grimorio está vacío — escribe algo que valga la pena recordar")

    vec_path, man_path = _rutas(grimorio)
    vec_path.write_text(
        json.dumps({"dim": DIM, "fragmentos": fragmentos}, ensure_ascii=False),
        encoding="utf-8",
    )
    manifest = {
        "grimorio": grimorio.name,
        "fragmentos": len(fragmentos),
        "dim": DIM,
        "vectorizador": "hashing-bag-of-words-local (no neuronal)",
        "creado": dt.datetime.now(dt.timezone.utc).isoformat(),
        "soberania": "local, borrable, nunca sube a ningún servidor",
    }
    man_path.write_text(json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8")
    return {"vec": str(vec_path), "manifest": str(man_path), "fragmentos": len(fragmentos)}


def buscar(grimorio: Path, consulta: str, k: int = 3) -> list[tuple[float, str]]:
    vec_path, _ = _rutas(grimorio)
    if not vec_path.exists():
        raise FileNotFoundError(f"aún no ingerido: falta {vec_path.name} (corre sin --buscar primero)")
    base = json.loads(vec_path.read_text(encoding="utf-8"))
    qv = _vectorizar(consulta)
    puntuados = [
        (_coseno(qv, f["vector"]), f["texto"]) for f in base.get("fragmentos", [])
    ]
    puntuados.sort(key=lambda p: p[0], reverse=True)
    return puntuados[:k]


def main(argv: list[str]) -> int:
    p = argparse.ArgumentParser(description="M2 · memoria local (RAG) offline del grimorio.")
    p.add_argument("grimorio", type=Path)
    p.add_argument("--buscar", metavar="CONSULTA", default=None)
    p.add_argument("-k", type=int, default=3, help="fragmentos a recuperar (def 3)")
    args = p.parse_args(argv)
    grimorio: Path = args.grimorio.expanduser()

    try:
        if args.buscar is not None:
            for score, texto in buscar(grimorio, args.buscar, args.k):
                corte = texto.replace("\n", " ")
                print(f"[{score:.3f}] {corte[:160]}")
            return 0
        res = ingerir(grimorio)
        print(f"✓ Ingerido en memoria LOCAL: {res['fragmentos']} fragmentos")
        print(f"  vector   : {res['vec']}")
        print(f"  manifiesto: {res['manifest']}")
        print("  Ahora fírmalo con tu mano (IronClaw):")
        print(f"    python3 {Path(__file__).parent / 'firmar_artefacto.py'} {res['manifest']}")
        return 0
    except (FileNotFoundError, ValueError) as e:
        print(f"ERROR: {e}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
