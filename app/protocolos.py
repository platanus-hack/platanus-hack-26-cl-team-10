"""FRENTE 1 — protocolo a pasos.

El protocolo ya es un recurso: se carga, se lee, se corrige y se le atribuyen pautas
(app/catalogo.py, rutas /interno/protocolos). Lo que sigue siendo un stub es extraer
los pasos: `extraer_pasos` devuelve la pauta del demo que está en datos/pauta-correa.json,
y las pautas de datos/ están escritas a mano.

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
DATOS = PAUTA_DEMO.parent
SEMILLA = DATOS / "protocolos.json"


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


def cargar_semilla(cx, actor: str = "equipo:factum") -> dict:
    """Deja en la base las pautas de datos/ y sus protocolos (datos/protocolos.json), ya atribuidos.

    Es lo que el equipo hace una vez al poner en marcha una estación, hecho de una vez para los
    casos del repo. Se puede repetir: lo que ya está no se toca. Las pautas quedan aprobadas por
    `supervisor:demo`, igual que en /pauta/demo.
    """
    from app import catalogo, db  # acá adentro: catalogo y db no dependen de este módulo

    pautas = []
    for ruta in sorted(DATOS.glob("pauta-*.json")):
        pauta = desde_json(ruta)
        if not catalogo.versiones(cx, pauta.id):
            db.guardar_pauta(cx, pauta)
        if not catalogo.aprobada(cx, pauta.id, pauta.version):
            catalogo.aprobar_pauta(cx, pauta.id, pauta.version, "supervisor:demo")
        pautas.append(pauta.id)
    protocolos = []
    for d in json.loads(SEMILLA.read_text(encoding="utf-8")):
        if not cx.execute("SELECT 1 FROM protocolos WHERE id = ?", (d["id"],)).fetchone():
            texto = (DATOS / d["documento"]).read_text(encoding="utf-8")
            catalogo.crear_protocolo(cx, {**d, "texto": texto, "pautas": []}, actor)
        for pauta_id in d["pautas"]:
            catalogo.atribuir(cx, pauta_id, d["id"], actor)
        protocolos.append(d["id"])
    return {"pautas": pautas, "protocolos": protocolos}
