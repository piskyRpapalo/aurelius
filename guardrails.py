"""Redacta claves, tokens, IPs privadas y rutas locales antes de que un texto
salga de la máquina. Un fichero, un interruptor, sin dependencias externas.

Dos familias de políticas:

* Core: siempre activas. La configuración no las puede apagar.
* Custom: se ajustan en policies.json, junto a este módulo.

Contrato de seguridad: si algo falla -- el motor, la configuración o su
lectura -- no hay envío. Un fallo nunca se lee como "no había nada que
redactar". Los hallazgos declaran clase y cantidad; jamás el texto encontrado.
"""

import hashlib
import json
import re
import shutil
from pathlib import Path

import casa as _casa

# El molde viaja con el producto; la configuracion efectiva vive en la casa de
# la persona. Nunca al reves: escribir sus ajustes junto al script publicaria
# sus nombres de maquina el dia que empujase el repositorio.
DEFECTO_PATH = Path(__file__).resolve().parent / "policies.default.json"

# None significa "usa la casa". Se deja como variable, y no como constante
# calculada al importar, por dos motivos: importar un modulo no debe crear
# directorios ni copiar ficheros, y una prueba necesita poder apuntar a otra
# ruta sin tocar el disco de quien la ejecuta.
POLICIES_PATH = None


class PoliticasInvalidas(RuntimeError):
    """La configuración de políticas no se puede leer o no es válida."""


class EnvioBloqueado(RuntimeError):
    """El filtro no pudo completarse: el texto no sale."""


CORE_POLICIES = ("API_KEY", "PRIVATE_KEY", "SSH_PUBLIC_KEY", "ASSIGNED_SECRET")
CUSTOM_POLICIES = ("PRIVATE_IP", "HOME_PATH", "NODE_PATH")

PATRONES_CORE = {
    "PRIVATE_KEY": (
        r"-----BEGIN(?: [A-Z]+)* PRIVATE KEY-----[\s\S]*?"
        r"-----END(?: [A-Z]+)* PRIVATE KEY-----"
        r"|-----BEGIN(?: [A-Z]+)* PRIVATE KEY-----.*"
    ),
    "SSH_PUBLIC_KEY": (
        r"\b(?:ssh-(?:rsa|dss|ed25519)"
        r"|ecdsa-sha2-nistp(?:256|384|521)"
        r"|sk-ssh-ed25519@openssh\.com"
        r"|sk-ecdsa-sha2-nistp256@openssh\.com)"
        r"\s+[A-Za-z0-9+/]{20,}={0,3}(?:[ \t]+\S+)?"
    ),
    "API_KEY": (
        # El nombre de la variable casi nunca es la palabra desnuda: es
        # `OPENAI_API_KEY`. Un \b delante no la ve, porque el guion bajo es
        # carácter de palabra. La condición real es "que no venga pegada a otra
        # letra", y eso lo dice el lookbehind, no \b.
        r"(?i)(?<![A-Za-z])(?:api[_-]?key|access[_-]?token|auth[_-]?token"
        r"|secret[_-]?key|bearer)(?:[_-][A-Za-z0-9]+)*\b"
        r"[\"'\s:=]+[A-Za-z0-9._\-]{16,}"
        r"|\bsk-[A-Za-z0-9_\-]{16,}"
        r"|\bghp_[A-Za-z0-9]{16,}"
        r"|\bgithub_pat_[A-Za-z0-9_]{20,}"
        r"|\bxox[abprs]-[A-Za-z0-9\-]{10,}"
        r"|\bAKIA[0-9A-Z]{12,}"
        r"|\bAIza[A-Za-z0-9_\-]{20,}"
        # Anadidos el 2026-08-22. Van AQUI, dentro de API_KEY, y no como
        # politicas nuevas en CUSTOM: las custom se pueden apagar desde la
        # configuracion, y un token de Stripe no es menos grave que uno de AWS.
        # Los tokens de proveedor viven todos en la misma clase que no se apaga.
        r"|\bsk_(?:live|test)_[A-Za-z0-9]{16,}"      # Stripe
        r"|\brk_(?:live|test)_[A-Za-z0-9]{16,}"      # Stripe · clave restringida
        r"|\bSG\.[A-Za-z0-9_\-]{16,}\.[A-Za-z0-9_\-]{16,}"   # SendGrid
        r"|\bSK[0-9a-f]{32}\b"                      # Twilio
        r"|\bAC[0-9a-f]{32}\b"                      # Twilio · SID de cuenta
        r"|\b(?:MT|NT|OT)[A-Za-z0-9_\-]{22,}\.[A-Za-z0-9_\-]{6,}\.[A-Za-z0-9_\-]{25,}"  # Discord
    ),
    "ASSIGNED_SECRET": (
        # El nombre real casi nunca es la palabra sola: es `aws_secret_access_key`.
        # La continuación con guion admite el sufijo sin abrir la puerta a
        # `secretaria`, que no lleva guion y por tanto no entra.
        r"(?i)(?<![A-Za-z])(?:password|passwd|pwd|passphrase|secret|credential)s?"
        r"(?:[_-][A-Za-z0-9]+)*\b"
        r"(?:"
        # Asignación explícita. Admite hasta tres palabras por medio, para que
        # `passphrase for key: …` no se escape por llevar rótulo humano.
        r"(?:\s+[A-Za-z]{1,12}){0,3}[\s\"']*[:=][\s\"']*\S{6,}"
        # Solo espacio de por medio (formato .netrc y compañía): entonces el
        # valor tiene que parecer un secreto. Si no, `password caducó ayer` se
        # redactaría entera, y un filtro que muerde la prosa se acaba apagando.
        r"|\s+(?:(?=\S{6,})\S*(?:\d|[^\w\s])\S*|[^\W\d_]{12,})"
        r")"
        # Credencial en URL. El usuario puede venir vacío: `redis://:clave@…`.
        r"|\b[a-z][a-z0-9+.\-]*://[^\s/@:]*:[^\s/@]+@"
        r"|\beyJ[A-Za-z0-9_\-]{8,}\.[A-Za-z0-9_\-]{8,}\.[A-Za-z0-9_\-]{6,}"
    ),
}

PATRONES_CUSTOM = {
    # Seis prefijos cubiertos desde el primer test. /tmp queda fuera por
    # decisión firmada: es el sitio donde todo el mundo deja ficheros de paso y
    # su tasa de falso positivo ahogaría el contador. Se revisa con datos.
    # Los dos puntos cortan la ruta: separan pares en un volumen de contenedor
    # (ejemplo: `/ruta/a:/ruta/b`) y la línea en una traza (ejemplo: `archivo.py:14`). Sin ese corte,
    # dos rutas seguidas se cuentan como una y el contador miente por defecto.
    "HOME_PATH": (
        r"(?<![\w.])/(?:home|mnt|srv|opt|var|media)/[^\s\"'<>|;,()\[\]:]+"
    ),
    "PRIVATE_IP": (
        r"\b(?:10(?:\.\d{1,3}){3}"
        r"|172\.(?:1[6-9]|2\d|3[01])(?:\.\d{1,3}){2}"
        r"|192\.168(?:\.\d{1,3}){2}"
        r"|100\.(?:6[4-9]|[7-9]\d|1[01]\d|12[0-7])(?:\.\d{1,3}){2}"
        r"|169\.254(?:\.\d{1,3}){2})\b"
        r"|\bf[cd][0-9a-f]{2}:[0-9a-f:]{4,}"
        r"|\bfe80::[0-9a-f:]{2,}"
    ),
}

# Orden de aplicación. Lo más específico primero, para que una política ancha
# no se coma la mitad de un secreto y deje la otra mitad en el texto.
ORDEN = (
    "PRIVATE_KEY",
    "SSH_PUBLIC_KEY",
    "API_KEY",
    "ASSIGNED_SECRET",
    "PRIVATE_IP",
    "HOME_PATH",
    "NODE_PATH",
)

MASCARAS = {nombre: f"[REDACTED:{nombre}]" for nombre in CORE_POLICIES + CUSTOM_POLICIES}

# Huella del conjunto de PATRONES de las políticas duras, no de sus nombres.
# Solo las duras: si cubriera las blandas cambiaría para todo el que ajuste su
# configuración, y dejaría de servir para comparar dos instalaciones.
POLICY_HASH = hashlib.sha256(
    "\n".join(sorted(PATRONES_CORE.values())).encode("utf-8")
).hexdigest()

_CLAVES_POR_POLITICA = {
    "PRIVATE_IP": {"activa"},
    "HOME_PATH": {"activa"},
    "NODE_PATH": {"activa", "nombres"},
}




def ruta_politicas():
    """Devuelve la configuración efectiva, sembrándola del molde la primera vez.

    Si POLICIES_PATH está fijado, manda: es la puerta de las pruebas.
    Si no, la configuración es policies.json en tu carpeta personal. Tres desenlaces y
    ninguno inventa nada: existe y se lee; no existe y se copia del molde; no
    hay molde y se para. Si la copia no tiene permiso, se para también -- el
    plan B sería escribir junto al script, y eso es cruzar la frontera hacia
    el producto.
    """
    if POLICIES_PATH is not None:
        return Path(POLICIES_PATH)
    try:
        base = _casa.asegurar()
    except _casa.CasaInaccesible as e:
        raise PoliticasInvalidas(str(e)) from None
    destino = base / "policies.json"
    if destino.exists():
        return destino
    if not DEFECTO_PATH.is_file():
        raise PoliticasInvalidas("falta el molde de políticas del producto")
    try:
        shutil.copy2(DEFECTO_PATH, destino)
    except OSError:
        raise PoliticasInvalidas(f"no tengo permiso para escribir en {destino}") from None
    return destino


def _cargar_politicas():
    """Lee y valida la configuración. Cualquier duda es un error, no un default."""
    try:
        crudo = ruta_politicas().read_text(encoding="utf-8")
    except OSError:
        raise PoliticasInvalidas("configuración de políticas ausente o ilegible") from None
    try:
        datos = json.loads(crudo)
    except ValueError:
        raise PoliticasInvalidas("configuración de políticas mal formada") from None
    if not isinstance(datos, dict):
        raise PoliticasInvalidas("la configuración debe ser un objeto de políticas")

    ajustes = {}
    for clave, valor in datos.items():
        if clave in CORE_POLICIES:
            raise PoliticasInvalidas("una política dura no se ajusta desde la configuración")
        if clave not in CUSTOM_POLICIES:
            raise PoliticasInvalidas("la configuración nombra una política que no existe")
        if not isinstance(valor, dict):
            raise PoliticasInvalidas("cada política se declara como un objeto")
        if not set(valor).issubset(_CLAVES_POR_POLITICA[clave]):
            raise PoliticasInvalidas("la configuración lleva un campo que no se reconoce")
        activa = valor.get("activa", True)
        if not isinstance(activa, bool):
            raise PoliticasInvalidas("el interruptor de una política es booleano")
        nombres = valor.get("nombres", [])
        if not isinstance(nombres, list) or any(
            not isinstance(n, str) or not n.strip() for n in nombres
        ):
            raise PoliticasInvalidas("los nombres declarados deben ser cadenas no vacías")
        ajustes[clave] = {"activa": activa, "nombres": nombres}
    return ajustes


def _politicas_efectivas():
    """Devuelve [(nombre, patrón)] en orden de aplicación."""
    ajustes = _cargar_politicas()
    efectivas = []
    for nombre in ORDEN:
        if nombre in PATRONES_CORE:
            efectivas.append((nombre, PATRONES_CORE[nombre]))
            continue
        ajuste = ajustes.get(nombre, {"activa": True, "nombres": []})
        if not ajuste["activa"]:
            continue
        if nombre == "NODE_PATH":
            # Sin nombres declarados no hay nada que buscar. Esta política nace
            # vacía a propósito: los nombres de máquina los pone quien la usa.
            declarados = ajuste["nombres"]
            if not declarados:
                continue
            alternativa = "|".join(re.escape(n.strip()) for n in declarados)
            efectivas.append((nombre, rf"(?i)\b(?:{alternativa})\b"))
            continue
        efectivas.append((nombre, PATRONES_CUSTOM[nombre]))
    return efectivas


def _aplicar(nombre, patron, texto):
    """Aplica una política entera al texto: (texto, veces que se redactó)."""
    return re.subn(patron, MASCARAS[nombre], texto)


def redactar_salida(texto):
    """Redacta el texto y declara qué clases aparecieron y cuántas veces.

    Devuelve (texto_redactado, [{"policy": str, "count": int}]). Los hallazgos
    no llevan nunca el fragmento encontrado: clase y cantidad, nada más.
    """
    if type(texto) is not str:
        raise TypeError("redactar_salida acepta texto y solo texto")

    hallazgos = []
    for nombre, patron in _politicas_efectivas():
        texto, veces = _aplicar(nombre, patron, texto)
        if veces:
            hallazgos.append({"policy": nombre, "count": veces})
    hallazgos.sort(key=lambda h: h["policy"])
    return texto, hallazgos


def preparar_envio(texto):
    """Prepara la respuesta que viaja al modelo. Si algo falla, no hay envío.

    Devuelve {"estado", "texto", "hallazgos", "policy_hash"}. El contador que
    ve la interfaz es este valor de retorno: la interfaz no lo recalcula.
    """
    # Doctrina: si no hay reglas o falla la config, no hay salida. Filtro vacío = bloqueo.
    try:
        politicas = _politicas_efectivas()
    except PoliticasInvalidas:
        raise EnvioBloqueado("configuración de políticas ausente o ilegible: envío bloqueado") from None
    if not politicas:
        raise EnvioBloqueado("sin políticas efectivas: envío bloqueado por seguridad")
    try:
        redactado, hallazgos = redactar_salida(texto)
    except Exception:
        raise EnvioBloqueado("el filtro no pudo completarse: envío bloqueado") from None
    return {
        "estado": "ok",
        "texto": redactado,
        "hallazgos": hallazgos,
        "policy_hash": POLICY_HASH,
    }
