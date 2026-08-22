# Marca · lo que hay que subir a mano

Los ficheros están hechos y verificados. Lo que sigue **lo subes tú**: son
acciones en la web de GitHub, y esta sesión no puede autenticarse contra ella.

---

## Ficheros listos

| Qué | Fichero | Medidas |
|---|---|---|
| Avatar de perfil | `assets/avatar-github.png` | 512×512 · fondo violeta `#6d5ae0` |
| Vista previa social | `assets/social-preview.png` | 1280×640 |
| Icono de la aplicación | `assets/icono-cyborg.png` | 512×512 · fondo transparente |
| Badges propios | `assets/badges/*.svg` | cinco, sin dependencias |

**Sobre el fondo del avatar.** No va transparente: GitHub lo pone sobre blanco
en un tema y sobre casi negro en el otro, y el busto es gris claro — en el tema
claro se perdería. El violeta de la casa es lo único que se ve igual en los dos.

**Sobre el recorte del sprite.** El fondo gris se quita por inundación desde los
bordes, no filtrando ese color en toda la imagen: el busto lleva grises
parecidos dentro, y un filtro global le abriría agujeros en la maquinaria.

---

## Bio del perfil · 160 caracteres

La tuya son **147** y ya cabe. Dos alternativas, por si prefieres otra cosa:

```
Sovereign AI Builder | Local-first edge systems | Zero cloud, zero sockets, your signature
```

**Más concreta** (139): dice qué construyes, no cómo te llamas a ti mismo.

```
Local-first AI that runs on your machine. No cloud, no telemetry, no account.
Your memory in one file you can carry.
```

**Más corta** (96): la que más se recuerda.

```
Local-first AI. It starts empty and says so. No cloud, no telemetry, one file you can carry.
```

*Recomiendo la segunda: la primera dice tres categorías, la segunda dice qué
hace el producto, y quien llega al perfil viene a ver qué hay.*

---

## Topics del repositorio `aurelius`

En la web del repo, la rueda dentada junto a *About*:

```
local-first  privacy  offline-ai  sqlite  pwa  llm
python  memory  self-hosted  human-in-the-loop  edge-computing
```

---

## Vista previa social

Ajustes del repo → *Social preview* → subir `assets/social-preview.png`.

---

## Los SVGs del perfil · lo que medí, y no es lo que parecía

Las cinco imágenes del README de perfil **funcionan**. Comprobadas una a una:

| | |
|---|---|
| `aurelius-talks.png` | HTTP 200 · `image/png` · 492 756 b |
| los cuatro shields | HTTP 200 · `image/svg+xml` · 1,2–1,4 kB cada uno |

Y el marcado es correcto: línea en blanco, los cuatro `<img>` seguidos, línea
en blanco. Eso es un bloque HTML válido en Markdown de GitHub.

**Así que no puedo reproducir el fallo.** Lo más probable es que el proxy de
imágenes de GitHub cachease un fallo transitorio de `shields.io` — pasa, y
persiste, y no se arregla desde el repositorio.

**El arreglo robusto, que sí puedo darte:** badges propios en
`assets/badges/*.svg`. Un badge de `shields.io` es una petición a un tercero
cada vez que alguien abre el README; si ese tercero falla, el badge desaparece
y no hay nada que tocar. Estos viven en el repo, igual que la cara no pide una
sola conexión.

Para el README de perfil, sustituye las cuatro líneas por estas:

```html
<img src="https://raw.githubusercontent.com/piskyRpapalo/aurelius/main/assets/badges/python.svg" alt="Python 3.10+">
<img src="https://raw.githubusercontent.com/piskyRpapalo/aurelius/main/assets/badges/deps.svg" alt="Dependencies: stdlib only">
<img src="https://raw.githubusercontent.com/piskyRpapalo/aurelius/main/assets/badges/code.svg" alt="Code licence: MIT">
<img src="https://raw.githubusercontent.com/piskyRpapalo/aurelius/main/assets/badges/prose.svg" alt="Prose licence: CC BY-SA 4.0">
```

**Aviso, y por eso no lo he hecho yo:** el badge de las pruebas del README de
Aurelius **sí** tiene que seguir siendo el de GitHub Actions. Ese no es
decoración: cambia de color solo cuando la tanda se pone roja, y uno guardado
en el repo diría «verde» para siempre. Un badge que no puede ponerse rojo es
peor que no tener badge.

**Y una nota sobre la copia local:** `~/p0x/github-profile/README.md` está
desfasado — no tiene ninguna de estas imágenes. Lo que está publicado y lo que
tienes en disco no son lo mismo.
