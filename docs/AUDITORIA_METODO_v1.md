# AUDITORIA DE CONFORMIDAD — Metodo v1, Fase 1 tarea 1

Fecha: 2026-08-04 · Rama: main · Base: `docs/AURELIUS_METODO_v1.txt` seccion 1.
Alcance: mecanismos que YA existen en el repositorio. **Nada se ha modificado en
este commit** — la auditoria solo mide.

## Como se ha clasificado

El test de tres preguntas de la Seccion 1, en orden. Basta un NO para rechazar:

1. Obliga a PREDECIR algo antes de que el sistema lo muestre?
2. O a RECUPERAR de memoria, o RECONSTRUIR una causa a partir de evidencia?
3. Si no: que aprende el usuario del coste que se le impone? Si la respuesta es
   "a cumplir el ritual", se descarta.

    CUMPLE       tiene prediccion previa o recuperacion.
    REESCRIBIBLE impone coste, pero la Seccion 1 muestra como convertirlo.
    DESCARTAR    impone coste sin conversion posible.

Columna SUJETO, anadida por necesidad y declarada como desviacion minima: la
Regla Unica gobierna la friccion sobre el ALUMNO. Un guardian de integracion
continua impone friccion sobre el DESARROLLADOR y queda fuera de su jurisdiccion;
se audita igual, pero se marca, para que nadie lea "CUMPLE" como si un check de
CI hubiera pasado un test pedagogico que no le corresponde.

Nota adicional: varios mecanismos marcados CUMPLE no son friccion en absoluto,
sino infraestructura u honest sensors. Se admiten con el mismo criterio con que
el arsenal admite [aur:templado]: "no es friccion, es infraestructura".

## Tabla

    MECANISMO                                  FICHERO:LINEA                          SUJETO  VEREDICTO
    ------------------------------------------ -------------------------------------- ------- ------------
    Prediccion previa de la RAM (gate)         interface/camino.js:251                alumno  CUMPLE
    Retencion de la medida hasta la apuesta    interface/camino.js:255,262            alumno  CUMPLE
    El hueco prediccion<->medicion             interface/camino.js:239                alumno  CUMPLE
    NO DATA si el inventario no reporta        interface/camino.js:245,273            alumno  CUMPLE
    Pizarra · fading del andamio por comando   interface/pizarra.js:247,296           alumno  CUMPLE
    Pizarra · comando no implementado declara  interface/pizarra.js:107               alumno  CUMPLE
    Pizarra · badge SIMULATION / RUNS NOTHING  interface/pizarra.js:232               alumno  CUMPLE
    Pizarra · puente COPIAR a tu terminal      interface/pizarra.js:280               alumno  CUMPLE
    Pizarra · borrado del progreso (reset)     interface/pizarra.js:310               alumno  CUMPLE
    Rail del Camino (pinta estado, no bloquea) interface/camino.js:152                alumno  CUMPLE
    Onboarding · tono (estilo, no reglas)      interface/camino.js:194                alumno  CUMPLE
    Oraculo · informa, jamas prohibe           interface/oraculo.js:2,84              alumno  CUMPLE
    Oraculo · etiqueta la procedencia del dato interface/oraculo.js:48                alumno  CUMPLE
    Oraculo · sin RAM reportada no estima      interface/oraculo.js:85,142            alumno  CUMPLE
    Demarcacion de datos no confiables         interface/aurelius_face.html:381       alumno  CUMPLE
    El modelo no tiene manos (suelo IronClaw)  interface/aurelius_face.html:226,233   alumno  CUMPLE
    Aviso de idioma sin revision humana        interface/i18n.js:16 · camino.js:81    alumno  CUMPLE
    Firma por hash, no por clave (progresion)  scripts/firmar_artefacto.py:1          alumno  CUMPLE
    Boton copiar que no miente al fallar       interface/camino.js:121                alumno  CUMPLE
    Inventario honesto (desconocido, jamas ojo)scripts/servir_interfaz.py:199,219     alumno  CUMPLE
    Guardian CI · sin <iframe>                 scripts/check_no_iframe.sh:1           desarr. CUMPLE
    Guardian CI · gate tsc + Playwright        .github/workflows/ci.yml:1             desarr. CUMPLE
    Sellado M1/M2 por SHA-256 pegado a mano    interface/camino.js:357 · servir:377   alumno  REESCRIBIBLE
    Camino estrictamente secuencial            scripts/servir_interfaz.py:184         alumno  REESCRIBIBLE
    Estado "locked" de las misiones            src/missions.ts:17,93,123,149,175      alumno  REESCRIBIBLE
    Onboarding · autodeclaracion de nivel      interface/camino.js:189                alumno  REESCRIBIBLE
    Correccion de hardware sin validar         interface/camino.js:225 · servir:431   alumno  REESCRIBIBLE
    Guardian CI · canon M3 = El Refugio        scripts/canon_m3_check.py:1            desarr. REESCRIBIBLE

    Total 28 · CUMPLE 22 · REESCRIBIBLE 6 · DESCARTAR 0

Metrica del Metodo (cabecera del documento de doctrina): porcentaje de mecanismos
que cumplen la Regla Unica sin excepcion declarada = **22/28 = 79 %**. n_medicion
del Metodo es 3: esta es la medicion 1 de 3 antes de que la doctrina se enmiende.

## Resultado que conviene decir en voz alta: cero DESCARTAR

El bloque punitivo del material de origen — la Sordina que mata procesos, la Bola
de Hierro que asfixia la memoria, el Precipicio que cierra el terminal, la Vena
que retira el bit de ejecucion — **nunca se construyo aqui**. Vivio en la
propuesta y murio en el registro. No hay ni una linea de codigo en este
repositorio que castigue al usuario. La auditoria no tiene nada que amputar.

Lo que si hay son seis mecanismos que imponen coste sin ensenar, todos con
conversion conocida. Ninguno es cruel; varios son simplemente andamio que se
puso antes de que existiera la doctrina que ahora los juzga.

## Los seis REESCRIBIBLE, con su conversion

**1. Sellado M1/M2 por SHA-256 pegado a mano** — `interface/camino.js:357`,
`scripts/servir_interfaz.py:377`

El usuario firma en su terminal y pega 64 caracteres hexadecimales en un campo.
Test 1: no predice nada. Test 2: no recupera nada. Test 3: lo que aprende del
coste es a copiar y pegar un hash. Es ritual.

Conversion (patron "predecir antes de mostrar", Seccion 1): antes de pegar el
hash, preguntar **si el hash cambiara al anadir un solo espacio al final del
fichero** — si/no, y por que. Luego que lo haga y lo recalcule. El hueco entre
"un espacio no cambia nada" y un digest completamente distinto es la leccion
entera de la funcion resumen, y cuesta un comando mas. El sellado sigue igual;
lo que cambia es que ahora ensena.

**2. Camino estrictamente secuencial** — `scripts/servir_interfaz.py:184`
(`_avanzar`), `interface/camino.js:399` (`render` solo pinta `modulo_actual`)

Es el mecanismo que el arsenal llama [aur:moratoria]: bloquea el avance por lo no
hecho. Choca de frente con el contrato del Abecedario, Seccion 2.2: "El sistema
NUNCA bloquea el avance. Un tema sin base medida queda marcado como tal y se
recuerda al abrirlo. El usuario es un adulto."

Conversion (la que el propio Metodo escribe en su tabla de la Seccion 1): marcar
el modulo como **SIN BASE MEDIDA** y recordarlo al abrirlo, sin cerrar la puerta.
Impacto real: `_avanzar` deja de ser el unico camino a `modulo_actual`, y el rail
gana un cuarto estado ademas de `fait`/`actuel`/`attente`.

**3. Estado `locked` de las misiones** — `src/missions.ts:17` (el tipo) y
`:93,123,149,175` (cuatro misiones nacidas bloqueadas)

Misma violacion que el punto 2, en la capa de datos y en el sistema de tipos.
`MissionStatus` incluye `"locked"` como valor legitimo, asi que la doctrina de no
bloquear no tiene donde apoyarse: el tipo permite expresar lo prohibido.

Conversion: sustituir `"locked"` por `"sin base medida"` — mismo coste de cambio,
significado opuesto. Un tema al que le falta base se **senala**, no se cierra.

**4. Onboarding · autodeclaracion de nivel** — `interface/camino.js:189`

El usuario declara si es principiante, intermedio o avanzado, y eso fija la
profundidad de las explicaciones para siempre. Es una **confianza declarada sin
resultado observado**: exactamente la mitad izquierda del Anclaje, recogida y
nunca contrastada. No es punitivo, pero pide un juicio sobre uno mismo y no
devuelve nada medido a cambio.

Conversion: conectarlo al Anclaje. La autodeclaracion pasa a ser la primera
`confianza` del registro, y cuando existan cinco resultados, la curva le muestra
al usuario cuanto se acerto al declararse. La declaracion deja de ser una etiqueta
y pasa a ser un dato con hueco.

**5. Correccion de hardware sin validar** — `interface/camino.js:225`,
`scripts/servir_interfaz.py:431`

El usuario puede desmarcar la casilla y escribir cualquier RAM entre 0 y 4096 GB,
y el sistema la guarda como verdad. El Oraculo despues estima sobre ese numero.
Es la puerta por la que se cuela una medida que no es una medida.

Conversion: [aur:crisol] del arsenal — **marcar, jamas bloquear ni juzgar**. Si la
RAM declarada se aleja de la detectada mas alla de un margen, el registro lo anota
como declarada-por-el-usuario y toda estimacion que dependa de ella se etiqueta
igual. El usuario mantiene la ultima palabra sobre su propia maquina; lo que no
puede es que su correccion se vuelva indistinguible de una lectura del sensor.

**6. Guardian CI · canon M3 = El Refugio** — `scripts/canon_m3_check.py:1`,
`.github/workflows/canon-m3.yml`

Sujeto desarrollador, asi que la Regla Unica no lo juzga. Se marca REESCRIBIBLE
por otro motivo, y conviene que quede escrito: **defiende una numeracion que el
arsenal acaba de abolir**. `ARSENALAURELIUS_DEFINITIVO.txt`, pestana 1.3, sustituye
los identificadores numericos por textuales; este check falla el build si alguien
se aparta de la asociacion M3 = El Refugio. Y ademas `[aur:refugio]` figura como
ARCHIVADO por [R2] en el registro de archivados.

**No se toca en esta fase.** La migracion de identificadores es la tarea 3 del
prompt ARSENAL-1, que exige inventario previo y firma del Soberano sobre los casos
no resolubles. Aqui solo se deja constancia de que el guardian y el registro se
contradicen.

## Hallazgos fuera del alcance de la Fase 1 (registrados, no tocados)

- **La numeracion M0-M7 esta viva en todo el repositorio**: `src/missions.ts`,
  `interface/camino.js:51`, `interface/i18n.js` (claves `step.M0`…`step.M7`),
  `scripts/servir_interfaz.py:77`, los directorios de `sovereign_vault/`, y el
  guardian de CI que la defiende. El arsenal la abolio. Inventario y migracion =
  ronda ARSENAL-1, no esta.
- **Ninguno de los ocho temas del Abecedario existe todavia.** El repositorio
  ensena el Camino (Totem, Fuego, Agua…), no los temas del Metodo (Magnitudes,
  Electricidad, Componentes…). El aviso electrico de la Seccion 2.3 se construye
  en esta fase sin tema al que engancharse todavia: queda como componente listo,
  con su registro de temas electricos declarado en un solo sitio.
- **`sovereign_vault/M1_Espejo_Roto`** aparece citado en `interface/camino.js:323`
  como ruta de artefacto del usuario. Numeracion en una ruta de disco: migrarla
  toca datos de usuarios existentes, no solo codigo. Es un caso "no resoluble sin
  firma" de manual para la ronda ARSENAL-1.
- **El aviso de idioma sin revision humana cubre la prosa, pero no separa la
  prosa de la seguridad.** Cuando exista el aviso electrico traducido, un locale
  no verificado caera a ingles por el mecanismo general (`interface/i18n.js:16`).
  Para doctrina larga eso es lo correcto; para una advertencia de seguridad
  merece decision explicita. Ver SUGERENCIAS.
