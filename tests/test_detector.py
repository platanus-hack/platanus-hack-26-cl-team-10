"""Experimento: detector ONNX en el servidor.

Correr:  uv run python -m unittest tests.test_detector
Sin numpy/opencv se salta. La prueba con el modelo real se salta si no está el .onnx.
"""

import importlib.util
import unittest
from pathlib import Path

TIENE = all(importlib.util.find_spec(m) for m in ("numpy", "cv2"))
MODELO = Path(__file__).resolve().parent.parent / "datos" / "modelos" / "yolo-mouse-pencil-640.onnx"
FOTOS = sorted((Path(__file__).resolve().parent.parent / "edge" / "data" / "frames").glob("*.jpg"))


@unittest.skipUnless(TIENE, "necesita numpy y opencv")
class Postproceso(unittest.TestCase):
    def test_caja_del_lienzo_vuelve_a_la_imagen_original_normalizada(self):
        import numpy as np

        from app.detector import letterbox, postproceso
        img = np.zeros((540, 960, 3), np.uint8)  # 16:9 → relleno arriba y abajo
        _, r, px, py = letterbox(img, 640)
        self.assertEqual((px, py), (0, 140))
        # una detección de "pencil" centrada en la imagen, de 96x54 px originales
        salida = np.zeros((1, 6, 3), np.float32)
        salida[0, :, 0] = [320, 320, 96 * r, 54 * r, 0.1, 0.9]   # la buena
        salida[0, :, 1] = [321, 320, 96 * r, 54 * r, 0.1, 0.8]   # duplicada: la quita el NMS
        salida[0, :, 2] = [100, 100, 10, 10, 0.1, 0.1]           # bajo el piso
        objetos = postproceso(salida, ["mouse", "pencil"], r, px, py, 960, 540)
        self.assertEqual(len(objetos), 1)
        self.assertEqual(objetos[0]["clase"], "pencil")
        self.assertEqual(objetos[0]["caja"], [0.45, 0.45, 0.55, 0.55])

    def test_sin_nada_sobre_el_piso_no_hay_objetos(self):
        import numpy as np

        from app.detector import postproceso
        self.assertEqual(postproceso(np.zeros((1, 6, 10), np.float32), ["a", "b"], 1, 0, 0, 640, 640), [])


class Modos(unittest.TestCase):
    def test_sin_modelo_la_api_igual_parte_en_modo_edge(self):
        import os
        from unittest import mock

        from app.detector import desde_entorno
        with mock.patch.dict(os.environ, {"DETECTOR_ONNX": "/no/existe.onnx"}):
            self.assertIsNone(desde_entorno(servicios=None))
        with mock.patch.dict(os.environ, {"DETECTOR_ONNX": ""}):
            self.assertIsNone(desde_entorno(servicios=None))


@unittest.skipUnless(TIENE and MODELO.exists() and FOTOS and importlib.util.find_spec("onnxruntime"),
                     "necesita el modelo exportado y fotos del colector")
class ModeloReal(unittest.TestCase):
    def test_detecta_con_el_modelo_exportado(self):
        from app.detector import DetectorServidor
        d = DetectorServidor(servicios=None, ruta=str(MODELO))
        self.assertEqual(d.clases, ["mouse", "pencil"])
        objetos = d.detectar(FOTOS[-1].read_bytes())
        for o in objetos:
            self.assertIn(o["clase"], d.clases)
            self.assertTrue(all(0 <= v <= 1 for v in o["caja"]))


if __name__ == "__main__":
    unittest.main()
