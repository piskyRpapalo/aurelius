#!/usr/bin/env bash
# Construye el fichero unico para PC. Requiere pyinstaller en el entorno.
set -euo pipefail
R="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
PY="${PYINSTALLER:-pyinstaller}"

# El producto entra COMO DATOS y ademas se declara como import oculto. Las dos
# cosas: los datos lo ponen en el paquete, y el import oculto hace que el
# analizador arrastre lo que cada modulo necesita. Con solo una de las dos, el
# binario se construye igual y muere al arrancar.
DATOS=""
for f in "$R"/*.py; do
  case "$(basename "$f")" in test_*|andamio.py|generar_leitmotivs.py) continue;; esac
  DATOS="$DATOS --add-data $f:."
done
OCULTOS=""
for m in memory guardrails captura conversacion cara casa textos tono estado \
         hilos fusible descarga interprete narrador manifest lore silencio \
         traza caracter voz oido fuga corredor; do
  OCULTOS="$OCULTOS --hidden-import $m"
done

exec $PY --onefile --name aurelius --noconfirm \
  --icon "$R/empaquetado/aurelius.png" --paths "$R" \
  --add-data "$R/bin/aurelius-pwa:bin" \
  --add-data "$R/interface:interface" \
  --add-data "$R/policies.default.json:." \
  --add-data "$R/assets:assets" \
  $DATOS $OCULTOS \
  --distpath "$R/dist" \
  --workpath "${TMPDIR:-/tmp}/aurelius-build" \
  --specpath "${TMPDIR:-/tmp}/aurelius-build" \
  "$R/empaquetado/lanzador.py"
