#!/usr/bin/env python3
"""hilos.py · Hilos y Estado sin Cerrar (D14).

Doctrina: El estado se deriva de eventos (event sourcing). Cero DELETE.
D16: El detector habla al arrancar en una sola línea.
"""
from __future__ import annotations
from datetime import datetime

import memory as _memory

def abrir(c, titulo: str, origen_dispositivo: str = "NO_DATA") -> int:
    """Abre un nuevo hilo y registra el evento 'abierto'.

    Se asegura el esquema antes de escribir: una memoria nacida antes de D14 no
    tiene estas tablas, y el producto no puede reventar contra la memoria de
    quien lleva mas tiempo usandolo.
    """
    _memory.asegurar_tablas(c)
    cur = c.execute(
        "INSERT INTO hilos (titulo, origen_dispositivo) VALUES (?, ?)",
        (titulo, origen_dispositivo)
    )
    hilo_id = cur.lastrowid
    c.execute(
        "INSERT INTO hilos_eventos (hilo_id, tipo, momento) VALUES (?, ?, ?)",
        (hilo_id, 'abierto', datetime.now().isoformat())
    )
    c.commit()
    return hilo_id

def cerrar(c, hilo_id: int):
    """Cierra un hilo registrando el evento 'cerrado'."""
    c.execute(
        "INSERT INTO hilos_eventos (hilo_id, tipo, momento) VALUES (?, ?, ?)",
        (hilo_id, 'cerrado', datetime.now().isoformat())
    )
    c.commit()

def reabrir(c, hilo_id: int):
    """Reabre un hilo registrando el evento 'reabierto'."""
    c.execute(
        "INSERT INTO hilos_eventos (hilo_id, tipo, momento) VALUES (?, ?, ?)",
        (hilo_id, 'reabierto', datetime.now().isoformat())
    )
    c.commit()

def eventos(c, hilo_id: int) -> list:
    """Devuelve todos los eventos de un hilo ordenados por momento."""
    return [dict(r) for r in c.execute(
        "SELECT * FROM hilos_eventos WHERE hilo_id = ? ORDER BY momento",
        (hilo_id,)
    )]

def estado(c, hilo_id: int) -> dict:
    """Deriva el estado actual del hilo a partir de su último evento."""
    evts = eventos(c, hilo_id)
    if not evts:
        return {"estado": "NO_DATA", "antiguedad_dias": None}
    
    ultimo_evento = evts[-1]
    estado_str = "sin_cerrar" if ultimo_evento["tipo"] in ('abierto', 'reabierto') else "cerrado"
    
    # Calcular antigüedad
    momento = datetime.fromisoformat(ultimo_evento["momento"])
    antiguedad = (datetime.now() - momento).days
    
    return {"estado": estado_str, "antiguedad_dias": antiguedad}

def aviso_sin_cerrar(c, umbral_dias: int = 7) -> str:
    """D16: Devuelve una línea de texto con el recuento de hilos sin cerrar."""
    hilos_data = [dict(r) for r in c.execute("SELECT id FROM hilos").fetchall()]
    count = 0
    oldest_days = 0
    
    for h in hilos_data:
        est = estado(c, h["id"])
        if est["estado"] == "sin_cerrar":
            if est["antiguedad_dias"] is not None and est["antiguedad_dias"] >= umbral_dias:
                count += 1
                if est["antiguedad_dias"] > oldest_days:
                    oldest_days = est["antiguedad_dias"]
    
    if count == 0:
        return ""
    
    return f"{count} hilos sin cerrar (el más antiguo: {oldest_days} días)"
