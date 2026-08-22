# Propuesta · el guardián de interfaz contra JavaScript real

**No la aplico. Los tests son doctrina y su redacción es del Soberano.**
Aquí está el dato y el diff mínimo, para tu firma.

## Qué pasó

`G2_FicherosDeInterfazLimpios` audita `interface/`. Se escribió cuando allí solo
vivían `privacy_toggle.html` y `.css` — **ficheros estáticos**. La cara premium
mete el primer JavaScript de verdad y dispara dos reglas, ninguna por hacer lo
que la regla vigila:

| Regla | Qué dispara | Qué está pasando de verdad |
|---|---|---|
| `no_recalcula_el_contador` | `.match(` en `sw.js` | Es `caches.match(request)`, la API de caché del navegador. No cuenta nada. |
| `solo_nombra_politicas_que_existen` | el token `JSON` | `JSON.stringify` al construir el cuerpo de un `fetch`. No es una política. |

La segunda es la más dura de las dos: `\b[A-Z][A-Z_]{3,}\b` marca **cualquier**
identificador de cuatro mayúsculas, así que la regla tal como está **prohíbe
`JSON` en el cliente** — es decir, prohíbe hablar con un endpoint.

## Lo que ya corregí, porque sí era culpa mía

Comentarios en mayúsculas (`<!-- HABLAR -->`, `LA REGLA QUE…`) y constantes como
`PANELES`. Eran ruido que la regla marcaba con razón: en un fichero de interfaz,
una palabra en mayúsculas se parece demasiado a un nombre de política.

## El diff mínimo, si lo firmas

```python
# 1 · la regla del contador mira lo que cuenta, no cualquier `.match(`
prohibido = re.compile(
    r"(?i)(\bnew RegExp|\bcount\s*\+\+|\bcount\s*\+=|"
    r"\.filter\([^)]*policy|hallazgos[^)]*\.length)")
```

Lo que gana: `hallazgos.length` —que **sí** sería la interfaz contando— pasa a
estar prohibido explícitamente, y hoy no lo está. La regla se vuelve más
estricta donde importa y deja de marcar la API del navegador.

```python
# 2 · la regla de nombres exime los globales del lenguaje, no inventa excepciones
INTRINSECOS = {"JSON", "DOCTYPE", "UTF", "HTML", "HTTP", "POST"}
if nombrada.startswith("REDACTED") or nombrada in INTRINSECOS:
    continue
```

## Y una alternativa que descarto, para que conste

Podría sacar el JavaScript de `interface/` y el guardián dejaría de verlo. Sería
pasar una auditoría moviendo el fichero: la cara premium **es** superficie
visible y tiene que auditarse como tal. Prefiero el árbol en rojo declarado.

## Estado mientras tanto

`bin/pruebas` queda **ROJO en `test_guardrails`, por estas dos líneas y solo por
estas dos**. Las otras 17 suites, verdes. Lo dejo así a propósito: un rojo
declarado se arregla; un rojo escondido bajo un test relajado, no.
