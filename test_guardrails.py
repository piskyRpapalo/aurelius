"""TANDA A · Fase 0 del filtro de privacidad · tests primero.

Estos once casos se escriben ANTES de que exista guardrails.py y deben estar
todos en rojo en esa primera ejecución. Un caso que pase sin implementación es
un caso mal escrito: no prueba nada.

Sin dependencias externas: librería estándar. Se ejecuta con
    python3 -m unittest -v test_guardrails
"""

import ast
import hashlib
import inspect
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock

RAIZ = Path(__file__).resolve().parent
FUENTE = RAIZ / "guardrails.py"
NOMBRE_LEXICO = "lexico_prohibido.txt"
LEXICO = Path(os.environ.get("GUARDRAILS_LEXICO") or (RAIZ / NOMBRE_LEXICO))

# Subconjunto sintético declarado: los únicos términos vigilados que este
# fichero puede escribir. Tres nombres inventados que no corresponden a ninguna
# máquina, persona ni servicio. Su trabajo es probar el MECANISMO anti-fuga, no
# su contenido: una suite que probara el mecanismo con los términos reales los
# publicaría con solo escribirlos, que es exactamente la fuga que estos casos
# existen para impedir. El léxico real vive fuera de la historia del repo.
LEXICO_SINTETICO = ("nodo-de-prueba", "maquina-ficticia", "host-inventado")

# Credenciales falsas, inventadas para los tests. No corresponden a nada real.
TOKEN_A = "sk-live-4kQ8ZzR2mN7pXw0aBcDeFgHiJkLmNoPq"
TOKEN_B = "ghp_9Xy2Wv4Ut6Sr8Qp0OnMlKjIhGfEdCbA1zZ23"
TOKEN_I = "sk-proj-Ab12Cd34Ef56Gh78Ij90Kl12Mn34Op56"

# Los seis prefijos que HOME_PATH cubre desde su primer test.
PREFIJOS_CUBIERTOS = [
    "/home/alice/proyecto/notas.txt",
    "/mnt/volumen1/datos.db",
    "/srv/www/app.conf",
    "/opt/herramientas/bin/arranque",
    "/var/log/aplicacion.log",
    "/media/usb0/copia.tar",
]

# Forma de un identificador de regla ajeno (letra + número, p. ej. "D31").
FORMA_ID_REGLA = re.compile(r"\b[A-Z]\d{1,3}\b")

# Rutas absolutas que jamás deben viajar en un mensaje mostrado al usuario.
RUTA_EN_MENSAJE = re.compile(r"/(?:home|mnt|srv|opt|var|media|Users)/")

IMPORTS_PERMITIDOS = {"re", "json", "hashlib", "pathlib", "typing", "dataclasses", "shutil", "casa"}

# Vocabulario de exención. Ni el módulo ni su configuración pueden usarlo.
FORMA_EXENCION = re.compile(
    r"(?i)(exent|exempt|allow_?list|white_?list|lista_blanca|bypass|"
    r"trusted_?dir|safe_?dir|dir_?seguro|omitir|saltar)"
)


def cargar(caso):
    """Importa guardrails o marca el caso en rojo si todavía no existe."""
    if not FUENTE.exists():
        caso.fail("guardrails.py no existe todavía: rojo esperado de la tanda A")
    if str(RAIZ) not in sys.path:
        sys.path.insert(0, str(RAIZ))
    import guardrails  # noqa: PLC0415

    return guardrails


def fuente(caso):
    """Devuelve el código de guardrails.py o marca el caso en rojo."""
    if not FUENTE.exists():
        caso.fail("guardrails.py no existe todavía: rojo esperado de la tanda A")
    return FUENTE.read_text(encoding="utf-8")


def cargar_lexico_para_test():
    """Devuelve (términos, procedencia), procedencia ∈ {"real", "sintetico"}.

    Con el fichero de léxico vigilado delante se usa ése: el árbol privado
    comprueba lo que de verdad le importa. Sin él —clon limpio, cualquiera que
    pase por aquí— se usa el subconjunto sintético declarado, y la suite sigue
    probando el mecanismo en vez de quedarse sin probar nada.

    Esta caída a lo sintético es de la SUITE y solo de la suite. En producción
    la falta de una lista es frontera cerrada, jamás una lista de repuesto: lo
    afirma el primer caso L, y es ese caso el que hace legítima la asimetría.
    """
    if LEXICO.exists():
        terminos = []
        for linea in LEXICO.read_text(encoding="utf-8").splitlines():
            linea = linea.strip()
            if linea and not linea.startswith("#"):
                terminos.append(linea.lower())
        if terminos:
            return terminos, "real"
    return [t.lower() for t in LEXICO_SINTETICO], "sintetico"


def lexico(caso):
    """Términos vigilados para los casos anti-fuga. Nunca una lista vacía."""
    terminos, _ = cargar_lexico_para_test()
    if not terminos:
        caso.fail(
            "no hay ni un término que comprobar: sin lista no se puede afirmar "
            "que no hay fugas (fail-closed)"
        )
    return terminos


def cuenta(hallazgos):
    """[{policy, count}] -> {policy: count}."""
    return {h["policy"]: h["count"] for h in hallazgos}


class A_RutaYTokenEnLaMismaLinea(unittest.TestCase):
    """A · una ruta local en la línea no puede eclipsar al token."""

    def test_ruta_local_y_token_en_la_misma_linea(self):
        g = cargar(self)
        linea = f'curl -H "Authorization: Bearer {TOKEN_A}" --netrc-file /home/alice/proyecto/.netrc'
        redactado, hallazgos = g.redactar_salida(linea)
        c = cuenta(hallazgos)

        self.assertGreaterEqual(c.get("API_KEY", 0), 1, "el token debía bloquear por API_KEY")
        self.assertNotIn(TOKEN_A, redactado, "el token sobrevivió a la redacción")
        self.assertGreaterEqual(
            c.get("HOME_PATH", 0), 1, "la ruta debía detectarse además del token"
        )
        self.assertNotIn("/home/alice", redactado)


class B_FirmaSinParametroDeRuta(unittest.TestCase):
    """B · redactar_salida(texto) y nada más."""

    def test_la_firma_es_exactamente_texto(self):
        g = cargar(self)
        parametros = list(inspect.signature(g.redactar_salida).parameters.values())

        self.assertEqual([p.name for p in parametros], ["texto"])
        p = parametros[0]
        self.assertIn(
            p.kind,
            (inspect.Parameter.POSITIONAL_ONLY, inspect.Parameter.POSITIONAL_OR_KEYWORD),
        )
        self.assertIs(p.default, inspect.Parameter.empty, "el único parámetro no lleva default")
        self.assertNotIn(
            inspect.Parameter.VAR_KEYWORD,
            [q.kind for q in parametros],
            "**kwargs abriría la puerta a un parámetro de ruta",
        )
        self.assertNotIn(inspect.Parameter.VAR_POSITIONAL, [q.kind for q in parametros])
        self.assertFalse(
            re.search(r"(?i)(ruta|path|dir|fich|file|base)", p.name),
            "el parámetro no puede nombrar una ruta",
        )


class C_SinExencionPorDirectorio(unittest.TestCase):
    """C · ningún directorio compra una excepción."""

    def test_el_modulo_no_expone_vocabulario_de_exencion(self):
        g = cargar(self)
        publicos = [n for n in dir(g) if not n.startswith("__")]
        for nombre in publicos:
            self.assertFalse(
                FORMA_EXENCION.search(nombre), f"el módulo expone una exención: {nombre}"
            )

    def test_la_configuracion_no_admite_exenciones(self):
        g = cargar(self)
        datos = json.loads(g.ruta_politicas().read_text(encoding="utf-8"))
        pendientes = [("", datos)]
        while pendientes:
            _, nodo = pendientes.pop()
            if isinstance(nodo, dict):
                for clave, valor in nodo.items():
                    self.assertFalse(
                        FORMA_EXENCION.search(str(clave)),
                        f"policies.json admite una exención: {clave}",
                    )
                    pendientes.append((clave, valor))

    def test_el_mismo_secreto_se_redacta_viva_donde_viva(self):
        g = cargar(self)
        resultados = []
        for directorio in ("/home/alice/publico", "/opt/compartido", "/srv/interno"):
            redactado, hallazgos = g.redactar_salida(f"{directorio}/x.env: {TOKEN_A}")
            self.assertNotIn(TOKEN_A, redactado)
            resultados.append(cuenta(hallazgos).get("API_KEY", 0))
        self.assertEqual(resultados, [1, 1, 1], "la cuenta cambió según el directorio")


class D_TodosLosHallazgosDeUnaLinea(unittest.TestCase):
    """D · sin break: una línea puede contener varios y se cuentan todos."""

    def test_multiples_hallazgos_en_una_sola_linea(self):
        g = cargar(self)
        linea = f"{TOKEN_A} y {TOKEN_B} contra 10.0.0.5 desde /srv/datos/entrada"
        redactado, hallazgos = g.redactar_salida(linea)
        c = cuenta(hallazgos)

        self.assertEqual(c.get("API_KEY", 0), 2, "el segundo token se perdió")
        self.assertEqual(c.get("PRIVATE_IP", 0), 1)
        self.assertEqual(c.get("HOME_PATH", 0), 1)
        for secreto in (TOKEN_A, TOKEN_B, "10.0.0.5", "/srv/datos/entrada"):
            self.assertNotIn(secreto, redactado)

    def test_la_forma_del_hallazgo_es_policy_y_count(self):
        g = cargar(self)
        _, hallazgos = g.redactar_salida(f"{TOKEN_A} {TOKEN_B}")
        self.assertIsInstance(hallazgos, list)
        for h in hallazgos:
            self.assertEqual(set(h.keys()), {"policy", "count"})
            self.assertIsInstance(h["policy"], str)
            self.assertIsInstance(h["count"], int)
            self.assertGreater(h["count"], 0, "un hallazgo con cuenta cero no es un hallazgo")


class E_LaFirmaRechazaLoQueNoEsTexto(unittest.TestCase):
    """E · TypeError ante kwargs inesperados o un objeto con atributo de ruta."""

    def test_kwargs_inesperados(self):
        g = cargar(self)
        for kwargs in ({"ruta": "/home/alice"}, {"path": "/home/alice"}, {"base_dir": "/srv"}):
            with self.subTest(kwargs=kwargs):
                with self.assertRaises(TypeError):
                    g.redactar_salida("texto cualquiera", **kwargs)

    def test_objeto_con_atributo_de_ruta(self):
        g = cargar(self)

        class ConRuta:
            ruta = "/home/alice/proyecto"

            def __str__(self):
                return "texto cualquiera"

        class ConPath:
            path = "/home/alice/proyecto"

            def __str__(self):
                return "texto cualquiera"

        for objeto in (ConRuta(), ConPath(), Path("/home/alice"), b"bytes", 42, None):
            with self.subTest(objeto=type(objeto).__name__):
                with self.assertRaises(TypeError):
                    g.redactar_salida(objeto)


class F_SinDependenciasNiRutasAjenas(unittest.TestCase):
    """F · el módulo no importa ni nombra nada del proyecto que lo vio nacer."""

    def test_solo_importa_libreria_estandar_permitida(self):
        arbol = ast.parse(fuente(self))
        for nodo in ast.walk(arbol):
            if isinstance(nodo, ast.Import):
                for alias in nodo.names:
                    raiz = alias.name.split(".")[0]
                    self.assertIn(raiz, IMPORTS_PERMITIDOS, f"import no permitido: {alias.name}")
            elif isinstance(nodo, ast.ImportFrom):
                self.assertEqual(nodo.level, 0, "sin imports relativos: el módulo es autónomo")
                raiz = (nodo.module or "").split(".")[0]
                self.assertIn(raiz, IMPORTS_PERMITIDOS, f"import no permitido: {nodo.module}")

    def test_el_codigo_no_menciona_el_lexico_vigilado(self):
        codigo = fuente(self).lower()
        for termino in lexico(self):
            self.assertNotIn(termino, codigo, f"el código menciona un término ajeno: {termino}")

    def test_el_codigo_no_lleva_identificadores_de_regla_ajenos(self):
        arbol = ast.parse(fuente(self))
        for nodo in ast.walk(arbol):
            if isinstance(nodo, ast.Constant) and isinstance(nodo.value, str):
                self.assertIsNone(
                    FORMA_ID_REGLA.search(nodo.value),
                    f"cadena con forma de ID de regla ajeno: {nodo.value!r}",
                )


class G_InterfazVisibleLimpia(unittest.TestCase):
    """G · nada de lo que el usuario ve nombra una regla ajena."""

    def cadenas_visibles(self, g):
        visibles = []
        visibles += list(g.CORE_POLICIES) + list(g.CUSTOM_POLICIES)
        visibles += [str(v) for v in g.MASCARAS.values()]
        visibles += list(json.loads(g.ruta_politicas().read_text(encoding="utf-8")).keys())
        visibles.append(g.__doc__ or "")
        visibles.append(g.redactar_salida.__doc__ or "")
        visibles.append(g.preparar_envio.__doc__ or "")

        respuesta = g.preparar_envio(f"{TOKEN_A} en 192.168.1.9 y /var/log/app.log")
        visibles.append(json.dumps(respuesta, ensure_ascii=False, sort_keys=True))

        with mock.patch.object(g, "POLICIES_PATH", RAIZ / "no_existe_policies.json"):
            with self.assertRaises(g.EnvioBloqueado) as capturado:
                g.preparar_envio("hola")
            visibles.append(str(capturado.exception))
        with mock.patch.object(g, "redactar_salida", side_effect=RuntimeError("fallo interno")):
            with self.assertRaises(g.EnvioBloqueado) as capturado:
                g.preparar_envio("hola")
            visibles.append(str(capturado.exception))
        return visibles

    def test_ninguna_cadena_visible_nombra_el_lexico_vigilado(self):
        g = cargar(self)
        terminos = lexico(self)
        for cadena in self.cadenas_visibles(g):
            for termino in terminos:
                self.assertNotIn(termino, cadena.lower(), f"fuga de léxico en: {cadena!r}")

    def test_ninguna_cadena_visible_lleva_id_de_regla_ni_ruta(self):
        g = cargar(self)
        for cadena in self.cadenas_visibles(g):
            self.assertIsNone(FORMA_ID_REGLA.search(cadena), f"ID de regla ajeno en: {cadena!r}")
        for cadena in self.cadenas_visibles(g):
            if cadena.startswith("{") or cadena.startswith("["):
                continue  # la respuesta serializada se examina en el caso I
            self.assertIsNone(
                RUTA_EN_MENSAJE.search(cadena), f"ruta absoluta en un mensaje: {cadena!r}"
            )


class H_HomePathContraLosSeisPrefijos(unittest.TestCase):
    """H · un caso por prefijo, más los controles negativos declarados."""

    def test_un_caso_por_prefijo_cubierto(self):
        g = cargar(self)
        for ruta in PREFIJOS_CUBIERTOS:
            with self.subTest(ruta=ruta):
                redactado, hallazgos = g.redactar_salida(f"se abrió {ruta} sin error")
                self.assertEqual(
                    cuenta(hallazgos).get("HOME_PATH", 0), 1, f"prefijo sin cubrir: {ruta}"
                )
                self.assertNotIn(ruta, redactado)

    def test_tmp_queda_fuera_por_decision_firmada(self):
        g = cargar(self)
        texto = "se abrió /tmp/trabajo/borrador.txt sin error"
        redactado, hallazgos = g.redactar_salida(texto)
        self.assertEqual(cuenta(hallazgos).get("HOME_PATH", 0), 0)
        self.assertEqual(redactado, texto, "/tmp no se redacta: decisión firmada")

    def test_users_y_windows_no_estan_cubiertos_todavia(self):
        # Hueco declarado, no olvidado: entran cuando tengan su test explícito,
        # y C:\ con su propio caso de escapado. Este test cae el día que se cubran.
        g = cargar(self)
        for ruta in ("/Users/alice/proyecto/notas.txt", r"C:\Users\alice\proyecto\notas.txt"):
            with self.subTest(ruta=ruta):
                _, hallazgos = g.redactar_salida(f"se abrió {ruta} sin error")
                self.assertEqual(cuenta(hallazgos).get("HOME_PATH", 0), 0)


class I_ElTokenNoViajaEnLaRespuesta(unittest.TestCase):
    """I · la cadena del token no aparece en ninguna parte de la respuesta."""

    def test_el_token_no_esta_en_la_respuesta_serializada(self):
        g = cargar(self)
        prompt = (
            f"revisa esto por favor: OPENAI_API_KEY={TOKEN_I}\n"
            f"lo lancé desde /home/alice/proyecto contra 10.1.2.3"
        )
        respuesta = g.preparar_envio(prompt)
        serializada = json.dumps(respuesta, ensure_ascii=False, sort_keys=True)

        self.assertNotIn(TOKEN_I, serializada, "el token viaja en la respuesta")
        self.assertNotIn(TOKEN_I[-16:], serializada, "viaja una cola del token")
        self.assertNotIn("/home/alice/proyecto", serializada)
        self.assertNotIn("10.1.2.3", serializada)

        for h in respuesta["hallazgos"]:
            self.assertEqual(set(h.keys()), {"policy", "count"})
        self.assertGreaterEqual(cuenta(respuesta["hallazgos"]).get("API_KEY", 0), 1)


class J_FailClosedDeError(unittest.TestCase):
    """J · si el redactor falla, el envío no sale."""

    def test_fallo_en_la_funcion_publica_bloquea(self):
        g = cargar(self)
        with mock.patch.object(g, "redactar_salida", side_effect=RuntimeError("fallo inyectado")):
            with self.assertRaises(g.EnvioBloqueado):
                g.preparar_envio(f"texto con {TOKEN_A}")

    def test_fallo_en_el_motor_interno_bloquea(self):
        g = cargar(self)
        with mock.patch.object(g, "_aplicar", side_effect=RuntimeError("fallo inyectado")):
            with self.assertRaises(g.EnvioBloqueado):
                g.preparar_envio(f"texto con {TOKEN_A}")

    def test_el_bloqueo_no_filtra_el_texto_original(self):
        g = cargar(self)
        with mock.patch.object(g, "_aplicar", side_effect=RuntimeError(TOKEN_A)):
            with self.assertRaises(g.EnvioBloqueado) as capturado:
                g.preparar_envio(f"texto con {TOKEN_A}")
        self.assertNotIn(TOKEN_A, str(capturado.exception))


class K_FailClosedDeConfiguracion(unittest.TestCase):
    """K · sin configuración válida no hay envío."""

    def test_policies_ausente_bloquea(self):
        g = cargar(self)
        with mock.patch.object(g, "POLICIES_PATH", RAIZ / "no_existe_policies.json"):
            with self.assertRaises(g.EnvioBloqueado):
                g.preparar_envio("hola")
            with self.assertRaises(g.PoliticasInvalidas):
                g.redactar_salida("hola")

    def test_policies_corrupto_bloquea(self):
        g = cargar(self)
        corruptos = [
            "{ esto no es json",
            "[]",
            '{"PRIVATE_IP": "sí"}',
            '{"POLITICA_QUE_NO_EXISTE": {"activa": true}}',
            '{"API_KEY": {"activa": false}}',
        ]
        for i, contenido in enumerate(corruptos):
            with self.subTest(caso=i):
                sucio = RAIZ / f".policies_corrupto_{i}.json"
                sucio.write_text(contenido, encoding="utf-8")
                try:
                    with mock.patch.object(g, "POLICIES_PATH", sucio):
                        with self.assertRaises(g.EnvioBloqueado):
                            g.preparar_envio("hola")
                finally:
                    sucio.unlink()


class G2_FicherosDeInterfazLimpios(unittest.TestCase):
    """G · la interfaz también es superficie visible: se audita como tal."""

    def ficheros(self):
        directorio = RAIZ / "interface"
        if not directorio.is_dir():
            self.fail("no hay interfaz que auditar: rojo esperado antes de escribirla")
        encontrados = sorted(
            p for p in directorio.rglob("*") if p.suffix in {".html", ".css", ".js"}
        )
        if not encontrados:
            self.fail("la interfaz no tiene ningún fichero auditable")
        return encontrados

    def test_la_interfaz_no_menciona_el_lexico_vigilado(self):
        terminos = lexico(self)
        for fichero in self.ficheros():
            contenido = fichero.read_text(encoding="utf-8").lower()
            for termino in terminos:
                self.assertNotIn(
                    termino, contenido, f"fuga de léxico en {fichero.name}: {termino}"
                )

    def test_la_interfaz_no_lleva_ids_de_regla_ni_rutas_locales(self):
        for fichero in self.ficheros():
            contenido = fichero.read_text(encoding="utf-8")
            self.assertIsNone(
                FORMA_ID_REGLA.search(contenido), f"ID de regla ajeno en {fichero.name}"
            )
            self.assertIsNone(
                RUTA_EN_MENSAJE.search(contenido), f"ruta local en {fichero.name}"
            )

    def test_la_interfaz_solo_nombra_politicas_que_existen(self):
        g = cargar(self)
        conocidas = set(g.CORE_POLICIES) | set(g.CUSTOM_POLICIES)
        INTRINSECOS = {"JSON", "DOCTYPE", "UTF", "HTML", "HTTP", "POST"}
        for fichero in self.ficheros():
            contenido = fichero.read_text(encoding="utf-8")
            for nombrada in re.findall(r"\b[A-Z][A-Z_]{3,}\b", contenido):
                if nombrada.startswith("REDACTED") or nombrada in INTRINSECOS:
                    continue
                self.assertIn(
                    nombrada, conocidas, f"la interfaz nombra algo que no es política: {nombrada}"
                )

    def test_la_interfaz_no_recalcula_el_contador(self):
        # El contador es el valor de retorno del endpoint. Si la interfaz
        # cuenta por su cuenta, puede discrepar de lo que de verdad se filtró.
        prohibido = re.compile(
            r"(?i)(\bnew RegExp|\bcount\s*\+\+|\bcount\s*\+=|"
            r"\.filter\([^)]*policy|hallazgos[^)]*\.length)"
        )
        for fichero in self.ficheros():
            if fichero.suffix not in {".js", ".html"}:
                continue
            contenido = fichero.read_text(encoding="utf-8")
            self.assertIsNone(
                prohibido.search(contenido),
                f"{fichero.name} parece recalcular el contador en el cliente",
            )


class BC_TokensDeProveedor(unittest.TestCase):
    """Anadidos el 2026-08-22: Stripe, SendGrid, Twilio, Discord.

    Van dentro de API_KEY, que es CORE, y no como politicas custom: las custom
    se apagan desde la configuracion, y un token de Stripe no es menos grave
    que uno de AWS. Los tokens de proveedor viven todos en la clase que no se
    puede apagar.

    Los fixtures se componen en ejecucion, como en test_frontera.py: la guardia
    de higiene no exime NUNCA la regla TOKEN-PROVEEDOR, y hace bien.
    """

    DEBEN_REDACTARSE = [
        ("Stripe live", "sk_" + "live_" + "aBcDeF1234567890xyz"),
        ("Stripe test", "sk_" + "test_" + "51H8aBcDeF1234567890"),
        ("Stripe restringida", "rk_" + "live_" + "aBcDeF1234567890xyz"),
        ("SendGrid", "SG." + "aBcDeF1234567890abcdef" + "."
                    + "xYz9876543210abcdefghijklmnopqrstuvwxyz1234"),
        ("Twilio SID", "AC" + "0123456789abcdef0123456789abcdef"),
        ("Twilio clave", "SK" + "fedcba9876543210fedcba9876543210"),
        ("Discord", "MT" + "AwNzI0NjQzOTk1NzE2NDU4Ng" + ".Gh3xYz"
                   + ".aBcDeFgHiJkLmNoPqRsTuVwXyZ12"),
    ]

    # Un filtro que marca de mas se apaga, y entonces no filtra nada. Estas
    # importan tanto como las de arriba.
    NO_DEBEN = [
        ("frase con SK y AC sueltos", "el barco SK va al puerto AC de noche"),
        ("iniciales", "SG es una isla y SK una marca de tornillos"),
        ("hex demasiado corto", "AC0123456789abcdef"),
        ("palabra que empieza por sk", "skate, skyline, sketch"),
    ]

    def test_los_tokens_de_proveedor_se_redactan(self):
        g = cargar(self)
        for nombre, token in self.DEBEN_REDACTARSE:
            with self.subTest(proveedor=nombre):
                texto, hallazgos = g.redactar_salida(f"mi clave es {token} y ya")
                self.assertTrue(hallazgos, f"{nombre} paso sin redactar")
                self.assertNotIn(token, texto,
                                 f"{nombre} sigue entero en la salida")

    def test_no_se_marca_texto_inocente(self):
        g = cargar(self)
        for nombre, texto in self.NO_DEBEN:
            with self.subTest(caso=nombre):
                _, hallazgos = g.redactar_salida(texto)
                self.assertEqual(hallazgos, [],
                                 f"falso positivo en {nombre}: {hallazgos}")

    def test_siguen_siendo_core_y_no_se_pueden_apagar(self):
        """Si un dia pasaran a custom, esta prueba lo dice antes que un incidente."""
        g = cargar(self)
        self.assertIn("API_KEY", g.CORE_POLICIES)
        self.assertNotIn("API_KEY", g.CUSTOM_POLICIES)


class BB_NombresDeClaveConPrefijo(unittest.TestCase):
    """TANDA B · hallazgo de la verificación manual, no de la tanda A.

    El nombre de una variable casi nunca es la palabra desnuda: es `db_password`
    o `OPENAI_API_KEY`. Un `\\b` delante de la palabra clave no ve ninguno de los
    dos, porque el guion bajo es carácter de palabra.
    """

    CON_PREFIJO = [
        ('db_password: "correcto-caballo-bateria"', "ASSIGNED_SECRET"),
        ("USER_PASSWORD=tapon-de-corcho-2024", "ASSIGNED_SECRET"),
        ("mi_client_secret = 7f3a9b2c4d6e8f0a", "ASSIGNED_SECRET"),
        ("OPENAI_API_KEY=Ab12Cd34Ef56Gh78Ij90", "API_KEY"),
        ("MY_AUTH_TOKEN=Zz9Yy8Xx7Ww6Vv5Uu4Tt3", "API_KEY"),
    ]

    SIN_SECRETO = [
        "notpassword: abcdefghij",
        "passwordless login habilitado en el equipo",
    ]

    def test_el_prefijo_no_esconde_el_secreto(self):
        g = cargar(self)
        for texto, politica in self.CON_PREFIJO:
            with self.subTest(texto=texto):
                redactado, hallazgos = g.redactar_salida(texto)
                self.assertGreaterEqual(
                    cuenta(hallazgos).get(politica, 0), 1, f"secreto no visto: {texto}"
                )
                valor = texto.split("=")[-1].split(":")[-1].strip().strip('"')
                self.assertNotIn(valor, redactado)

    def test_una_palabra_pegada_no_dispara(self):
        g = cargar(self)
        for texto in self.SIN_SECRETO:
            with self.subTest(texto=texto):
                redactado, hallazgos = g.redactar_salida(texto)
                self.assertEqual(hallazgos, [], f"falso positivo en: {texto}")
                self.assertEqual(redactado, texto)


class CC_CorpusDeFalsosNegativos(unittest.TestCase):
    """TANDA C · el corpus.

    El agujero del prefijo lo encontró una mirada humana, no la suite. Esto
    convierte esa mirada en algo que no depende de que alguien mire: muestras
    con la forma que tienen de verdad los ficheros de configuración, los logs y
    las trazas. Todo el contenido es inventado.
    """

    CORPUS = RAIZ / "corpus" / "muestras.json"

    def corpus(self):
        if not self.CORPUS.exists():
            self.fail("no hay corpus que ejecutar: rojo esperado antes de escribirlo")
        datos = json.loads(self.CORPUS.read_text(encoding="utf-8"))
        if not datos.get("casos"):
            self.fail("el corpus no tiene casos")
        return datos

    def test_cada_caso_detecta_lo_que_declara(self):
        g = cargar(self)
        for caso in self.corpus()["casos"]:
            with self.subTest(caso=caso["id"]):
                redactado, hallazgos = g.redactar_salida(caso["texto"])
                c = cuenta(hallazgos)
                for politica, minimo in caso["espera"].items():
                    self.assertGreaterEqual(
                        c.get(politica, 0),
                        minimo,
                        f"{caso['id']}: {politica} esperaba >={minimo}, salió {c.get(politica, 0)}",
                    )
                for fragmento in caso.get("no_sobrevive", []):
                    self.assertNotIn(
                        fragmento, redactado, f"{caso['id']}: sobrevivió un fragmento"
                    )
                for politica in caso.get("no_dispara", []):
                    self.assertEqual(
                        c.get(politica, 0), 0, f"{caso['id']}: {politica} no debía disparar"
                    )

    def test_los_limites_declarados_siguen_siendo_limites(self):
        # Estos casos deben salir intactos. El día que uno se cubra, este test
        # cae y obliga a mover la línea a mano, que es lo que se quiere: una
        # cobertura que crece sin que nadie se entere no es cobertura, es azar.
        g = cargar(self)
        for caso in self.corpus()["limites_declarados"]:
            with self.subTest(caso=caso["id"]):
                redactado, hallazgos = g.redactar_salida(caso["texto"])
                self.assertEqual(
                    hallazgos, [], f"{caso['id']}: disparó, y estaba declarado como límite"
                )
                self.assertEqual(redactado, caso["texto"])

    def test_el_corpus_no_lleva_lexico_vigilado(self):
        terminos = lexico(self)
        contenido = self.CORPUS.read_text(encoding="utf-8").lower()
        for termino in terminos:
            self.assertNotIn(termino, contenido, f"fuga de léxico en el corpus: {termino}")

    def test_el_corpus_no_lleva_credenciales_de_esta_maquina(self):
        # Un corpus de muestras es el sitio más fácil del mundo para pegar sin
        # querer algo real. Se comprueba que no coincida con lo que hay en disco.
        contenido = self.CORPUS.read_text(encoding="utf-8")
        for sospechoso in (str(Path.home()), Path.home().name):
            if len(sospechoso) > 3:
                self.assertNotIn(sospechoso, contenido, "el corpus nombra esta máquina")


class L_BlindajeDelLexicoDePrueba(unittest.TestCase):
    """L · la suite puede caer a lo sintético; el producto no puede.

    Los cuatro casos anti-fuga (F, G, G2, CC) ya no se ponen rojos por la
    ausencia del léxico real, y esa comodidad hay que pagarla. Estos tres casos
    son el precio: uno sostiene la asimetría producción/test, otro impide que
    la lista publicable se contamine con la vigilada, y el tercero comprueba
    que la vigilada nunca entró en la historia del repo.
    """

    def test_produccion_sin_lexico_cierra_la_frontera_y_nunca_usa_la_sintetica(self):
        # La asimetría firmada, en tres afirmaciones sobre el módulo real.
        g = cargar(self)
        codigo = fuente(self).lower()

        # 1 · el producto no lleva escrita la lista de la suite.
        for termino in LEXICO_SINTETICO:
            self.assertNotIn(
                termino.lower(), codigo,
                f"el módulo lleva un término de la lista de pruebas: {termino}",
            )

        # 2 · ni la lleva de repuesto por dentro. Con la configuración tal cual
        # se publica, un nombre de máquina no dispara nada: los nombres los pone
        # quien usa el filtro, no el filtro. Si esto redactara, existiría una
        # lista oculta — y una lista oculta es la fuga que se quiere impedir.
        muestra = " y ".join(LEXICO_SINTETICO)
        redactado, hallazgos = g.redactar_salida(muestra)
        self.assertEqual(redactado, muestra, "el módulo redactó por una lista propia")
        self.assertEqual(hallazgos, [], f"hallazgos de una lista que no se declaró: {hallazgos}")

        # 3 · y sin configuración legible no hay salida. La suite, sin léxico,
        # sigue probando; el producto, sin políticas, se cierra. Ahí está la
        # diferencia entre un subconjunto declarado y un default silencioso.
        with mock.patch.object(g, "POLICIES_PATH", RAIZ / "no_existe_policies.json"):
            with self.assertRaises(g.EnvioBloqueado):
                g.preparar_envio(muestra)

    def test_la_lista_sintetica_no_lleva_ni_un_termino_del_lexico_real(self):
        # Se afirma primero lo que se puede afirmar SIEMPRE: la lista publicada
        # es exactamente la declarada. Sin esto, en un clon limpio este caso se
        # quedaría sin comparar nada y pasaría por vacío, que es peor que rojo.
        self.assertEqual(
            LEXICO_SINTETICO, ("nodo-de-prueba", "maquina-ficticia", "host-inventado"),
            "la lista publicable cambió: cualquier término nuevo hay que declararlo",
        )
        sinteticos = [t.lower() for t in LEXICO_SINTETICO]
        self.assertEqual(len(set(sinteticos)), len(sinteticos), "la lista repite términos")

        terminos, procedencia = cargar_lexico_para_test()
        if procedencia != "real":
            self.skipTest("sin léxico vigilado en el árbol: no hay contra qué comparar")

        # Ni iguales ni contenidos: `nodo-de-prueba` no puede llevar dentro un
        # nombre vigilado, ni al revés. La igualdad sola dejaría pasar la fuga
        # por trozos, que es la forma en que de verdad se escapan estas cosas.
        for s in sinteticos:
            for real in terminos:
                self.assertNotEqual(s, real, "un término vigilado está publicado en la suite")
                self.assertNotIn(real, s, "un término vigilado está dentro de uno publicado")
                self.assertNotIn(s, real, "un término publicado está dentro de uno vigilado")

    def test_el_lexico_vigilado_no_esta_en_la_historia_del_repo(self):
        # Se pregunta a git, no a .gitignore. El fichero de exclusiones dice lo
        # que NO se añadirá a partir de ahora; no dice nada de lo que ya está
        # dentro. Un fichero seguido sigue seguido aunque se le añada la línea,
        # y esa confusión es justo la que deja un léxico publicado.
        def correr(*args):
            try:
                return subprocess.run(
                    ["git", *args], cwd=RAIZ, capture_output=True, text=True, timeout=30
                )
            except (OSError, subprocess.SubprocessError) as e:
                self.fail(f"no se pudo preguntar a git ({type(e).__name__}): sin respuesta "
                          "no se puede afirmar que el léxico está fuera (fail-closed)")

        def git(*args):
            r = correr(*args)
            if r.returncode != 0:
                self.fail(f"git {' '.join(args)} falló: {r.stderr.strip() or r.returncode}")
            return r.stdout

        # Un árbol que no es un repositorio no tiene historia en la que colarse:
        # aquí no hay nada que auditar, y se dice. Se separa a propósito del caso
        # anterior — git ausente es «no he podido mirar» y eso es rojo; un árbol
        # sin repositorio es «no hay dónde mirar», que es otra cosa. El modo
        # sabotaje corre sobre copias sin .git: sin esta distinción, este caso se
        # pondría rojo en TODAS las roturas y firmaría detecciones que no son suyas.
        if correr("rev-parse", "--is-inside-work-tree").returncode != 0:
            self.skipTest("el árbol no es un repositorio git: no hay historia que auditar")

        seguidos = [l for l in git("ls-files").splitlines() if NOMBRE_LEXICO in l]
        self.assertEqual(seguidos, [], f"el léxico vigilado está seguido por git: {seguidos}")

        # Ni ahora ni antes: un fichero que entró y se sacó sigue en la historia,
        # y de ahí no se saca sin reescribirla.
        historia = git("log", "--all", "--format=%H", "--", NOMBRE_LEXICO).split()
        self.assertEqual(
            historia, [], f"el léxico vigilado aparece en {len(historia)} commit(s)"
        )


# --- modo sabotaje · el rojo también se prueba ----------------------------
# Una suite verde solo demuestra que el código pasa la suite. Que la suite
# DETECTE la rotura es otra afirmación distinta. Comprobarla a mano una vez no
# deja registro y nadie la repite; este modo la vuelve mecánica.
#
# Por cada invariante: se copia el árbol a un temporal, se rompe la invariante
# EN LA COPIA, se corre la suite contra esa copia y se exige que falle. El
# módulo original no se toca nunca, y su sha256 se compara al cerrar.
#
# Si la suite pasa con una invariante rota, ESE es el fallo: ese test no vale.

# (nombre, fichero, ancla exacta, sustitución). El ancla debe aparecer UNA vez:
# un ancla que ya no aplica dejaría la copia sana, la suite verde y produciría
# la conclusión falsa de "invariante no detectada". Se verifica antes de romper.
SABOTAJES = (
    (
        "política dura desactivada · API_KEY sale del orden de aplicación",
        "guardrails.py",
        '    "API_KEY",\n    "ASSIGNED_SECRET",',
        '    "ASSIGNED_SECRET",',
    ),
    (
        "parámetro de ruta reintroducido en la firma pública",
        "guardrails.py",
        "def redactar_salida(texto):",
        "def redactar_salida(texto, ruta_politicas=None):",
    ),
    (
        "término vigilado escrito en el módulo como ejemplo de uso",
        # La fuga real no llega nunca como un volcado de la lista: llega como un
        # comentario que documenta la función con un nombre de máquina de verdad.
        # En el árbol privado la suite compara contra el léxico REAL, así que un
        # término de la lista sintética no lo ve ninguno de los cuatro casos
        # anti-fuga: lo ve el caso L y solo el caso L. Por eso está aquí.
        "guardrails.py",
        'CUSTOM_POLICIES = ("PRIVATE_IP", "HOME_PATH", "NODE_PATH")',
        'CUSTOM_POLICIES = ("PRIVATE_IP", "HOME_PATH", "NODE_PATH")\n'
        '# ejemplo de uso: NODE_PATH con nombres ["nodo-de-prueba"]',
    ),
    (
        "los hallazgos devuelven el texto coincidente",
        "guardrails.py",
        "        texto, veces = _aplicar(nombre, patron, texto)\n"
        "        if veces:\n"
        '            hallazgos.append({"policy": nombre, "count": veces})',
        "        encontrados = re.findall(patron, texto)\n"
        "        texto, veces = _aplicar(nombre, patron, texto)\n"
        "        if veces:\n"
        '            hallazgos.append({"policy": nombre, "count": veces,\n'
        '                              "match": encontrados})',
    ),
)

VIGILADOS = ("guardrails.py", "policies.json", NOMBRE_LEXICO)


def _sha256(ruta):
    """Huella del fichero, o su ausencia declarada. En un clon limpio el léxico
    vigilado NO está, y eso es lo correcto: se compara ausencia contra ausencia.
    Si el modo sabotaje lo creara o lo borrara, la comparación lo vería igual."""
    ruta = Path(ruta)
    if not ruta.exists():
        return "(ausente)"
    return hashlib.sha256(ruta.read_bytes()).hexdigest()


def _copia_del_arbol():
    """Copia de trabajo, siempre bajo un temporal recién creado."""
    destino = Path(tempfile.mkdtemp(prefix="sabotaje_gr_")) / "arbol"
    shutil.copytree(
        RAIZ, destino, ignore=shutil.ignore_patterns("__pycache__", "*.pyc", ".git")
    )
    return destino


def _romper(destino, fichero, ancla, sustitucion):
    """Aplica la rotura en la copia. Devuelve None, o el motivo del rechazo."""
    ruta = destino / fichero
    fuente = ruta.read_text(encoding="utf-8")
    veces = fuente.count(ancla)
    if veces != 1:
        return (
            f"el ancla aparece {veces} veces en {fichero}; el código cambió y "
            "este sabotaje ya no rompe nada"
        )
    ruta.write_text(fuente.replace(ancla, sustitucion), encoding="utf-8")
    return None


def _lineas_rojas(salida):
    return [l.strip() for l in salida.splitlines() if l.startswith(("FAIL:", "ERROR:"))]


def main_sabotaje():
    print("── FASE 0 · MODO SABOTAJE · se EXIGE que la suite se ponga roja ───────")
    print(f"   original: {RAIZ}")
    print("   se rompe una copia temporal; el original no se toca\n")
    huella_antes = {f: _sha256(RAIZ / f) for f in VIGILADOS}
    no_detectados = []

    for nombre, fichero, ancla, sustitucion in SABOTAJES:
        destino = _copia_del_arbol()
        try:
            motivo = _romper(destino, fichero, ancla, sustitucion)
            if motivo is not None:
                no_detectados.append((nombre, motivo))
                print(f"  SIN ROMPER · {nombre}\n               -> {motivo}")
                continue
            r = subprocess.run(
                [sys.executable, str(destino / Path(__file__).name)],
                cwd=destino,
                capture_output=True,
                text=True,
            )
            salida = r.stderr + r.stdout
            if r.returncode == 0:
                no_detectados.append((nombre, "la suite quedó VERDE con la invariante rota"))
                print(f"  NO DETECTADO · {nombre}")
                print("                 -> la suite quedó VERDE con la invariante rota")
                continue
            rojas = _lineas_rojas(salida)
            print(f"  roja  · {nombre}")
            for l in rojas:
                print(f"          detectado por: {l}")
            resumen = [l for l in salida.splitlines() if l.startswith(("Ran ", "FAILED"))]
            print(f"          {' · '.join(resumen)} (exit {r.returncode})")
        finally:
            shutil.rmtree(destino.parent, ignore_errors=True)

    huella_despues = {f: _sha256(RAIZ / f) for f in VIGILADOS}
    intacto = huella_antes == huella_despues
    print(
        f"\nMODULO ORIGINAL {'INTACTO' if intacto else 'ALTERADO'} "
        f"(sha256 guardrails.py {huella_despues['guardrails.py'][:16]}…)"
    )
    if not intacto:
        print("  CRÍTICO: el modo sabotaje escribió en el árbol original")

    total = len(SABOTAJES)
    print(f"\nRESULTADO SABOTAJE: {total - len(no_detectados)}/{total} roturas detectadas")
    for nombre, motivo in no_detectados:
        print(f"  NO DETECTADA · {nombre}\n                 -> {motivo}")
    if no_detectados:
        print("\n  PARADA: una invariante rota que la suite no ve significa que ese")
        print("  test no vale. Hay que reescribirlo antes de seguir.")
    return 1 if (no_detectados or not intacto) else 0


if __name__ == "__main__":
    if "--sabotaje" in sys.argv[1:]:
        sys.exit(main_sabotaje())
    unittest.main(verbosity=2)
