#!/usr/bin/env python3
"""M2 · el Agua · la memoria de Aurelius.

sistema: MVP · solo biblioteca estandar (python3 + sqlite3).
Un unico fichero .db que la persona se lleva consigo.

Tres invariantes que este modulo no negocia:
  1. Ausente, vacia y con datos son tres estados distintos. Nunca se confunden.
  2. La redaccion ocurre en la FRONTERA (exportar), jamas al escribir en disco.
     La memoria guarda las palabras de la persona tal cual: es su maquina.
  3. Archivar es una columna, no una carpeta. Cero DELETE en este fichero.
  4. Devolver es prometer: si una escritura devuelve, esta en disco. Cada
     escritura es su propia transaccion y confirma ANTES del return. La sesion
     entera fue una sola transaccion hasta M-D64, y eso convertia Ctrl+C -el
     modo normal de salir de una conversacion- en un borrado completo.

Los textos visibles para la persona salen de `textos.py`, en los dos idiomas
que el producto habla (D74). Los comentarios y nombres internos, en espanol,
porque su lector es el equipo.
"""
from __future__ import annotations

import contextlib
import os
import sqlite3
import threading
from datetime import datetime, timezone

import textos as TX

AUSENTE = "NO_DATA"          # marca visible de ausencia declarada
CAMPOS_HUECO = ("why", "where_ref", "learned")

# El marco, que no es contenido. Donde corre Aurelius y como quiere la persona
# que la llamen no son recuerdos: un recuerdo es algo que le paso y decidio
# escribir. Guardarlos como engramas metería dos filas que nadie escribio en el
# recuento de huecos, y daria la mision por cumplida sin que la persona hubiera
# escrito nada suyo. Por eso viven en una tabla aparte, clave-valor.
# El idioma vive aqui por la misma razon: no es un recuerdo, es el marco en el
# que se cuentan. Y se declara ausente como cualquier otra clave — quien no lo
# eligio no queda registrado como si hubiera elegido ingles (D74).
CLAVES_PERFIL = ("device", "name", "language", "voice")

ESQUEMA = """
create table if not exists engrams (
    id         integer primary key autoincrement,
    what       text not null check (length(trim(what)) > 0),
    why        text not null default 'NO_DATA',
    where_ref  text not null default 'NO_DATA',
    learned    text not null default '',
    origin     text not null default 'persona'
               check (origin in ('persona', 'intencion', 'importado')),
    status     text not null default 'activo'
               check (status in ('activo', 'archivado')),
    created_at text not null default (datetime('now')),
    updated_at text not null default (datetime('now'))
);
create table if not exists links (
    id          integer primary key autoincrement,
    from_engram integer not null references engrams(id),
    to_engram   integer not null references engrams(id),
    label       text not null default 'NO_DATA',
    created_at  text not null default (datetime('now'))
);
"""

# Se declara aparte del resto del esquema a proposito: es lo unico que puede
# faltarle a una base creada antes de que el perfil existiera, y es lo unico
# que hace falta anadir. Crear la tabla que falta no es migrar: engrams no se
# toca, no se copia y no se recrea, asi que sus CHECK siguen siendo los suyos.
ESQUEMA_PERFIL = """
create table if not exists profile (
    key        text primary key,
    value      text not null default 'NO_DATA',
    updated_at text not null default (datetime('now'))
);
"""



# La tabla de salidas registra cada texto que cruza la frontera hacia fuera.
# Append-only: nunca se borra una fila. Lo que salio, salio, y queda constancia.

# D14: Esquema de Hilos y Eventos (Event Sourcing)
# D69 · la capa de BORRADORES. Lo que propone la maquina vive aqui y NO en
# `engrams`: la memoria firmada es lo que la persona escribio o lo que la
# persona ascendio, nunca lo que un modelo creyo entender.
#
# `engrama_id` y `motivo` no estaban en el encargo y se anaden declarandolo:
# sin el primero, promover borraria la unica prueba de que aquello lo propuso
# la maquina -- y el CHECK de `origin` en engrams no se migra (D69), asi que la
# procedencia no cabe alli. Sin el segundo, "descartar deja constancia" seria
# constancia de que se descarto, pero no de por que.
#
# Cero DELETE y cero DROP: los tres estados son valores de una columna, y la
# capa no se vacia nunca.
ESQUEMA_BORRADORES = """
create table if not exists borradores (
    id         integer primary key autoincrement,
    cuando     text not null default (datetime('now')),
    texto      text not null,
    estado     text not null default 'pendiente'
               check (estado in ('pendiente', 'promovido', 'descartado')),
    origen     text not null default 'NO_DATA',
    engrama_id integer references engrams(id),
    motivo     text not null default 'NO_DATA'
);
"""

ESQUEMA_HILOS = """
CREATE TABLE IF NOT EXISTS hilos (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    titulo TEXT NOT NULL,
    origen_dispositivo TEXT NOT NULL DEFAULT 'NO_DATA',
    creado_en TEXT NOT NULL DEFAULT (datetime('now'))
);
CREATE TABLE IF NOT EXISTS hilos_eventos (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    hilo_id INTEGER NOT NULL,
    tipo TEXT NOT NULL CHECK (tipo IN ('abierto', 'tocado', 'cerrado', 'reabierto')),
    momento TEXT NOT NULL,
    FOREIGN KEY (hilo_id) REFERENCES hilos(id)
);
"""

ESQUEMA_SALIDAS = """
create table if not exists salidas (
    id            integer primary key autoincrement,
    cuando        text not null default (datetime('now')),
    canal         text not null default 'NO_DATA',
    texto         text not null,
    hallazgos     text not null default '[]',
    hash_original text not null,
    estado        text not null default 'ok',
    motivo        text not null default 'NO_DATA'
);
"""


class FronteraSinFiltro(Exception):
    """Se intento exportar sin filtro de redaccion. Falla cerrado."""


class SalidaSinPuerta(Exception):
    """Se intento registrar una salida sin cruzar por `cruzar_frontera`."""


class SalidaNoAprobada(Exception):
    """La persona miro la salida y dijo que no. No se registra ni sale."""


class PromocionSinPersona(Exception):
    """Se intento ascender un borrador a memoria firmada sin acto de la persona."""


class BorradorNoEncontrado(Exception):
    """El borrador citado no existe. Que no exista es dato, no obstaculo."""


class RespaldoNoVerificado(Exception):
    """La copia se hizo pero no cuadra con el original. No se da por buena."""


# --- componente 1 · memory_state ------------------------------------------

def estado(ruta):
    """('SIN_ESQUEMA'|'VACIA'|'CON_DATOS', recuentos). Nunca adivina."""
    recuentos = {"engrams": 0, "links": 0, "archivados": 0}
    if not os.path.exists(ruta):
        return "SIN_ESQUEMA", recuentos
    try:
        with abrir(ruta) as c:
            tablas = {r[0] for r in c.execute(
                "select name from sqlite_master where type='table'")}
            if not {"engrams", "links"} <= tablas:
                return "SIN_ESQUEMA", recuentos
            recuentos["engrams"] = c.execute(
                "select count(*) from engrams where status='activo'").fetchone()[0]
            recuentos["archivados"] = c.execute(
                "select count(*) from engrams where status='archivado'").fetchone()[0]
            recuentos["links"] = c.execute("select count(*) from links").fetchone()[0]
    except sqlite3.DatabaseError:
        return "SIN_ESQUEMA", recuentos
    total = recuentos["engrams"] + recuentos["archivados"]
    return ("VACIA" if total == 0 else "CON_DATOS"), recuentos


def mensaje_estado(est, recuentos, idioma=TX.DEFECTO):
    """Texto visible. Ausente y vacia dicen cosas distintas, a proposito.

    El idioma es un parametro con valor por defecto: quien llamaba a esto antes
    de que el producto hablara dos idiomas sigue recibiendo lo mismo, byte a
    byte. Una firma que cambia de conducta sin avisar rompe a sus llamantes en
    silencio, y aqui los llamantes son el manifiesto y las tres vistas.
    """
    if est == "SIN_ESQUEMA":
        return TX.texto(idioma, "estado_sin_esquema")
    if est == "VACIA":
        return TX.texto(idioma, "estado_vacia")
    n, a, l = recuentos["engrams"], recuentos["archivados"], recuentos["links"]
    return (TX.texto(idioma, "estado_con_datos", n=n, l=l)
            + (TX.texto(idioma, "estado_archivados", a=a) if a else "")
            + TX.texto(idioma, "estado_cola"))


# --- componente 2 · memory_init -------------------------------------------

def crear(ruta):
    """Crea el esquema. Solo se llama tras confirmacion explicita."""
    carpeta = os.path.dirname(os.path.abspath(ruta))
    os.makedirs(carpeta, exist_ok=True)
    with abrir(ruta) as c:
        c.executescript(ESQUEMA + ESQUEMA_PERFIL + ESQUEMA_SALIDAS
                        + ESQUEMA_HILOS + ESQUEMA_BORRADORES)
        # D12: Migracion aditiva. Si la DB es vieja, le anyade la columna.
        try:
            c.execute("ALTER TABLE engrams ADD COLUMN origen_dispositivo TEXT NOT NULL DEFAULT 'NO_DATA'")
        except sqlite3.OperationalError:
            pass  # La columna ya existe
    
    # B2: Permisos restrictivos desde el primer byte
    try:
        os.chmod(carpeta, 0o700)
        os.chmod(ruta, 0o600)
    except OSError:
        pass  # En Windows o sistemas sin soporte, no falla
    return ruta


@contextlib.contextmanager
def abrir(ruta):
    """Conexion con diario WAL: un corte de luz no corrompe el fichero.

    El rollback se queda. Con una transaccion por escritura solo puede alcanzar
    a una escritura incompleta, que es su proposito legitimo. Lo que se elimino
    no fue la red de seguridad: fue que la red abarcara la sesion entera, de
    modo que una interrupcion descartaba todo lo escrito en ella.
    """
    con = sqlite3.connect(ruta)
    con.row_factory = sqlite3.Row
    try:
        con.execute("pragma journal_mode=wal")
        con.execute("pragma foreign_keys=on")
        yield con
        con.commit()
    except BaseException:
        con.rollback()
        raise
    finally:
        con.close()


# --- componente 3 · engram_write ------------------------------------------

def _o_ausente(v):
    """None o cadena vacia -> ausencia DECLARADA, no celda en blanco."""
    return AUSENTE if v is None or str(v).strip() == "" else v


def escribir_engrama(c, what, why=None, where_ref=None, learned="",
                     origin="persona", origen_dispositivo="NO_DATA"):
    """Inserta un recuerdo con las palabras de la persona, sin normalizar.
    `what` es obligatorio; el resto puede quedar en NO_DATA y el recuerdo
    sigue siendo valido: un recuerdo sin motivo declarado es informacion.
    `origen_dispositivo` marca donde nacio (D11: Identidad por Origen)."""
    if what is None or str(what).strip() == "":
        raise ValueError("what es obligatorio: un recuerdo sin qué no es un recuerdo")
    cur = c.execute(
        "insert into engrams (what, why, where_ref, learned, origin, origen_dispositivo) "
        "values (?, ?, ?, ?, ?, ?)",
        (what, _o_ausente(why), _o_ausente(where_ref), learned or "", origin, origen_dispositivo))
    c.commit()      # durabilidad ANTES de devolver: si se devuelve, esta en disco
    return leer_engrama(c, cur.lastrowid)


def leer_engrama(c, ident):
    fila = c.execute("select * from engrams where id=?", (ident,)).fetchone()
    return dict(fila) if fila else None


def escribir_enlace(c, desde, hacia, label=None):
    """La etiqueta es texto libre: las palabras de la persona, no una lista."""
    cur = c.execute(
        "insert into links (from_engram, to_engram, label) values (?, ?, ?)",
        (desde, hacia, _o_ausente(label)))
    c.commit()      # durabilidad ANTES de devolver: si se devuelve, esta en disco
    return cur.lastrowid


def archivar(c, ident):
    """Sale de la vista por defecto. Sigue en la tabla. No se borra nada."""
    c.execute("update engrams set status='archivado', "
              "updated_at=datetime('now') where id=?", (ident,))
    c.commit()      # durabilidad ANTES de devolver: si se devuelve, esta en disco


def desarchivar(c, ident):
    c.execute("update engrams set status='activo', "
              "updated_at=datetime('now') where id=?", (ident,))
    c.commit()      # durabilidad ANTES de devolver: si se devuelve, esta en disco


# --- componente 3b · el perfil --------------------------------------------

def _hay_perfil(c):
    return c.execute("select name from sqlite_master where type='table' "
                     "and name='profile'").fetchone() is not None


def leer_perfil(c, clave=None):
    """Con clave, su valor; sin clave, el perfil entero como diccionario.

    Nunca devuelve celda en blanco ni None: lo que no se contesto sale como
    NO_DATA, igual que en un recuerdo. Y nunca escribe: una base creada antes
    de que el perfil existiera se puede mirar sin que mirarla la modifique.
    """
    if not _hay_perfil(c):
        return AUSENTE if clave else {k: AUSENTE for k in CLAVES_PERFIL}
    guardado = {r["key"]: r["value"] for r in c.execute("select key, value from profile")}
    if clave:
        return guardado.get(clave) or AUSENTE
    perfil = {k: guardado.get(k) or AUSENTE for k in CLAVES_PERFIL}
    for k in sorted(set(guardado) - set(CLAVES_PERFIL)):
        perfil[k] = guardado[k]
    return perfil


def guardar_perfil(c, pares, commit=True):
    """Escribe pares del perfil. El UNICO sitio del arbol con SQL de `profile`.

    `ON CONFLICT(key) DO UPDATE`, jamas `INSERT OR REPLACE`. Lo segundo borra
    la fila entera y mete otra, asi que toda columna que la fila tuviera y la
    sentencia no nombre vuelve a su DEFAULT: es un DELETE con otro nombre, y la
    regla de cero DELETE no tiene una excepcion para cuando es una sola fila.

    La diferencia NO se ve con una clave nueva -- ahi las dos formas escriben
    lo mismo. Solo aparece al reescribir una clave que YA EXISTE, que es el
    caso que ocurre de verdad: corregir una errata, volver a una sala. Una
    prueba montada sobre una clave nueva no distingue las dos y da verde con
    la mala dentro.

    `commit=False` para quien escribe un lote y confirma una sola vez al final.
    La Fuga vuelca el perfil de una sala entero o no lo vuelca: un commit por
    clave convertiria esa promesa en media sala escrita.

    La tabla se crea aqui si falta: asi el esquema se actualiza cuando la
    persona contesta, no al abrir.
    """
    # Las claves se validan TODAS antes de escribir ninguna. Validarlas sobre
    # la marcha dejaria escritas las anteriores y sin escribir las siguientes:
    # exactamente la media escritura que este modulo existe para no hacer.
    limpio = []
    for clave, valor in dict(pares).items():
        if clave is None or str(clave).strip() == "":
            raise ValueError("una clave de perfil vacia no identifica nada")
        limpio.append((str(clave).strip(), _o_ausente(valor)))
    # execute y no executescript: executescript confirma lo que hubiera pendiente
    # antes de correr, y aqui no toca decidir por la transaccion de quien llama.
    c.execute(ESQUEMA_PERFIL)
    for clave, valor in limpio:
        c.execute("insert into profile (key, value) values (?, ?) "
                  "on conflict(key) do update set value=excluded.value, "
                  "updated_at=datetime('now')", (clave, valor))
    if commit:
        c.commit()  # durabilidad ANTES de devolver: si se devuelve, esta en disco
    return [k for k, _ in limpio]


def escribir_perfil(c, clave, valor):
    """Guarda UNA respuesta del perfil. Contestar dos veces corrige en sitio.

    La pareja de `leer_perfil` para el caso de una clave sola. El SQL no vive
    aqui: lo pone `guardar_perfil`, para que haya un solo escritor de `profile`
    en todo el arbol y no dos que puedan separarse con el tiempo.
    """
    guardar_perfil(c, {clave: valor})
    return {"key": str(clave).strip(), "value": leer_perfil(c, str(clave).strip())}


# --- componente 4 · memory_view -------------------------------------------

def _filas(c, incluir_archivados=False):
    q = "select * from engrams"
    if not incluir_archivados:
        q += " where status='activo'"
    return [dict(r) for r in c.execute(q + " order by id")]


def vista_perfil(c):
    """Cabecera de una linea: el marco de esta memoria, huecos incluidos.

    Las claves sin contestar se muestran en NO_DATA en vez de esconderse. Una
    cabecera que solo ensenara lo relleno mentiria por omision: nadie echa de
    menos una pregunta que no sabe que existe.
    """
    perfil = leer_perfil(c)
    return "profile · " + " · ".join(f"{k}: {v}" for k, v in perfil.items())


def _con_perfil(c, cuerpo):
    """Toda vista se lee bajo su cabecera: quien es y donde, antes del que."""
    return f"{vista_perfil(c)}\n\n{cuerpo}"


def vista_tabla(c, incluir_archivados=False):
    """Una fila por recuerdo. NO_DATA escrito, nunca celda en blanco."""
    filas = _filas(c, incluir_archivados)
    if not filas:
        return _con_perfil(c, "(no memories yet)")
    cols = ("id", "what", "why", "where_ref", "learned", "origin", "status")
    ancho = {k: max(len(k), *(len(str(f[k]) or "") for f in filas)) for k in cols}
    ancho["what"] = min(ancho["what"], 40)
    ancho["learned"] = min(ancho["learned"], 24)

    def celda(v, k):
        s = AUSENTE if v is None or str(v) == "" else str(v)
        s = s.replace("\n", "\\n").replace("\t", "\\t")
        return (s[:ancho[k] - 1] + "…") if len(s) > ancho[k] else s.ljust(ancho[k])

    cab = " | ".join(k.upper().ljust(ancho[k]) for k in cols)
    sep = "-+-".join("-" * ancho[k] for k in cols)
    cuerpo = "\n".join(" | ".join(celda(f[k], k) for k in cols) for f in filas)
    return _con_perfil(c, f"{cab}\n{sep}\n{cuerpo}")


def vista_arbol(c):
    """Recuerdos como raices; sus enlaces como hijos indentados dos espacios.
    Un recuerdo sin enlaces aparece como raiz suelta, y eso es informacion."""
    filas = {f["id"]: f for f in _filas(c)}
    if not filas:
        return _con_perfil(c, "(no memories yet)")
    enlaces = [dict(r) for r in c.execute("select * from links order by id")]
    hijos = {}
    for e in enlaces:
        hijos.setdefault(e["from_engram"], []).append(e)
    salida = []
    for ident, f in filas.items():
        marca = " [archived]" if f["status"] == "archivado" else ""
        salida.append(f"{f['what']}{marca}")
        for e in hijos.get(ident, []):
            destino = filas.get(e["to_engram"])
            nombre = destino["what"] if destino else AUSENTE
            salida.append(f"  --({e['label']})--> {nombre}")
    return _con_perfil(c, "\n".join(salida))


# --- modo formulario · el puente con la cara, sin nadie en medio -----------

def formulario(c):
    """El estado que la cara necesita para dibujarse, en un diccionario.

    Se lee entero de una vez y se entrega. No hay servidor entre la cara y
    esto: quien la genera ya tiene la conexion abierta, y quien la mira solo
    recibe el resultado. Un intermediario aqui seria una pieza mas que puede
    mentir sobre lo que hay escrito.
    """
    return {
        "profile": leer_perfil(c),
        "engrams": [dict(r) for r in c.execute(
            "select id, what, why, where_ref, learned, origin, created_at "
            "from engrams where status='activo' order by id")],
        "links": [dict(r) for r in c.execute(
            "select from_engram, to_engram, label from links order by id")],
        "recuento": recuento_huecos(c),
    }


def aplicar_formulario(c, datos):
    """Escribe lo que la cara recogio. Solo anade.

    Tres reglas, y las tres son la misma regla mirada desde tres sitios:

      · Un formulario nunca reemplaza. Lo que ya estaba escrito sigue estando,
        con su id y su fecha. La cara propone recuerdos nuevos; no tiene
        permiso para opinar sobre los viejos.
      · Un formulario vacio no cambia nada. Recibir cero recuerdos no es la
        orden de vaciar la memoria: es que no habia nada que anadir.
      · Una fila sin `what` no es un recuerdo y no se escribe. Igual que en la
        conversacion: sin un que, no hay nada que guardar.

    Devuelve el recuento de lo que SI se escribio, para que quien llame pueda
    decirselo a la persona en cifras y no en adjetivos.
    """
    resumen = {"engrams": 0, "profile": 0, "language": False}

    idioma = (datos.get("language") or "").strip()
    if idioma:
        escribir_perfil(c, "language", idioma)
        resumen["language"] = True

    for clave, valor in (datos.get("profile") or {}).items():
        if clave in CLAVES_PERFIL and str(valor).strip():
            escribir_perfil(c, clave, valor)
            resumen["profile"] += 1

    for fila in (datos.get("engrams") or []):
        what = str(fila.get("what") or "").strip()
        if not what:
            continue
        escribir_engrama(c, what=what,
                         why=(fila.get("why") or "").strip() or None,
                         where_ref=(fila.get("where_ref") or "").strip() or None,
                         learned=(fila.get("learned") or "").strip(),
                         origin=fila.get("origin") or "persona")
        resumen["engrams"] += 1
    return resumen


def recuento_huecos(c):
    """Cuantos campos quedan en NO_DATA. La cifra que mide el avance real."""
    filas = _filas(c)
    rec = {k: 0 for k in CAMPOS_HUECO}
    for f in filas:
        for k in CAMPOS_HUECO:
            if f[k] == AUSENTE or str(f[k]).strip() == "":
                rec[k] += 1
    rec["total"] = sum(rec[k] for k in CAMPOS_HUECO)
    rec["engrams"] = len(filas)
    return rec


def vista_recuento(c):
    r = recuento_huecos(c)
    l = c.execute("select count(*) from links").fetchone()[0]
    lineas = [f"memories: {r['engrams']}", f"links:    {l}", "gaps (NO_DATA):"]
    lineas += [f"  {k:<10} {r[k]}" for k in CAMPOS_HUECO]
    lineas.append(f"  {'total':<10} {r['total']}")
    return _con_perfil(c, "\n".join(lineas))


def mision_completa(c):
    """Con UN recuerdo basta. Si la persona paro en uno, funciono."""
    return c.execute(
        "select count(*) from engrams where status='activo'").fetchone()[0] >= 1


# --- componente 6 · el respaldo -------------------------------------------
# Un `cp` del .db no es un respaldo. Con diario WAL, lo escrito y aun no
# consolidado vive en el fichero -wal: la copia del .db a secas puede salir
# vacia, y salio — `memory.db.antes-de-p0` era el respaldo de nada, y nadie lo
# supo hasta que hizo falta. Aqui se usa la API de respaldo de SQLite, que
# consolida el WAL en un fichero unico, y despues se vuelve a abrir la copia
# para contar: un respaldo que nadie ha leido no es un respaldo, es un fichero.

def _recuento_verificable(c):
    """Lo que tiene que salir identico en la copia. El perfil tambien."""
    return {
        "engrams": c.execute("select count(*) from engrams").fetchone()[0],
        "links": c.execute("select count(*) from links").fetchone()[0],
        "profile": (c.execute("select count(*) from profile").fetchone()[0]
                    if _hay_perfil(c) else 0),
    }


def ruta_respaldo(ruta, cuando=None):
    """Nombre con marca de tiempo UTC: dos respaldos nunca se pisan."""
    marca = cuando or datetime.now(timezone.utc).strftime("%Y%m%d-%H%M%SZ")
    return f"{ruta}.backup-{marca}.db"


def respaldar(ruta, destino=None):
    """Copia entera y comprobada. Devuelve (destino, recuentos de la COPIA).

    Los recuentos se leen de la copia, no del original: son la prueba de que
    lo que hay en el fichero nuevo es lo que habia, y no una promesa sobre el
    fichero viejo.
    """
    if not os.path.exists(ruta):
        raise FileNotFoundError(
            f"there is no memory to back up at {ruta}. "
            "Nothing was copied, and nothing is wrong: nothing exists yet.")
    destino = destino or ruta_respaldo(ruta)
    if os.path.exists(destino):
        # Un respaldo jamas pisa un respaldo: el fichero que sobrescribiria
        # puede ser la unica copia buena que queda.
        raise FileExistsError(
            f"{destino} already exists. A backup never overwrites a backup.")
    origen = sqlite3.connect(ruta)
    copia = sqlite3.connect(destino)
    try:
        origen.backup(copia)
        antes = _recuento_verificable(origen)
        despues = _recuento_verificable(copia)
    finally:
        copia.close()
        origen.close()
    if antes != despues:
        # No se borra: se marca. Borrar seria decidir por la persona sobre un
        # fichero que quiza contiene algo. Pero no puede quedarse con nombre de
        # respaldo bueno, porque el dia que haga falta se cogera este.
        roto = destino + ".INCOMPLETO"
        os.replace(destino, roto)
        raise RespaldoNoVerificado(
            f"the copy does not match the original ({antes} vs {despues}). "
            f"It was renamed to {roto} and must not be trusted as a backup.")
    return destino, despues



def restaurar(respaldo, destino):
    """Restaura un respaldo en una ruta nueva. Nunca pisa el destino.

    Simetrico a respaldar(): falla cerrado si el respaldo no existe,
    si el destino ya existe, o si los recuentos no coinciden despues.
    No destruye el original: restaurar es copiar hacia adelante, no mover.
    """
    if not os.path.exists(respaldo):
        raise FileNotFoundError(
            f"there is no backup at {respaldo}. Nothing to restore.")
    if os.path.exists(destino):
        # Restaurar jamas pisa una memoria viva: el destino puede ser
        # la unica copia que la persona tiene en uso.
        raise FileExistsError(
            f"{destino} already exists. Restore never overwrites a live memory.")
    origen = sqlite3.connect(respaldo)
    copia = sqlite3.connect(destino)
    try:
        origen.backup(copia)
        antes = _recuento_verificable(origen)
        despues = _recuento_verificable(copia)
    finally:
        copia.close()
        origen.close()
    if antes != despues:
        roto = destino + ".INCOMPLETO"
        os.replace(destino, roto)
        raise RespaldoNoVerificado(
            f"the restore does not match the backup ({antes} vs {despues}). "
            f"It was renamed to {roto} and must not be trusted as a memory.")
    return destino, despues

# La puerta se abre desde dentro, y por un solo hilo. Con una global bastaria
# hoy -- el CLI es un proceso de un hilo --, pero el puente del tailnet mete un
# servidor en este mismo proceso, y alli dos turnos a la vez convertirian la
# bandera en una puerta abierta por accidente.
_paso = threading.local()

# Los mensajes de estas excepciones son fijos y no llevan fragmento del texto:
# se pueden guardar enteros. Se comparan por NOMBRE en vez de importar
# guardrails o fusible aqui: la dependencia del arbol va producto -> memoria, y
# no se invierte por comodidad.
_MOTIVOS_CITABLES = ("EnvioBloqueado", "SinInspeccion", "RespuestaBloqueada",
                     "FronteraSinFiltro")


def _motivo(e):
    """Por que se bloqueo, sin arrastrar el texto que lo provoco.

    De una excepcion ajena solo se guarda el NOMBRE del tipo: su mensaje puede
    llevar dentro el fragmento que la causo, y el registro se ensena.
    """
    nombre = type(e).__name__
    if nombre in _MOTIVOS_CITABLES:
        return f"{nombre}: {e}"
    return nombre


def asegurar_tablas(c):
    """Crea las tablas jovenes si faltan y anyade las columnas nuevas.

    No vale con hacerlo en `crear()`: una memoria que ya existe no vuelve a
    pasar por ahi nunca, y las tablas que llegaron despues (salidas en R2, hilos
    en D14) no aparecen solas. Medido contra la memoria viva del Soberano
    (2026-08-18): nacida antes de las dos, no tenia ninguna.

    Idempotente y aditivo: cero DELETE, cero DROP, cero valores tocados.
    """
    c.executescript(ESQUEMA_SALIDAS + ESQUEMA_HILOS + ESQUEMA_BORRADORES)
    for columna, defecto in (("estado", "'ok'"), ("motivo", f"'{AUSENTE}'")):
        try:
            c.execute(f"alter table salidas add column {columna} "
                      f"text not null default {defecto}")
        except sqlite3.OperationalError:
            pass  # La columna ya existe (D12: migracion aditiva)


def registrar_salida(c, canal, texto_redactado, hallazgos, hash_original,
                     estado="ok", motivo=AUSENTE):
    """Registra una salida que cruzo la frontera. Append-only, nunca se borra.

    Simetrico a la doctrina de memoria: lo que salio, salio, y queda constancia.
    Falla cerrado si la insercion falla: sin registro, no hay salida valida.

    Esto NO es la puerta: es el cuaderno de la puerta. Llamarlo a mano levanta
    SalidaSinPuerta, porque una segunda ruta al registro es una segunda puerta,
    y una frontera con dos puertas no es una frontera.
    """
    import json
    if not getattr(_paso, "abierto", False):
        raise SalidaSinPuerta(
            "registrar_salida no se llama a mano: toda salida cruza por "
            "cruzar_frontera(). Una segunda ruta al registro es una segunda "
            "puerta.")
    asegurar_tablas(c)
    hallazgos_json = json.dumps(hallazgos, ensure_ascii=False)
    cur = c.execute(
        "insert into salidas "
        "(canal, texto, hallazgos, hash_original, estado, motivo) "
        "values (?, ?, ?, ?, ?, ?)",
        (canal, texto_redactado, hallazgos_json, hash_original, estado, motivo)
    )
    c.commit()  # durabilidad ANTES de devolver
    return cur.lastrowid



def cruzar_frontera(c, canal, texto_original, preparar_fn, confirmar=None):
    """Puerta única de salida. Falla cerrado si cualquier paso falla.

    Orquesta el flujo entero: preparar -> (confirmar) -> registrar. Las tres
    preparaciones del árbol -- preparar_envio (guardrails), preparar_respuesta
    (fusible) y preparar_salida_andamio -- desembocan aquí. Nadie sale por otro
    sitio: fuera de esta función, `registrar_salida` levanta SalidaSinPuerta.

    QUÉ CUENTA COMO BLOQUEO, Y POR QUÉ
    ----------------------------------
    El registro anota los veredictos del FILTRO -- guardrails, fusible, falta de
    inspección --, no las decisiones de la persona. Un `confirmar` que dice que
    no NO escribe fila: que alguien decida no exportar su propia memoria no es un
    evento de seguridad, es su criterio, y anotarlo sería vigilarla en su propia
    máquina. Se anota lo que la máquina frenó, no lo que la persona eligió.

    Args:
        c: conexión a la base de datos
        canal: canal de salida (e.g., "cli_export", "ia_externa", "modelo_local")
        texto_original: el texto a enviar (antes de redactar)
        preparar_fn: función de preparación: texto -> dict con "texto"/"hallazgos",
            o texto plano
        confirmar: opcional, (texto_redactado, hallazgos) -> bool. Corre ENTRE
            preparar y registrar, para que la inspección humana no necesite una
            segunda puerta.

    Returns:
        dict con {"estado": "ok", "texto": redactado, "hallazgos": [...], "id_salida": int}

    Raises:
        SalidaNoAprobada: si `confirmar` dice que no (y no deja fila)
        lo que levante `preparar_fn` (EnvioBloqueado, RespuestaBloqueada,
            SinInspeccion...), después de dejar la fila del bloqueo
    """
    import hashlib

    # La huella se calcula sobre el ORIGINAL, no sobre lo redactado: un registro
    # que hashea su propia redacción no puede probar qué salió de aquí.
    hash_original = hashlib.sha256(texto_original.encode('utf-8')).hexdigest()

    _paso.abierto = True
    try:
        # Paso 1: preparación (valida inspección, redacta, o inspecciona la respuesta)
        try:
            resultado = preparar_fn(texto_original)
        except Exception as e:
            # Constancia ANTES de re-lanzar: un bloqueo del que no queda rastro
            # es indistinguible de un bloqueo que nunca ocurrió.
            registrar_salida(c, canal, AUSENTE, [], hash_original,
                             estado="bloqueado", motivo=_motivo(e))
            raise

        # Paso 2: extraer texto redactado y hallazgos
        if isinstance(resultado, dict):
            # preparar_envio() y preparar_respuesta() devuelven dict
            texto_redactado = resultado["texto"]
            hallazgos = resultado.get("hallazgos", [])
        else:
            # preparar_salida_andamio() devuelve string
            texto_redactado = resultado
            hallazgos = []

        # Paso 3: la inspección humana, si la hay. No deja fila (ver arriba).
        if confirmar is not None and not confirmar(texto_redactado, hallazgos):
            raise SalidaNoAprobada(
                "la salida no fue aprobada: no se registra ni sale nada")

        # Paso 4: registrar la salida
        id_salida = registrar_salida(c, canal, texto_redactado, hallazgos,
                                     hash_original)
    finally:
        _paso.abierto = False

    return {
        "estado": "ok",
        "texto": texto_redactado,
        "hallazgos": hallazgos,
        "id_salida": id_salida
    }


def resumen_salidas(c, limite=50):
    """Qué salió y qué se frenó. Sin el texto, y no por descuido.

    Lo mira la persona y puede mirarlo el modelo conversacional: por eso la
    columna `texto` no aparece aquí. Un registro que hay que redactar para poder
    enseñarlo es un registro que no se enseña.
    """
    asegurar_tablas(c)
    filas = c.execute(
        "select id, cuando, canal, estado, motivo, hallazgos, hash_original "
        "from salidas order by id desc limit ?", (limite,)).fetchall()
    return [dict(f) for f in filas]




# --- componente 4b · D69 · la capa de borradores --------------------------

def proponer_borrador(c, texto, origen="aurelius"):
    """Aurelius propone. No escribe memoria: deja una propuesta esperando.

    Es la mitad de la maquina en IronClaw: el gerente escribe por quien no
    puede, y la persona firma. Esta funcion no toca `engrams` ni de lejos.
    """
    if texto is None or str(texto).strip() == "":
        raise ValueError("un borrador sin texto no es una propuesta")
    asegurar_tablas(c)
    cur = c.execute(
        "insert into borradores (texto, origen) values (?, ?)",
        (texto, origen))
    c.commit()      # durabilidad ANTES de devolver
    return cur.lastrowid


def leer_borradores(c, estado=None):
    """Los borradores, o solo los de un estado. La capa no se vacia nunca."""
    asegurar_tablas(c)
    if estado is None:
        filas = c.execute("select * from borradores order by id")
    else:
        filas = c.execute(
            "select * from borradores where estado = ? order by id", (estado,))
    return [dict(f) for f in filas]


def promover_a_engrama(c, borrador_id, acto_persona=False, why=None,
                       where_ref=None, learned="", origen_dispositivo=AUSENTE):
    """Asciende un borrador a memoria firmada. Solo lo hace la persona.

    `acto_persona` no es una cortesia de la firma: es la firma. Un llamante que
    lo pone en cierto esta declarando que hubo un acto humano, y esa declaracion
    es lo unico que separa esta capa de un bucle autonomo escribiendo memoria
    (IronClaw). Por eso el defecto es falso y no hay atajo.

    Devuelve la fila del engrama nuevo, igual que `escribir_engrama`.

    El engrama nace con `origin='persona'` porque la promocion ES su acto, y
    porque el CHECK de `origin` no se migra (D69). La prueba de que aquello lo
    propuso la maquina no se pierde: la fila del borrador queda en 'promovido'
    apuntando al engrama que llego a ser.
    """
    if not acto_persona:
        raise PromocionSinPersona(
            "un borrador solo asciende por acto de la persona: la maquina "
            "propone, la persona firma")
    asegurar_tablas(c)
    fila = c.execute(
        "select * from borradores where id = ?", (borrador_id,)).fetchone()
    if fila is None:
        raise BorradorNoEncontrado(f"no hay borrador con id {borrador_id}")
    if fila["estado"] != "pendiente":
        raise PromocionSinPersona(
            f"el borrador {borrador_id} ya esta en '{fila['estado']}': "
            "una promocion no se repite")
    # `escribir_engrama` devuelve la FILA, no el id: se sigue su convencion en
    # vez de inventar otra a media casa.
    engrama = escribir_engrama(
        c, what=fila["texto"], why=why, where_ref=where_ref, learned=learned,
        origin="persona", origen_dispositivo=origen_dispositivo)
    c.execute(
        "update borradores set estado = 'promovido', engrama_id = ? where id = ?",
        (engrama["id"], borrador_id))
    c.commit()
    return engrama


def descartar_borrador(c, borrador_id, motivo=AUSENTE):
    """Descarta un borrador. La fila SE QUEDA: descartar no es borrar.

    Cero DELETE, como en el resto de esta memoria. Que la persona dijera que no
    a una propuesta es parte de su historia con la maquina, y borrarlo dejaria
    la capa contando solo los aciertos.
    """
    asegurar_tablas(c)
    fila = c.execute(
        "select * from borradores where id = ?", (borrador_id,)).fetchone()
    if fila is None:
        raise BorradorNoEncontrado(f"no hay borrador con id {borrador_id}")
    c.execute(
        "update borradores set estado = 'descartado', motivo = ? where id = ?",
        (motivo, borrador_id))
    c.commit()
    return borrador_id


# --- componente 5 · la frontera -------------------------------------------

def importar(c, ruta_ext):
    """Importa engramas de una memoria externa (otro dispositivo).

    D11 (Identidad por Origen): no fusiona ni sobreescribe. Inserta los engramas
    externos tal cual, conservando su origen_dispositivo. El ID local autoincremental
    les asignara un nuevo numero, evitando choques. Cero DELETE.
    """
    import sqlite3 as _sqlite3
    if not os.path.isfile(ruta_ext):
        raise FileNotFoundError(f"Memoria externa no encontrada: {ruta_ext}")
    
    con_ext = _sqlite3.connect(f"file:{ruta_ext}?mode=ro", uri=True)
    con_ext.row_factory = _sqlite3.Row
    try:
        # Leer engramas externos. Si la DB externa es vieja y no tiene origen_dispositivo, usamos NO_DATA
        try:
            filas_ext = con_ext.execute(
                "SELECT what, why, where_ref, learned, origin, origen_dispositivo FROM engrams"
            ).fetchall()
        except _sqlite3.OperationalError:
            filas_ext = con_ext.execute(
                "SELECT what, why, where_ref, learned, origin, 'NO_DATA' as origen_dispositivo FROM engrams"
            ).fetchall()
        
        for f in filas_ext:
            c.execute(
                "INSERT INTO engrams (what, why, where_ref, learned, origin, origen_dispositivo) "
                "VALUES (?, ?, ?, ?, ?, ?)",
                (f["what"], f["why"], f["where_ref"], f["learned"], f["origin"], f["origen_dispositivo"])
            )
        c.commit()
        return len(filas_ext)
    finally:
        con_ext.close()


def _exportar_crudo(c, incluir_archivados=False, estado_hilo=None):
    """Compone el markdown SIN redactar. No sale de aqui: se lo come la frontera.

    `estado_hilo` es la funcion de `hilos` -- (c, id) -> {"estado", ...} -- y se
    INYECTA, igual que el redactor. El esquema de los hilos vive en este modulo
    (ESQUEMA_HILOS), pero su conducta no, y `memory` no importa `hilos`.
    """
    asegurar_tablas(c)
    filas = _filas(c, incluir_archivados)
    partes = ["# My memory", "", vista_recuento(c), "", "## Memories", ""]
    for f in filas:
        partes += [f"### {f['what']}",
                   f"- why: {f['why']}",
                   f"- where: {f['where_ref']}",
                   f"- learned: {f['learned'] or AUSENTE}",
                   f"- origin: {f['origin']}", ""]
    enlaces = [dict(r) for r in c.execute("select * from links order by id")]
    if enlaces:
        partes += ["## Links", ""]
        idx = {f["id"]: f["what"] for f in _filas(c, True)}
        for e in enlaces:
            partes.append(f"- {idx.get(e['from_engram'], AUSENTE)} "
                          f"--({e['label']})--> {idx.get(e['to_engram'], AUSENTE)}")
    # Los hilos tambien son memoria de la persona, y su titulo lo escribio ella:
    # si no salieran, el export mentiria por omision. Salen por la MISMA frontera
    # que todo lo demas, asi que el redactor los ve.
    try:
        hilos_filas = [dict(r) for r in c.execute(
            "select id, titulo from hilos order by id")]
    except sqlite3.OperationalError:
        hilos_filas = []  # Memoria anterior a D14: no hay seccion que inventar
    if hilos_filas:
        partes += ["", "## Threads", ""]
        for h in hilos_filas:
            est = AUSENTE
            if estado_hilo is not None:
                est = estado_hilo(c, h["id"]).get("estado", AUSENTE)
            titulo = h["titulo"]
            partes.append(f"- {titulo} [{est}]")
    return "\n".join(partes)


def exportar(c, redactor=None, incluir_archivados=False, estado_hilo=None):
    """Markdown legible para llevarselo. La redaccion ocurre AQUI y solo aqui.

    `redactor` es la funcion del producto (guardrails): texto -> (texto, hallazgos).
    No se importa ni se copia desde otro arbol: se inyecta.
    Sin redactor NO se devuelve texto. Falla cerrado.
    """
    if redactor is None:
        raise FronteraSinFiltro(
            "export blocked: no redaction filter provided. "
            "Nothing leaves this machine unfiltered.")
    crudo = _exportar_crudo(c, incluir_archivados, estado_hilo)
    # Un filtro ausente y un filtro roto son el mismo riesgo: en los dos casos
    # nadie ha redactado el texto. Sin este try la excepcion del redactor se
    # propaga tal cual — el export no devuelve nada, pero el fallo llega como
    # traza de un modulo interno y no como frontera cerrada. Se bloquea con el
    # mismo tipo que la ausencia, conservando la causa con `from e` para que el
    # diagnostico no se pierda.
    try:
        texto, hallazgos = redactor(crudo)
        return texto, hallazgos
    except Exception as e:
        raise FronteraSinFiltro(
            f"export blocked: redaction filter failed ({type(e).__name__}). "
            "Nothing leaves this machine with a broken filter."
        ) from e
