#!/usr/bin/env python3
"""fusible.py · El Fusible de Alucinación (Joya 3.3 · V-3).

Normaliza el texto del LLM y lo inspecciona por forma estructural.
Determinista, cero LLM. No es completo: frena, no sustituye a la persona.
"""
from __future__ import annotations
import re

# Patrones por forma estructural, no por nombre exacto.
# Cada patrón lleva NOMBRE porque el registro de la frontera guarda clase y
# cantidad, nunca el fragmento: un hallazgo sin nombre obligaría a guardar el
# trozo de texto para saber qué saltó, que es justo lo que no se guarda.
PATRONES_PELIGROSOS = [
    ("rm_raiz",     r'rm\s+(-\S*\s+)*[\/\*]'),      # rm sobre raíz o comodín
    ("shred",       r'shred\s+(-\S*\s+)*'),         # sobrescritura segura
    ("dd",          r'dd\s+if='),                   # sobrescritura de disco
    ("mkfs",        r'mkfs\.\w+\s+/dev/'),          # formateo
    ("fork_bomb",   r':\(\)\{\s*:\|\:&\s*\};:'),    # fork bomb
    ("escribe_dev", r'>\s*/dev/sd[a-z]'),           # escritura directa a bloque
    ("chmod_raiz",  r'chmod\s+(-\S*\s+)*0+\s+/'),   # permisos 000 sobre raíz
    ("killall9",    r'killall\s+(-\S*\s+)*-9'),     # kill -9 a todo
    ("pipe_shell",  r'(wget|curl)\s+.*\|\s*(ba)?sh'), # pipe a shell (remote exec)
]


class RespuestaBloqueada(Exception):
    """El fusible vio forma peligrosa en la respuesta del modelo. No pasa."""

def _normalizar(texto: str) -> str:
    """Normaliza continuaciones de línea y espacios para cazar la forma."""
    # Quitar backslash y espacios/newlines que le siguen (unión de líneas)
    t = re.sub(r'\\\s*', '', texto)
    # Colapsar multiples whitespace (incluido newlines) a un solo espacio
    t = re.sub(r'\s+', ' ', t)
    return t.strip()

def inspeccionar(texto: str) -> dict:
    """Inspecciona el texto y devuelve si está bloqueado y los hallazgos."""
    normalizado = _normalizar(texto)
    hallazgos = []
    clases = []
    for nombre, patron in PATRONES_PELIGROSOS:
        match = re.search(patron, normalizado, re.IGNORECASE)
        if match:
            hallazgos.append(match.group(0).strip())
            clases.append({"policy": nombre, "count": 1})

    return {
        "bloqueado": len(hallazgos) > 0,
        "hallazgos": hallazgos,
        "clases": clases
    }


def preparar_respuesta(texto: str) -> dict:
    """Prepara la respuesta del modelo para que cruce la frontera.

    Es lo que le faltaba al fusible para ser una puerta y no solo un dictamen:
    `memory.cruzar_frontera` la llama, y de su veredicto sale la fila del
    registro. Lo que viaja son CLASE Y CANTIDAD, jamás el fragmento -- el mismo
    criterio que `guardrails.redactar_salida`.
    """
    resultado = inspeccionar(texto)
    if resultado["bloqueado"]:
        raise RespuestaBloqueada(
            "el fusible encontró forma peligrosa en la respuesta: no pasa")
    return {"texto": texto, "hallazgos": resultado["clases"]}
