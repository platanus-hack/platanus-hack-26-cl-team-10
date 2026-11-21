"""El video del edge: entra cuadro a cuadro, se guarda poco y sale rápido.

La cámara del demo es el celular del operario (FLUJO, paso 1): la página
app/estatico/camara.html toma la cámara del navegador y manda JPEG por un
WebSocket. Una ESP32-CAM puede mandar lo mismo por POST.

Por cada edge se guardan solo los últimos segundos, en memoria. Sirven para:
- que el juez de cámara mire el cuadro actual cuando el paso es de cámara;
- que la UI vea el video en vivo (MJPEG, un <img> que apunta a una URL);
- que el cuadro que cerró un paso quede como evidencia en disco.

El video va por su propio canal y nunca por el WebSocket de la OT: una ráfaga de
cuadros no puede atrasar una alerta.

Junto al video llegan las detecciones del modelo del edge (qué objeto, confianza y
caja normalizada 0-1). Se guardan igual que los cuadros: los últimos segundos, en
memoria, cada una apuntando al último cuadro que había cuando llegó.
"""

from __future__ import annotations

import threading
import time
from collections import defaultdict, deque
from dataclasses import dataclass
from pathlib import Path

JPEG_INICIO = b"\xff\xd8"
TAMANO_MAX = 2_000_000
SEGUNDOS_GUARDADOS = 10
FPS_MAX = 20
# El edge_id lo elige quien manda: sin tope, cada id nuevo reserva su propio buffer de cuadros.
EDGES_MAX = 8
OBJETOS_MAX = 50
TEXTO_MAX = 64  # largo máximo de clase y modelo: lo que entra se reenvía a la UI
RAIZ = Path(__file__).resolve().parent.parent
EVIDENCIAS = RAIZ / "datos" / "evidencias"


class CuadroInvalido(ValueError):
    pass


class DeteccionInvalida(ValueError):
    pass


def validar_detecciones(d: dict) -> dict:
    """Lo que manda el edge, revisado campo por campo: es entrada de afuera."""
    objetos = d.get("objetos")
    if not isinstance(objetos, list) or len(objetos) > OBJETOS_MAX:
        raise DeteccionInvalida(f"'objetos' debe ser una lista de hasta {OBJETOS_MAX}")
    limpios = []
    for o in objetos:
        try:
            clase, conf, caja = str(o["clase"])[:TEXTO_MAX], float(o["conf"]), [float(v) for v in o["caja"]]
        except (KeyError, TypeError, ValueError) as e:
            raise DeteccionInvalida(f"objeto mal formado: {str(o)[:200]}") from e
        if not 0 <= conf <= 1 or len(caja) != 4 or not all(0 <= v <= 1 for v in caja):
            raise DeteccionInvalida(f"conf y caja van entre 0 y 1 (caja = x1, y1, x2, y2): {str(o)[:200]}")
        limpios.append({"clase": clase, "conf": round(conf, 3), "caja": [round(v, 4) for v in caja]})
    try:
        ts_edge = float(d["ts"]) if d.get("ts") is not None else None
    except (TypeError, ValueError) as e:
        raise DeteccionInvalida("'ts' debe ser un número (epoch en segundos)") from e
    return {"modelo": str(d.get("modelo", ""))[:TEXTO_MAX], "ts_edge": ts_edge, "objetos": limpios}


@dataclass(frozen=True, slots=True)
class Cuadro:
    n: int
    ts: float
    jpeg: bytes


class Video:
    def __init__(self, carpeta_evidencias: Path | None = None) -> None:
        self._cuadros: dict[str, deque[Cuadro]] = defaultdict(
            lambda: deque(maxlen=SEGUNDOS_GUARDADOS * FPS_MAX)
        )
        self._contador: dict[str, int] = defaultdict(int)
        self._detecciones: dict[str, deque[dict]] = defaultdict(
            lambda: deque(maxlen=SEGUNDOS_GUARDADOS * FPS_MAX)
        )
        self._visto: dict[str, float] = {}
        self._lock = threading.Lock()
        self.carpeta = carpeta_evidencias or EVIDENCIAS

    def _anotar(self, edge_id: str) -> None:
        """Con el lock tomado. Si llega un edge nuevo y no cabe, sale el que lleva más tiempo callado."""
        if edge_id not in self._visto and len(self._visto) >= EDGES_MAX:
            callado = min(self._visto, key=self._visto.__getitem__)
            for de in (self._visto, self._cuadros, self._detecciones, self._contador):
                de.pop(callado, None)
        self._visto[edge_id] = time.monotonic()

    def recibir_detecciones(self, edge_id: str, d: dict) -> dict:
        det = validar_detecciones(d)
        with self._lock:
            self._anotar(edge_id)
            det["ts"] = time.time()
            det["cuadro"] = self._contador[edge_id]  # el último cuadro que había al llegar
            self._detecciones[edge_id].append(det)
        return det

    def ultimas_detecciones(self, edge_id: str) -> dict | None:
        with self._lock:
            cola = self._detecciones.get(edge_id)
            return cola[-1] if cola else None

    def detecciones_recientes(self, edge_id: str, segundos: float) -> list[dict]:
        """Las detecciones del último tramo, de la más vieja a la más nueva."""
        desde = time.time() - segundos
        with self._lock:
            return [d for d in self._detecciones.get(edge_id, ()) if d["ts"] >= desde]

    def recibir(self, edge_id: str, jpeg: bytes) -> Cuadro:
        if not jpeg.startswith(JPEG_INICIO):
            raise CuadroInvalido("el cuadro no es un JPEG")
        if len(jpeg) > TAMANO_MAX:
            raise CuadroInvalido(f"el cuadro pesa {len(jpeg)} bytes; el máximo es {TAMANO_MAX}")
        with self._lock:
            self._anotar(edge_id)
            self._contador[edge_id] += 1
            cuadro = Cuadro(self._contador[edge_id], time.time(), jpeg)
            self._cuadros[edge_id].append(cuadro)
        return cuadro

    def edges(self) -> list[str]:
        """Los edges que mandaron video alguna vez desde que arrancó el servidor."""
        with self._lock:
            return list(self._cuadros)

    def ultimo(self, edge_id: str) -> Cuadro | None:
        with self._lock:
            cola = self._cuadros.get(edge_id)
            return cola[-1] if cola else None

    def estado(self, edge_id: str) -> dict:
        """Si hay video y qué tan fresco es: sin cuadros recientes el juez no tiene qué mirar."""
        c = self.ultimo(edge_id)
        if c is None:
            return {"edge_id": edge_id, "hay_video": False}
        with self._lock:
            cola = list(self._cuadros[edge_id])
        ventana = [x for x in cola if x.ts >= c.ts - 2]
        fps = (len(ventana) - 1) / (c.ts - ventana[0].ts) if len(ventana) > 1 and c.ts > ventana[0].ts else 0.0
        return {
            "edge_id": edge_id,
            "hay_video": True,
            "cuadros": c.n,
            "edad_s": round(time.time() - c.ts, 1),
            "fps": round(fps, 1),
        }

    def guardar_evidencia(self, cuadro: Cuadro, nombre: str) -> str:
        """El cuadro que cerró un paso queda en disco; el evento guarda su ruta."""
        self.carpeta.mkdir(parents=True, exist_ok=True)
        ruta = self.carpeta / f"{nombre}.jpg"
        ruta.write_bytes(cuadro.jpeg)
        return str(ruta.relative_to(RAIZ)) if ruta.is_relative_to(RAIZ) else str(ruta)
