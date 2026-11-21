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
FPS_MAX = 10
RAIZ = Path(__file__).resolve().parent.parent
EVIDENCIAS = RAIZ / "datos" / "evidencias"


class CuadroInvalido(ValueError):
    pass


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
        self._lock = threading.Lock()
        self.carpeta = carpeta_evidencias or EVIDENCIAS

    def recibir(self, edge_id: str, jpeg: bytes) -> Cuadro:
        if not jpeg.startswith(JPEG_INICIO):
            raise CuadroInvalido("el cuadro no es un JPEG")
        if len(jpeg) > TAMANO_MAX:
            raise CuadroInvalido(f"el cuadro pesa {len(jpeg)} bytes; el máximo es {TAMANO_MAX}")
        with self._lock:
            self._contador[edge_id] += 1
            cuadro = Cuadro(self._contador[edge_id], time.time(), jpeg)
            self._cuadros[edge_id].append(cuadro)
        return cuadro

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
