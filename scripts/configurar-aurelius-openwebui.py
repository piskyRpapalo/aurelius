#!/usr/bin/env python3
"""Configura el modelo "Aurelius" en OpenWebUI sobre soberano-coder:latest (§Prompt 2).

Crea (o actualiza) un modelo custom en OpenWebUI cuyo system prompt es la identidad
de Aurelius (el Preceptor), leída de `aurelius.system.txt` (junto a este script).

SEGURO POR DISEÑO — para la MANO DE DAVID (como el script de prompts que ya corriste):
  1. Backup de la DB (webui.db + -wal + -shm).
  2. PARA el servicio (systemctl --user stop open-webui) para volcar el WAL — escribir
     la DB con el servicio vivo puede corromperla o no reflejarse.
  3. INSERT OR REPLACE del modelo `aurelius` en la tabla `model`.
  4. Arranca el servicio.

Uso:
    python3 configurar-aurelius-openwebui.py            # aplica
    python3 configurar-aurelius-openwebui.py --dry-run  # solo enseña qué haría

Por qué no por API: OpenWebUI tiene `auth.enable_api_keys=false` y no hay token admin
disponible a CC; la DB (con el servicio parado) es la única vía limpia. Verificado
2026-07-20: 0 modelos custom, sin límite de longitud de system prompt en config.
"""
from __future__ import annotations

import argparse
import datetime as _dt
import json
import shutil
import sqlite3
import subprocess
import sys
import time
from pathlib import Path

DB = Path(
    "/home/pisky/.local/share/uv/tools/open-webui/lib/python3.12/"
    "site-packages/open_webui/data/webui.db"
)
UNIDAD = "open-webui.service"
SYSTEM_TXT = Path(__file__).with_name("aurelius.system.txt")

# Identidad del modelo Aurelius.
MODEL_ID = "aurelius"
MODEL_NAME = "Aurelius"
BASE_MODEL = "soberano-coder:latest"
ADMIN_USER_ID = "0fcd46db-fcfa-4f34-b4bf-240491ab96db"  # Hexelion (davidpecero@gmail.com)


def _systemctl(accion: str) -> None:
    subprocess.run(["systemctl", "--user", accion, UNIDAD], check=True)


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--dry-run", action="store_true")
    args = ap.parse_args()

    if not DB.exists():
        print(f"ERROR: no encuentro la DB viva en {DB}", file=sys.stderr)
        return 1
    if not SYSTEM_TXT.exists():
        print(f"ERROR: falta {SYSTEM_TXT.name} junto al script", file=sys.stderr)
        return 1

    system_prompt = SYSTEM_TXT.read_text(encoding="utf-8").strip()
    now = int(time.time())
    params = json.dumps({"system": system_prompt}, ensure_ascii=False)
    meta = json.dumps(
        {
            "description": "El Preceptor del Camino Hexelion — voz estoica, IronClaw.",
            "profile_image_url": "/static/favicon.png",
        },
        ensure_ascii=False,
    )
    print(f"→ system prompt: {len(system_prompt)} chars · modelo '{MODEL_NAME}' sobre {BASE_MODEL}")

    if args.dry_run:
        print("[dry-run] pararía el servicio, backup, y haría:")
        print(f"  INSERT OR REPLACE INTO model(id={MODEL_ID}, base_model_id={BASE_MODEL}, …)")
        return 0

    # 1) backup
    sello = _dt.datetime.now().strftime("%Y%m%d-%H%M%S")
    destino = DB.parent / f"backup-aurelius-{sello}"
    destino.mkdir(exist_ok=True)
    for sufijo in ("", "-wal", "-shm"):
        f = Path(str(DB) + sufijo)
        if f.exists():
            shutil.copy2(f, destino / f.name)
    print(f"→ backup en {destino}")

    # 2) parar (vuelca el WAL)
    print(f"→ parando {UNIDAD} …")
    _systemctl("stop")

    # 3) upsert del modelo
    con = sqlite3.connect(DB)
    try:
        cols = [c[1] for c in con.execute("PRAGMA table_info(model)")]
        fila = {
            "id": MODEL_ID,
            "user_id": ADMIN_USER_ID,
            "base_model_id": BASE_MODEL,
            "name": MODEL_NAME,
            "params": params,
            "meta": meta,
            "updated_at": now,
            "created_at": now,
            "is_active": 1,
        }
        usados = [k for k in fila if k in cols]  # defensivo ante variaciones de esquema
        marcas = ", ".join("?" for _ in usados)
        con.execute(
            f"INSERT OR REPLACE INTO model({', '.join(usados)}) VALUES({marcas})",
            [fila[k] for k in usados],
        )
        con.commit()
        print(f"→ modelo '{MODEL_NAME}' escrito ({len(usados)} columnas)")
    finally:
        con.close()

    # 4) arrancar
    print(f"→ arrancando {UNIDAD} …")
    _systemctl("start")
    print("✓ listo. En OpenWebUI, elige el modelo 'Aurelius' y salúdalo — te recibirá el Preceptor.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
