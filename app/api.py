"""FRENTE 2 entra por acá — la API que une los cuatro frentes.

Correr:  uv run uvicorn app.api:app --reload
La UI mínima vive en app/estatico/ y se sirve en /.

La app impone el orden (ADR-0002): /ot/{id}/declarar solo evalúa el paso actual.
"""

from __future__ import annotations

from pathlib import Path

from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse
from pydantic import BaseModel

from app import cerebro, db, protocolos, verificacion
from app.contratos import Evento, TipoEvento
from app.reglas import evaluar, paso_actual, reglas_seguridad, estados_desde_eventos, propuesta_de_mejora

app = FastAPI(title="Mantenimiento verificado — esqueleto")
cx = db.conectar()

ESTATICO = Path(__file__).resolve().parent / "estatico"


class Declaracion(BaseModel):
    actor: str
    texto: str


class LecturaSensor(BaseModel):
    sensor_id: str
    valor: str


class Pregunta(BaseModel):
    actor: str
    texto: str


@app.get("/")
def portada() -> FileResponse:
    return FileResponse(ESTATICO / "index.html")


@app.post("/pauta/demo")
def cargar_pauta_demo() -> dict:
    """Frente 1: cuando exista PDF→pasos, este endpoint recibe el PDF."""
    pauta = protocolos.desde_json()
    db.guardar_pauta(cx, pauta)
    return {"pauta": pauta.id, "version": pauta.version, "pasos": len(pauta.pasos)}


@app.post("/ot/{ot_id}/abrir")
def abrir_ot(ot_id: str, actor: str = "sistema") -> dict:
    pauta = db.leer_pauta(cx, "pauta-correa-ct-01")
    db.abrir_ot(cx, ot_id, pauta, actor)
    return {"ot": ot_id, "pauta": f"{pauta.nombre} v{pauta.version}"}


@app.get("/ot/{ot_id}")
def estado_ot(ot_id: str) -> dict:
    fila = db.leer_ot(cx, ot_id)
    pauta = db.leer_pauta(cx, fila["pauta_id"], fila["pauta_version"])
    return cerebro.estado_de_ot(pauta, db.eventos(cx, ot_id))


@app.post("/ot/{ot_id}/declarar")
def declarar(ot_id: str, d: Declaracion) -> dict:
    """El operario habla. La evidencia manda: el veredicto lo decide reglas.py."""
    fila = db.leer_ot(cx, ot_id)
    pauta = db.leer_pauta(cx, fila["pauta_id"], fila["pauta_version"])
    evs = db.eventos(cx, ot_id)
    paso = paso_actual(pauta, estados_desde_eventos(evs))
    if paso is None:
        raise HTTPException(409, "la pauta ya está completa")

    db.agregar(cx, Evento(ot_id=ot_id, tipo=TipoEvento.DECLARACION, ts=db.ahora(),
                          actor=d.actor, paso_id=paso.id, declarado=d.texto,
                          detalle=f"declara sobre «{paso.titulo}»"))
    v = evaluar(paso, d.texto, db.estado_sensores(cx), verificacion.juez_camara)
    db.agregar(cx, Evento(ot_id=ot_id, tipo=TipoEvento.VEREDICTO, ts=db.ahora(),
                          actor="sistema", paso_id=paso.id, estado=v.estado, capa=v.capa,
                          declarado=d.texto, evidencia=v.evidencia, detalle=v.detalle))
    return {"paso": paso.id, "estado": str(v.estado), "capa": v.capa,
            "detalle": v.detalle, "interrumpe": v.interrumpe}


@app.post("/sensores")
def sensor(lec: LecturaSensor) -> dict:
    """El ESP32 (o el simulador) escribe acá. Cada lectura evalúa las reglas de
    seguridad, que no dependen del paso en curso."""
    db.escribir_sensor(cx, lec.sensor_id, lec.valor)
    alertas = reglas_seguridad(db.estado_sensores(cx))
    for a in alertas:
        for fila in cx.execute("SELECT id FROM ots").fetchall():
            db.agregar(cx, Evento(ot_id=fila["id"], tipo=TipoEvento.ALERTA, ts=db.ahora(),
                                  actor="sistema", estado=a.estado, capa=a.capa,
                                  evidencia=a.evidencia, detalle=a.detalle))
    return {"ok": True, "alertas": [a.detalle for a in alertas]}


@app.get("/sensores")
def sensores() -> dict:
    return db.estado_sensores(cx)


@app.post("/ot/{ot_id}/relevo/entregar")
def entregar_turno(ot_id: str, actor: str) -> dict:
    fila = db.leer_ot(cx, ot_id)
    pauta = db.leer_pauta(cx, fila["pauta_id"], fila["pauta_version"])
    evs = db.eventos(cx, ot_id)
    estado = cerebro.estado_de_ot(pauta, evs)
    resumen = cerebro.redactar_resumen(estado, evs)
    db.agregar(cx, Evento(ot_id=ot_id, tipo=TipoEvento.RELEVO_ENTREGADO, ts=db.ahora(),
                          actor=actor, detalle=resumen))
    return {"resumen": resumen, "estado": estado}


@app.post("/ot/{ot_id}/relevo/recibir")
def recibir_turno(ot_id: str, actor: str) -> dict:
    """El traspaso se firma: quién recibió y cuándo queda como evento."""
    db.agregar(cx, Evento(ot_id=ot_id, tipo=TipoEvento.RELEVO_RECIBIDO, ts=db.ahora(),
                          actor=actor, detalle=f"{actor} confirma que recibió el turno"))
    return {"firmado_por": actor}


@app.post("/ot/{ot_id}/preguntar")
def preguntar(ot_id: str, p: Pregunta) -> dict:
    """«¿Se puso el bloqueo?» → la respuesta viaja con su evidencia y su hora."""
    fila = db.leer_ot(cx, ot_id)
    pauta = db.leer_pauta(cx, fila["pauta_id"], fila["pauta_version"])
    return cerebro.responder(p.texto, pauta, db.eventos(cx, ot_id))


@app.get("/ot/{ot_id}/eventos")
def bitacora(ot_id: str) -> list[dict]:
    return [vars(e) for e in db.eventos(cx, ot_id)]


@app.get("/supervisor/propuestas")
def propuestas() -> list[dict]:
    """Frente 4: desviaciones repetidas → propuesta de cambio a la pauta."""
    return propuesta_de_mejora(db.todos_los_eventos(cx))
