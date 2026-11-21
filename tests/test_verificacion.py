"""Capa 3: el juez de cámara con Gemini, sin red (cliente falso).

Correr:  uv run python -m unittest tests.test_verificacion
Sin google-genai instalado se salta, para que `python3 -m unittest discover tests` siga sin dependencias.
"""

import importlib.util
import os
import unittest
from types import SimpleNamespace
from unittest import mock

from app import verificacion

TIENE_GENAI = importlib.util.find_spec("google.genai") is not None
JPEG = b"\xff\xd8cuadro\xff\xd9"


class ClienteFalso:
    def __init__(self, texto):
        self.texto, self.pedidos = texto, []
        self.models = SimpleNamespace(generate_content=self._generar)

    def _generar(self, **kw):
        self.pedidos.append(kw)
        return SimpleNamespace(text=self.texto)


@unittest.skipUnless(TIENE_GENAI, "necesita google-genai")
class JuezGemini(unittest.TestCase):
    def test_manda_la_foto_y_la_pregunta_y_lee_el_json(self):
        c = ClienteFalso('{"respuesta": true, "confianza": 0.87}')
        self.assertEqual(verificacion.preguntar_gemini("¿Hay un mouse?", JPEG, c), (True, 0.87))
        pedido = c.pedidos[0]
        imagen, pregunta = pedido["contents"]
        self.assertEqual(imagen.inline_data.data, JPEG)
        self.assertEqual(imagen.inline_data.mime_type, "image/jpeg")
        self.assertEqual(pregunta, "¿Hay un mouse?")
        self.assertEqual(pedido["config"].response_mime_type, "application/json")
        self.assertEqual(pedido["model"], verificacion.MODELO_POR_DEFECTO)

    def test_la_confianza_se_acota_entre_0_y_1(self):
        self.assertEqual(verificacion.preguntar_gemini("p", JPEG, ClienteFalso('{"respuesta": false, "confianza": 7}')),
                         (False, 1.0))

    def test_si_el_vlm_falla_no_verifica(self):
        with mock.patch.dict(os.environ, {"GEMINI_API_KEY": "prueba"}), \
                mock.patch.object(verificacion, "preguntar_gemini", side_effect=TimeoutError):
            self.assertEqual(verificacion.juez_camara("p", JPEG), (False, 0.0))


class SinVLM(unittest.TestCase):
    def test_sin_key_o_sin_cuadro_queda_el_stub_de_ensayo(self):
        with mock.patch.dict(os.environ, {}, clear=True):
            self.assertEqual(verificacion.juez_camara("p", JPEG), (True, 0.55))
        with mock.patch.dict(os.environ, {"GEMINI_API_KEY": "prueba"}):
            self.assertEqual(verificacion.juez_camara("p", None), (True, 0.55))


if __name__ == "__main__":
    unittest.main()
