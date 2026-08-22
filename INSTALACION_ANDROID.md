# Instalar Aurelius en un teléfono Android

**Estado, a 2026-08-22: hay dos caminos, y solo uno existe hoy.** Lo digo
primero para que nadie descargue lo que no está.

| | Estado |
|---|---|
| **Termux** · una línea, y Aurelius habla | **funciona hoy** |
| **APK** · instalar y abrir, sin terminal | **no existe todavía** — ver §3 |

---

## §1 · Camino que funciona hoy · Termux

Pide teclear una vez. Después no hace falta la terminal para usarlo.

1. Instala **Termux** desde F-Droid *(no desde Google Play: esa versión está
   abandonada y falla)*.
2. Ábrelo y teclea:

```
pkg install -y git
git clone --depth 1 https://github.com/piskyRpapalo/aurelius ~/aurelius
cd ~/aurelius && bash bin/instalar-android
```

3. Cuando termine:

```
python3 aurelius.py                  # crear tu memoria
bin/crear-acceso-directo-android     # el atajo (opcional, recomendado)
bin/aurelius-servicio arranca        # la cara web
```

4. Abre el navegador del teléfono en **http://127.0.0.1:8740**

### El icono en la pantalla de inicio

Dos formas, y resuelven mitades distintas.

**Un atajo que arranca todo.** `bin/crear-acceso-directo-android` escribe un
guion que arranca el servidor **y** abre el navegador de una vez. Para verlo
como icono hace falta **Termux:Widget** (F-Droid): mantén pulsada la pantalla
de inicio → Widgets → Termux → elige *Aurelius*. Si Termux:Widget no está, el
guion lo dice y explica qué hacer — no crea un icono que no va a aparecer.

**Un atajo del navegador.** Con la cara abierta en Chrome: menú **⋮ → Añadir a
pantalla de inicio**. Queda un icono que abre Aurelius a pantalla completa, sin
barra de navegador. Lo que **no** hace es arrancar el servidor: si no está
corriendo, el icono abre una página que no carga. Por eso existe la primera.

### Después de reiniciar el teléfono

Android no arranca Termux solo. Hay que abrir Termux y teclear
`bin/aurelius-servicio arranca`.

Para evitarlo hace falta la aplicación **Termux:Boot** (F-Droid) y eximir a
Termux de la optimización de batería. Las dos se hacen a mano, en los ajustes.
Ningún guion puede concedérselas a sí mismo.

---

## ¿Cerraste todo y no sabes volver?

Le pasó al propio autor. Hasta hoy no había forma de reabrirlo sin recordar un
comando, y eso es una barrera para cualquiera que no lo haya construido.

### Si creaste el acceso directo

Toca el icono **Aurelius** en la pantalla de inicio. Arranca el servidor y abre
el navegador de una vez. Si no lo creaste, ver §1.

### Si no lo creaste

1. Abre **Termux**.
2. Escribe:

```
cd ~/aurelius && bin/aurelius-servicio arranca
```

3. Abre el navegador del teléfono en **http://127.0.0.1:8740**

### Si dice que el puerto está ocupado

Quedó una copia anterior corriendo:

```
bin/aurelius-servicio para
```

Y si aun así sigue ocupado:

```
pkill -f aurelius-pwa
```

### Cómo saber si está vivo

```
bin/aurelius-servicio estado
```

Dice el pid y si responde.

### Después de reiniciar el teléfono

Android no arranca Termux solo. O tocas el icono, o abres Termux y escribes el
comando de arriba. Para que arranque solo hacen falta **Termux:Boot** y eximir
a Termux de la optimización de batería — las dos se conceden desde los ajustes,
a mano.

---

## §2 · Qué se descarga, y cuándo

Nada pesado llega sin que lo aceptes. En el primer arranque Aurelius te ofrece,
con su licencia y su huella delante:

- el **cerebro**, 2,3 GB — sin él pregunta y recuerda, pero no conversa;
- la **voz**, 60 MB — opcional; sin ella el botón lo dice.

Medido en un Doogee S110: **unos 3 tokens por segundo**. Una respuesta corta
tarda minutos, y la interfaz lo avisa. No es que se haya colgado.

---

## §3 · Por qué todavía no hay APK

Lo pedido es una APK que se instale con un clic y abra Aurelius. **Un envoltorio
con un WebView no sirve**, y conviene entender por qué antes de encargarlo:

Un WebView apuntando a `127.0.0.1:8740` solo enseña algo **si hay un servidor
escuchando ahí**. Ese servidor es Python. Una aplicación Android no ejecuta
Python salvo que lo lleve dentro. Así que una APK que sea solo un WebView se
instalaría, se abriría, y mostraría una página en blanco — **peor que no tener
nada**, porque parece rota en vez de no estar.

Una APK de verdad tiene que empaquetar el intérprete de Python junto al
producto. Eso es un proyecto de aplicación, no un envoltorio, y necesita cadena
de construcción de Android — que **no está instalada en el nodo donde se
compila hoy** (solo hay `platform-tools`; ni Java, ni Gradle, ni las
herramientas del SDK).

**Lo que sí se puede prometer sin mentir:** el camino §1 más el icono en la
pantalla de inicio da, hoy, un Aurelius que se abre desde un icono. Lo que falta
para el clic único es que el servidor arranque solo, y eso son las dos piezas
del §1 (Termux:Boot y la exención de batería) o una aplicación de verdad.
