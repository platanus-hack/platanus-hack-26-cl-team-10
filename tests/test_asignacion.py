"""A quién le toca cada OT: asignar, el estado general en la lista y el relevo que la cambia de manos.

Correr:  uv run --with httpx python -m unittest tests.test_asignacion
El operador no se guarda en ninguna columna: sale de la bitácora, como el resto del estado de la OT.
"""

import importlib.util
import unittest

TIENE_HTTPX = importlib.util.find_spec("httpx") is not None and importlib.util.find_spec("fastapi") is not None

PASOS = ["p1", "p2", "p3", "p4", "p5", "p6"]


@unittest.skipUnless(TIENE_HTTPX, "necesita fastapi y httpx")
class Base(unittest.TestCase):
    def setUp(self):
        from fastapi.testclient import TestClient

        from app import api, db
        from app.servicios import Servicios

        api.cx = db.conectar(":memory:")
        api.servicios = Servicios(api.cx)
        self.c = TestClient(api.app)
        self.c.post("/pauta/demo")
        self.c.post("/ot/ot-1/abrir")

    def ot(self, ot_id="ot-1"):
        return next(o for o in self.c.get("/ots").json() if o["ot"] == ot_id)

    def asignar(self, operador="operario:2", ot_id="ot-1"):
        return self.c.post(f"/ot/{ot_id}/asignar", json={"operador": operador})

    def cerrar(self, *pasos):
        for p in pasos:
            if p == "p6":  # es de confirmación: se cierra declarando
                r = self.c.post("/ot/ot-1/declarar", json={"actor": "operario:1", "texto": "prueba hecha", "paso_id": p})
            else:
                r = self.c.post(f"/ot/ot-1/pasos/{p}/confirmar", json={"actor": "supervisor:1", "motivo": "lo vi hecho"})
            self.assertEqual(r.status_code, 200, r.text)


class Asignar(Base):
    def test_una_ot_recien_abierta_esta_sin_asignar(self):
        o = self.ot()
        self.assertIsNone(o["operador"])
        self.assertEqual(o["estado_general"], "sin_asignar")
        self.assertIsNone(o["entregada_por"])
        self.assertEqual((o["cerrados"], o["total"]), (0, len(PASOS)))

    def test_asignar_devuelve_el_resumen_con_la_forma_de_la_lista(self):
        r = self.asignar()
        self.assertEqual(r.status_code, 200)
        self.assertEqual(r.json(), self.ot())
        self.assertEqual((r.json()["operador"], r.json()["estado_general"]), ("operario:2", "asignada"))

    def test_la_asignacion_queda_en_la_bitacora(self):
        self.c.post("/ot/ot-1/asignar", json={"operador": "operario:1", "actor": "supervisor:1"})
        ev = self.c.get("/ot/ot-1/eventos").json()[-1]
        self.assertEqual((ev["tipo"], ev["actor"], ev["evidencia"]), ("ot_asignada", "supervisor:1", {"operador": "operario:1"}))

    def test_solo_un_supervisor_asigna(self):
        for actor in ("operario:1", "sistema", "simulador"):
            r = self.c.post("/ot/ot-1/asignar", json={"operador": "operario:2", "actor": actor})
            self.assertEqual(r.status_code, 409, actor)
            self.assertIn("solo un supervisor", r.json()["regla"])
        self.assertIsNone(self.ot()["operador"])

    def test_una_ot_que_no_existe_es_404(self):
        r = self.asignar(ot_id="no-existe")
        self.assertEqual(r.status_code, 404)
        self.assertIn("no-existe", r.json()["no_existe"])

    def test_un_operador_que_no_existe_es_409(self):
        r = self.asignar("operario:99")
        self.assertEqual(r.status_code, 409)
        self.assertIn("no existe", r.json()["regla"])
        self.assertIsNone(self.ot()["operador"])

    def test_una_ot_que_ya_tiene_operador_no_se_asigna_de_nuevo(self):
        self.asignar("operario:1")
        r = self.asignar("operario:2")
        self.assertEqual(r.status_code, 409)
        self.assertIn("ya tiene operador", r.json()["regla"])
        self.assertEqual(self.ot()["operador"], "operario:1")

    def test_una_ot_completa_no_se_asigna(self):
        self.cerrar(*PASOS)
        r = self.asignar()
        self.assertEqual(r.status_code, 409)
        self.assertIn("completa", r.json()["regla"])


class EstadoGeneral(Base):
    def test_con_sesion_abierta_esta_en_ejecucion(self):
        self.asignar()
        self.c.post("/ot/ot-1/sesion", json={"edge_id": "edge-1", "operario": "operario:2"})
        self.assertEqual(self.ot()["estado_general"], "en_ejecucion")

    def test_con_un_veredicto_esta_en_ejecucion_aunque_no_haya_sesion(self):
        self.asignar()
        self.cerrar("p1")
        o = self.ot()
        self.assertEqual((o["estado_general"], o["cerrados"], o["paso_actual"]), ("en_ejecucion", 1, "p2"))

    def test_sin_operador_ni_la_sesion_ni_los_veredictos_la_sacan_de_sin_asignar(self):
        self.c.post("/ot/ot-1/sesion", json={"edge_id": "edge-1", "operario": "operario:2"})
        self.cerrar("p1")
        self.assertEqual(self.ot()["estado_general"], "sin_asignar")

    def test_completa_manda_sobre_todo_lo_demas(self):
        self.asignar()
        self.cerrar(*PASOS)
        self.c.post("/ot/ot-1/relevo/entregar", params={"actor": "operario:2"})
        o = self.ot()
        self.assertEqual((o["estado_general"], o["completa"], o["cerrados"]), ("completa", True, len(PASOS)))

    def test_el_estado_de_una_ot_no_depende_de_las_otras(self):
        self.c.post("/ot/ot-2/abrir")
        self.asignar(ot_id="ot-2")
        self.assertEqual(self.ot("ot-1")["estado_general"], "sin_asignar")
        self.assertEqual(self.ot("ot-2")["estado_general"], "asignada")


class ElRelevoCambiaElOperador(Base):
    def setUp(self):
        super().setUp()
        self.asignar("operario:1")
        self.cerrar("p1")

    def test_entregar_deja_la_ot_sin_operador_y_entregada(self):
        self.assertEqual(self.c.post("/ot/ot-1/relevo/entregar", params={"actor": "operario:1"}).status_code, 200)
        o = self.ot()
        self.assertEqual((o["operador"], o["estado_general"], o["entregada_por"]), (None, "entregada", "operario:1"))

    def test_recibir_la_deja_en_quien_firma(self):
        self.c.post("/ot/ot-1/relevo/entregar", params={"actor": "operario:1"})
        self.c.post("/ot/ot-1/relevo/recibir", params={"actor": "operario:2"})
        o = self.ot()
        self.assertEqual((o["operador"], o["estado_general"], o["entregada_por"]), ("operario:2", "en_ejecucion", None))

    def test_una_ot_entregada_se_puede_reasignar(self):
        self.c.post("/ot/ot-1/relevo/entregar", params={"actor": "operario:1"})
        r = self.asignar("operario:2")
        self.assertEqual(r.status_code, 200)
        self.assertEqual((r.json()["operador"], r.json()["estado_general"], r.json()["entregada_por"]),
                         ("operario:2", "en_ejecucion", None))

    def test_entregar_de_nuevo_despues_de_recibir_vuelve_a_entregada(self):
        self.c.post("/ot/ot-1/relevo/entregar", params={"actor": "operario:1"})
        self.c.post("/ot/ot-1/relevo/recibir", params={"actor": "operario:2"})
        self.c.post("/ot/ot-1/relevo/entregar", params={"actor": "operario:2"})
        o = self.ot()
        self.assertEqual((o["operador"], o["estado_general"], o["entregada_por"]), (None, "entregada", "operario:2"))


if __name__ == "__main__":
    unittest.main()
