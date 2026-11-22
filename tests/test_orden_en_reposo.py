"""El orden invertido se avisa por algo que cambió, no por el estado en que ya estaba el equipo.

Correr:  uv run --with httpx python -m unittest tests.test_orden_en_reposo
En las 10 corridas LOTO de la VM del 2026-11-21, «equipo = frio» llegaba cada 5 s desde el
reposo y, con «Poner el dispositivo de bloqueo» abierto, sonaba ORDEN INVERTIDO en cada una.
"""

import unittest

from app import db
from app.bus import Bus
from app.protocolos import DATOS, desde_json
from app.servicios import Servicios


class LotoConElEquipoFrioDesdeElInicio(unittest.TestCase):
    def setUp(self):
        self.cx = db.conectar(":memory:")
        pauta = desde_json(DATOS / "pauta-loto.json")
        db.guardar_pauta(self.cx, pauta)
        db.abrir_ot(self.cx, "ot-1", pauta, "supervisor:X")
        self.s = Servicios(self.cx, Bus())
        self.s.iniciar_sesion("ot-1", "edge-1", "operario:A")

    def tearDown(self):
        self.cx.close()

    def leer(self, sensor, valor):
        return self.s.recibir_lectura("edge-1", sensor, valor)

    def ordenes(self):
        return [k for k in self.s.alertas_activas("ot-1") if k.startswith("orden:")]

    def test_la_lectura_repetida_del_reposo_no_suena_mientras_el_bloqueo_sigue_abierto(self):
        self.leer("equipo", "frio")
        self.leer("operario", "presente")  # cierra l1; el paso actual es l2, el bloqueo, un control crítico
        for _ in range(5):
            self.leer("equipo", "frio")
        self.assertEqual(self.ordenes(), [])

    def test_si_el_valor_cambia_fuera_de_orden_si_suena(self):
        self.leer("equipo", "caliente")
        self.leer("operario", "presente")
        self.leer("equipo", "frio")
        self.assertEqual(self.ordenes(), ["orden:l3"])


if __name__ == "__main__":
    unittest.main()
