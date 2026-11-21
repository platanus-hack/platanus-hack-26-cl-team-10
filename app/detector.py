"""Experimento: el detector corre en el servidor en vez de en el edge.

YOLO-World exportado a ONNX con las clases ya fijadas (edge/exportar_onnx.py), así
el servidor no necesita PyTorch ni CLIP: solo onnxruntime + OpenCV. Un hilo toma el
último cuadro de cada edge, detecta y entrega el resultado por el mismo camino que
las detecciones que manda el edge (servicios.recibir_detecciones). El resto del
sistema no se entera de dónde corrió el modelo.

Es el modo de detección por defecto en la VM (deploy/vm/instalar.sh pone DETECTOR_ONNX).
El otro modo, YOLO en el edge (edge.py --deteccion edge), sigue disponible: sin
DETECTOR_ONNX el servidor no detecta y usa lo que manda el edge. Con el detector activo,
las detecciones que mande un edge se ignoran, para no mezclar dos modelos.
"""

from __future__ import annotations

import ast
import logging
import os
import threading
import time

import cv2
import numpy as np

log = logging.getLogger(__name__)

CONF_MIN = 0.25    # el mismo piso con que el edge manda detecciones
NMS_IOU = 0.5
CUADRO_VIEJO_S = 2.0  # un edge que dejó de mandar video no se sigue procesando


def letterbox(img: np.ndarray, lado: int) -> tuple[np.ndarray, float, int, int]:
    """BGR HxWx3 → tensor 1x3xLxL en [0, 1], conservando proporciones (relleno gris)."""
    h, w = img.shape[:2]
    r = lado / max(h, w)
    nh, nw = round(h * r), round(w * r)
    py, px = (lado - nh) // 2, (lado - nw) // 2
    lienzo = np.full((lado, lado, 3), 114, np.uint8)
    lienzo[py:py + nh, px:px + nw] = cv2.resize(img, (nw, nh))
    x = lienzo[:, :, ::-1].transpose(2, 0, 1)[None].astype(np.float32) / 255
    return np.ascontiguousarray(x), r, px, py


def postproceso(salida: np.ndarray, clases: list[str], r: float, px: int, py: int,
                w: int, h: int, conf_min: float = CONF_MIN) -> list[dict]:
    """Salida YOLOv8 [1, 4+nc, N] (cx, cy, ancho, alto en píxeles del lienzo) → objetos
    con caja normalizada 0-1 sobre la imagen original, tras NMS por clase."""
    p = salida[0].T
    puntajes = p[:, 4:]
    cls, conf = puntajes.argmax(1), puntajes.max(1)
    m = conf >= conf_min
    p, cls, conf = p[m], cls[m], conf[m]
    if not len(p):
        return []
    x1 = (p[:, 0] - p[:, 2] / 2 - px) / r
    y1 = (p[:, 1] - p[:, 3] / 2 - py) / r
    x2 = (p[:, 0] + p[:, 2] / 2 - px) / r
    y2 = (p[:, 1] + p[:, 3] / 2 - py) / r
    cajas = np.stack([x1, y1, x2 - x1, y2 - y1], 1).tolist()
    idx = cv2.dnn.NMSBoxesBatched(cajas, conf.tolist(), cls.tolist(), conf_min, NMS_IOU)
    return [{"clase": clases[int(cls[i])], "conf": round(float(conf[i]), 3),
             "caja": [round(float(np.clip(v, 0, 1)), 4) for v in (x1[i] / w, y1[i] / h, x2[i] / w, y2[i] / h)]}
            for i in np.array(idx).flatten()]


class DetectorServidor:
    def __init__(self, servicios, ruta: str, hilos: int = 2) -> None:
        import onnxruntime as ort

        opciones = ort.SessionOptions()
        opciones.intra_op_num_threads = hilos
        self.sesion = ort.InferenceSession(ruta, opciones, providers=["CPUExecutionProvider"])
        self.entrada = self.sesion.get_inputs()[0].name
        self.lado = self.sesion.get_inputs()[0].shape[2]
        nombres = ast.literal_eval(self.sesion.get_modelmeta().custom_metadata_map["names"])
        self.clases = [nombres[i] for i in sorted(nombres)]
        self.modelo = "servidor:" + os.path.basename(ruta)
        self.servicios = servicios
        self.ms_ultimo = 0.0

    def detectar(self, jpeg: bytes) -> list[dict]:
        img = cv2.imdecode(np.frombuffer(jpeg, np.uint8), cv2.IMREAD_COLOR)
        if img is None:
            return []
        x, r, px, py = letterbox(img, self.lado)
        salida = self.sesion.run(None, {self.entrada: x})[0]
        return postproceso(salida, self.clases, r, px, py, img.shape[1], img.shape[0])

    def iniciar(self) -> None:
        threading.Thread(target=self._bucle, name="detector-servidor", daemon=True).start()
        log.info("detector en el servidor: %s, clases %s", self.modelo, self.clases)

    def _bucle(self) -> None:
        vistos: dict[str, int] = {}
        while True:
            hubo = False
            for edge in self.servicios.video.edges():
                c = self.servicios.video.ultimo(edge)
                if c is None or vistos.get(edge) == c.n or time.time() - c.ts > CUADRO_VIEJO_S:
                    continue
                vistos[edge], hubo = c.n, True
                try:
                    t = time.time()
                    objetos = self.detectar(c.jpeg)
                    self.ms_ultimo = (time.time() - t) * 1000
                    self.servicios.recibir_detecciones(edge, {"tipo": "detecciones", "modelo": self.modelo,
                                                              "ts": c.ts, "objetos": objetos})
                except Exception:  # noqa: BLE001 - un cuadro malo no debe matar el hilo
                    log.exception("el detector del servidor falló con un cuadro de %s", edge)
            if not hubo:
                time.sleep(0.02)


def desde_entorno(servicios) -> DetectorServidor | None:
    ruta = os.environ.get("DETECTOR_ONNX")
    if not ruta:
        return None
    if not os.path.exists(ruta):  # sin el modelo la API igual parte: queda el modo edge
        log.warning("DETECTOR_ONNX=%s no existe: detección en el servidor apagada", ruta)
        return None
    d = DetectorServidor(servicios, ruta, int(os.environ.get("DETECTOR_HILOS", "2")))
    d.iniciar()
    return d
