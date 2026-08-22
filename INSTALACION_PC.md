# Instalar Aurelius en un ordenador

Dos caminos. El primero es para usar Aurelius; el segundo, para trastearlo.

---

## Camino 1 · el fichero que se abre con doble clic

**Un solo fichero, 14 MB. No hace falta instalar Python ni nada más.**

1. Descarga `aurelius`.
2. Ábrelo con doble clic.
3. Se abre tu navegador en Aurelius. Ya está.

Para cerrarlo, cierra la ventana negra que se abrió con él.

### Qué hace y qué no, dicho antes de que lo descubras

**Sí hace:** crea tu memoria, te hace las preguntas del primer arranque, guarda
tus recuerdos, y te enseña la frontera — el filtro que tacha claves, rutas y
direcciones antes de que un texto salga de tu máquina.

**No hace, todavía:** conversar. Para eso hacen falta dos piezas grandes que no
caben dentro y **no se descargan sin tu permiso**:

| Pieza | Tamaño | Por qué está fuera |
|---|---|---|
| El motor | ~10 MB | Es código ejecutable de otros. Este proyecto firma datos, no programas. |
| El cerebro | **2,3 GB** | Se ofrece con su licencia y su huella delante, y lo aceptas tú. |

Sin ellas, **Aurelius pregunta y recuerda pero no conversa**. Es la descripción
honesta, y este fichero no promete más de lo que trae dentro.

### Dónde queda lo tuyo

En `~/.aurelius/memory.db`. **Un solo fichero.** Puedes copiarlo, llevártelo en
un USB, o borrarlo. Nada sale de tu máquina si tú no lo exportas.

### Si algo va mal

La ventana negra dice qué pasó. Las dos cosas que suelen ocurrir:

- **«Aurelius ya estaba abierto»** — lo está. Se abrió el navegador y no se
  arrancó un segundo, porque dos a la vez sobre la misma memoria haría que
  vieras una cosa y el fichero dijera otra.
- **«El servidor no llegó a responder»** — algo ocupa el puerto 8740. Cierra la
  otra copia y vuelve a abrirlo.

---

## Camino 2 · desde el código

Para quien quiera leerlo, cambiarlo o auditarlo.

```
git clone https://github.com/piskyRpapalo/aurelius
cd aurelius
python3 aurelius.py             # crear tu memoria
python3 aurelius.py --charla    # hablar, si hay cerebro
bin/aurelius-servicio arranca   # la cara web
```

Python 3.10 o más nuevo. **Sin dependencias**: solo biblioteca estándar. Eso no
es una virtud abstracta — es lo que hace que el fichero del camino 1 quepa en
14 MB y no en 400.

---

## Cómo se construye el fichero del camino 1

```
uv pip install pyinstaller
bash empaquetado/construir_pc.sh
```

Sale en `dist/aurelius`. El guion declara las piezas que el empaquetador no
puede ver solo — ver el comentario en `empaquetado/lanzador.py`, que existe
porque la primera versión construyó un binario que moría con
`No module named 'json'`.
