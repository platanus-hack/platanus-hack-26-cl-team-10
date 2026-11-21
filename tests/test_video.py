"""El video del edge, sin HTTP.

Correr:  python3 -m unittest discover tests
"""

import tempfile
import unittest
from pathlib import Path

from app.video import TAMANO_MAX, CuadroInvalido, Video

JPEG = b"\xff\xd8" + b"cuadro" + b"\xff\xd9"


class EntraVideo(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.v = Video(Path(self.tmp.name))

    def tearDown(self):
        self.tmp.cleanup()

    def test_sin_cuadros_no_hay_video(self):
        self.assertIsNone(self.v.ultimo("edge-1"))
        self.assertFalse(self.v.estado("edge-1")["hay_video"])

    def test_el_ultimo_cuadro_es_el_que_cuenta(self):
        self.v.recibir("edge-1", JPEG + b"1")
        self.v.recibir("edge-1", JPEG + b"2")
        self.assertEqual(self.v.ultimo("edge-1").jpeg, JPEG + b"2")
        self.assertEqual(self.v.estado("edge-1")["cuadros"], 2)

    def test_cada_edge_tiene_su_video(self):
        self.v.recibir("edge-1", JPEG)
        self.assertIsNone(self.v.ultimo("edge-2"))

    def test_lo_que_no_es_jpeg_se_rechaza(self):
        with self.assertRaises(CuadroInvalido):
            self.v.recibir("edge-1", b"no es una imagen")

    def test_un_cuadro_demasiado_grande_se_rechaza(self):
        with self.assertRaises(CuadroInvalido):
            self.v.recibir("edge-1", b"\xff\xd8" + b"x" * TAMANO_MAX)

    def test_solo_se_guardan_los_ultimos_segundos(self):
        for i in range(500):
            self.v.recibir("edge-1", JPEG)
        self.assertEqual(len(self.v._cuadros["edge-1"]), 100)

    def test_la_evidencia_queda_en_disco(self):
        c = self.v.recibir("edge-1", JPEG)
        ruta = self.v.guardar_evidencia(c, "ot-1-p3-1")
        self.assertEqual(Path(ruta).read_bytes(), JPEG)


if __name__ == "__main__":
    unittest.main()
