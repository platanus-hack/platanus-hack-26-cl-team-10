"""La latencia de capa 1: de la lectura en el edge a la alerta escrita (`evidencia.lectura`).

Correr:  uv run --with httpx python -m unittest tests.test_latencia
"""

import importlib.util
import unittest
from datetime import UTC, datetime, timedelta

from app import db
from app.protocolos import DATOS

TIENE_HTTPX = importlib.util.find_spec("httpx") is not None and importlib.util.find_spec("fastapi") is not None


@unittest.skipUnless(TIENE_HTTPX, "falta httpx o fastapi")
class LaLecturaTraeSuHora(unittest.TestCase):
    def setUp(self):
        from fastapi.testclient import TestClient

        from app import api
        from app.servicios import Servicios

        api.cx = db.conectar(":memory:")
        api.servicios = Servicios(api.cx)
        self.c = TestClient(api.app)
        self.c.post("/pauta/demo?pauta=polin")
        self.c.post("/ot/ot-1/abrir?pauta_id=pauta-polin-estacion")
        self.c.post("/ot/ot-1/sesion", json={"edge_id": "edge-1", "operario": "operario:1"})

    def leer(self, **cuerpo):
        return self.c.post("/edge/edge-1/lecturas", json=[cuerpo]).json()[0]["eventos"]

    def test_la_alerta_de_seguridad_guarda_cuanto_tardo_desde_la_medicion(self):
        self.leer(sensor_id="energia", valor="viva")
        hace = (datetime.now(UTC) - timedelta(milliseconds=250)).isoformat()
        alerta = next(e for e in self.leer(sensor_id="operario", valor="presente", medido_en=hace) if e["tipo"] == "alerta")
        lectura = alerta["evidencia"]["lectura"]
        self.assertEqual(lectura["sensor"], "operario")
        self.assertGreaterEqual(lectura["ms_hasta_el_evento"], 250)
        self.assertLess(lectura["ms_hasta_el_evento"], 5000)
        self.assertLessEqual(lectura["ms_hasta_recibir"], lectura["ms_hasta_el_evento"])

    def test_sin_medido_en_todo_sigue_igual(self):
        self.leer(sensor_id="energia", valor="viva")
        alerta = next(e for e in self.leer(sensor_id="operario", valor="presente") if e["tipo"] == "alerta")
        self.assertNotIn("lectura", alerta["evidencia"])

    def test_una_hora_sin_zona_no_entra(self):
        r = self.c.post("/edge/edge-1/lecturas", json=[{"sensor_id": "energia", "valor": "viva", "medido_en": "2026-11-21T10:00:00"}])
        self.assertEqual(r.status_code, 422)


if __name__ == "__main__":
    unittest.main()
