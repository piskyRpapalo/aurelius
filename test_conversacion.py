#!/usr/bin/env python3
"""El bucle de conversación · Batería Roja C-a…C-f.

Rojo C-a: un turno deja EXACTAMENTE una fila en el registro de salidas.
Rojo C-b: el prompt del sistema lleva el glosario y ni un nombre interno.
Rojo C-c: lo que el modelo contesta cruza por la puerta única.
Rojo C-d: sin motor el producto sigue vivo, y no se inventa una respuesta.
Rojo C-e: el game master no propone dominio, ni en la guía ni en el carácter.
Rojo C-f: lo que el turno sugiere va al Cuaderno, nunca a la memoria firmada.

EL GERENTE SINTÉTICO. Estas pruebas no necesitan `llama-cli`: el motor se
inyecta como una función `prompt -> texto`. Era la pieza que faltaba para
mantener rojo-antes-verde con un modelo externo de por medio, y llevaba
declarada como pendiente desde antes de que existiera el motor.

sistema: MVP · solo biblioteca estándar. Sin red, sin dependencias.
"""
from __future__ import annotations

import os
import sys
import tempfile
import unittest

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import cara
import conversacion as C
import memory as M
import narrador as N


def motor_sintetico(respuesta="Lo que has escrito queda como lo escribiste."):
    """Un gerente que cumple el contrato: entra prompt, sale texto.

    Guarda lo que se le pidió, para poder mirar el prompt del sistema sin
    arrancar un modelo de 2,3 GiB.
    """
    visto = {}

    def hablar(prompt):
        visto["prompt"] = prompt
        return respuesta

    hablar.visto = visto
    return hablar


class TestBucle(unittest.TestCase):

    def setUp(self):
        self.tmpdir = tempfile.TemporaryDirectory()
        self.db = os.path.join(self.tmpdir.name, "memory.db")
        M.crear(self.db)

    def tearDown(self):
        self.tmpdir.cleanup()

    def _camino(self, c):
        return cara.progreso_camino(c, self.db)

    def _salidas(self, c):
        return c.execute("select count(*) from salidas").fetchone()[0]

    # ------------------------------------------------------------------
    # Rojo C-a: un turno, una fila
    # ------------------------------------------------------------------
    def test_rojo_ca_un_turno_una_fila(self):
        """Ni cero —hablar sin constancia— ni dos —contar de más—."""
        motor = motor_sintetico()
        with M.abrir(self.db) as c:
            antes = self._salidas(c)
            C.turno(c, "hola", self._camino(c), motor=motor, idioma="es")
            despues = self._salidas(c)
        self.assertEqual(despues - antes, 1, "un turno deja una huella, y una sola")

    # ------------------------------------------------------------------
    # Rojo C-b: el prompt lleva vocabulario, no cocina
    # ------------------------------------------------------------------
    def test_rojo_cb_el_prompt_lleva_glosario_sin_internos(self):
        """El modelo tiene que aprender los nombres del juego, no los del código."""
        sistema = C.prompt_sistema("nucleo", "es")
        self.assertIn(N.narrar("memory.cruzar_frontera", "es"), sistema,
                      "el prompt no enseña el vocabulario firmado")
        for interno in ("cruzar_frontera", "promover_a_engrama", "engrams",
                        "memory.py", "progreso_camino"):
            self.assertNotIn(interno, sistema,
                             f"el prompt del sistema lleva {interno!r}")

    def test_rojo_cb_el_prompt_lleva_el_caracter(self):
        """Carácter entero y al principio, en el idioma de la sesión."""
        self.assertIn("Eres Aurelius", C.prompt_sistema("nucleo", "es"))
        self.assertIn("You are Aurelius", C.prompt_sistema("nucleo", "en"))
        self.assertNotIn("You are Aurelius", C.prompt_sistema("nucleo", "es"),
                         "dos caracteres a la vez producen uno confuso")

    # ------------------------------------------------------------------
    # Rojo C-c: la respuesta cruza la puerta
    # ------------------------------------------------------------------
    def test_rojo_cc_la_respuesta_cruza_la_puerta(self):
        """Queda huella con su canal, y el fusible mira antes de dejar pasar."""
        with M.abrir(self.db) as c:
            resultado = C.turno(c, "hola", self._camino(c),
                                motor=motor_sintetico(), idioma="es")
            fila = c.execute("select * from salidas where id = ?",
                             (resultado["id_salida"],)).fetchone()
        self.assertEqual(fila["canal"], "modelo_local")
        self.assertEqual(fila["estado"], "ok")

    def test_rojo_cc_lo_peligroso_deja_cicatriz_y_no_pasa(self):
        """Si el modelo propone algo destructivo, salta el fusible.

        Y lo que queda es la marca, no el texto: la cicatriz no guarda la herida.
        """
        motor = motor_sintetico("Para limpiarlo: rm -rf /")
        with M.abrir(self.db) as c:
            with self.assertRaises(fusible_bloqueado()):
                C.turno(c, "¿cómo lo borro?", self._camino(c), motor=motor,
                        idioma="es")
            fila = c.execute(
                "select * from salidas order by id desc limit 1").fetchone()
        self.assertEqual(fila["estado"], "bloqueado")
        self.assertEqual(fila["texto"], "NO_DATA",
                         "la cicatriz no guarda lo que paró")
        self.assertNotIn("rm -rf", fila["motivo"])

    # ------------------------------------------------------------------
    # Rojo C-d: sin motor, el producto sigue vivo
    # ------------------------------------------------------------------
    def test_rojo_cd_sin_motor_no_se_inventa_nada(self):
        """Sin cerebro se declara la ausencia y no se escribe una sola fila.

        Una respuesta plausible sin modelo detrás es el fallo que ninguna
        prueba automática detecta y todas las personas notan.
        """
        with M.abrir(self.db) as c:
            antes = self._salidas(c)
            with self.assertRaises(C.SinCerebro):
                C.turno(c, "hola", self._camino(c), motor=None, idioma="es")
            # Y un motor que existe pero no contesta se trata igual.
            with self.assertRaises(C.SinCerebro):
                C.turno(c, "hola", self._camino(c), motor=lambda p: "",
                        idioma="es")
            self.assertEqual(self._salidas(c), antes,
                             "sin respuesta no hay huella que registrar")

    def test_rojo_cd_la_memoria_funciona_entera_sin_motor(self):
        """El camino se mide y la memoria se escribe aunque no haya cerebro."""
        with M.abrir(self.db) as c:
            M.escribir_engrama(c, what="un recuerdo sin cerebro de por medio")
            camino = self._camino(c)
        self.assertEqual(camino["estado"]["M2"], "empezado")
        self.assertEqual(camino["estado"]["M1"], "no_medible",
                         "y el peldaño del cerebro sigue declarándose")

    # ------------------------------------------------------------------
    # Rojo C-e: el game master no elige por la persona
    # ------------------------------------------------------------------
    def test_rojo_ce_el_game_master_no_propone_dominio(self):
        """La orden de no elegir tema tiene que estar en el prompt, literal."""
        for idioma, marca in (("es", "NUNCA propongas"), ("en", "NEVER propose")):
            sistema = C.prompt_sistema("proyecto", idioma)
            self.assertIn(marca, sistema,
                          f"[{idioma}] el prompt del proyecto no prohíbe elegir tema")
        # Y ningún dominio concreto asoma en las guías: ni música, ni código.
        for idioma in ("es", "en"):
            for f in C.FASES:
                sistema = C.prompt_sistema(f, idioma).lower()
                for dominio in ("música", "music", "trading", "javascript"):
                    self.assertNotIn(dominio, sistema,
                                     f"[{idioma}/{f}] el prompt sugiere un dominio")

    def test_rojo_ce_la_fase_sale_de_lo_medido(self):
        """Núcleo, decisión, parada opcional y proyecto, derivados y no supuestos."""
        with M.abrir(self.db) as c:
            self.assertEqual(C.fase(self._camino(c)), "nucleo")

            M.escribir_engrama(c, what="una piedra")
            open(os.path.join(os.path.dirname(self.db),
                              "manifest-latest.txt"), "w").close()
            self.assertEqual(C.fase(self._camino(c)), "decision")

            import hilos as H
            H.abrir(c, "un sendero", origen_dispositivo="pc")
            self.assertEqual(C.fase(self._camino(c)), "side_quest")

            C.elegir_modo(c, "proyecto")
            self.assertEqual(C.fase(self._camino(c), M.leer_perfil(c)),
                             "proyecto")

    # ------------------------------------------------------------------
    # Rojo C-f: lo que sugiere va al Cuaderno
    # ------------------------------------------------------------------
    def test_rojo_cf_lo_sugerido_no_entra_en_la_memoria(self):
        """El game master apunta; firmar es de la persona."""
        with M.abrir(self.db) as c:
            antes = c.execute("select count(*) from engrams").fetchone()[0]
            C.proponer(c, "creo que aprendiste algo del cable")
            despues = c.execute("select count(*) from engrams").fetchone()[0]
            pendientes = M.leer_borradores(c, "pendiente")
        self.assertEqual(despues, antes, "proponer no puede escribir memoria")
        self.assertEqual(len(pendientes), 1)


# --- la sesion enchufada · aurelius.py --charla ---------------------------

class TestSesionCharla(unittest.TestCase):
    """C-g…C-i · el bucle deja de ser una funcion sin llamante."""

    def setUp(self):
        self.tmpdir = tempfile.TemporaryDirectory()
        self.db = os.path.join(self.tmpdir.name, "memory.db")
        M.crear(self.db)
        with M.abrir(self.db) as c:
            M.escribir_perfil(c, "language", "es")

    def tearDown(self):
        self.tmpdir.cleanup()

    def _guion(self, *lineas):
        """Una entrada de teclado escrita de antemano."""
        cola = list(lineas)
        return lambda: cola.pop(0) if cola else ""

    # ------------------------------------------------------------------
    # Rojo C-g: un turno de la SESION deja una fila, con su canal
    # ------------------------------------------------------------------
    def test_rojo_cg_un_turno_de_sesion_una_fila(self):
        """La sesion existe, corre, y su turno queda registrado."""
        import aurelius
        dicho = []
        aurelius.charla(self.db, motor=motor_sintetico("Queda como lo escribiste."),
                        entrada=self._guion("hola"), salida=dicho.append)

        with M.abrir(self.db) as c:
            filas = c.execute("select * from salidas").fetchall()
        self.assertEqual(len(filas), 1, "un turno, una huella")
        self.assertEqual(filas[0]["canal"], "modelo_local")
        self.assertEqual(filas[0]["estado"], "ok")
        self.assertIn("Queda como lo escribiste.", "\n".join(dicho),
                      "lo que contesto el motor tiene que llegar a la persona")

    def test_rojo_cg_dos_turnos_dos_filas(self):
        """Y no cuenta de mas: dos vueltas, dos huellas."""
        import aurelius
        aurelius.charla(self.db, motor=motor_sintetico(),
                        entrada=self._guion("una", "dos"), salida=lambda t: None)
        with M.abrir(self.db) as c:
            self.assertEqual(
                c.execute("select count(*) from salidas").fetchone()[0], 2)

    # ------------------------------------------------------------------
    # Rojo C-h: sin motor, la sesion lo dice y no escribe nada
    # ------------------------------------------------------------------
    def test_rojo_ch_sin_motor_la_sesion_declara(self):
        """Se ofrece lo que hay, no lo que gustaria tener."""
        import aurelius
        dicho = []
        aurelius.charla(self.db, motor=None, entrada=self._guion("hola"),
                        salida=dicho.append)
        texto = "\n".join(dicho)
        self.assertIn("no tiene motor", texto,
                      "la ausencia de cerebro se declara")
        with M.abrir(self.db) as c:
            self.assertEqual(
                c.execute("select count(*) from salidas").fetchone()[0], 0,
                "sin charla no hay huella")

    # ------------------------------------------------------------------
    # Rojo C-i: la sesion habla con el nombre del juego, no con el interno
    # ------------------------------------------------------------------
    def test_rojo_ci_la_sesion_dice_donde_esta_con_su_nombre(self):
        """El peldano se anuncia por su nombre de juego y con lo que lo mide."""
        import aurelius
        import narrador as NN
        dicho = []
        aurelius.charla(self.db, motor=None, entrada=self._guion(),
                        salida=dicho.append)
        texto = "\n".join(dicho)
        self.assertIn(NN.narrar("M0", "es"), texto,
                      "no dice en que peldano esta, o lo dice en jerga")
        # Y NO afirma lo que no esta hecho: en limpio, M0 no esta puesto.
        self.assertNotIn(NN.decir("M0", "es"), texto,
                         "dice que has hecho algo que no has hecho")
        for interno in ("M0", "progreso_camino", "cruzar_frontera"):
            self.assertNotIn(interno, texto,
                             f"la sesion ensena el nombre interno {interno!r}")

    # ------------------------------------------------------------------
    # Rojo C-i (b): un bloqueo se cuenta sin repetir lo bloqueado
    # ------------------------------------------------------------------
    def test_rojo_ci_un_bloqueo_no_repite_la_herida(self):
        """Si el fusible salta, la persona se entera y el texto no se reimprime."""
        import aurelius
        dicho = []
        aurelius.charla(self.db, motor=motor_sintetico("hazlo con rm -rf /"),
                        entrada=self._guion("borra"), salida=dicho.append)
        texto = "\n".join(dicho)
        self.assertIn("parado", texto, "el bloqueo se cuenta")
        self.assertNotIn("rm -rf", texto,
                         "y no se repite lo que se acaba de parar")
        with M.abrir(self.db) as c:
            fila = c.execute("select * from salidas").fetchone()
        self.assertEqual(fila["estado"], "bloqueado")


class TestMotorUnaSolaVerdad(unittest.TestCase):
    """C-j · quien ejecuta el binario es quien dice como se llama."""

    def test_rojo_cj_no_hay_dos_nombres_del_motor(self):
        """aurelius.py no puede tener su propia idea de cual es el motor.

        Ya paso con la voz: el catalogo declaraba una pieza y el modulo cargaba
        otra. Dos verdades sobre la misma pieza no discrepan el dia que se
        escriben, sino seis meses despues.
        """
        import aurelius
        self.assertIs(aurelius.MOTOR, C.MOTOR,
                      "el nombre del motor vive en conversacion.py, y solo ahi")
        self.assertIs(aurelius.motor_conversacion.__wrapped__
                      if hasattr(aurelius.motor_conversacion, "__wrapped__")
                      else True, True)

    def test_rojo_cj_el_readme_nombra_el_motor_de_verdad(self):
        """Un README que promete otro binario manda a la persona a instalar
        lo que no es."""
        ruta = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                            "README.md")
        with open(ruta, encoding="utf-8") as fh:
            readme = fh.read()
        self.assertIn(C.MOTOR, readme,
                      "el README no nombra el motor que el codigo ejecuta")
        self.assertNotIn("llama-cli", readme,
                         "el README sigue nombrando el binario viejo")

class TestLimpieza(unittest.TestCase):
    """C-k · lo que se registra es lo que dijo el modelo, y nada mas.

    Este rojo existe por un fallo que quince pruebas unitarias no vieron: un
    motor sintetico devuelve lo que se le dice que devuelva, asi que el ruido
    del binario solo aparecio en el primer turno REAL. Ahora el recorte tiene
    su propia prueba, y si el binario cambia sus marcadores esto se pone rojo
    aqui en vez de salir como basura en el registro de una persona.
    """

    def test_rojo_ck_se_van_los_marcadores_del_binario(self):
        for crudo, esperado in (
            ("Una piedra es lo que has inscrito. [end of text]",
             "Una piedra es lo que has inscrito."),
            ("Una piedra es lo que has inscrito.\n\n> EOF by user",
             "Una piedra es lo que has inscrito."),
            ("Hola. [end of text]\n> EOF by user", "Hola."),
            ("   Hola.   ", "Hola."),
        ):
            self.assertEqual(C.limpiar(crudo), esperado)

    def test_rojo_ck_se_va_el_eco_del_prompt(self):
        """Si faltara la bandera, el prompt no puede colarse en el registro."""
        prompt = "Eres Aurelius. Se breve."
        self.assertEqual(C.limpiar(prompt + "Una piedra.", prompt), "Una piedra.")

    def test_rojo_ck_no_se_come_el_texto_del_modelo(self):
        """Recortar de mas es tan malo como no recortar."""
        for intacto in ("Una piedra es lo que has inscrito.",
                        "Te propongo esto: > y esto otro",
                        "El texto acaba en corchete [asi]"):
            self.assertEqual(C.limpiar(intacto), intacto)

    def test_rojo_ck_nada_es_cadena_vacia(self):
        self.assertEqual(C.limpiar(None), "")
        self.assertEqual(C.limpiar(""), "")

class TestAusenciasYTeclado(unittest.TestCase):
    """C-l y C-m · por que no hay charla, y una entrada que aguanta un dedo."""

    def setUp(self):
        self.tmpdir = tempfile.TemporaryDirectory()
        self.db = os.path.join(self.tmpdir.name, "memory.db")
        M.crear(self.db)
        with M.abrir(self.db) as c:
            M.escribir_perfil(c, "language", "es")

    def tearDown(self):
        self.tmpdir.cleanup()

    # ------------------------------------------------------------------
    # Rojo C-l: tres ausencias, tres razones
    # ------------------------------------------------------------------
    def test_rojo_cl_el_diagnostico_distingue_que_falta(self):
        """Quien tiene el binario y no el modelo no necesita el mismo consejo
        que quien tiene el modelo y no el binario."""
        falso = os.path.join(self.tmpdir.name, "no-existe.gguf")
        real = os.path.join(self.tmpdir.name, "cerebro.gguf")
        open(real, "w").close()

        anterior = C.motor_disponible
        try:
            C.motor_disponible = lambda: "/usr/bin/algo"
            self.assertEqual(C.diagnostico(falso)[1], C.SIN_MODELO)
            C.motor_disponible = lambda: None
            self.assertEqual(C.diagnostico(real)[1], C.SIN_BINARIO)
            self.assertEqual(C.diagnostico(falso)[1], C.SIN_NADA)
        finally:
            C.motor_disponible = anterior

    def test_rojo_cl_la_sesion_dice_cual_es_la_ausencia(self):
        """Y el mensaje nombra lo que falta: el binario, o la ruta del cerebro."""
        import aurelius
        ruta = "/una/ruta/cerebro.gguf"

        dicho = []
        aurelius.charla(self.db, motor=None, motivo=C.SIN_MODELO, modelo=ruta,
                        entrada=lambda: "", salida=dicho.append)
        self.assertIn(ruta, "\n".join(dicho),
                      "no dice DONDE tendria que estar el cerebro")

        dicho = []
        aurelius.charla(self.db, motor=None, motivo=C.SIN_BINARIO,
                        entrada=lambda: "", salida=dicho.append)
        texto = "\n".join(dicho)
        self.assertIn(C.MOTOR, texto, "no dice QUE hay que instalar")
        self.assertNotIn("/una/ruta", texto,
                         "y no manda a buscar un cerebro que si esta")

    # ------------------------------------------------------------------
    # Rojo C-m: la entrada aguanta un telefono
    # ------------------------------------------------------------------
    def test_rojo_cm_sale_por_palabra_ademas_de_por_vacio(self):
        """En un telefono, confiar solo en un Enter en blanco es confiar en que
        nadie lo pulse sin querer."""
        import aurelius
        for palabra in aurelius.SALIDAS_EXPLICITAS:
            cola = [palabra, "esto no deberia llegar"]
            aurelius.charla(self.db, motor=motor_sintetico(),
                            entrada=lambda: cola.pop(0), salida=lambda t: None)
        with M.abrir(self.db) as c:
            self.assertEqual(
                c.execute("select count(*) from salidas").fetchone()[0], 0,
                "la palabra de salida tiene que cortar antes del turno")

    def test_rojo_cm_cerrar_la_entrada_no_es_un_error(self):
        """EOF y Ctrl-C salen limpios: en un telefono son la tecla comoda.

        Se prueba `_teclado` de verdad, sustituyendo `input`. La primera version
        de este caso rodeaba la funcion y comprobaba su propio andamio, que es
        una forma elegante de no probar nada.
        """
        import builtins
        import aurelius
        original = builtins.input
        try:
            for romper in (EOFError, KeyboardInterrupt):
                def falla():
                    raise romper
                builtins.input = falla
                self.assertEqual(aurelius._teclado(lambda t: None), "",
                                 f"{romper.__name__} tiene que salir limpio")
        finally:
            builtins.input = original

    def test_rojo_cm_el_prompt_se_vacia_antes_de_bloquear(self):
        """Si la salida esta redirigida, un prompt en el buffer es una pantalla
        en blanco esperando a que pregunten algo que ya se pregunto."""
        import builtins
        import aurelius
        visto = []
        original = builtins.input
        try:
            builtins.input = lambda: "hola"
            aurelius._teclado(visto.append)
        finally:
            builtins.input = original
        self.assertEqual(visto, ["> "], "el prompt tiene que salir antes de leer")




def fusible_bloqueado():
    import fusible
    return fusible.RespuestaBloqueada


if __name__ == '__main__':
    unittest.main(verbosity=2)
