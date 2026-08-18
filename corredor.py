#!/usr/bin/env python3
"""corredor.py · corredor canónico de Aurelius.

Ejecuta las 20 suites (15 unittest + 5 propias), cuenta los tests,
y falla cerrado si falta una suite o si alguna no pasa.
No es interactivo. Determinista. Sin buffering.
"""
import os
import re
import subprocess
import sys

SUITES_UNITTEST = [
    "test_descarga.py", "test_estado.py", "test_fuga.py",
    "test_guardrails.py", "test_interprete.py", "test_leitmotivs.py",
    "test_recuperacion.py", "test_silencio.py", "test_voz_cyber.py", "test_frontera.py", "test_andamio.py", "test_fusible.py", "test_identidad.py", "test_costura.py", "test_traza.py",
]
SUITES_PROPIAS = [
    "test_cara.py", "test_idioma.py", "test_manifest.py",
    "test_memory.py", "test_tono.py",
]

def correr_unittest(suite):
    r = subprocess.run(
        [sys.executable, "-u", "-m", "unittest", suite],
        capture_output=True, text=True, stdin=subprocess.DEVNULL,
    )
    salida = r.stdout + r.stderr
    m = re.search(r"Ran (\d+) tests", salida)
    n = int(m.group(1)) if m else 0
    ok = r.returncode == 0
    return n, ok, salida

def correr_propia(suite):
    r = subprocess.run(
        [sys.executable, suite],
        capture_output=True, text=True, stdin=subprocess.DEVNULL,
    )
    salida = r.stdout + r.stderr
    n = len(re.findall(r"^\s*ok", salida, re.M))
    # si la propia suite imprime un resumen de fallo, lo detectamos
    ok = r.returncode == 0 and "FALLO" not in salida and "FAIL" not in salida
    return n, ok, salida

def main():
    todas = SUITES_UNITTEST + SUITES_PROPIAS
    faltantes = [s for s in todas if not os.path.exists(s)]
    if faltantes:
        print("ROJO · faltan suites: " + ", ".join(faltantes))
        return 1

    # Rojo B-Inverso: buscar suites en disco que no esten declaradas
    suites_en_disco = [f for f in os.listdir('.') if f.startswith('test_') and f.endswith('.py')]
    no_declaradas = [s for s in suites_en_disco if s not in todas]
    if no_declaradas:
        print("ROJO · suites no declaradas en corredor: " + ", ".join(no_declaradas))
        return 1

    total = 0
    fallo = False
    for suite in SUITES_UNITTEST:
        n, ok, _ = correr_unittest(suite)
        total += n
        print(f"{'ok ' if ok else 'ROJ'} {n:>3}  {suite}")
        if not ok:
            fallo = True
    for suite in SUITES_PROPIAS:
        n, ok, _ = correr_propia(suite)
        total += n
        print(f"{'ok ' if ok else 'ROJ'} {n:>3}  {suite}")
        if not ok:
            fallo = True

    print(f"\nTOTAL: {total} tests en {len(todas)} suites")
    return 1 if fallo else 0

if __name__ == "__main__":
    sys.exit(main())
