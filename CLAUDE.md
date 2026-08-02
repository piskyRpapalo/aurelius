# CLAUDE.md · aurelius

**Backlog UI/software autoritativo:** `p0x/mente/backlog/BACKLOG_UI.md` (repo `p0x`,
privado). Este repo **no** lo copia (contiene rutas `by-id` y nombres de nodo).

## Formato de reporte (obligatorio · máximo 12 líneas)

```
RONDA <id> · <repo>@<rama>
HECHO      <hash> · <una línea por commit>
BLOQUEADO  <ítem> ← <dependencia exacta>
DECIDE     <pregunta en una línea, o "nada">
BACKLOG_UI.md actualizado: sí/no
```

La narrativa larga va al BACKLOG, no al chat. El presupuesto de contexto del
Soberano es el cuello de botella real.

## Invariantes (resumen; canon en BACKLOG_UI.md §1)

- **Higiene dura**: `tsc --noEmit`=0 · 0 pageerrors · sin deps nuevas sin justificar ·
  cero IPs/hostnames/usuarios-en-ruta/wallets/claves en nada que se **publique**
  (aurelius es público vía HTTPS; el scrubber corre ANTES del push).
- **Honest sensors**: antigüedad del **dato**, no del render; ante la duda `NO DATA`.
  Aplica también a simulaciones (La Pizarra): jamás inventar una salida plausible.
- **IronClaw**: propose-only en infra — sin deploy, sin restart en producción, sin `git push`.
  El modelo no tiene manos: cero endpoint de ejecución en backend.
- **Sin `<iframe>`** (vector de recursión cara→camino; hay CI que lo prohíbe).
- **Editar `src/`/`interface/`, nunca `dist/`.** Commits atómicos, sin push.
- **Regla de parada**: ante ambigüedad, PARA y pregunta. No adivines.
