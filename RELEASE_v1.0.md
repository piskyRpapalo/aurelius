# Aurelius v1.0.0 · MVP cerrado

## Qué es este release

El primer producto mínimo viable de Aurelius: un compañero de memoria
local-first, sin nube, sin telemetría, que empieza vacío y lo dice.

## Dos puertas de entrada

### Para usuarios finales, sin terminal

- **PC** — un ejecutable de 14 MB, doble clic, abre el navegador.
  [INSTALACION_PC.md](INSTALACION_PC.md)
- **Android** — Termux y un icono en la pantalla de inicio.
  [INSTALACION_ANDROID.md](INSTALACION_ANDROID.md)

### Para desarrolladores

```
git clone https://github.com/piskyRpapalo/aurelius.git
cd aurelius
python3 aurelius.py
```

Sin dependencias externas: Python 3.10+ y su biblioteca estándar. Esa
disciplina es también lo que hace que el ejecutable quepa en 14 MB.

## Qué hace

- Recuerda lo que le dices, con tus palabras.
- No manda tus datos a ningún sitio.
- Pregunta antes de hacer nada destructivo.
- Funciona sin conexión, en tu máquina.
- Empieza vacío, lo dice, y te ayuda a llenarlo.

## Qué NO hace, y lo dice

- **No busca — todavía.** Con pocos recuerdos, buscar es la solución a un
  problema que no tienes.
- **No redacta lo que guardas.** Tu máquina, tus datos. La redacción ocurre en
  la frontera, cuando algo está a punto de salir.
- **No necesita red, ni GPU, ni dependencias más allá de Python 3.**
- **No conversa sin cerebro instalado.** Sin él pregunta y recuerda, y te lo
  dice en vez de disimular.

## Seguridad

El fusible inspecciona lo que el modelo escribe antes de que lo veas.
Reconoce formas estructurales, no palabras prohibidas. **No** resuelve
variables, no descodifica base64 y no sigue indirecciones. Frena; no te
sustituye. **La última comprobación la haces tú.**

Los límites exactos están escritos enteros en [TECHNICAL.md](TECHNICAL.md), no
resumidos.

## Verificado en este release

| | |
|---|---|
| Pruebas | **278 en 17 suites**, verde |
| Versiones de Python | 3.10 a 3.14, en CI, cada push |
| La cara | cuatro estados de la frontera, medidos con tráfico real en un teléfono |
| El ejecutable | arranca, sirve y filtra — comprobado corriendo, no supuesto |

## Lo que queda como horizonte, con su medida

- **Un LoRA que generalice la doctrina.** Siete ciclos medidos. La conclusión
  honesta: transfiere entre situaciones de una conducta enseñada, y nada entre
  conductas que no vio. La puerta de producto sigue roja y el modelo base es lo
  que se despliega.
- **APK nativa de Android.** Un envoltorio con WebView no sirve: sin un
  servidor Python escuchando, se instala y enseña una página en blanco. Hace
  falta empaquetar el intérprete, y eso es un proyecto de aplicación.
- **Persistencia sin pasos a mano.** Android no arranca Termux solo. Hacen
  falta Termux:Boot y la exención de batería, y las dos se conceden desde los
  ajustes, mirando la pantalla.

## Licencia

- **Código** — MIT · [LICENSE](LICENSE)
- **Prosa, lore y sprites** — CC BY-SA 4.0 · [LICENSE-PROSE](LICENSE-PROSE)
