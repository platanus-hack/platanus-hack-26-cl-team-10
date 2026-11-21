"""Capa 3: el juez de cámara con Claude, sin red (cliente falso).

Correr:  python3 -m unittest discover tests
"""

import base64
import os
import unittest
from types import SimpleNamespace
from unittest import mock

from app import verificacion

JPEG = b"\xff\xd8cuadro\xff\xd9"


class ClienteFalso:
    def __init__(self, texto, stop_reason="end_turn"):
        self.pedidos = []
        respuesta = SimpleNamespace(stop_reason=stop_reason,
                                    content=[SimpleNamespace(type="thinking", thinking=""),
                                             SimpleNamespace(type="text", text=texto)])
        self.messages = SimpleNamespace(create=lambda **kw: self.pedidos.append(kw) or respuesta)


class JuezClaude(unittest.TestCase):
    def test_manda_la_foto_y_la_pregunta_y_lee_el_json(self):
        c = ClienteFalso('{"respuesta": true, "confianza": 0.87}')
        self.assertEqual(verificacion.preguntar_claude("¿Hay un mouse?", JPEG, c), (True, 0.87))
        p = c.pedidos[0]
        imagen, texto = p["messages"][0]["content"]
        self.assertEqual(base64.b64decode(imagen["source"]["data"]), JPEG)
        self.assertEqual(imagen["source"]["media_type"], "image/jpeg")
        self.assertEqual(texto["text"], "¿Hay un mouse?")
        self.assertEqual(p["model"], "claude-haiku-5-5")
        self.assertEqual(p["output_config"]["format"]["type"], "json_schema")

    def test_con_foto_de_antes_manda_las_dos_rotuladas_y_en_orden(self):
        c = ClienteFalso('{"respuesta": true, "confianza": 0.8}')
        self.assertEqual(verificacion.preguntar_claude("¿La reemplazó?", JPEG, c, antes=b"antes"), (True, 0.8))
        r1, antes, r2, ahora, pregunta = c.pedidos[0]["messages"][0]["content"]
        self.assertEqual((r1["text"], r2["text"], pregunta["text"]), ("Foto 1, de antes:", "Foto 2, de ahora:", "¿La reemplazó?"))
        self.assertEqual([base64.b64decode(f["source"]["data"]) for f in (antes, ahora)], [b"antes", JPEG])

    def test_la_confianza_se_acota_entre_0_y_1(self):
        c = ClienteFalso('{"respuesta": false, "confianza": 7}')
        self.assertEqual(verificacion.preguntar_claude("p", JPEG, c), (False, 1.0))

    def test_una_negativa_o_un_corte_no_verifica(self):
        for motivo in ("refusal", "max_tokens"):
            with self.subTest(motivo=motivo):
                self.assertEqual(verificacion.preguntar_claude("p", JPEG, ClienteFalso("", motivo)), (False, 0.0))

    def test_si_el_vlm_falla_no_verifica(self):
        with mock.patch.dict(os.environ, {"ANTHROPIC_API_KEY": "prueba"}), \
                mock.patch.object(verificacion, "preguntar_claude", side_effect=TimeoutError):
            self.assertEqual(verificacion.juez_camara("p", JPEG), (False, 0.0))

    def test_agotado_el_tope_de_llamadas_el_juez_no_verifica_ni_llama(self):
        with mock.patch.dict(os.environ, {"ANTHROPIC_API_KEY": "prueba"}), \
                mock.patch.object(verificacion, "_llamadas", 0), \
                mock.patch.object(verificacion, "LLAMADAS_MAX", 2), \
                mock.patch.object(verificacion, "preguntar_claude", return_value=(True, 0.9)) as vlm:
            respuestas = [verificacion.juez_camara("p", JPEG) for _ in range(3)]
        self.assertEqual(respuestas, [(True, 0.9), (True, 0.9), (False, 0.0)])
        self.assertEqual(vlm.call_count, 2)


class SinVLM(unittest.TestCase):
    def test_sin_key_o_sin_cuadro_queda_el_stub_de_ensayo(self):
        with mock.patch.dict(os.environ, {}, clear=True):
            self.assertEqual(verificacion.juez_camara("p", JPEG), (True, 0.55))
        with mock.patch.dict(os.environ, {"ANTHROPIC_API_KEY": "prueba"}):
            self.assertEqual(verificacion.juez_camara("p", None), (True, 0.55))


if __name__ == "__main__":
    unittest.main()
