"""FRENTE 1 — protocolo a pasos.

Hoy es un stub: devuelve la pauta del demo que está en datos/pauta-correa.json.

Lo que hay que construir acá: recibir el PDF del cliente, extraer los pasos, y
por cada paso decidir su tipo_evidencia y su pregunta_visual. Lo demás del
sistema no cambia, porque el contrato de salida es el mismo: una Pauta.

Regla que no se puede saltar (ADR-0003): una persona aprueba la pauta convertida
antes de que se use. El stub la marca como aprobada porque es una pauta de demo.
"""

from __future__ import annotations

import json
from pathlib import Path

from app.contratos import Pauta, Paso

PAUTA_DEMO = Path(__file__).resolve().parent.parent / "datos" / "pauta-correa.json"


def desde_json(ruta: Path | str = PAUTA_DEMO) -> Pauta:
    d = json.loads(Path(ruta).read_text(encoding="utf-8"))
    return Pauta(
        id=d["id"],
        nombre=d["nombre"],
        version=d["version"],
        equipo=d["equipo"],
        pasos=tuple(Paso.desde_dict(x) for x in d["pasos"]),
    )


def extraer_pasos(pdf: bytes) -> Pauta:  # noqa: ARG001
    """TODO frente 1: PDF → pasos. Por ahora ignora el PDF y devuelve el demo."""
    return desde_json()
