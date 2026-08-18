#!/usr/bin/env python3
"""andamio.py · El Andamio de Intención (Joya 3.1).

Ensambla prompts guiados para el usuario novato, uniendo el carácter base
con el contexto de la memoria y la intención elegida. No invoca al LLM.
"""
from __future__ import annotations
import os

class SinInspeccion(Exception):
    """Se intentó exportar el prompt sin haberlo inspeccionado antes."""
    pass

# Catálogo de intenciones (datos, no código)
INTENCIONES = {
    "explicar_concepto": {
        "plantilla": "Explica el concepto de {concepto} a un nivel {nivel}.",
        "requiere": ["concepto", "nivel"]
    },
    "depurar_error": {
        "plantilla": "Tengo este error: {error}. ¿Cómo lo soluciono?",
        "requiere": ["error"]
    }
}

# Estado interno de inspección
_inspeccionado = False

def ensamblar(intencion: str, perfil: dict, contexto: dict) -> str:
    """Ensabla el prompt final sin llamar al modelo. Devuelve un string."""
    global _inspeccionado
    _inspeccionado = False  # Reset: un prompt nuevo no está inspeccionado

    if intencion not in INTENCIONES:
        return f"NO_DATA (intención '{intencion}' no encontrada)"

    plantilla = INTENCIONES[intencion]["plantilla"]
    requiere = INTENCIONES[intencion].get("requiere", [])
    
    # Rellenar contexto: lo que falta es NO_DATA
    ctx = {}
    for k in requiere:
        ctx[k] = contexto.get(k, "NO_DATA")
        
    # Añadir cualquier otro contexto extra pasado
    for k, v in contexto.items():
        if k not in ctx:
            ctx[k] = v

    nombre = perfil.get("nombre", "NO_DATA")
    
    # Cargar carácter base (ARQUETIPO.md)
    arquetipo_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "ARQUETIPO.md")
    arquetipo = "NO_DATA (ARQUETIPO.md no encontrado)"
    if os.path.isfile(arquetipo_path):
        with open(arquetipo_path, "r", encoding="utf-8") as f_arch:
            arquetipo = f_arch.read().strip()
    
    prompt_text = f"=== CARÁCTER ===\n{arquetipo}\n\n"
    prompt_text += f"=== PERFIL ===\nNombre: {nombre}\n\n"
    prompt_text += f"=== INTENCIÓN ===\n{plantilla.format(**ctx)}"
    
    return prompt_text

def marcar_inspeccionado():
    """Marca el prompt actual como inspeccionado por el humano."""
    global _inspeccionado
    _inspeccionado = True

def preparar_salida_andamio(prompt: str) -> str:
    """Valida que el prompt haya sido inspeccionado antes de dejarlo salir."""
    if not _inspeccionado:
        raise SinInspeccion("El prompt no ha sido inspeccionado. No puede salir.")
    return prompt
