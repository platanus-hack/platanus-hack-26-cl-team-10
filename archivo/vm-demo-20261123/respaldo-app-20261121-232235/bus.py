"""Reparto en vivo dentro del proceso: lo que entra a una OT sale al instante a quien la escucha.

Una aplicación y una base (ADR-0003), así que no hay broker: cada WebSocket se
suscribe a un canal y el servicio publica. Se publica desde endpoints síncronos
(corren en hilos), por eso la entrega pasa por el loop de cada suscriptor.
"""

from __future__ import annotations

import asyncio
import threading
from collections import defaultdict

TAMANO_COLA = 1000


class Bus:
    def __init__(self) -> None:
        self._subs: dict[str, set[tuple[asyncio.AbstractEventLoop, asyncio.Queue]]] = defaultdict(set)
        self._lock = threading.Lock()

    def suscribir(self, canal: str) -> asyncio.Queue:
        cola: asyncio.Queue = asyncio.Queue(maxsize=TAMANO_COLA)
        with self._lock:
            self._subs[canal].add((asyncio.get_running_loop(), cola))
        return cola

    def desuscribir(self, canal: str, cola: asyncio.Queue) -> None:
        with self._lock:
            self._subs[canal] = {s for s in self._subs[canal] if s[1] is not cola}

    def publicar(self, canal: str, mensaje: dict) -> None:
        with self._lock:
            subs = list(self._subs.get(canal, ()))
        for loop, cola in subs:
            try:
                loop.call_soon_threadsafe(_poner, cola, mensaje)
            except RuntimeError:
                self.desuscribir(canal, cola)

    def suscriptores(self, canal: str) -> int:
        with self._lock:
            return len(self._subs.get(canal, ()))


def _poner(cola: asyncio.Queue, mensaje: dict) -> None:
    """Si un cliente no da abasto se pierde lo más viejo, nunca lo nuevo.

    El cliente que vuelve a conectar pide el registro desde su último evento, así
    que lo perdido de la bitácora se recupera; solo se pierden lecturas en vivo.
    """
    if cola.full():
        cola.get_nowait()
    cola.put_nowait(mensaje)


def canal_ot(ot_id: str) -> str:
    return f"ot:{ot_id}"


def canal_edge(edge_id: str) -> str:
    return f"edge:{edge_id}"
