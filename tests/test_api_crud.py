"""El CRUD por HTTP: códigos de respuesta de cada regla. Necesita httpx.

Correr:  uv run --with httpx python -m unittest tests.test_api_crud
"""

import importlib.util
import json
import unittest

TIENE_HTTPX = importlib.util.find_spec("httpx") is not None and importlib.util.find_spec("fastapi") is not None


@unittest.skipUnless(TIENE_HTTPX, "necesita fastapi y httpx")
class CrudPorHTTP(unittest.TestCase):
    def setUp(self):
        from fastapi.testclient import TestClient

        from app import api, db
        from app.protocolos import PAUTA_DEMO
        from app.servicios import Servicios

        api.cx = db.conectar(":memory:")
        api.servicios = Servicios(api.cx)
        self.c = TestClient(api.app)
        self.pauta_ruta = PAUTA_DEMO
        self.pauta = json.loads(PAUTA_DEMO.read_text(encoding="utf-8"))

    def test_el_ciclo_de_una_pauta_hasta_su_ot(self):
        self.assertEqual(self.c.post("/pautas", json=self.pauta).status_code, 201)
        self.assertEqual(self.c.post("/ot/ot-1/abrir").status_code, 409)
        r = self.c.post("/pautas/pauta-correa-ct-01/versiones/1/aprobar", json={"actor": "supervisor:X"})
        self.assertTrue(r.json()["aprobada"])
        self.assertEqual(self.c.post("/ot/ot-1/abrir").status_code, 200)
        self.assertEqual(self.c.get("/ots").json()[0]["paso_actual"], "p1")

    def test_el_edge_pregunta_que_clases_pide_su_ot(self):
        from app import api, db
        from app.protocolos import desde_json
        loto = desde_json(self.pauta_ruta.parent / "pauta-loto.json")
        db.guardar_pauta(api.cx, loto)
        db.abrir_ot(api.cx, "ot-1", loto, "supervisor:X")
        self.assertEqual(self.c.get("/edge/edge-1/clases").json(), {"ot": None, "clases": [], "detector_no_conoce": []})
        self.c.post("/ot/ot-1/sesion", json={"edge_id": "edge-1", "operario": "operario:A"})
        self.assertEqual(self.c.get("/edge/edge-1/clases").json(),
                         {"ot": "ot-1", "clases": ["mouse", "pencil"], "detector_no_conoce": []})

    def test_escribir_encima_de_una_version_es_409(self):
        self.c.post("/pautas", json=self.pauta)
        r = self.c.post("/pautas", json=self.pauta)
        self.assertEqual(r.status_code, 409)
        self.assertIn("versión", r.json()["regla"])

    def test_lo_que_no_existe_es_404(self):
        self.assertEqual(self.c.get("/pautas/no-existe").status_code, 404)
        self.assertEqual(self.c.get("/ot/no-existe").status_code, 404)
        self.assertEqual(self.c.get("/eventos/999").status_code, 404)

    def test_un_bug_no_se_disfraza_de_404(self):
        from unittest import mock

        from fastapi.testclient import TestClient

        from app import api

        self.c.post("/pauta/demo")
        self.c.post("/ot/ot-1/abrir")
        c = TestClient(api.app, raise_server_exceptions=False)
        with mock.patch.object(api.servicios, "calificacion", side_effect=KeyError("clave_mal_escrita")):
            self.assertEqual(c.get("/ot/ot-1/calificacion").status_code, 500)

    def test_la_bitacora_no_se_edita_ni_se_borra(self):
        self.c.post("/pauta/demo")
        self.c.post("/ot/ot-1/abrir")
        self.assertEqual(self.c.delete("/ot/ot-1/eventos").status_code, 405)
        self.assertEqual(self.c.put("/ot/ot-1/eventos", json={}).status_code, 405)

    def test_la_sesion_se_abre_se_lee_y_se_termina(self):
        self.c.post("/pauta/demo")
        self.c.post("/ot/ot-1/abrir")
        self.c.post("/ot/ot-1/sesion", json={"edge_id": "edge-1", "operario": "operario:A"})
        self.assertEqual(self.c.get("/edge/edge-1/sesion").json()["ot_id"], "ot-1")
        self.assertEqual(len(self.c.get("/sesiones").json()), 1)
        self.assertEqual(self.c.delete("/edge/edge-1/sesion").status_code, 204)
        self.assertEqual(self.c.get("/edge/edge-1/sesion").status_code, 404)

    def test_con_clave_de_equipo_un_edge_en_sesion_no_se_toma_ni_se_suelta_sin_ella(self):
        import os
        from unittest import mock

        self.c.post("/pauta/demo")
        self.c.post("/ot/ot-1/abrir")
        self.c.post("/ot/ot-2/abrir")
        sesion = {"edge_id": "edge-1", "operario": "operario:A"}
        clave = {"X-Clave-Equipo": "secreta"}
        self.assertEqual(self.c.get("/clave").json(), {"requerida": False, "valida": True})
        with mock.patch.dict(os.environ, {"CLAVE_EQUIPO": "secreta"}):
            self.assertEqual(self.c.get("/clave").json(), {"requerida": True, "valida": False})
            self.assertEqual(self.c.get("/clave", headers=clave).json(), {"requerida": True, "valida": True})
            # un edge libre, y repetir la sesión que ya tiene, no piden clave
            self.assertEqual(self.c.post("/ot/ot-1/sesion", json=sesion).status_code, 200)
            self.assertEqual(self.c.post("/ot/ot-1/sesion", json=sesion).status_code, 200)
            # quitárselo a la OT que ejecuta, o soltarlo, sí
            r = self.c.post("/ot/ot-2/sesion", json=sesion)
            self.assertEqual(r.status_code, 401)
            self.assertIn("ot-1", r.json()["clave"])
            self.assertEqual(self.c.post("/ot/ot-2/sesion", json=sesion, headers={"X-Clave-Equipo": "otra"}).status_code, 401)
            self.assertEqual(self.c.delete("/edge/edge-1/sesion").status_code, 401)
            self.assertEqual(self.c.get("/edge/edge-1/sesion").json()["ot_id"], "ot-1")
            self.assertEqual(self.c.delete("/edge/edge-sin-sesion/sesion").status_code, 204)
            self.assertEqual(self.c.post("/ot/ot-2/sesion", json=sesion, headers=clave).status_code, 200)
            self.assertEqual(self.c.get("/edge/edge-1/sesion").json()["ot_id"], "ot-2")
            self.assertEqual(self.c.delete("/edge/edge-1/sesion", headers=clave).status_code, 204)
        # sin la variable, el servidor queda abierto como siempre
        self.c.post("/ot/ot-1/sesion", json=sesion)
        self.assertEqual(self.c.post("/ot/ot-2/sesion", json=sesion).status_code, 200)

    def test_la_guia_del_agente_lista_todas_las_rutas_con_la_url_del_servidor(self):
        from fastapi.routing import APIRoute
        from starlette.routing import WebSocketRoute

        from app import api
        from app.guia import OCULTAS

        r = self.c.get("/agente")
        self.assertIn("text/markdown", r.headers["content-type"])
        for ruta in api.app.routes:
            if isinstance(ruta, (APIRoute, WebSocketRoute)) and ruta.path not in OCULTAS:
                self.assertIn(f"`{ruta.path}`", r.text)
        self.assertIn("http://testserver/pauta/demo", r.text)
        self.assertIn("ws://testserver/ot/", r.text)
        self.assertEqual(self.c.get("/llms-full.txt").text, r.text)

    def test_detras_de_un_proxy_https_la_guia_usa_https_y_wss(self):
        from app import api
        from app.guia import guia

        texto = guia(api.app, "https://factum.example/")
        self.assertIn("https://factum.example/openapi.json", texto)
        self.assertIn("wss://factum.example/edge/", texto)


if __name__ == "__main__":
    unittest.main()
