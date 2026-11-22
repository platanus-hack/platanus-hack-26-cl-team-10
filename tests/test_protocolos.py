"""Protocolos, sus pautas y las OT que pide un cliente. Casos de uso.

Correr:  uv run --with httpx python -m unittest tests.test_protocolos
Un protocolo es el documento del cliente. De él salen una o más pautas, y una pauta puede
salir de más de un protocolo. El equipo los carga por el servicio interno; el cliente solo
pide OT de las pautas que quedaron listas (ADR-0011).
"""

import importlib.util
import json
import os
import tempfile
import unittest
from pathlib import Path
from unittest import mock

from app import catalogo, db, protocolos
from app.bus import Bus
from app.catalogo import ReglaDeNegocio
from app.protocolos import DATOS, PAUTA_DEMO, SEMILLA
from app.servicios import Servicios
from app.video import Video

TIENE_HTTPX = importlib.util.find_spec("httpx") is not None and importlib.util.find_spec("fastapi") is not None
EQUIPO = "equipo:factum"
CORREA = "pauta-correa-ct-01"


def pauta_demo(version=1, **cambios):
    d = json.loads(PAUTA_DEMO.read_text(encoding="utf-8"))
    d["version"] = version
    d.update(cambios)
    return d


def protocolo(protocolo_id="prot-a", **cambios):
    return {"id": protocolo_id, "nombre": "Cambio de rodillo", "industria": "minería", "origen": "PDF del cliente",
            "texto": "1. Cortar la energía...", **cambios}


class Base(unittest.TestCase):
    def setUp(self):
        self.cx = db.conectar(":memory:")
        catalogo.preparar(self.cx)

    def tearDown(self):
        self.cx.close()


class ElProtocoloEsUnRecurso(Base):
    def test_se_carga_y_se_lee_con_su_texto(self):
        catalogo.crear_protocolo(self.cx, protocolo(), EQUIPO)
        p = catalogo.leer_protocolo(self.cx, "prot-a")
        self.assertEqual((p["nombre"], p["industria"], p["creado_por"]), ("Cambio de rodillo", "minería", EQUIPO))
        self.assertEqual(p["texto"], "1. Cortar la energía...")
        self.assertEqual(p["pautas"], [])

    def test_la_lista_no_trae_el_texto(self):
        catalogo.crear_protocolo(self.cx, protocolo(), EQUIPO)
        self.assertNotIn("texto", catalogo.listar_protocolos(self.cx)[0])

    def test_necesita_id_y_nombre_y_lo_carga_una_persona(self):
        for malo, actor in [(protocolo(id=" "), EQUIPO), (protocolo(nombre=""), EQUIPO), (protocolo(), "sistema"), (protocolo(), "")]:
            with self.assertRaises(ReglaDeNegocio):
                catalogo.crear_protocolo(self.cx, malo, actor)

    def test_no_se_carga_dos_veces_el_mismo_id(self):
        catalogo.crear_protocolo(self.cx, protocolo(), EQUIPO)
        with self.assertRaises(ReglaDeNegocio):
            catalogo.crear_protocolo(self.cx, protocolo(), EQUIPO)

    def test_se_corrigen_sus_datos_pero_no_su_id(self):
        catalogo.crear_protocolo(self.cx, protocolo(), EQUIPO)
        p = catalogo.cambiar_protocolo(self.cx, "prot-a", {"nombre": "Cambio de rodillo CT-01", "texto": "v2"})
        self.assertEqual((p["nombre"], p["texto"], p["industria"]), ("Cambio de rodillo CT-01", "v2", "minería"))
        for malo in ({"id": "otro"}, {"nombre": " "}):
            with self.assertRaises(ReglaDeNegocio):
                catalogo.cambiar_protocolo(self.cx, "prot-a", malo)

    def test_uno_que_no_existe_es_404(self):
        for accion in (lambda: catalogo.leer_protocolo(self.cx, "nada"), lambda: catalogo.borrar_protocolo(self.cx, "nada"),
                       lambda: catalogo.cambiar_protocolo(self.cx, "nada", {"nombre": "x"})):
            with self.assertRaises(db.NoExiste):
                accion()

    def test_se_borra_solo_si_ninguna_pauta_sale_de_el(self):
        catalogo.crear_protocolo(self.cx, protocolo(), EQUIPO)
        catalogo.crear_pauta_de(self.cx, ["prot-a"], pauta_demo(), EQUIPO)
        with self.assertRaises(ReglaDeNegocio):
            catalogo.borrar_protocolo(self.cx, "prot-a")
        catalogo.quitar_atribucion(self.cx, CORREA, "prot-a")
        catalogo.borrar_protocolo(self.cx, "prot-a")
        self.assertEqual(catalogo.listar_protocolos(self.cx), [])


class LasPautasSalenDeProtocolos(Base):
    def setUp(self):
        super().setUp()
        catalogo.crear_protocolo(self.cx, protocolo("prot-a"), EQUIPO)
        catalogo.crear_protocolo(self.cx, protocolo("prot-b", nombre="Aislamiento de energías"), EQUIPO)

    def test_una_pauta_creada_desde_un_protocolo_nace_atribuida_y_sin_aprobar(self):
        r = catalogo.crear_pauta_de(self.cx, ["prot-a"], pauta_demo(), EQUIPO)
        self.assertFalse(r["aprobada"])
        self.assertEqual([p["id"] for p in r["protocolos"]], ["prot-a"])
        self.assertEqual([p["id"] for p in catalogo.leer_protocolo(self.cx, "prot-a")["pautas"]], [CORREA])

    def test_una_pauta_puede_salir_de_mas_de_un_protocolo(self):
        r = catalogo.crear_pauta_de(self.cx, ["prot-a", "prot-b", "prot-a"], pauta_demo(), EQUIPO)
        self.assertEqual([p["id"] for p in r["protocolos"]], ["prot-a", "prot-b"])

    def test_un_protocolo_da_mas_de_una_pauta(self):
        catalogo.crear_pauta_de(self.cx, ["prot-a"], pauta_demo(), EQUIPO)
        catalogo.crear_pauta_de(self.cx, ["prot-a"], pauta_demo(id="pauta-otra", nombre="Otra tarea"), EQUIPO)
        self.assertEqual([p["id"] for p in catalogo.pautas_de(self.cx, "prot-a")], [CORREA, "pauta-otra"])

    def test_sin_protocolo_o_con_uno_que_no_existe_la_pauta_no_se_crea(self):
        with self.assertRaises(ReglaDeNegocio):
            catalogo.crear_pauta_de(self.cx, [], pauta_demo(), EQUIPO)
        with self.assertRaises(db.NoExiste):
            catalogo.crear_pauta_de(self.cx, ["prot-a", "nada"], pauta_demo(), EQUIPO)
        self.assertEqual(catalogo.listar_pautas(self.cx), [])

    def test_la_version_siguiente_hereda_la_atribucion(self):
        catalogo.crear_pauta_de(self.cx, ["prot-a"], pauta_demo(), EQUIPO)
        catalogo.crear_pauta(self.cx, pauta_demo(version=2))
        self.assertEqual([p["id"] for p in catalogo.protocolos_de(self.cx, CORREA)], ["prot-a"])

    def test_una_pauta_que_ya_existe_se_atribuye_y_repetirlo_no_cambia_nada(self):
        catalogo.crear_pauta(self.cx, pauta_demo())
        catalogo.atribuir(self.cx, CORREA, "prot-b", EQUIPO)
        r = catalogo.atribuir(self.cx, CORREA, "prot-b", EQUIPO)
        self.assertEqual([p["id"] for p in r["protocolos"]], ["prot-b"])

    def test_un_protocolo_se_puede_cargar_ya_atribuido_a_pautas(self):
        catalogo.crear_pauta(self.cx, pauta_demo())
        p = catalogo.crear_protocolo(self.cx, protocolo("prot-c", pautas=[CORREA]), EQUIPO)
        self.assertEqual([x["id"] for x in p["pautas"]], [CORREA])
        with self.assertRaises(db.NoExiste):
            catalogo.crear_protocolo(self.cx, protocolo("prot-d", pautas=["pauta-fantasma"]), EQUIPO)
        with self.assertRaises(db.NoExiste):
            catalogo.leer_protocolo(self.cx, "prot-d")

    def test_una_pauta_con_ot_no_queda_sin_protocolo(self):
        catalogo.crear_pauta_de(self.cx, ["prot-a", "prot-b"], pauta_demo(), EQUIPO)
        catalogo.aprobar_pauta(self.cx, CORREA, 1, "supervisor:X")
        catalogo.generar_ot(self.cx, CORREA, "cliente:planta")
        catalogo.quitar_atribucion(self.cx, CORREA, "prot-b")
        with self.assertRaises(ReglaDeNegocio):
            catalogo.quitar_atribucion(self.cx, CORREA, "prot-a")
        with self.assertRaises(db.NoExiste):
            catalogo.quitar_atribucion(self.cx, CORREA, "prot-b")


class ElClientePideOt(Base):
    def setUp(self):
        super().setUp()
        catalogo.crear_protocolo(self.cx, protocolo(), EQUIPO)

    def test_solo_ve_pautas_aprobadas_y_atribuidas(self):
        catalogo.crear_pauta_de(self.cx, ["prot-a"], pauta_demo(), EQUIPO)
        catalogo.crear_pauta(self.cx, pauta_demo(id="pauta-suelta"))
        catalogo.aprobar_pauta(self.cx, "pauta-suelta", 1, "supervisor:X")
        self.assertEqual(catalogo.pautas_disponibles(self.cx), [])
        catalogo.aprobar_pauta(self.cx, CORREA, 1, "supervisor:X")
        lista = catalogo.pautas_disponibles(self.cx)
        self.assertEqual([(p["id"], p["version"], [x["id"] for x in p["protocolos"]]) for p in lista], [(CORREA, 1, ["prot-a"])])

    def test_la_ot_sale_de_la_ultima_version_aprobada_y_dice_de_que_protocolos(self):
        catalogo.crear_pauta_de(self.cx, ["prot-a"], pauta_demo(), EQUIPO)
        catalogo.aprobar_pauta(self.cx, CORREA, 1, "supervisor:X")
        catalogo.crear_pauta(self.cx, pauta_demo(version=2))  # nadie la aprobó todavía
        r = catalogo.generar_ot(self.cx, CORREA, "cliente:planta")
        self.assertEqual((r["ot"], r["version"], [p["id"] for p in r["protocolos"]]), ("ot-0001", 1, ["prot-a"]))
        self.assertEqual(catalogo.pautas_disponibles(self.cx)[0]["version"], 1)
        self.assertEqual(db.eventos(self.cx, "ot-0001")[0].actor, "cliente:planta")

    def test_el_servicio_le_pone_el_id_y_no_repite(self):
        catalogo.crear_pauta_de(self.cx, ["prot-a"], pauta_demo(), EQUIPO)
        catalogo.aprobar_pauta(self.cx, CORREA, 1, "supervisor:X")
        catalogo.abrir_ot(self.cx, "ot-0002", CORREA, "supervisor:X")
        ids = [catalogo.generar_ot(self.cx, CORREA, "cliente:planta")["ot"] for _ in range(2)]
        self.assertEqual(ids, ["ot-0003", "ot-0004"])
        self.assertEqual(catalogo.generar_ot(self.cx, CORREA, "cliente:planta", "ot-mia")["ot"], "ot-mia")
        with self.assertRaises(ReglaDeNegocio):
            catalogo.generar_ot(self.cx, CORREA, "cliente:planta", "ot-mia")

    def test_lo_que_no_se_puede_pedir(self):
        catalogo.crear_pauta(self.cx, pauta_demo())
        with self.assertRaises(ReglaDeNegocio):  # sin aprobar
            catalogo.generar_ot(self.cx, CORREA, "cliente:planta")
        catalogo.aprobar_pauta(self.cx, CORREA, 1, "supervisor:X")
        with self.assertRaises(ReglaDeNegocio):  # aprobada, pero no sale de ningún protocolo
            catalogo.generar_ot(self.cx, CORREA, "cliente:planta")
        catalogo.atribuir(self.cx, CORREA, "prot-a", EQUIPO)
        with self.assertRaises(ReglaDeNegocio):  # sin solicitante
            catalogo.generar_ot(self.cx, CORREA, " ")
        with self.assertRaises(db.NoExiste):
            catalogo.generar_ot(self.cx, "pauta-fantasma", "cliente:planta")


class AislarBloquearYComprobar(Base):
    """Las pautas del polín y del brazo separan aislar, bloquear y comprobar energía cero
    (REFERENCIAS 56). Se corren contra los servicios, con las reglas de capa 1 que ya hay."""

    def abrir(self, archivo, orden, reposo):
        # en la base de la prueba es la primera versión, vaya en la que vaya el archivo
        pauta = {**json.loads((DATOS / archivo).read_text(encoding="utf-8")), "version": 1}
        catalogo.crear_pauta(self.cx, pauta)
        catalogo.aprobar_pauta(self.cx, pauta["id"], 1, "supervisor:X")
        catalogo.abrir_ot(self.cx, "ot-1", pauta["id"], "supervisor:X")
        self.juez = []  # lo que se le preguntó a la cámara: (pregunta, foto de ahora, foto de antes)
        self.camara = lambda pregunta, antes: True
        self.s = Servicios(self.cx, Bus(), Video(Path(tempfile.mkdtemp())),
                           lambda pregunta, cuadro, antes=None: (self.juez.append((pregunta, cuadro, antes))
                                                                 or self.camara(pregunta, antes), 0.91))
        self.s.iniciar_sesion("ot-1", "edge-1", "operario:1")
        self.orden, self.estado, self.seq = orden, dict(reposo), 0

    def leer(self, **cambios):
        """Una tanda del edge con el estado completo; devuelve las alertas nuevas."""
        antes = len(db.eventos(self.cx, "ot-1"))
        self.estado.update(cambios)
        for sensor in self.orden:
            self.seq += 1
            self.s.recibir_lectura("edge-1", sensor, self.estado[sensor], self.seq)
        return [e.detalle for e in db.eventos(self.cx, "ot-1")[antes:] if e.tipo.value == "alerta"]

    def declarar(self, texto, foto=b"cuadro"):
        self.s.video.recibir("edge-1", b"\xff\xd8" + foto + b"\xff\xd9")
        self.s.declarar("ot-1", "operario:1", texto)

    def cerrados(self):
        return self.s.ots()[0]["cerrados"]

    def polin(self):
        self.abrir("pauta-polin.json", ["correa", "energia", "bloqueo", "guarda"],
                   {"correa": "en_marcha", "energia": "viva", "bloqueo": "retirado", "guarda": "cerrada"})

    def test_abrir_la_guarda_sin_aislar_es_peligro_y_orden_invertido(self):
        self.polin()
        self.leer(correa="detenida")
        alertas = self.leer(guarda="abierta")
        self.assertTrue(any(a.startswith("GUARDA ABIERTA CON ENERGÍA VIVA") for a in alertas), alertas)
        self.assertTrue(any(a.startswith("ORDEN INVERTIDO") for a in alertas), alertas)
        self.assertEqual(self.s.calificacion("ot-1")["nivel"], "error")
        self.leer(guarda="cerrada")
        self.assertEqual(self.s.calificacion("ot-1")["nivel"], "ok")

    def test_bloqueado_pero_sin_comprobar_energia_cero_la_guarda_no_se_abre(self):
        self.polin()
        self.leer(correa="detenida"), self.leer(energia="cortada"), self.leer(bloqueo="puesto")
        self.assertEqual(self.cerrados(), 3)
        alertas = self.leer(guarda="abierta")
        self.assertTrue(any("Sacar la tapa protectora" in a for a in alertas), alertas)
        self.declarar("di partida y la correa no se movió")
        self.assertEqual(self.leer(), [])
        self.assertEqual((self.cerrados(), self.s.calificacion("ot-1")["nivel"]), (5, "ok"))

    def test_sacar_el_candado_antes_de_reponer_la_guarda_es_control_perdido(self):
        self.polin()
        self.leer(correa="detenida"), self.leer(energia="cortada"), self.leer(bloqueo="puesto")
        self.declarar("energía cero comprobada"), self.leer(guarda="abierta"), self.declarar("polín cambiado")
        alertas = self.leer(bloqueo="retirado")
        self.assertTrue(any(a.startswith("CONTROL PERDIDO") for a in alertas), alertas)
        self.leer(bloqueo="puesto")
        self.assertEqual(self.s.calificacion("ot-1")["nivel"], "ok")

    def test_la_pauta_del_polin_se_completa_en_su_orden_sin_avisos(self):
        self.polin()
        alertas = self.leer(correa="detenida") + self.leer(energia="cortada") + self.leer(bloqueo="puesto")
        self.declarar("energía cero comprobada")
        alertas += self.leer(guarda="abierta")
        self.declarar("polín cambiado")
        alertas += self.leer(guarda="cerrada") + self.leer(bloqueo="retirado") + self.leer(energia="viva") + self.leer(correa="en_marcha")
        self.declarar("el polín gira y la correa corre centrada")
        self.assertEqual(alertas, [])
        self.assertEqual((self.s.ots()[0]["estado_general"], self.cerrados()), ("completa", 10))

    def test_en_el_brazo_nadie_entra_sin_comprobar_energia_cero(self):
        self.abrir("pauta-brazo.json", ["energia", "bloqueo", "zona"], {"energia": "viva", "bloqueo": "retirado", "zona": "libre"})
        self.assertTrue(any("Entrar a la celda" in a for a in self.leer(zona="ocupada")))
        self.leer(zona="libre"), self.leer(energia="cortada"), self.leer(bloqueo="puesto")
        self.assertTrue(any("Entrar a la celda" in a for a in self.leer(zona="ocupada")))
        self.leer(zona="libre")
        self.declarar("di la orden de partida y el brazo no se movió")
        alertas = self.leer(zona="ocupada")
        self.declarar("pinza ajustada")
        alertas += self.leer(zona="libre") + self.leer(bloqueo="retirado") + self.leer(energia="viva")
        self.declarar("el brazo completó un ciclo")
        self.assertEqual(alertas, [])
        self.assertEqual((self.s.ots()[0]["estado_general"], self.cerrados()), ("completa", 9))


    def demo(self):
        self.abrir("pauta-polin-demo.json", ["temp_c", "energia", "bloqueo", "operario"],
                   {"temp_c": "24.0", "energia": "viva", "bloqueo": "retirado", "operario": "ausente"})
        for t in ("24.0", "24.2", "23.9", "24.1", "24.3", "23.8", "24.1", "24.0", "24.2", "23.9"):
            self.leer(temp_c=t)

    def test_demo_acercarse_con_el_motor_encendido_avisa_siempre(self):
        self.demo()
        alertas = self.leer(operario="presente")
        self.assertTrue(any(a.startswith("PERSONA JUNTO A LA MÁQUINA CON EL MOTOR ENCENDIDO") for a in alertas), alertas)
        self.assertTrue(any(a.startswith("ORDEN INVERTIDO: «Acercarte a la correa»") for a in alertas), alertas)
        self.assertEqual(self.s.calificacion("ot-1")["nivel"], "error")
        self.leer(operario="ausente")
        self.assertEqual(self.s.calificacion("ot-1")["nivel"], "ok")

    def test_demo_el_polin_caliente_avisa_sin_detener_y_se_calma_con_el_nuevo(self):
        self.demo()
        alertas = self.leer(temp_c="41.0")
        self.assertTrue(any(a.startswith("temp_c = 41, lejos de su mediana") for a in alertas), alertas)
        self.assertEqual(self.s.calificacion("ot-1")["nivel"], "warning")
        self.leer(temp_c="24.4")
        self.assertEqual(self.s.calificacion("ot-1")["nivel"], "ok")

    def test_demo_en_su_orden_se_completa_sin_avisos(self):
        self.demo()
        alertas = self.leer(energia="cortada") + self.leer(bloqueo="puesto") + self.leer(operario="presente")
        self.declarar("saqué el polín caliente")
        self.declarar("puse el polín nuevo")
        alertas += self.leer(operario="ausente") + self.leer(bloqueo="retirado") + self.leer(energia="viva")
        self.assertEqual(alertas, [])
        self.assertEqual((self.s.ots()[0]["estado_general"], self.cerrados()), ("completa", 8))

    def estacion(self, equipo="caliente"):
        """La estación física: lo que manda edge/edge.py (energia sale del motor del ESP32)."""
        self.abrir("pauta-polin-estacion.json", ["energia", "operario", "equipo"],
                   {"energia": "viva", "operario": "ausente", "equipo": equipo})
        return self.leer()

    def test_estacion_acercarse_sin_apagar_el_motor_avisa(self):
        self.estacion()
        alertas = self.leer(operario="presente")
        self.assertTrue(any(a.startswith("PERSONA JUNTO A LA MÁQUINA CON EL MOTOR ENCENDIDO") for a in alertas), alertas)
        self.assertEqual(self.s.calificacion("ot-1")["nivel"], "error")
        self.leer(operario="ausente")
        self.assertEqual((self.s.calificacion("ot-1")["nivel"], self.cerrados()), ("ok", 0))

    def test_estacion_en_su_orden_se_completa_sin_avisos(self):
        alertas = self.estacion() + self.leer(energia="cortada") + self.leer(operario="presente")
        self.assertEqual(self.cerrados(), 2)  # con el equipo caliente no pasa de «esperar»
        alertas += self.leer(equipo="frio")
        self.declarar("este es el polín rojo", foto=b"con el rojo")
        self.assertEqual(self.cerrados(), 4)
        self.declarar("lo reemplacé", foto=b"con el nuevo")
        # para juzgar el reemplazo la cámara recibe la foto de ahora y la de cuando vio el rojo
        _, ahora, antes = self.juez[-1]
        self.assertEqual((ahora, antes), (b"\xff\xd8con el nuevo\xff\xd9", b"\xff\xd8con el rojo\xff\xd9"))
        alertas += self.leer(operario="ausente") + self.leer(energia="viva")
        self.assertEqual(alertas, [])
        self.assertEqual((self.s.ots()[0]["estado_general"], self.cerrados()), ("completa", 7))

    def test_estacion_encender_el_motor_sin_alejarse_avisa_y_no_cierra(self):
        self.estacion(equipo="frio"), self.leer(energia="cortada"), self.leer(operario="presente"), self.leer(equipo="frio")
        self.declarar("este es el polín rojo", foto=b"con el rojo")
        self.declarar("lo reemplacé", foto=b"con el nuevo")
        alertas = self.leer(energia="viva")  # junto a la cinta
        self.assertTrue(any(a.startswith("PERSONA JUNTO A LA MÁQUINA CON EL MOTOR ENCENDIDO") for a in alertas), alertas)
        self.assertEqual(self.cerrados(), 5)

    def test_estacion_sacar_el_polin_rojo_sin_poner_otro_no_cierra_el_paso(self):
        self.estacion(), self.leer(energia="cortada"), self.leer(operario="presente"), self.leer(equipo="frio")
        self.declarar("este es el polín rojo")
        self.camara = lambda pregunta, antes: antes is None  # al comparar, la cámara responde que no
        self.declarar("lo reemplacé")
        self.assertEqual(self.cerrados(), 4)
        self.assertEqual(self.s.snapshot("ot-1")["estado"]["en_conflicto"], ["e5"])
        self.camara = lambda pregunta, antes: True  # ahora sí hay un polín normal en su lugar
        self.declarar("lo reemplacé")
        self.assertEqual(self.cerrados(), 5)

    def test_estacion_sin_la_foto_del_polin_rojo_no_hay_con_que_comparar(self):
        self.estacion(), self.leer(energia="cortada"), self.leer(operario="presente"), self.leer(equipo="frio")
        self.s.confirmar_por_persona("ot-1", "e4", "supervisor:X", "la cámara no lo enfoca")  # se cierra sin foto
        self.declarar("lo reemplacé")
        self.assertEqual(self.cerrados(), 4)
        self.assertEqual([p for p, _, _ in self.juez], [])  # ni se le preguntó a la cámara

    def test_estacion_con_el_equipo_ya_frio_no_avisa_al_empezar(self):
        # «Apagar el motor» no lleva control_critico porque, con el paso actual crítico, la lectura repetida
        # de «equipo = frio» sonaba ORDEN INVERTIDO. Desde el 2026-11-21 el orden solo mira lecturas que
        # cambian (tests/test_orden_en_reposo.py): marcarlo crítico ya es decisión de la pauta, no del código.
        self.assertEqual(self.estacion(equipo="frio"), [])

    def test_botella_poner_y_abrir_completa_la_ot(self):
        self.abrir("pauta-botella.json", [], {})
        self.declarar("puse la botella", foto=b"cerrada")
        self.declarar("la abrí", foto=b"abierta")
        _, ahora, antes = self.juez[-1]
        self.assertEqual((ahora, antes), (b"\xff\xd8abierta\xff\xd9", b"\xff\xd8cerrada\xff\xd9"))
        self.assertEqual((self.s.ots()[0]["estado_general"], self.cerrados()), ("completa", 2))

    def test_botella_si_sigue_tapada_no_cierra_el_paso(self):
        self.abrir("pauta-botella.json", [], {})
        self.declarar("puse la botella")
        self.camara = lambda pregunta, antes: antes is None
        self.declarar("la abrí")
        self.assertEqual(self.cerrados(), 1)


class LaSemillaDeLosCasos(Base):
    def test_cada_protocolo_de_datos_tiene_su_documento_y_pautas_que_existen(self):
        pautas = {json.loads(r.read_text(encoding="utf-8"))["id"] for r in DATOS.glob("pauta-*.json")}
        for d in json.loads(SEMILLA.read_text(encoding="utf-8")):
            self.assertTrue((DATOS / d["documento"]).is_file(), d["documento"])
            self.assertTrue(d["pautas"], d["id"])
            self.assertLessEqual(set(d["pautas"]), pautas, d["id"])

    def test_deja_cada_pauta_de_datos_aprobada_y_con_al_menos_un_protocolo(self):
        r = protocolos.cargar_semilla(self.cx)
        disponibles = {p["id"]: p for p in catalogo.pautas_disponibles(self.cx)}
        self.assertEqual(sorted(disponibles), sorted(r["pautas"]))
        self.assertTrue(all(p["protocolos"] for p in disponibles.values()))

    def test_una_pauta_de_caso_sale_de_su_protocolo_y_del_de_aislamiento(self):
        protocolos.cargar_semilla(self.cx)
        self.assertEqual([p["id"] for p in catalogo.protocolos_de(self.cx, "pauta-celda-mt-01")], ["prot-aislamiento-01", "prot-celda-mt-01"])
        self.assertGreater(len(catalogo.pautas_de(self.cx, "prot-aislamiento-01")), 1)

    def test_las_pautas_de_la_maqueta_son_ejemplos_y_no_salen_del_de_aislamiento(self):
        protocolos.cargar_semilla(self.cx)
        ejemplos = ["pauta-loto-escritorio", "pauta-polin-demo", "pauta-polin-estacion"]
        self.assertEqual([p["id"] for p in catalogo.pautas_de(self.cx, "prot-maqueta-01")], ejemplos)
        self.assertFalse(set(ejemplos) & {p["id"] for p in catalogo.pautas_de(self.cx, "prot-aislamiento-01")})

    def test_una_atribucion_que_se_saco_de_datos_se_saca_de_la_base_al_repetir(self):
        protocolos.cargar_semilla(self.cx)
        catalogo.atribuir(self.cx, "pauta-loto-escritorio", "prot-aislamiento-01", "equipo:factum")  # la de antes
        catalogo.crear_pauta(self.cx, {**json.loads((DATOS / "pauta-loto.json").read_text(encoding="utf-8")), "id": "pauta-de-un-cliente"})
        catalogo.atribuir(self.cx, "pauta-de-un-cliente", "prot-aislamiento-01", "equipo:factum")  # no es de datos/
        protocolos.cargar_semilla(self.cx)
        de_aislamiento = {p["id"] for p in catalogo.pautas_de(self.cx, "prot-aislamiento-01")}
        self.assertNotIn("pauta-loto-escritorio", de_aislamiento)
        self.assertIn("pauta-de-un-cliente", de_aislamiento)

    def test_un_protocolo_da_dos_pautas_la_del_rodillo_y_la_del_polin(self):
        protocolos.cargar_semilla(self.cx)
        self.assertEqual([p["id"] for p in catalogo.pautas_de(self.cx, "prot-correa-01")], ["pauta-correa-ct-01", "pauta-polin-ct-01", "pauta-polin-demo", "pauta-polin-estacion"])

    def test_se_puede_repetir_sin_duplicar(self):
        a = protocolos.cargar_semilla(self.cx)
        self.assertEqual(protocolos.cargar_semilla(self.cx), a)
        self.assertEqual(len(catalogo.listar_protocolos(self.cx)), len(a["protocolos"]))

    def test_el_protocolo_de_un_tercero_guarda_el_enlace_y_no_su_texto(self):
        protocolos.cargar_semilla(self.cx)
        p = catalogo.leer_protocolo(self.cx, "prot-camion-rigido-01")
        self.assertTrue(p["origen"].startswith("https://"))
        self.assertIn("no se copia su texto", p["texto"])



class LasOtDeEjemplo(Base):
    """datos/ots-semilla.json, ejecutadas contra los servicios: cada estado y cada aviso es el que da el sistema."""

    def setUp(self):
        super().setUp()
        from datetime import UTC, datetime

        from app import semilla
        self.semilla = semilla
        db.escribir_sensor(self.cx, "operario", "presente")
        self.r = semilla.cargar(self.cx, datetime(2026, 11, 21, 18, 0, tzinfo=UTC))
        self.ots = {o["ot"]: o for o in self.r["ots_creadas"]}
        self.s = Servicios(self.cx)

    def test_cada_protocolo_tiene_pautas_y_cada_pauta_tiene_ot(self):
        for p in catalogo.listar_protocolos(self.cx):
            self.assertTrue(p["pautas"], p["id"])
        self.assertEqual({o["pauta"] for o in self.ots.values()}, set(self.r["pautas"]))

    def test_hay_ot_en_cada_estado(self):
        estados = {o["estado_general"] for o in self.ots.values()}
        self.assertEqual(estados, {"completa", "en_ejecucion", "asignada", "sin_asignar"})
        self.assertEqual(self.ots["ot-1007"]["operador"], "operario:1")
        self.assertIsNone(self.ots["ot-1009"]["operador"])

    def test_la_calificacion_de_cada_una_es_la_que_da_el_sistema(self):
        nivel = {o: self.s.calificacion(o)["nivel"] for o in self.ots}
        self.assertEqual(nivel["ot-1004"], "error")    # sacó el candado antes de tiempo
        self.assertEqual(nivel["ot-1002"], "warning")  # el polín sigue caliente
        self.assertEqual(nivel["ot-1006"], "warning")  # la cámara respondió con 62 %
        self.assertEqual(nivel["ot-1001"], "ok")       # tuvo avisos, y se resolvieron

    def test_las_completas_guardan_sus_avisos_resueltos(self):
        alertas = [e.detalle for e in db.eventos(self.cx, "ot-1001") if e.tipo.value == "alerta"]
        self.assertTrue(any(a.startswith("PERSONA JUNTO A LA MÁQUINA") for a in alertas), alertas)
        self.assertEqual(self.ots["ot-1001"]["estado_general"], "completa")

    def test_las_horas_van_hacia_atras_y_los_eventos_en_orden(self):
        self.assertTrue(self.ots["ot-1005"]["abierta_en"].startswith("2026-11-12"))
        ts = [e.ts for e in db.eventos(self.cx, "ot-1003")]
        self.assertEqual(ts, sorted(ts))
        self.assertNotEqual(db.ahora()[:10], "2026-11-12")

    def test_no_deja_sensores_ni_sesiones_y_se_puede_repetir(self):
        self.assertEqual(db.estado_sensores(self.cx), {"operario": "presente"})
        self.assertEqual(self.s.sesiones(), [])
        otra = self.semilla.cargar(self.cx)
        self.assertEqual((otra["ots_creadas"], len(otra["ots_que_ya_estaban"])), ([], 21))

    def test_la_camara_de_la_semilla_queda_dicha_en_la_evidencia(self):
        ev = next(e for e in db.eventos(self.cx, "ot-1006") if e.tipo.value == "veredicto" and e.capa == 3)
        self.assertIn("semilla", ev.evidencia)
        self.assertIsNone(ev.evidencia["cuadro"])


@unittest.skipUnless(TIENE_HTTPX, "necesita fastapi y httpx")
class PorHTTP(unittest.TestCase):
    def setUp(self):
        from fastapi.testclient import TestClient

        from app import api
        from app.servicios import Servicios

        api.cx = db.conectar(":memory:")
        api.servicios = Servicios(api.cx)
        self.c = TestClient(api.app)

    def supervisor(self, pautas=()):
        """Una empresa con un supervisor que entró; devuelve la cabecera con su token."""
        from app import acceso, api
        acceso.crear_cliente(api.cx, "planta", "Planta Norte")
        _, clave = acceso.crear_persona(api.cx, "planta", "supervisor:planta", "Sofía", "sofia@planta.example", "supervisor")
        for pauta_id in pautas:
            acceso.habilitar(api.cx, "planta", pauta_id)
        token = self.c.post("/auth/entrar", json={"usuario": "sofia@planta.example", "clave": clave}).json()["token"]
        return {"Authorization": f"Bearer {token}"}

    def test_de_cargar_el_protocolo_a_la_ot_del_cliente(self):
        c = self.c
        r = c.post("/interno/protocolos", json={**protocolo(), "actor": EQUIPO})
        self.assertEqual((r.status_code, r.json()["id"]), (201, "prot-a"))
        r = c.post("/interno/protocolos/prot-a/pautas", json={"pauta": pauta_demo(), "actor": EQUIPO})
        self.assertEqual((r.status_code, r.json()["aprobada"], r.json()["protocolos"][0]["id"]), (201, False, "prot-a"))
        yo = self.supervisor()
        self.assertEqual(c.put(f"/interno/clientes/planta/pautas/{CORREA}").status_code, 200)
        self.assertEqual(c.get("/cliente/pautas", headers=yo).json(), [])
        self.assertEqual(c.post("/cliente/ots", json={"pauta_id": CORREA}, headers=yo).status_code, 403)
        self.assertEqual(c.post(f"/interno/pautas/{CORREA}/versiones/1/aprobar", json={"actor": "supervisor:X"}).status_code, 200)
        self.assertEqual([p["id"] for p in c.get("/cliente/pautas", headers=yo).json()], [CORREA])
        r = c.post("/cliente/ots", json={"pauta_id": CORREA}, headers=yo)
        self.assertEqual((r.status_code, r.json()["ot"], r.json()["version"], r.json()["cliente"]), (201, "ot-0001", 1, "planta"))
        self.assertEqual(db.eventos(api_cx(), "ot-0001")[0].actor, "supervisor:planta")
        ots = c.get("/cliente/ots", headers=yo).json()
        self.assertEqual([(o["ot"], o["pauta"], o["estado_general"]) for o in ots], [("ot-0001", CORREA, "sin_asignar")])
        self.assertEqual(c.get("/ot/ot-0001").json()["paso_actual"], "p1")

    def test_el_crud_del_protocolo_y_de_la_atribucion(self):
        c = self.c
        c.post("/interno/protocolos", json={**protocolo(), "actor": EQUIPO})
        c.post("/interno/protocolos", json={**protocolo("prot-b"), "actor": EQUIPO})
        self.assertEqual(c.post("/interno/protocolos", json={**protocolo(), "actor": EQUIPO}).status_code, 409)
        self.assertEqual([p["id"] for p in c.get("/interno/protocolos").json()], ["prot-a", "prot-b"])
        self.assertEqual(c.put("/interno/protocolos/prot-a", json={"nombre": "Otro nombre"}).json()["nombre"], "Otro nombre")
        self.assertEqual(c.get("/interno/protocolos/prot-a").json()["texto"], "1. Cortar la energía...")
        self.assertEqual(c.get("/interno/protocolos/nada").status_code, 404)
        c.post("/pautas", json=pauta_demo())
        r = c.put(f"/interno/pautas/{CORREA}/protocolos/prot-a", json={"actor": EQUIPO})
        self.assertEqual([p["id"] for p in r.json()["protocolos"]], ["prot-a"])
        c.put(f"/interno/pautas/{CORREA}/protocolos/prot-b", json={"actor": EQUIPO})
        self.assertEqual([p["id"] for p in c.get(f"/interno/pautas/{CORREA}/protocolos").json()], ["prot-a", "prot-b"])
        self.assertEqual(c.delete("/interno/protocolos/prot-a").status_code, 409)
        self.assertEqual(c.delete(f"/interno/pautas/{CORREA}/protocolos/prot-a").status_code, 204)
        self.assertEqual(c.delete("/interno/protocolos/prot-a").status_code, 204)
        self.assertEqual(c.put(f"/interno/pautas/{CORREA}/protocolos/nada", json={"actor": EQUIPO}).status_code, 404)
        self.assertEqual(c.get("/interno/pautas/nada/protocolos").status_code, 404)

    def test_una_pauta_mal_formada_es_422_y_un_protocolo_que_no_existe_404(self):
        self.c.post("/interno/protocolos", json={**protocolo(), "actor": EQUIPO})
        mala = pauta_demo()
        del mala["pasos"][0]["sensor"]
        self.assertEqual(self.c.post("/interno/protocolos/prot-a/pautas", json={"pauta": mala, "actor": EQUIPO}).status_code, 422)
        self.assertEqual(self.c.post("/interno/protocolos/nada/pautas", json={"pauta": pauta_demo(), "actor": EQUIPO}).status_code, 404)

    def test_con_clave_de_equipo_el_servicio_interno_la_pide_y_el_del_cliente_no(self):
        clave = {"X-Clave-Equipo": "secreta"}
        with mock.patch.dict(os.environ, {"CLAVE_EQUIPO": "secreta"}):
            cuerpo = {**protocolo(), "actor": EQUIPO}
            for r in (self.c.post("/interno/protocolos", json=cuerpo), self.c.get("/interno/protocolos"), self.c.post("/interno/protocolos/semilla"),
                      self.c.post("/interno/protocolos", json=cuerpo, headers={"X-Clave-Equipo": "otra"})):
                self.assertEqual(r.status_code, 401)
            self.assertEqual(self.c.get("/interno/protocolos", headers=clave).json(), [])
            self.assertEqual(self.c.post("/interno/protocolos/semilla", headers=clave).status_code, 200)
            yo = self.supervisor(["pauta-brazo-01"])
            self.assertEqual(self.c.get("/cliente/pautas", headers=yo).status_code, 200)
            self.assertEqual(self.c.post("/cliente/ots", json={"pauta_id": "pauta-brazo-01"}, headers=yo).status_code, 201)

    def test_la_semilla_de_ot_pide_la_clave_y_deja_las_ot_en_la_lista(self):
        with mock.patch.dict(os.environ, {"CLAVE_EQUIPO": "secreta"}):
            self.assertEqual(self.c.post("/interno/ots/semilla").status_code, 401)
            r = self.c.post("/interno/ots/semilla", headers={"X-Clave-Equipo": "secreta"})
        self.assertEqual((r.status_code, len(r.json()["ots_creadas"]), len(r.json()["accesos"])), (200, 21, 3))
        carla = next(a for a in r.json()["accesos"] if a["rol"] == "supervisor")
        token = self.c.post("/auth/entrar", json={"usuario": carla["usuario"], "clave": carla["clave"]}).json()["token"]
        self.assertEqual(len(self.c.get("/cliente/ots", headers={"Authorization": f"Bearer {token}"}).json()), 21)

    def test_la_semilla_deja_los_casos_listos_para_el_cliente(self):
        r = self.c.post("/interno/protocolos/semilla").json()
        self.assertIn("prot-camion-rigido-01", r["protocolos"])
        yo = self.supervisor(r["pautas"])
        self.assertEqual(sorted(p["id"] for p in self.c.get("/cliente/pautas", headers=yo).json()), sorted(r["pautas"]))

    def test_la_guia_del_agente_explica_los_dos_servicios(self):
        guia = self.c.get("/agente").text
        for ruta in ("/interno/protocolos", "/interno/pautas/{pauta_id}/protocolos/{protocolo_id}", "/cliente/pautas", "/cliente/ots", "/auth/entrar"):
            self.assertIn(ruta, guia)



def api_cx():
    from app import api
    return api.cx


if __name__ == "__main__":
    unittest.main()
