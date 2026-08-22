# ASSETS · las dos hojas de la cara

Documento interno del equipo (por eso va en español, como los comentarios del
código, y no en el inglés de industria de `README.md`). Describe qué son los
dos PNG de `assets/`, de dónde salieron, bajo qué licencia viajan, y el
contrato de animación que la cara está obligada a respetar.

## Procedencia y licencia

Los dos sprites fueron **generados por el Soberano** en su propio nodo. No
provienen de un banco de imágenes, no llevan marca de agua ajena y no arrastran
condiciones de terceros. Viajan bajo **CC BY-SA 4.0**, la misma licencia que la prosa y el lore, y
**no la del código**: `memory.py` es MIT y estos PNG no. Son arte, y se licencian
como el resto del arte de esta casa — se remezclan citando la fuente y
compartiendo igual.

Firmado el 2026-08-22. Antes esta línea decía «la licencia del repo:
Apache-2.0», que no existe en ningún fichero de este árbol, y despues «la misma
que el código», que tampoco: el código es MIT.

Se guardan en el árbol, no se descargan. Una cara que necesita ir a buscarse a
sí misma a algún sitio no es una cara: es una dependencia con dibujos.

## Las dos hojas

Las dos son PNG de **1024 × 341**, RGBA, con **4 fotogramas en horizontal** de
**256 × 341** cada uno. No hay filas: una sola tira. En CSS eso es
`background-size: 400% 100%` y `background-position-x` en `0%`, `33.333%`,
`66.667%` y `100%` para los fotogramas 1 a 4.

### `aurelius-talks.png` · la boca

| # | Qué es |
|---|---|
| 1 | boca abierta poca |
| 2 | boca abierta más |
| 3 | boca en "o" |
| 4 | sonrisa de reposo |

### `aurelius-up.png` · el despertar

| # | Qué es |
|---|---|
| 1 | mármol sin romper (espera) |
| 2 | apertura progresiva |
| 3 | apertura progresiva, más |
| 4 | forma final con trozos volando |

## Contrato de animación

Esto no es una sugerencia estética: es el contrato que `test_cara.py` comprueba
y que la cara implementa como una máquina de cuatro estados.

| Momento | Qué se ve | Estado |
|---|---|---|
| Antes de la primera frase del día | `up[1]` fijo | `dormido` |
| La primera frase | `up[1→2→3→4]`, **una sola vez** | `despertar` |
| Tras despertar, en silencio | `talks[4]` | `reposo` |
| Mientras escribe o habla | `talks[1→2→3]` en bucle | `hablando` |
| Al terminar de hablar | `talks[4]` | `reposo` |

Tres condiciones que hacen falta para que el contrato signifique algo:

- **El despertar ocurre una vez.** Hay una bandera que se apaga al terminar la
  secuencia. Un despertar que se repite en cada frase deja de ser un despertar
  y se convierte en un tic.
- **La animación es estado LOCAL de la UI.** No depende de la red, ni de un
  servidor, ni de que nadie le diga en qué fotograma va. La cara se abre con
  doble clic desde el disco y se anima igual con el cable desenchufado.
- **Se respeta `prefers-reduced-motion`.** Quien pidió a su sistema que no le
  muevan cosas por delante recibe los fotogramas finales sin la secuencia. El
  contenido es el mismo; lo que cambia es cuánto se mueve.

## Por qué dos hojas y no un vídeo

Un sprite se incrusta en el HTML como `data:` y viaja dentro del fichero. Un
vídeo obliga a un segundo fichero al lado, y un fichero al lado se pierde en
cuanto alguien mueve la cara de sitio. La cara tiene que seguir siendo **un
solo fichero que se puede enviar por correo**.
