"""FRENTE 2 entra por acá — la API que une los cuatro frentes.

Correr:  uv run uvicorn app.api:app --reload
La demo (monitor en vivo) se sirve en / y en /monitor; la UI mínima de ensayo, en /ensayo.

La app impone el orden (ADR-0002): /ot/{id}/declarar solo evalúa el paso actual.
"""

from __future__ import annotations

import asyncio
import hmac
import json
import os
from pathlib import Path

from fastapi import FastAPI, Header, HTTPException, Request, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, JSONResponse, Response, StreamingResponse
from pydantic import BaseModel

from app import catalogo, cerebro, db, escenarios, protocolos, verificacion
from app.catalogo import ReglaDeNegocio
from app.guia import guia as texto_de_la_guia
from app.bus import canal_ot
from app.contratos import Evento, TipoEvento
from app.reglas import evaluar, paso_actual, estados_desde_eventos, propuesta_de_mejora
from app.servicios import Servicios, evento_dict
from app.video import FPS_MAX, TAMANO_MAX, CuadroInvalido, DeteccionInvalida

app = FastAPI(
    title="Factum · flujos operacionales verificables",
    description="API del demo. La guía para un agente que se conecta, con el recorrido, los "
    "WebSocket y los errores, está en `/agente` (Markdown).",
)
# El front y el agente del equipo viven en otros dominios: sin CORS el navegador los bloquea.
# Sin credenciales ni cookies, así que abrirlo a cualquier origen no expone sesiones.
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"])
cx = db.conectar()
servicios = Servicios(cx)
detector = None  # experimento: YOLO en el servidor (app/detector.py), solo con DETECTOR_ONNX


@app.on_event("startup")
def iniciar_detector() -> None:
    global detector
    from app import detector as modulo_detector
    detector = modulo_detector.desde_entorno(servicios)


@app.get("/detector")
def estado_detector() -> dict:
    """Si el detector corre en el servidor, con qué modelo y cuánto tardó el último cuadro."""
    if detector is None:
        return {"en_servidor": False}
    return {"en_servidor": True, "modelo": detector.modelo, "clases": detector.clases,
            "ms_ultimo_cuadro": round(detector.ms_ultimo)}

EDGE_POR_DEFECTO = "edge-1"
PAUTA_DEMO = "pauta-correa-ct-01"
PAUTAS_DEMO = {"correa": protocolos.PAUTA_DEMO, "loto": protocolos.PAUTA_DEMO.parent / "pauta-loto.json"}


@app.exception_handler(ReglaDeNegocio)
def regla_de_negocio(_: Request, e: ReglaDeNegocio) -> JSONResponse:
    return JSONResponse(status_code=409, content={"regla": str(e)})


@app.exception_handler(CuadroInvalido)
def cuadro_invalido(_: Request, e: CuadroInvalido) -> JSONResponse:
    return JSONResponse(status_code=422, content={"cuadro": str(e)})


@app.exception_handler(db.NoExiste)
def no_existe(_: Request, e: db.NoExiste) -> JSONResponse:
    return JSONResponse(status_code=404, content={"no_existe": str(e.args[0]) if e.args else ""})

ESTATICO = Path(__file__).resolve().parent / "estatico"


class Declaracion(BaseModel):
    actor: str
    texto: str
    paso_id: str | None = None


class LecturaSensor(BaseModel):
    sensor_id: str
    valor: str


class ConfirmacionPersona(BaseModel):
    actor: str
    motivo: str


class Pregunta(BaseModel):
    actor: str
    texto: str


class Aprobacion(BaseModel):
    actor: str


class Asignacion(BaseModel):
    operador: str
    actor: str = "supervisor"


class ProtocoloNuevo(BaseModel):
    id: str
    nombre: str
    actor: str
    industria: str = ""
    origen: str = ""
    texto: str = ""
    pautas: list[str] = []


class ProtocoloCambio(BaseModel):
    nombre: str | None = None
    industria: str | None = None
    origen: str | None = None
    texto: str | None = None


class PautaDeProtocolo(BaseModel):
    pauta: dict
    actor: str
    protocolos: list[str] = []


class PedidoOt(BaseModel):
    pauta_id: str
    solicitante: str
    ot_id: str | None = None


class Sesion(BaseModel):
    edge_id: str = EDGE_POR_DEFECTO
    operario: str


class LecturaEdge(BaseModel):
    sensor_id: str
    valor: str
    seq: int | None = None


@app.get("/")
def portada() -> FileResponse:
    """La demo: el monitor de la OT en vivo (video, cajas, sensores, pasos y bitácora)."""
    return FileResponse(ESTATICO / "monitor.html")


@app.get("/ensayo")
def pagina_ensayo() -> FileResponse:
    """La UI mínima del esqueleto para ensayar el flujo a mano (pauta de la correa)."""
    return FileResponse(ESTATICO / "index.html")


@app.post("/pauta/demo")
def cargar_pauta_demo(pauta: str = "correa") -> dict:
    """Frente 1: cuando exista PDF→pasos, este endpoint recibe el PDF.
    `pauta`: `correa` (cambio de rodillo) o `loto` (bloqueo con cámara y ESP32)."""
    if pauta not in PAUTAS_DEMO:
        raise HTTPException(404, f"pauta de demo desconocida: {pauta}; hay {sorted(PAUTAS_DEMO)}")
    pauta = protocolos.desde_json(PAUTAS_DEMO[pauta])
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
        raise db.NoExiste(f"pauta {pauta_id}")
    return v


@app.post("/pautas/{pauta_id}/versiones/{version}/aprobar")
def aprobar_pauta(pauta_id: str, version: int, a: Aprobacion) -> dict:
    return catalogo.aprobar_pauta(cx, pauta_id, version, a.actor)


@app.get("/ots")
def listar_ots() -> list[dict]:
    """Cada OT con su avance (`cerrados` de `total`), su `operador` y su `estado_general`: `sin_asignar`,
    `asignada`, `en_ejecucion`, `entregada` (relevo que nadie recibió; `entregada_por` dice quién) o `completa`."""
    return servicios.ots()


@app.post("/ot/{ot_id}/asignar")
def asignar_ot(ot_id: str, a: Asignacion) -> dict:
    """El supervisor asigna una OT sin operador, o reasigna una entregada. Devuelve su resumen, como en `/ots`.
    409 si está completa, si ya tiene operador o si el operador no existe."""
    return servicios.asignar(ot_id, a.operador, a.actor)


@app.get("/eventos/{evento_id}")
def leer_evento(evento_id: int) -> dict:
    return evento_dict(catalogo.leer_evento(cx, evento_id))


# ─── Clave del equipo: quién puede mover un edge de una OT a otra ───────────
# La API es pública. Con CLAVE_EQUIPO definida, tomar un edge que ya ejecuta otra OT o
# soltarlo pide la cabecera X-Clave-Equipo; sin la variable todo queda abierto, como en local.


class ClaveRequerida(Exception):
    pass


@app.exception_handler(ClaveRequerida)
def clave_requerida(_: Request, e: ClaveRequerida) -> JSONResponse:
    return JSONResponse(status_code=401, content={"clave": str(e)})


def _clave_valida(clave: str | None) -> bool:
    esperada = os.environ.get("CLAVE_EQUIPO", "")
    return not esperada or hmac.compare_digest((clave or "").encode(), esperada.encode())


@app.get("/clave")
def estado_de_la_clave(x_clave_equipo: str | None = Header(default=None)) -> dict:
    """Si este servidor pide clave para mover un edge, y si la que llega en `X-Clave-Equipo` sirve."""
    return {"requerida": bool(os.environ.get("CLAVE_EQUIPO")), "valida": _clave_valida(x_clave_equipo)}


# ─── Servicio interno: protocolos y sus pautas (app/catalogo.py) ────────────
# Lo usa el equipo, una vez por protocolo, al poner en marcha una estación. Con CLAVE_EQUIPO
# definida pide la cabecera X-Clave-Equipo; sin la variable queda abierto, como en local.


def _solo_equipo(clave: str | None) -> None:
    if not _clave_valida(clave):
        raise ClaveRequerida("el servicio interno pide la clave del equipo (cabecera X-Clave-Equipo)")


@app.post("/interno/protocolos", status_code=201)
def crear_protocolo(p: ProtocoloNuevo, x_clave_equipo: str | None = Header(default=None)) -> dict:
    """Carga el protocolo de un cliente. `pautas` lo deja atribuido a pautas que ya existen. 409 si el id ya existe."""
    _solo_equipo(x_clave_equipo)
    return catalogo.crear_protocolo(cx, p.model_dump(exclude={"actor"}), p.actor)


@app.get("/interno/protocolos")
def listar_protocolos(x_clave_equipo: str | None = Header(default=None)) -> list[dict]:
    """Cada protocolo con las pautas que salen de él, sin su texto."""
    _solo_equipo(x_clave_equipo)
    return catalogo.listar_protocolos(cx)


@app.post("/interno/protocolos/semilla")
def sembrar_protocolos(x_clave_equipo: str | None = Header(default=None)) -> dict:
    """Deja cargadas y aprobadas las pautas de `datos/`, con sus protocolos atribuidos. Se puede repetir."""
    _solo_equipo(x_clave_equipo)
    return protocolos.cargar_semilla(cx)


@app.get("/interno/protocolos/{protocolo_id}")
def leer_protocolo(protocolo_id: str, x_clave_equipo: str | None = Header(default=None)) -> dict:
    """Un protocolo con su texto y sus pautas."""
    _solo_equipo(x_clave_equipo)
    return catalogo.leer_protocolo(cx, protocolo_id)


@app.put("/interno/protocolos/{protocolo_id}")
def cambiar_protocolo(protocolo_id: str, c: ProtocoloCambio, x_clave_equipo: str | None = Header(default=None)) -> dict:
    """Corrige nombre, industria, origen o texto. El id no cambia."""
    _solo_equipo(x_clave_equipo)
    return catalogo.cambiar_protocolo(cx, protocolo_id, c.model_dump(exclude_none=True))


@app.delete("/interno/protocolos/{protocolo_id}", status_code=204)
def borrar_protocolo(protocolo_id: str, x_clave_equipo: str | None = Header(default=None)) -> None:
    """Solo si ninguna pauta sale de él (409 si tiene)."""
    _solo_equipo(x_clave_equipo)
    catalogo.borrar_protocolo(cx, protocolo_id)


@app.post("/interno/protocolos/{protocolo_id}/pautas", status_code=201)
def crear_pauta_de_protocolo(protocolo_id: str, p: PautaDeProtocolo, x_clave_equipo: str | None = Header(default=None)) -> dict:
    """Crea la versión siguiente de una pauta, atribuida a este protocolo y a los de `protocolos`. Nace sin aprobar."""
    _solo_equipo(x_clave_equipo)
    try:
        return catalogo.crear_pauta_de(cx, [protocolo_id, *p.protocolos], p.pauta, p.actor)
    except (KeyError, ValueError) as e:
        if isinstance(e, db.NoExiste):
            raise
        raise HTTPException(422, f"pauta mal formada: {e}") from e


@app.get("/interno/pautas/{pauta_id}/protocolos")
def protocolos_de_pauta(pauta_id: str, x_clave_equipo: str | None = Header(default=None)) -> list[dict]:
    """De qué protocolos sale una pauta."""
    _solo_equipo(x_clave_equipo)
    catalogo.leer_pauta(cx, pauta_id)
    return catalogo.protocolos_de(cx, pauta_id)


@app.put("/interno/pautas/{pauta_id}/protocolos/{protocolo_id}")
def atribuir_pauta(pauta_id: str, protocolo_id: str, a: Aprobacion, x_clave_equipo: str | None = Header(default=None)) -> dict:
    """Atribuye una pauta que ya existe a un protocolo. Una pauta puede salir de varios."""
    _solo_equipo(x_clave_equipo)
    return catalogo.atribuir(cx, pauta_id, protocolo_id, a.actor)


@app.delete("/interno/pautas/{pauta_id}/protocolos/{protocolo_id}", status_code=204)
def quitar_atribucion(pauta_id: str, protocolo_id: str, x_clave_equipo: str | None = Header(default=None)) -> None:
    """Quita la atribución. 409 si es el único protocolo de una pauta que ya tiene OT."""
    _solo_equipo(x_clave_equipo)
    catalogo.quitar_atribucion(cx, pauta_id, protocolo_id)


@app.post("/interno/pautas/{pauta_id}/versiones/{version}/aprobar")
def aprobar_pauta_interno(pauta_id: str, version: int, a: Aprobacion, x_clave_equipo: str | None = Header(default=None)) -> dict:
    """Lo mismo que aprobar una pauta, dentro del servicio interno: una persona, una sola vez."""
    _solo_equipo(x_clave_equipo)
    return catalogo.aprobar_pauta(cx, pauta_id, version, a.actor)


# ─── Servicio para clientes: pedir OT de las pautas que el equipo dejó listas ─


@app.get("/cliente/pautas")
def pautas_para_clientes() -> list[dict]:
    """Las pautas que se pueden pedir: con una versión aprobada y al menos un protocolo."""
    return catalogo.pautas_disponibles(cx)


@app.post("/cliente/ots", status_code=201)
def pedir_ot(p: PedidoOt) -> dict:
    """Genera una OT de la última versión aprobada de la pauta. Sin `ot_id`, el servicio le pone uno.
    409 si la pauta no está aprobada, no sale de ningún protocolo o el id ya existe."""
    return catalogo.generar_ot(cx, p.pauta_id, p.solicitante, p.ot_id)


@app.get("/cliente/ots")
def ots_para_clientes() -> list[dict]:
    """Cada OT con su avance, su operador y su estado general, como en `/ots`."""
    return servicios.ots()


@app.get("/sesiones")
def listar_sesiones() -> list[dict]:
    return servicios.sesiones()


@app.get("/edge/{edge_id}/sesion")
def sesion_de_edge(edge_id: str) -> dict:
    s = servicios.sesion(edge_id)
    if s is None:
        raise db.NoExiste(f"sesión del edge {edge_id}")
    return s


@app.delete("/edge/{edge_id}/sesion", status_code=204)
def terminar_sesion(edge_id: str, x_clave_equipo: str | None = Header(default=None)) -> None:
    """Soltar un edge que está en sesión pide la clave del equipo, si el servidor tiene una."""
    if servicios.sesion(edge_id) and not _clave_valida(x_clave_equipo):
        raise ClaveRequerida(f"soltar el edge {edge_id} pide la clave del equipo (cabecera X-Clave-Equipo)")
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
    return servicios.declarar(ot_id, d.actor, d.texto, d.paso_id)


@app.post("/ot/{ot_id}/pasos/{paso_id}/confirmar")
def confirmar_paso(ot_id: str, paso_id: str, c: ConfirmacionPersona) -> dict:
    """Una persona confirma el paso en curso aunque su sensor o la cámara no lo muestren. Queda quién, por qué y qué
    marcaba el sensor; la OT queda en warning y la seguridad sigue mandando. Solo el paso en curso; sin motivo, 409."""
    return servicios.confirmar_por_persona(ot_id, paso_id, c.actor, c.motivo)


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
def iniciar_sesion(ot_id: str, s: Sesion, x_clave_equipo: str | None = Header(default=None)) -> dict:
    """El operario elige la OT en la interfaz: desde ahora lo de ese edge es de esta OT.
    Un edge libre, o repetir la sesión que ya tiene, no pide clave; quitárselo a otra OT, sí."""
    actual = servicios.sesion(s.edge_id)
    if actual and actual["ot_id"] != ot_id and not _clave_valida(x_clave_equipo):
        raise ClaveRequerida(f"el edge {s.edge_id} ejecuta la OT {actual['ot_id']}: "
                             "tomarlo pide la clave del equipo (cabecera X-Clave-Equipo)")
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
    """La cámara manda JPEG en mensajes binarios y las detecciones de su modelo en mensajes
    de texto: {"tipo": "detecciones", "modelo", "ts", "objetos": [{"clase", "conf", "caja"}]},
    con la caja normalizada 0-1 (x1, y1, x2, y2). Un mensaje malo se avisa y no corta la conexión."""
    await ws.accept()
    while True:
        m = await ws.receive()
        if m["type"] == "websocket.disconnect":
            return
        try:
            if m.get("bytes"):
                servicios.video.recibir(edge_id, m["bytes"])
            elif m.get("text"):
                d = json.loads(m["text"])
                if not isinstance(d, dict) or d.get("tipo") != "detecciones":
                    raise DeteccionInvalida('se espera un objeto con "tipo": "detecciones"')
                if detector is None:  # con detección en el servidor, las del edge se ignoran
                    servicios.recibir_detecciones(edge_id, d)
        except (CuadroInvalido, DeteccionInvalida, json.JSONDecodeError) as e:
            await ws.send_json({"error": str(e)})


@app.post("/edge/{edge_id}/cuadro")
async def cuadro_entrada(edge_id: str, request: Request) -> dict:
    """Lo mismo por HTTP, para una ESP32-CAM: el cuerpo es el JPEG."""
    # Se corta al pasar el máximo: sin esto un cuerpo enorme entra entero a memoria antes de validarse.
    partes, total = [], 0
    async for parte in request.stream():
        total += len(parte)
        if total > TAMANO_MAX:
            raise CuadroInvalido(f"el cuadro pasa de {TAMANO_MAX} bytes")
        partes.append(parte)
    c = servicios.video.recibir(edge_id, b"".join(partes))
    return {"edge_id": edge_id, "cuadro": c.n}


@app.get("/edge/{edge_id}/video")
def video_estado(edge_id: str) -> dict:
    return servicios.video.estado(edge_id)


@app.get("/edge/{edge_id}/detecciones")
def detecciones_actuales(edge_id: str) -> dict:
    """Lo último que vio el modelo del edge: clase, confianza y caja normalizada."""
    d = servicios.video.ultimas_detecciones(edge_id)
    if d is None:
        raise db.NoExiste(f"detecciones del edge {edge_id}")
    return d


@app.get("/edge/{edge_id}/cuadro.jpg")
def cuadro_actual(edge_id: str) -> Response:
    c = servicios.video.ultimo(edge_id)
    if c is None:
        raise db.NoExiste(f"video del edge {edge_id}")
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


@app.get("/casos")
def pagina_casos() -> FileResponse:
    """El banco de pruebas: cada criterio del PRD, corrido contra este servidor u otro."""
    return FileResponse(ESTATICO / "casos.html")


# ─── Escenarios por industria (app/escenarios.py) ───────────────────────────


@app.get("/escenarios")
def listar_escenarios() -> list[dict]:
    """Cada patrón de ejecución en cada industria, con la barrera que lo decide y lo que se espera."""
    return [e.como_dict() for e in escenarios.catalogo()]


@app.get("/industrias")
def listar_industrias() -> dict:
    """Cada industria con su pauta, sensores, reglas, trasfondo y casos de uso; y las piezas de la arquitectura."""
    return {"industrias": [escenarios.industria_dict(i) for i in escenarios.INDUSTRIAS],
            "arquitectura": escenarios.arquitectura()}


@app.post("/escenarios/correr")
def correr_escenarios() -> list[dict]:
    """Corre todos en una caja aislada (base en memoria, juez y reloj propios). Sin trazas, para que pese poco."""
    return [{k: v for k, v in r.items() if k not in ("bitacora", "stream")} for r in escenarios.correr_todos()]


@app.post("/escenarios/{escenario_id}/correr")
def correr_escenario(escenario_id: str) -> dict:
    """Uno, con su bitácora y lo que habría llegado por el stream. No toca la base del servidor."""
    return escenarios.correr(escenarios.buscar(escenario_id))


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
