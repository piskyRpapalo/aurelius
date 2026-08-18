#!/usr/bin/env python3
"""traza.py · La Traza de Verificación (D10).

Genera la traza determinista de la comprobación del fusible.
No es pensamiento, es veredicto. No es narración, es hecho.
"""
from __future__ import annotations
import datetime
import fusible

ALCANCE_DECLARADO = "reviso patrones estructurales; no lo reconozco todo; la última comprobación es tuya"

def generar(texto: str | None) -> dict:
    """Genera la traza para un texto dado. Si texto es None, falla cerrado."""
    momento = datetime.datetime.now().isoformat()
    
    if texto is None:
        return {
            "momento": momento,
            "estado": "[x] NO_DATA",
            "bloqueado": True,
            "hallazgos": [],
            "alcance": ALCANCE_DECLARADO,
            "entrada": "NO_DATA"
        }
    
    resultado_fusible = fusible.inspeccionar(texto)
    bloqueado = resultado_fusible["bloqueado"]
    hallazgos = resultado_fusible["hallazgos"]
    
    if bloqueado:
        estado = "[x] bloqueado"
    else:
        estado = "[ok] limpio"
        
    return {
        "momento": momento,
        "estado": estado,
        "bloqueado": bloqueado,
        "hallazgos": hallazgos,
        "alcance": ALCANCE_DECLARADO
        # Doctrina V3: el texto crudo del modelo no viaja en la traza.
        # Se guarda en el registro de R2 (memory.registrar_salida), no aquí.
    }
