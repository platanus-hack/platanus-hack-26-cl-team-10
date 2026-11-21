"""El WebSocket de la OT, de punta a punta. Necesita httpx para el TestClient.

Correr:  uv run --with httpx python -m unittest tests.test_stream
Sin httpx se salta, para que `python3 -m unittest discover tests` siga sin dependencias.
"""

import importlib.util
import unittest

TIENE_HTTPX = importlib.util.find_spec("httpx") is not None and importlib.util.find_spec("fastapi") is not None


@unittest.skipUnless(TIENE_HTTPX, "necesita fastapi y httpx")
class StreamDeLaOT(unittest.TestCase):
    def setUp(self):
        from fastapi.testclient import TestClient

        from app import api, db
        from app.servicios import Servicios

        api.cx = db.conectar(":memory:")
        api.servicios = Servicios(api.cx)
        self.c = TestClient(api.app)
        self.c.post("/pauta/demo")
        self.c.post("/ot/ot-1/abrir")
        self.c.post("/ot/ot-1/sesion", json={"edge_id": "edge-1", "operario": "operario:A"})

    def test_la_ui_recibe_el_snapshot_y_despues_lo_que_manda_el_edge(self):
        with self.c.websocket_connect("/ot/ot-1/stream") as ws:
            snap = ws.receive_json()
            self.assertEqual(snap["tipo"], "snapshot")
            self.assertEqual(snap["estado"]["paso_actual"], "p1")

            self.c.post("/edge/edge-1/lecturas", json=[{"sensor_id": "reed_bloqueo", "valor": "cerrado", "seq": 1}])
            tipos = [ws.receive_json()["tipo"] for _ in range(3)]
            self.assertEqual(tipos, ["lectura", "evento", "calificacion_ot"])

    def test_la_declaracion_del_operario_tambien_llega_por_el_stream(self):
        self.c.post("/edge/edge-1/lecturas", json=[{"sensor_id": "reed_bloqueo", "valor": "abierto"}])
        with self.c.websocket_connect("/ot/ot-1/stream") as ws:
            ws.receive_json()
            self.c.post("/ot/ot-1/declarar", json={"actor": "operario:A", "texto": "bloqueo puesto"})
            mensajes = [ws.receive_json() for _ in range(3)]
            veredicto = mensajes[1]["evento"]
            self.assertEqual(veredicto["estado"], "en_conflicto")
            self.assertEqual(veredicto["calificacion"]["nivel"], "error")

    def test_la_bitacora_por_rest_ya_no_falla(self):
        r = self.c.get("/ot/ot-1/eventos")
        self.assertEqual(r.status_code, 200)
        self.assertEqual(r.json()[0]["tipo"], "ot_abierta")

    def test_el_warning_aparece_y_se_va_por_el_stream(self):
        self.c.post("/edge/edge-1/lecturas", json=[{"sensor_id": "energia", "valor": "viva"}])
        with self.c.websocket_connect("/ot/ot-1/stream") as ws:
            ws.receive_json()
            self.c.post("/edge/edge-1/lecturas", json=[{"sensor_id": "guarda", "valor": "abierta"}])
            m = [ws.receive_json() for _ in range(3)]
            self.assertEqual(m[1]["evento"]["tipo"], "alerta")
            self.assertEqual(m[2]["calificacion"]["avisos"][0]["nivel"], "error")

            self.c.post("/edge/edge-1/lecturas", json=[{"sensor_id": "guarda", "valor": "cerrada"}])
            m = [ws.receive_json() for _ in range(3)]
            self.assertEqual(m[1]["evento"]["tipo"], "alerta_resuelta")
            self.assertEqual(m[2]["calificacion"]["avisos"], [])
        self.assertEqual(self.c.get("/ot/ot-1/alertas").json(), [])

    def test_entra_video_por_websocket_y_sale_por_http(self):
        jpeg = b"\xff\xd8" + b"cuadro" + b"\xff\xd9"
        with self.c.websocket_connect("/edge/edge-1/video") as ws:
            ws.send_bytes(jpeg)
            ws.send_bytes(b"no es jpeg")
            self.assertIn("JPEG", ws.receive_json()["error"])
        self.assertEqual(self.c.get("/edge/edge-1/cuadro.jpg").content, jpeg)
        self.assertTrue(self.c.get("/edge/edge-1/video").json()["hay_video"])
        r = self.c.get("/edge/edge-1/video.mjpg?limite=1")
        self.assertIn(jpeg, r.content)
        self.assertIn("multipart/x-mixed-replace", r.headers["content-type"])
        snap_video = None
        with self.c.websocket_connect("/ot/ot-1/stream") as ws:
            snap_video = ws.receive_json()["video"]
        self.assertEqual(snap_video["url"], "/edge/edge-1/video.mjpg")

    def test_entra_un_cuadro_por_post_y_uno_malo_es_422(self):
        jpeg = b"\xff\xd8" + b"esp32" + b"\xff\xd9"
        self.assertEqual(self.c.post("/edge/edge-2/cuadro", content=jpeg).json()["cuadro"], 1)
        self.assertEqual(self.c.post("/edge/edge-2/cuadro", content=b"texto").status_code, 422)
        self.assertEqual(self.c.get("/edge/edge-9/cuadro.jpg").status_code, 404)

    def test_las_paginas_de_camara_y_monitor_se_sirven(self):
        self.assertIn("getUserMedia", self.c.get("/camara").text)
        self.assertIn("avisos", self.c.get("/monitor").text)

    def test_una_ot_que_no_existe_cierra_el_stream(self):
        from starlette.websockets import WebSocketDisconnect

        with self.assertRaises(WebSocketDisconnect):
            with self.c.websocket_connect("/ot/ot-99/stream") as ws:
                ws.receive_json()


if __name__ == "__main__":
    unittest.main()
