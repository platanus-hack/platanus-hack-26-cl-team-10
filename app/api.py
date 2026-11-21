"""FRENTE 2 entra por acá — la API que une los cuatro frentes.

Correr:  uv run uvicorn app.api:app --reload
La UI mínima vive en app/estatico/ y se sirve en /.

La app impone el orden (ADR-0002): /ot/{id}/declarar solo evalúa el paso actual.
"""

from __future__ import annotations

import asyncio
from pathlib import Path

from fastapi import FastAPI, HTTPException, Request, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, JSONResponse, Response, StreamingResponse
from pydantic import BaseModel

from app import catalogo, cerebro, db, protocolos, verificacion
from app.catalogo import ReglaDeNegocio
from app.guia import guia as texto_de_la_guia
from app.bus import canal_ot
from app.contratos import Evento, TipoEvento
from app.reglas import evaluar, paso_actual, estados_desde_eventos, propuesta_de_mejora
from app.servicios import Servicios, evento_dict
from app.video import FPS_MAX, CuadroInvalido

app = FastAPI(
    title="Factum · mantenimiento verificado",
    description="API del demo. La guía para un agente que se conecta, con el recorrido, los "
    "WebSocket y los errores, está en `/agente` (Markdown).",
)
# El front y el agente del equipo viven en otros dominios: sin CORS el navegador los bloquea.
# Sin credenciales ni cookies, así que abrirlo a cualquier origen no expone sesiones.
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"])
cx = db.conectar()
servicios = Servicios(cx)

EDGE_POR_DEFECTO = "edge-1"
PAUTA_DEMO = "pauta-correa-ct-01"


@app.exception_handler(ReglaDeNegocio)
def regla_de_negocio(_: Request, e: ReglaDeNegocio) -> JSONResponse:
    return JSONResponse(status_code=409, content={"regla": str(e)})


@app.exception_handler(CuadroInvalido)
def cuadro_invalido(_: Request, e: CuadroInvalido) -> JSONResponse:
    return JSONResponse(status_code=422, content={"cuadro": str(e)})


@app.exception_handler(KeyError)
def no_existe(_: Request, e: KeyError) -> JSONResponse:
    return JSONResponse(status_code=404, content={"no_existe": str(e.args[0]) if e.args else ""})

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


class Aprobacion(BaseModel):
    actor: str


class Sesion(BaseModel):
    edge_id: str = EDGE_POR_DEFECTO
    operario: str


class LecturaEdge(BaseModel):
    sensor_id: str
    valor: str
    seq: int | None = None


@app.get("/")
def portada() -> FileResponse:
    return FileResponse(ESTATICO / "index.html")


@app.post("/pauta/demo")
def cargar_pauta_demo() -> dict:
    """Frente 1: cuando exista PDF→pasos, este endpoint recibe el PDF."""
    pauta = protocolos.desde_json()
    db.guardar_pauta(cx, pauta)
    if not catalogo.aprobada(cx, pauta.id, pauta.version):
        catalogo.aprobar_pauta(cx, pauta.id, pauta.version, "supervisor:demo")
    return {"pauta": pauta.id, "version": pauta.version, "pasos": len(pauta.pasos)}


@app.post("/ot/{ot_id}/abrir")
def abrir_ot(ot_id: str, actor: str = "sistema", pauta_id: str = PAUTA_DEMO,
             version: int | None = None) -> dict:
    """La OT nace de una pauta APROBADA y guarda qué versión ejecuta (ADR-0003, ADR-0006)."""
    return catalogo.abrir_ot(cx, ot_id, pauta_id, actor, version)


# ─── CRUD de lo que piden las reglas de negocio (app/catalogo.py) ───────────


@app.get("/pautas")
def listar_pautas() -> list[dict]:
    return catalogo.listar_pautas(cx)


@app.post("/pautas", status_code=201)
def crear_pauta(pauta: dict) -> dict:
    """Crear y cambiar son lo mismo: la versión siguiente. Nace sin aprobar."""
    try:
        return catalogo.crear_pauta(cx, pauta)
    except (KeyError, ValueError) as e:
        raise HTTPException(422, f"pauta mal formada: {e}") from e


@app.get("/pautas/{pauta_id}")
def leer_pauta(pauta_id: str, version: int | None = None) -> dict:
    return catalogo.leer_pauta(cx, pauta_id, version)


@app.get("/pautas/{pauta_id}/versiones")
def versiones_de_pauta(pauta_id: str) -> list[dict]:
    v = catalogo.versiones(cx, pauta_id)
    if not v:
        raise KeyError(f"pauta {pauta_id}")
    return v


@app.post("/pautas/{pauta_id}/versiones/{version}/aprobar")
def aprobar_pauta(pauta_id: str, version: int, a: Aprobacion) -> dict:
    return catalogo.aprobar_pauta(cx, pauta_id, version, a.actor)


@app.get("/ots")
def listar_ots() -> list[dict]:
    return catalogo.listar_ots(cx)


@app.get("/eventos/{evento_id}")
def leer_evento(evento_id: int) -> dict:
    return evento_dict(catalogo.leer_evento(cx, evento_id))


@app.get("/sesiones")
def listar_sesiones() -> list[dict]:
    return servicios.sesiones()


@app.get("/edge/{edge_id}/sesion")
def sesion_de_edge(edge_id: str) -> dict:
    s = servicios.sesion(edge_id)
    if s is None:
        raise KeyError(f"sesión del edge {edge_id}")
    return s


@app.delete("/edge/{edge_id}/sesion", status_code=204)
def terminar_sesion(edge_id: str) -> None:
    servicios.terminar_sesion(edge_id)


@app.get("/ot/{ot_id}")
def estado_ot(ot_id: str) -> dict:
    fila = db.leer_ot(cx, ot_id)
    pauta = db.leer_pauta(cx, fila["pauta_id"], fila["pauta_version"])
    return cerebro.estado_de_ot(pauta, db.eventos(cx, ot_id))


@app.post("/ot/{ot_id}/declarar")
def declarar(ot_id: str, d: Declaracion) -> dict:
    """El operario habla. La evidencia manda: el veredicto lo decide reglas.py, y un paso
    de cámara se juzga con el último cuadro del edge de la OT."""
    return servicios.declarar(ot_id, d.actor, d.texto)


@app.post("/sensores")
def sensor(lec: LecturaSensor) -> dict:
    """Compatibilidad con el ESP32 de un solo equipo: es una lectura del edge por defecto."""
    r = servicios.recibir_lectura(EDGE_POR_DEFECTO, lec.sensor_id, lec.valor)
    return {"ok": True, "ot": r["ot"],
            "alertas": [e["detalle"] for e in r["eventos"] if e["tipo"] == TipoEvento.ALERTA]}


@app.post("/edge/{edge_id}/lecturas")
def lecturas_edge(edge_id: str, lecturas: list[LecturaEdge]) -> list[dict]:
    """Lo que manda el edge, en lote. Se atribuye a la OT que ese edge está ejecutando."""
    return [servicios.recibir_lectura(edge_id, l.sensor_id, l.valor, l.seq) for l in lecturas]


@app.post("/ot/{ot_id}/sesion")
def iniciar_sesion(ot_id: str, s: Sesion) -> dict:
    """El operario elige la OT en la interfaz: desde ahora lo de ese edge es de esta OT."""
    try:
        return servicios.iniciar_sesion(ot_id, s.edge_id, s.operario)
    except KeyError as e:
        raise HTTPException(404, str(e)) from e


@app.get("/ot/{ot_id}/calificacion")
def calificacion(ot_id: str) -> dict:
    """La calificación vigente y los avisos activos, lo más grave primero."""
    db.leer_ot(cx, ot_id)
    return servicios.calificacion(ot_id)


@app.get("/ot/{ot_id}/alertas")
def alertas_activas(ot_id: str) -> list[dict]:
    """Las alertas abiertas que todavía no tienen su alerta_resuelta."""
    db.leer_ot(cx, ot_id)
    return [evento_dict(e) for e in servicios.alertas_activas(ot_id).values()]


# ─── Video del edge (app/video.py) ──────────────────────────────────────────


@app.websocket("/edge/{edge_id}/video")
async def video_entrada(ws: WebSocket, edge_id: str) -> None:
    """La cámara manda JPEG en mensajes binarios. Un cuadro malo se avisa y no corta la conexión."""
    await ws.accept()
    while True:
        m = await ws.receive()
        if m["type"] == "websocket.disconnect":
            return
        if m.get("bytes"):
            try:
                servicios.video.recibir(edge_id, m["bytes"])
            except CuadroInvalido as e:
                await ws.send_json({"error": str(e)})


@app.post("/edge/{edge_id}/cuadro")
async def cuadro_entrada(edge_id: str, request: Request) -> dict:
    """Lo mismo por HTTP, para una ESP32-CAM: el cuerpo es el JPEG."""
    c = servicios.video.recibir(edge_id, await request.body())
    return {"edge_id": edge_id, "cuadro": c.n}


@app.get("/edge/{edge_id}/video")
def video_estado(edge_id: str) -> dict:
    return servicios.video.estado(edge_id)


@app.get("/edge/{edge_id}/cuadro.jpg")
def cuadro_actual(edge_id: str) -> Response:
    c = servicios.video.ultimo(edge_id)
    if c is None:
        raise KeyError(f"video del edge {edge_id}")
    return Response(c.jpeg, media_type="image/jpeg", headers={"Cache-Control": "no-store"})


@app.get("/edge/{edge_id}/video.mjpg")
async def video_salida(edge_id: str, request: Request, limite: int | None = None) -> StreamingResponse:
    """Video en vivo para un <img>. Manda solo cuadros nuevos; si no llegan, espera."""

    async def cuadros():
        visto, enviados = 0, 0
        while not await request.is_disconnected():
            c = servicios.video.ultimo(edge_id)
            if c is not None and c.n != visto:
                visto = c.n
                enviados += 1
                yield (b"--cuadro\r\nContent-Type: image/jpeg\r\nContent-Length: "
                       + str(len(c.jpeg)).encode() + b"\r\n\r\n" + c.jpeg + b"\r\n")
                if limite is not None and enviados >= limite:
                    return
            await asyncio.sleep(1 / FPS_MAX)

    return StreamingResponse(cuadros(), media_type="multipart/x-mixed-replace; boundary=cuadro")


@app.get("/agente")
@app.get("/llms.txt", include_in_schema=False)
def guia_para_el_agente(request: Request) -> Response:
    """La guía en Markdown para el agente que se conecta: recorrido, WebSocket, errores y endpoints."""
    return Response(texto_de_la_guia(app, str(request.base_url)), media_type="text/markdown; charset=utf-8")


@app.get("/camara")
def pagina_camara() -> FileResponse:
    """La cámara del celular del operario como edge de video."""
    return FileResponse(ESTATICO / "camara.html")


@app.get("/monitor")
def pagina_monitor() -> FileResponse:
    """Video, calificación, avisos y bitácora de una OT, en vivo."""
    return FileResponse(ESTATICO / "monitor.html")


@app.websocket("/ot/{ot_id}/stream")
async def stream(ws: WebSocket, ot_id: str, desde: int = 0) -> None:
    """Primero el snapshot con la bitácora desde `desde`; después, todo lo nuevo al instante.

    Para reconectar sin perder bitácora, el cliente vuelve con `desde` = el último
    id de evento que vio.
    """
    await ws.accept()
    canal = canal_ot(ot_id)
    cola = servicios.bus.suscribir(canal)
    try:
        try:
            await ws.send_json(servicios.snapshot(ot_id, desde))
        except KeyError:
            await ws.close(code=4404, reason=f"OT {ot_id} no existe")
            return
        while True:
            await ws.send_json(await cola.get())
    except WebSocketDisconnect:
        pass
    finally:
        servicios.bus.desuscribir(canal, cola)


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
    servicios.agregar(Evento(ot_id=ot_id, tipo=TipoEvento.RELEVO_ENTREGADO, ts=db.ahora(),
                             actor=actor, detalle=resumen))
    return {"resumen": resumen, "estado": estado}


@app.post("/ot/{ot_id}/relevo/recibir")
def recibir_turno(ot_id: str, actor: str) -> dict:
    """El traspaso se firma: quién recibió y cuándo queda como evento."""
    servicios.agregar(Evento(ot_id=ot_id, tipo=TipoEvento.RELEVO_RECIBIDO, ts=db.ahora(),
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
    return [evento_dict(e) for e in db.eventos(cx, ot_id)]


@app.get("/supervisor/propuestas")
def propuestas() -> list[dict]:
    """Frente 4: desviaciones repetidas → propuesta de cambio a la pauta."""
    return propuesta_de_mejora(db.todos_los_eventos(cx))
