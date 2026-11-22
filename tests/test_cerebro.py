"""El relevo y las preguntas con un modelo: el código comprueba lo que cita (cliente falso, sin red).

Correr:  python3 -m unittest tests.test_cerebro
"""

import json
import unittest
from types import SimpleNamespace

from app import cerebro
from app.contratos import Estado, Evento, TipoEvento
from app.protocolos import desde_json

PAUTA = desde_json()


class ClienteFalso:
    def __init__(self, salida: dict, stop_reason: str = "end_turn"):
        self.pedidos: list[dict] = []
        r = SimpleNamespace(stop_reason=stop_reason, content=[SimpleNamespace(type="text", text=json.dumps(salida))])
        self.beta = SimpleNamespace(messages=SimpleNamespace(create=lambda **kw: self.pedidos.append(kw) or r))


def ev(i, tipo, paso=None, estado=None, detalle="", evidencia=None):
    return Evento(ot_id="ot-1", tipo=tipo, ts=f"2026-11-21T10:00:{i:02d}+00:00", actor="sistema", detalle=detalle,
                  id=i, paso_id=paso, estado=estado, evidencia=evidencia)


EVENTOS = [
    ev(1, TipoEvento.OT_ABIERTA, detalle="OT abierta"),
    ev(2, TipoEvento.VEREDICTO, "p1", Estado.VERIFICADO, "energia = cortada", {"tipo": "sensor", "id": "energia"}),
    ev(3, TipoEvento.VEREDICTO, "p2", Estado.EN_CONFLICTO, "declaró hecho y el sensor no", {"tipo": "sensor"}),
    ev(4, TipoEvento.ALERTA, detalle="GUARDA ABIERTA CON ENERGÍA VIVA"),
]
ESTADO = cerebro.estado_de_ot(PAUTA, EVENTOS)


class ElRelevo(unittest.TestCase):
    def test_usa_lo_que_redacta_el_modelo_si_cita_eventos_de_la_ot(self):
        c = ClienteFalso({"frases": [
            {"texto": "Se cortó la energía.", "eventos": [2]},
            {"texto": "El bloqueo quedó en conflicto y sonó la alerta de guarda.", "eventos": [3, 4]},
        ]})
        texto, ev_ = cerebro.redactar_resumen(ESTADO, EVENTOS, c)
        self.assertEqual(texto, "Se cortó la energía. [#2] El bloqueo quedó en conflicto y sonó la alerta de guarda. [#3, #4]")
        self.assertEqual(ev_["redactado_por"], cerebro.MODELO_POR_DEFECTO)
        self.assertIn('"id": 4', c.pedidos[0]["messages"][0]["content"])  # recibe la bitácora completa

    def test_si_cita_un_evento_que_no_existe_queda_el_del_codigo(self):
        c = ClienteFalso({"frases": [{"texto": "Todo listo.", "eventos": [2, 3, 4, 99]}]})
        texto, ev_ = cerebro.redactar_resumen(ESTADO, EVENTOS, c)
        self.assertEqual(texto, cerebro.resumen_determinista(ESTADO, EVENTOS))
        self.assertEqual(ev_["redactado_por"], "codigo")

    def test_si_calla_un_paso_en_conflicto_queda_el_del_codigo(self):
        c = ClienteFalso({"frases": [{"texto": "Se cortó la energía y sonó una alerta.", "eventos": [2, 4]}]})
        self.assertEqual(cerebro.redactar_resumen(ESTADO, EVENTOS, c)[1]["redactado_por"], "codigo")

    def test_si_calla_las_alertas_queda_el_del_codigo(self):
        c = ClienteFalso({"frases": [{"texto": "p2 quedó en conflicto.", "eventos": [3]}]})
        self.assertEqual(cerebro.redactar_resumen(ESTADO, EVENTOS, c)[1]["redactado_por"], "codigo")

    def test_una_frase_sin_cita_no_pasa(self):
        c = ClienteFalso({"frases": [{"texto": "Conflicto y alerta.", "eventos": [3, 4]}, {"texto": "Ánimo.", "eventos": []}]})
        self.assertEqual(cerebro.redactar_resumen(ESTADO, EVENTOS, c)[1]["redactado_por"], "codigo")

    def test_si_el_modelo_se_niega_queda_el_del_codigo(self):
        c = ClienteFalso({"frases": []}, stop_reason="refusal")
        self.assertEqual(cerebro.redactar_resumen(ESTADO, EVENTOS, c)[1]["redactado_por"], "codigo")

    def test_sin_key_no_llama_a_nadie(self):
        texto, ev_ = cerebro.redactar_resumen(ESTADO, EVENTOS)
        self.assertEqual((texto, ev_), (cerebro.resumen_determinista(ESTADO, EVENTOS), {"redactado_por": "codigo"}))


class LasPreguntas(unittest.TestCase):
    def test_la_evidencia_y_la_hora_salen_de_la_bitacora_no_del_modelo(self):
        c = ClienteFalso({"respuesta": "Sí, la energía se cortó.", "evento": 2})
        r = cerebro.responder("¿se cortó la energía?", PAUTA, EVENTOS, c)
        self.assertEqual((r["evento"], r["ts"], r["evidencia"]), (2, EVENTOS[1].ts, EVENTOS[1].evidencia))

    def test_si_nombra_un_evento_que_no_existe_responde_el_codigo(self):
        c = ClienteFalso({"respuesta": "Sí.", "evento": 42})
        r = cerebro.responder("¿se cortó la energía?", PAUTA, EVENTOS, c)
        self.assertNotIn("redactado_por", r)


if __name__ == "__main__":
    unittest.main()
