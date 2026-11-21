"""GET /voz: el aviso en voz con ElevenLabs, guardado en disco. Necesita httpx.

Correr:  uv run --with httpx python -m unittest tests.test_voz
"""

import importlib.util
import os
import tempfile
import unittest
import urllib.error
from pathlib import Path
from unittest import mock

TIENE_HTTPX = importlib.util.find_spec("httpx") is not None and importlib.util.find_spec("fastapi") is not None


@unittest.skipUnless(TIENE_HTTPX, "necesita fastapi y httpx")
class Voz(unittest.TestCase):
    def setUp(self):
        from fastapi import FastAPI
        from fastapi.testclient import TestClient

        from app import voz

        self.voz = voz
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.addCleanup(mock.patch.object(voz, "CARPETA", Path(self.tmp.name)).stop)
        mock.patch.object(voz, "CARPETA", Path(self.tmp.name)).start()

        self.llamadas = []

        def pedir_audio(texto, voice_id, llave):
            self.llamadas.append((texto, voice_id, llave))
            return b"ID3audio"

        patch = mock.patch.object(voz, "pedir_audio", side_effect=pedir_audio)
        patch.start()
        self.addCleanup(patch.stop)

        entorno = mock.patch.dict(os.environ, {"ELEVENLABS_API_KEY": "llave"}, clear=False)
        entorno.start()
        self.addCleanup(entorno.stop)
        os.environ.pop("ELEVENLABS_VOICE_ID", None)

        app = FastAPI()
        app.include_router(voz.router)
        self.c = TestClient(app)

    def test_sin_llave_responde_503(self):
        del os.environ["ELEVENLABS_API_KEY"]
        r = self.c.get("/voz", params={"texto": "Oye"})
        self.assertEqual(r.status_code, 503)
        self.assertIn("ELEVENLABS_API_KEY", r.json()["voz"])
        self.assertEqual(self.llamadas, [])

    def test_texto_vacio_o_largo_responde_422(self):
        self.assertEqual(self.c.get("/voz", params={"texto": "   "}).status_code, 422)
        self.assertEqual(self.c.get("/voz", params={"texto": "x" * 301}).status_code, 422)
        self.assertEqual(self.llamadas, [])

    def test_devuelve_audio_y_lo_guarda_en_cache(self):
        r = self.c.get("/voz", params={"texto": "Oye, el candado no aparece puesto"})
        self.assertEqual(r.status_code, 200)
        self.assertEqual(r.headers["content-type"], "audio/mpeg")
        self.assertEqual(r.content, b"ID3audio")
        otra = self.c.get("/voz", params={"texto": "Oye, el candado no aparece puesto"})
        self.assertEqual(otra.content, b"ID3audio")
        self.assertEqual(len(self.llamadas), 1)
        self.assertEqual(len(list(Path(self.tmp.name).glob("*.mp3"))), 1)

    def test_usa_la_voz_por_defecto_sin_voice_id(self):
        self.c.get("/voz", params={"texto": "Oye"})
        self.assertEqual(self.llamadas[0], ("Oye", self.voz.VOZ_POR_DEFECTO, "llave"))

    def test_usa_la_voz_configurada(self):
        os.environ["ELEVENLABS_VOICE_ID"] = "voz-chilena"
        self.c.get("/voz", params={"texto": "Oye"})
        self.assertEqual(self.llamadas[0][1], "voz-chilena")

    def test_error_de_elevenlabs_responde_502(self):
        error = urllib.error.HTTPError("https://api.elevenlabs.io", 401, "Unauthorized", {}, None)
        with mock.patch.object(self.voz, "pedir_audio", side_effect=error):
            r = self.c.get("/voz", params={"texto": "Oye"})
        self.assertEqual(r.status_code, 502)
        self.assertEqual(r.json()["voz"], "ElevenLabs respondió 401")
        self.assertEqual(list(Path(self.tmp.name).glob("*.mp3")), [])

    def test_tope_de_audios_nuevos_por_proceso(self):
        with mock.patch.object(self.voz, "MAX_GENERACIONES", 2), mock.patch.object(self.voz, "_generadas", 0):
            self.assertEqual(self.c.get("/voz", params={"texto": "uno"}).status_code, 200)
            self.assertEqual(self.c.get("/voz", params={"texto": "dos"}).status_code, 200)
            r = self.c.get("/voz", params={"texto": "tres"})
            self.assertEqual(r.status_code, 503)
            self.assertIn("máximo", r.json()["voz"])
            # Lo que ya está guardado se sigue sirviendo.
            self.assertEqual(self.c.get("/voz", params={"texto": "uno"}).status_code, 200)
        self.assertEqual(len(self.llamadas), 2)

    def test_sin_red_responde_502(self):
        with mock.patch.object(self.voz, "pedir_audio", side_effect=urllib.error.URLError("sin red")):
            r = self.c.get("/voz", params={"texto": "Oye"})
        self.assertEqual(r.status_code, 502)
        self.assertEqual(r.json()["voz"], "no se pudo llegar a ElevenLabs")


@unittest.skipUnless(TIENE_HTTPX, "necesita fastapi y httpx")
class LaApiMontaVoz(unittest.TestCase):
    def test_la_api_sirve_voz(self):
        from fastapi.testclient import TestClient

        from app import api

        r = TestClient(api.app).get("/voz", params={"texto": "   "})
        self.assertEqual(r.status_code, 422)
        self.assertIn("voz", r.json())


if __name__ == "__main__":
    unittest.main()
