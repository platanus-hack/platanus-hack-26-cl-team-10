"""Datos de ejemplo en la base: los protocolos con sus pautas y OT en distintos estados.

Correr:  uv run python -m app.semilla            # en datos/bitacora.sqlite3
         POST /interno/ots/semilla               # en el servidor, con la clave del equipo

Las OT de datos/ots-semilla.json se abren por el servicio del cliente y se ejecutan contra
los servicios reales: cada lectura y cada declaración pasan por las mismas reglas que en
vivo, así que sus alertas y su calificación son las que daría el sistema. Dos cosas no son
de verdad, y quedan dichas en la evidencia: la cámara responde con un valor fijo, sin mirar
ningún cuadro, y las horas se reparten hacia atrás según `hace_dias`.

Se puede repetir: una OT que ya existe no se toca. Los sensores y las sesiones vuelven a como
estaban, para que la semilla no deje lecturas que disparen una regla en una OT de verdad.
"""

from __future__ import annotations

import json
import sqlite3
import tempfile
import time
from collections.abc import Iterator
from contextlib import contextmanager
from datetime import UTC, datetime, timedelta
from pathlib import Path

from app import catalogo, db, protocolos
from app.bus import Bus
from app.contratos import TipoEvidencia
from app.servicios import Servicios
from app.video import Cuadro, Video

OTS = protocolos.DATOS / "ots-semilla.json"
CAMARA_POR_DEFECTO = 0.9
SEGUNDOS_ENTRE_EVENTOS = 40
EDGE = "edge-semilla"


class _Video(Video):
    """Siempre hay un cuadro fresco y vacío: el juez de la semilla no lo mira."""

    def ultimo(self, edge_id: str) -> Cuadro | None:
        return Cuadro(0, time.time(), b"")


class _Servicios(Servicios):
    def _con_cuadro(self, evidencia, ot_id, paso_id, edge_id):
        return {**evidencia, "cuadro": None, "semilla": "respuesta de cámara fija, sin cuadro"} if evidencia else None


@contextmanager
def _reloj(desde: datetime) -> Iterator[None]:
    """Las horas de la OT, hacia atrás: cada evento, SEGUNDOS_ENTRE_EVENTOS después del anterior."""
    original, t = db.ahora, [desde]

    def ahora() -> str:
        t[0] += timedelta(seconds=SEGUNDOS_ENTRE_EVENTOS)
        return t[0].isoformat(timespec="seconds")

    db.ahora = ahora
    try:
        yield
    finally:
        db.ahora = original


def _ejecutar(s: Servicios, d: dict, pauta) -> None:
    confianza = {"valor": CAMARA_POR_DEFECTO}
    s.juez = lambda pregunta, cuadro: (True, confianza["valor"])
    operador = d["operador"]
    s.iniciar_sesion(d["ot"], EDGE, operador)
    seq = [0]

    def lecturas(antes_del_paso: int) -> None:
        for bloque in d.get("intercalar", []):
            if bloque["antes_del_paso"] == antes_del_paso:
                for sensor, valor in bloque["lecturas"]:
                    seq[0] += 1
                    s.recibir_lectura(EDGE, sensor, valor, seq[0])

    hasta = len(pauta.pasos) if d["cerrar"] == "todos" else d["cerrar"]
    for paso in pauta.en_orden[:hasta]:
        lecturas(paso.orden)
        if paso.tipo_evidencia is TipoEvidencia.SENSOR:
            seq[0] += 1
            s.recibir_lectura(EDGE, paso.sensor.id, paso.sensor.espera, seq[0])
        else:
            confianza["valor"] = d.get("camara", {}).get(paso.id, CAMARA_POR_DEFECTO)
            s.declarar(d["ot"], operador, f"listo: {paso.titulo.lower()}")
    lecturas(hasta + 1)
    s.terminar_sesion(EDGE)


def cargar(cx: sqlite3.Connection, ahora: datetime | None = None) -> dict:
    """Carga los protocolos con sus pautas y las OT de ejemplo. Devuelve qué OT creó y cuáles ya estaban."""
    catalogo.preparar(cx)
    semilla = protocolos.cargar_semilla(cx)
    spec = json.loads(OTS.read_text(encoding="utf-8"))["ots"]
    ahora = ahora or datetime.now(UTC).replace(microsecond=0)
    sensores = cx.execute("SELECT id, valor, ts FROM sensores").fetchall()
    creadas, estaban = [], []
    try:
        for i, d in enumerate(spec):
            if cx.execute("SELECT 1 FROM ots WHERE id = ?", (d["ot"],)).fetchone():
                estaban.append(d["ot"])
                continue
            cx.execute("DELETE FROM sensores")
            s = _Servicios(cx, Bus(), _Video(Path(tempfile.mkdtemp())))
            pauta = db.leer_pauta(cx, d["pauta"], catalogo.ultima_aprobada(cx, d["pauta"]))
            desde = (ahora - timedelta(days=d["hace_dias"])).replace(hour=8 + i % 9, minute=(i * 13) % 60, second=0)
            with _reloj(min(desde, ahora - timedelta(hours=2))):
                catalogo.generar_ot(cx, d["pauta"], d["solicitante"], d["ot"])
                if d["operador"]:
                    s.asignar(d["ot"], d["operador"], "supervisor:planta")
                    if d["cerrar"]:
                        _ejecutar(s, d, pauta)
            creadas.append(d["ot"])
    finally:
        cx.execute("DELETE FROM sensores")
        cx.executemany("INSERT INTO sensores (id, valor, ts) VALUES (?, ?, ?)", [tuple(f) for f in sensores])
        cx.commit()
    resumen = {o["ot"]: o for o in catalogo.listar_ots(cx)}
    return {**semilla, "ots_creadas": [resumen[o] for o in creadas], "ots_que_ya_estaban": estaban}


if __name__ == "__main__":
    cx = db.conectar()
    r = cargar(cx)
    print(f"{len(r['protocolos'])} protocolos, {len(r['pautas'])} pautas; "
          f"{len(r['ots_creadas'])} OT creadas, {len(r['ots_que_ya_estaban'])} ya estaban")
    for o in r["ots_creadas"]:
        print(f"  {o['ot']}  {o['pauta']:26} {o['estado_general']:12} {o['cerrados']}/{o['total']}  {o['operador'] or '—'}")
