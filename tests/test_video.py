"""El video del edge, sin HTTP.

Correr:  python3 -m unittest discover tests
"""

import tempfile
import unittest
from pathlib import Path

from app.video import (FPS_MAX, SEGUNDOS_GUARDADOS, TAMANO_MAX, CuadroInvalido,
                       DeteccionInvalida, Video, validar_detecciones)

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
        self.assertEqual(len(self.v._cuadros["edge-1"]), SEGUNDOS_GUARDADOS * FPS_MAX)

    def test_la_evidencia_queda_en_disco(self):
        c = self.v.recibir("edge-1", JPEG)
        ruta = self.v.guardar_evidencia(c, "ot-1-p3-1")
        self.assertEqual(Path(ruta).read_bytes(), JPEG)


DET = {"tipo": "detecciones", "modelo": "yolov8s-worldv2", "ts": 1.0,
       "objetos": [{"clase": "mouse", "conf": 0.93, "caja": [0.27, 0.65, 0.43, 0.91]}]}


class EntranDetecciones(unittest.TestCase):
    def setUp(self):
        self.v = Video(Path(tempfile.gettempdir()))

    def test_la_deteccion_apunta_al_ultimo_cuadro(self):
        self.v.recibir("edge-1", JPEG)
        self.v.recibir("edge-1", JPEG)
        d = self.v.recibir_detecciones("edge-1", DET)
        self.assertEqual(d["cuadro"], 2)
        self.assertEqual(d["objetos"][0]["clase"], "mouse")
        self.assertEqual(self.v.ultimas_detecciones("edge-1"), d)

    def test_los_textos_largos_se_recortan(self):
        d = validar_detecciones({"modelo": "m" * 500, "objetos": [{"clase": "x" * 500, "conf": 0.5, "caja": [0, 0, 1, 1]}]})
        self.assertEqual(len(d["modelo"]), 64)
        self.assertEqual(len(d["objetos"][0]["clase"]), 64)

    def test_una_lista_vacia_tambien_es_informacion(self):
        self.assertEqual(self.v.recibir_detecciones("edge-1", {"objetos": []})["objetos"], [])

    def test_lo_mal_formado_se_rechaza(self):
        malos = [{}, {"objetos": "mouse"}, {"objetos": [{"clase": "mouse"}]},
                 {"objetos": [{"clase": "mouse", "conf": 1.5, "caja": [0, 0, 1, 1]}]},
                 {"objetos": [{"clase": "mouse", "conf": 0.9, "caja": [0, 0, 640, 480]}]},
                 {"objetos": [{"clase": "mouse", "conf": 0.9, "caja": [0, 0, 1]}]},
                 {"objetos": [{"clase": "mouse", "conf": float("nan"), "caja": [0, 0, 1, 1]}]},
                 {"objetos": [], "ts": "ayer"}]
        for m in malos:
            with self.subTest(m=m), self.assertRaises(DeteccionInvalida):
                validar_detecciones(m)


if __name__ == "__main__":
    unittest.main()
