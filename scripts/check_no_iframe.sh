#!/usr/bin/env bash
# Prohíbe <iframe> en Aurelius. El bug de recursión (cara → iframe → camino.html →
# "volver" → cara dentro de la cara) costó tres rondas. camino.html sigue existiendo
# como página standalone, así que la vía de regresión sigue abierta: si alguien vuelve
# a embeber con un <iframe>, este check FALLA el build.
#
# Falla (exit 1) si aparece una etiqueta <iframe o un createElement('iframe').
# Escanea interface/ y src/ (la cara viva y la app Vite). Se excluye a sí mismo.
set -uo pipefail
RAIZ="$(cd "$(dirname "$0")/.." && pwd)"
PATRON='<iframe|createElement\((["'"'"'])iframe\1'
hits=$(grep -rnE "$PATRON" "$RAIZ/interface" "$RAIZ/src" 2>/dev/null \
  | grep -vE 'scripts/check_no_iframe' || true)
if [ -n "$hits" ]; then
  echo "PROHIBIDO · <iframe> reintroducido en Aurelius (vector de recursión):"
  echo "$hits"
  exit 1
fi
echo "OK · sin <iframe> en Aurelius (cara + app)."
exit 0
