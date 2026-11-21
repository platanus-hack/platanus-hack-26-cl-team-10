"""Una persona confirma un paso que el sensor no muestra hecho. Casos de uso.

Correr:  uv run --with httpx python -m unittest tests.test_confirmar
Se le cree a la persona, pero no en silencio: queda quién, por qué y qué marcaba el
sensor, la OT queda en warning y la seguridad sigue mandando (LOGICA, «Cuando la
persona y el sensor no coinciden»; PRD de servicios en vivo, CA16).
"""

import importlib.util
import unittest

from app import db
from app.catalogo import ReglaDeNegocio
from app.contratos import Estado, TipoEvento
from app.protocolos import desde_json
from app.bus import Bus
from app.servicios import Servicios

TIENE_HTTPX = importlib.util.find_spec("httpx") is not None and importlib.util.find_spec("fastapi") is not None


class BusDePrueba(Bus):
    def __init__(self):
        super().__init__()
        self.mensajes: list[tuple[str, dict]] = []

    def publicar(self, canal, mensaje):
        self.mensajes.append((canal, mensaje))


class Base(unittest.TestCase):
    def setUp(self):
        self.cx = db.conectar(":memory:")
        pauta = desde_json()
        db.guardar_pauta(self.cx, pauta)
        db.abrir_ot(self.cx, "ot-1", pauta, "supervisor:X")
        self.bus = BusDePrueba()
        self.s = Servicios(self.cx, self.bus)
        self.s.iniciar_sesion("ot-1", "edge-1", "operario:A")
        for sensor, valor in [("reed_bloqueo", "abierto"), ("guarda", "cerrada"), ("energia", "cortada")]:
            self.s.recibir_lectura("edge-1", sensor, valor)

    def tearDown(self):
        self.cx.close()

    def veredictos(self, paso_id):
        return [e for e in db.eventos(self.cx, "ot-1") if e.tipo is TipoEvento.VEREDICTO and e.paso_id == paso_id]


class LaPersonaCierraElPasoQueElSensorNoVe(Base):
    def test_el_candado_puesto_con_el_reed_danado_se_confirma_y_la_pauta_avanza(self):
        self.s.declarar("ot-1", "operario:A", "bloqueo puesto")
        r = self.s.confirmar_por_persona("ot-1", "p1", "supervisor:B", "el reed está dañado; el candado está puesto, lo vi")
        self.assertEqual(r["estado"], "verificado")
        self.assertEqual(self.s.snapshot("ot-1")["estado"]["paso_actual"], "p2")

    def test_queda_quien_por_que_y_que_marcaba_el_sensor(self):
        self.s.confirmar_por_persona("ot-1", "p1", "operario:A", "el sensor no marca, el candado está puesto")
        ev = self.veredictos("p1")[-1]
        self.assertEqual((ev.estado, ev.capa, ev.actor), (Estado.VERIFICADO, None, "operario:A"))
        self.assertEqual(ev.evidencia["tipo"], "persona")
        self.assertEqual(ev.evidencia["motivo"], "el sensor no marca, el candado está puesto")
        self.assertEqual(ev.evidencia["contra"], {"sensor": "reed_bloqueo", "valor": "abierto", "espera": "cerrado"})

    def test_el_conflicto_anterior_sigue_en_la_bitacora(self):
        self.s.declarar("ot-1", "operario:A", "bloqueo puesto")
        self.s.confirmar_por_persona("ot-1", "p1", "supervisor:B", "reed dañado")
        self.assertEqual([e.estado for e in self.veredictos("p1")], [Estado.EN_CONFLICTO, Estado.VERIFICADO])

    def test_la_ot_queda_en_warning_y_no_interrumpe(self):
        r = self.s.confirmar_por_persona("ot-1", "p1", "supervisor:B", "reed dañado")
        c = self.s.calificacion("ot-1")
        self.assertEqual(c["nivel"], "warning")
        self.assertIn("contra la evidencia", c["avisos"][0]["motivos"][0])
        self.assertFalse(r["interrumpe"])

    def test_sale_por_el_stream_de_la_ot(self):
        self.bus.mensajes.clear()
        self.s.confirmar_por_persona("ot-1", "p1", "supervisor:B", "reed dañado")
        tipos = [m["tipo"] for _, m in self.bus.mensajes]
        self.assertEqual(tipos, ["evento", "calificacion_ot"])

    def test_un_paso_de_camara_sin_juez_tambien_se_puede_confirmar(self):
        for sensor, valor in [("reed_bloqueo", "cerrado"), ("guarda", "abierta")]:
            self.s.recibir_lectura("edge-1", sensor, valor)
        r = self.s.confirmar_por_persona("ot-1", "p3", "supervisor:B", "la cámara no tiene vista del rodillo")
        self.assertEqual(r["evidencia"]["contra"], {"camara": "¿Está el rodillo nuevo instalado y con los dos pernos puestos?"})


class LaSeguridadSigueMandando(Base):
    def test_confirmar_el_bloqueo_no_apaga_la_alerta_de_guarda_con_energia_viva(self):
        self.s.confirmar_por_persona("ot-1", "p1", "supervisor:B", "reed dañado")
        self.s.recibir_lectura("edge-1", "energia", "viva")
        self.s.recibir_lectura("edge-1", "guarda", "abierta")
        self.assertEqual(self.s.calificacion("ot-1")["nivel"], "error")
        self.assertIn("GUARDA ABIERTA CON ENERGÍA VIVA", self.s.calificacion("ot-1")["avisos"][0]["motivos"][0])

    def test_un_control_confirmado_a_mano_no_cuenta_como_control_perdido(self):
        self.s.confirmar_por_persona("ot-1", "p1", "supervisor:B", "reed dañado")
        r = self.s.recibir_lectura("edge-1", "guarda", "abierta")
        self.assertEqual([e for e in r["eventos"] if e["tipo"] == "alerta"], [])

    def test_resuelve_el_orden_invertido_que_esperaba_ese_paso(self):
        self.s.recibir_lectura("edge-1", "guarda", "abierta")
        self.assertIn("orden:p2", self.s.alertas_activas("ot-1"))
        self.s.confirmar_por_persona("ot-1", "p1", "supervisor:B", "reed dañado")
        self.assertNotIn("orden:p2", self.s.alertas_activas("ot-1"))


class LoQueNoSePuede(Base):
    def test_sin_motivo_no(self):
        with self.assertRaises(ReglaDeNegocio):
            self.s.confirmar_por_persona("ot-1", "p1", "supervisor:B", "  ")

    def test_el_sistema_no_confirma(self):
        with self.assertRaises(ReglaDeNegocio):
            self.s.confirmar_por_persona("ot-1", "p1", "sistema", "porque sí")

    def test_solo_el_paso_en_curso(self):
        with self.assertRaises(ReglaDeNegocio):
            self.s.confirmar_por_persona("ot-1", "p2", "supervisor:B", "adelanto")

    def test_un_paso_de_confirmacion_se_cierra_declarando(self):
        for sensor, valor in [("reed_bloqueo", "cerrado"), ("guarda", "abierta")]:
            self.s.recibir_lectura("edge-1", sensor, valor)
        self.s.confirmar_por_persona("ot-1", "p3", "supervisor:B", "sin cámara")
        for sensor, valor in [("guarda", "cerrada"), ("reed_bloqueo", "abierto")]:
            self.s.recibir_lectura("edge-1", sensor, valor)
        with self.assertRaises(ReglaDeNegocio):
            self.s.confirmar_por_persona("ot-1", "p6", "supervisor:B", "paró")

    def test_un_paso_que_no_existe_es_404(self):
        with self.assertRaises(KeyError):
            self.s.confirmar_por_persona("ot-1", "p99", "supervisor:B", "x")


@unittest.skipUnless(TIENE_HTTPX, "necesita fastapi y httpx")
class PorHTTP(unittest.TestCase):
    def setUp(self):
        from fastapi.testclient import TestClient

        from app import api

        api.cx = db.conectar(":memory:")
        api.servicios = Servicios(api.cx)
        self.c = TestClient(api.app)
        self.c.post("/pauta/demo")
        self.c.post("/ot/ot-1/abrir")
        self.c.post("/ot/ot-1/sesion", json={"edge_id": "edge-1", "operario": "operario:A"})
        self.c.post("/edge/edge-1/lecturas", json=[{"sensor_id": "reed_bloqueo", "valor": "abierto"}])

    def test_el_endpoint_confirma_y_los_errores_son_409_y_404(self):
        url = "/ot/ot-1/pasos/p1/confirmar"
        self.assertEqual(self.c.post(url, json={"actor": "supervisor:B", "motivo": ""}).status_code, 409)
        self.assertEqual(self.c.post("/ot/ot-1/pasos/p2/confirmar", json={"actor": "supervisor:B", "motivo": "x"}).status_code, 409)
        self.assertEqual(self.c.post("/ot/ot-1/pasos/p99/confirmar", json={"actor": "supervisor:B", "motivo": "x"}).status_code, 404)
        r = self.c.post(url, json={"actor": "supervisor:B", "motivo": "reed dañado"})
        self.assertEqual(r.status_code, 200)
        self.assertEqual(r.json()["evidencia"]["tipo"], "persona")
        self.assertEqual(self.c.get("/ot/ot-1").json()["paso_actual"], "p2")

    def test_la_guia_del_agente_lo_explica(self):
        self.assertIn("/ot/{ot_id}/pasos/{paso_id}/confirmar", self.c.get("/agente").text)


if __name__ == "__main__":
    unittest.main()
