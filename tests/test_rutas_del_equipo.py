"""Crear o aprobar pautas y abrir OT sin empresa es del equipo, no del cliente (ADR-0011).

Correr:  uv run --with httpx python -m unittest tests.test_rutas_del_equipo
Con CLAVE_EQUIPO definida, esas rutas piden la cabecera X-Clave-Equipo; sin la variable quedan abiertas, como en local.
"""

import importlib.util
import json
import os
import unittest
from unittest import mock

from app import db
from app.protocolos import DATOS

TIENE_HTTPX = importlib.util.find_spec("httpx") is not None and importlib.util.find_spec("fastapi") is not None


@unittest.skipUnless(TIENE_HTTPX, "falta httpx o fastapi")
class LasRutasQueArmanPautasPidenLaClave(unittest.TestCase):
    def setUp(self):
        from fastapi.testclient import TestClient

        from app import api
        from app.servicios import Servicios

        api.cx = db.conectar(":memory:")
        api.servicios = Servicios(api.cx)
        self.c = TestClient(api.app)
        self.pauta = json.loads((DATOS / "pauta-correa.json").read_text(encoding="utf-8"))

    def pedidos(self, cabeceras):
        return {
            "POST /pauta/demo": self.c.post("/pauta/demo", headers=cabeceras).status_code,
            "POST /pautas": self.c.post("/pautas", json={**self.pauta, "id": "pauta-x"}, headers=cabeceras).status_code,
            "aprobar": self.c.post("/pautas/pauta-x/versiones/1/aprobar", json={"actor": "supervisor:x"},
                                   headers=cabeceras).status_code,
            "abrir": self.c.post(f"/ot/ot-x/abrir?pauta_id={self.pauta['id']}", headers=cabeceras).status_code,
        }

    def test_sin_la_clave_responden_401_y_con_ella_hacen_su_trabajo(self):
        with mock.patch.dict(os.environ, {"CLAVE_EQUIPO": "secreta"}):
            self.assertEqual(set(self.pedidos({}).values()), {401})
            self.assertEqual(self.pedidos({"X-Clave-Equipo": "secreta"}),
                             {"POST /pauta/demo": 200, "POST /pautas": 201, "aprobar": 200, "abrir": 200})

    def test_sin_clave_en_el_servidor_quedan_abiertas_como_en_local(self):
        with mock.patch.dict(os.environ, {}, clear=False):
            os.environ.pop("CLAVE_EQUIPO", None)
            self.assertEqual(self.pedidos({})["POST /pautas"], 201)


if __name__ == "__main__":
    unittest.main()
