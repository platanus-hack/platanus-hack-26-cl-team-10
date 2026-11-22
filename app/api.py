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
from datetime import date
from pathlib import Path
from typing import Literal

from fastapi import FastAPI, Header, HTTPException, Query, Request, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, JSONResponse, PlainTextResponse, Response, StreamingResponse
from pydantic import BaseModel, Field

from app import (acceso, catalogo, cerebro, db, escenarios, inventario, mejora, metricas, protocolos, referencia, reporte,
                 semilla, skills, verificacion)
from app.catalogo import ReglaDeNegocio
from app.guia import guia as texto_de_la_guia
from app.bus import canal_ot
from app.contratos import Evento, TipoEvento
from app.reglas import evaluar, paso_actual, estados_desde_eventos, propuesta_de_mejora
from app.servicios import Servicios, evento_dict
from app.video import FPS_MAX, TAMANO_MAX, CuadroInvalido, DeteccionInvalida

app = FastAPI(title=referencia.TITULO, version=referencia.VERSION)
app.openapi = lambda: referencia.completa(app)  # el OpenAPI ordenado: grupos, seguridad, errores y ejemplos
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
PAUTAS_DEMO = {"correa": protocolos.PAUTA_DEMO, "loto": protocolos.DATOS / "pauta-loto.json",
               "polin": protocolos.DATOS / "pauta-polin-estacion.json",
               "botella": protocolos.DATOS / "pauta-botella.json"}


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
    pauta_id: str = Field(description="Una pauta de `GET /cliente/pautas`. La OT sale de su última versión aprobada.")
    ot_id: str | None = Field(default=None, description="El id que tendrá la OT. Si no viene, el servicio le pone uno.")


class Credenciales(BaseModel):
    usuario: str = Field(description="El usuario que entregó el equipo de Factum. No distingue mayúsculas.")
    clave: str = Field(description="La clave de esa persona. La genera el sistema y se ve una sola vez.")


class ClienteNuevo(BaseModel):
    id: str
    nombre: str
    industria: str = ""


class PersonaNueva(BaseModel):
    id: str
    nombre: str
    usuario: str
    rol: str


class OtDelEquipo(BaseModel):
    pauta_id: str
    supervisor: str
    operador: str


class AsignacionCliente(BaseModel):
    operador: str = Field(description="El `id` de un operador de `GET /cliente/operadores`.")


class Sesion(BaseModel):
    edge_id: str = EDGE_POR_DEFECTO
    operario: str


class SesionCliente(BaseModel):
    edge_id: str = Field(default=EDGE_POR_DEFECTO, description="La estación donde se ejecuta la OT.")
    tomar: bool = Field(default=False, description="En true, le quita la estación a la OT abierta que la ocupa. "
                        "Esa OT deja de recibir sus sensores, así que se manda solo cuando la persona lo pide.")


class Observacion(BaseModel):
    texto: str = Field(description="Lo que el operario vio, en sus palabras.")
    categoria: Literal["pauta", "seguridad", "equipo", "otra"] = Field(
        default="pauta", description="`pauta` y `seguridad` alimentan la mejora de la pauta; `equipo` habla de la "
        "máquina y va a las métricas por equipo.")
    paso_id: str | None = Field(default=None, description="El paso del que habla, si habla de uno.")


class Revision(BaseModel):
    decision: Literal["aceptar", "descartar"] = Field(description="Aceptar la manda al equipo de Factum para la versión "
                                                      "siguiente de la pauta; descartar la cierra.")
    nota: str = Field(default="", description="Por qué. Descartar la exige.")


class DeclaracionCliente(BaseModel):
    texto: str = Field(description="Lo que dice el operario, en sus palabras.")
    paso_id: str | None = Field(default=None, description="El paso que la interfaz le mostraba. Si su evidencia ya lo "
                                "cerró, la palabra se registra y no se evalúa contra el paso siguiente.")


class ConfirmacionCliente(BaseModel):
    motivo: str = Field(description="Por qué se confirma aunque la evidencia no lo muestre. Sin motivo, 409.")


class PautaAValidar(BaseModel):
    pauta: dict = Field(description="La pauta como se crearía en `POST /interno/protocolos/{id}/pautas`.")
    reposo: dict[str, str] = Field(default={}, description="El valor de cada sensor antes de empezar. Sin él, se toma el "
                                   "que deja el último paso que usa ese sensor.")
    estacion: str | None = Field(default=None, description="Una estación de `datos/estaciones/` (`correa-ct-01`, "
                                 "`solo-camara`…): con ella dice qué capa puede cerrar cada paso.")
    analisis: dict | None = Field(default=None, description="El `analisis` del borrador de la skill `reconocer-proceso`, "
                                  "con la cita de cada paso y lo que no puede pasar.")
    protocolo_id: str | None = Field(default=None, description="El protocolo guardado contra cuyo texto se buscan las citas.")


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
    `pauta`: `correa` (cambio de rodillo), `polin` (cambio de polín en la estación: motor, distancia,
    temperatura y cámara) o `loto` (bloqueo con cámara y ESP32)."""
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


@app.exception_handler(acceso.NoAutenticado)
def no_autenticado(_: Request, e: acceso.NoAutenticado) -> JSONResponse:
    return JSONResponse(status_code=401, content={"login": str(e)}, headers={"WWW-Authenticate": "Bearer"})


@app.exception_handler(acceso.SinPermiso)
def sin_permiso(_: Request, e: acceso.SinPermiso) -> JSONResponse:
    return JSONResponse(status_code=403, content={"permiso": str(e)})


def _token(authorization: str | None) -> str | None:
    tipo, _, token = (authorization or "").partition(" ")
    return token.strip() if tipo.lower() == "bearer" and token.strip() else None


def _persona(authorization: str | None) -> dict:
    return acceso.quien(cx, _token(authorization))


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


@app.post("/interno/ots/semilla")
def sembrar_ots(x_clave_equipo: str | None = Header(default=None)) -> dict:
    """La minera ficticia Oculta con sus personas, los protocolos con sus pautas habilitadas para ella y 19 OT
    de ejemplo (`datos/ots-semilla.json`), ejecutadas contra las reglas reales. `accesos` trae las claves de las
    personas creadas en esta llamada: es la única vez que se ven. Se puede repetir sin duplicar."""
    _solo_equipo(x_clave_equipo)
    return semilla.cargar(cx)


@app.post("/interno/ots", status_code=201)
def dejar_ot_lista(p: OtDelEquipo, x_clave_equipo: str | None = Header(default=None)) -> dict:
    """El equipo deja una OT lista para ejecutar: pedida a nombre de un supervisor y asignada a un operador de su
    empresa, con las mismas reglas que si la pidiera él. Es lo que hace «Nueva demo». 403 si la pauta no está
    habilitada o el operador es de otra empresa; 404 si la persona no existe."""
    _solo_equipo(x_clave_equipo)
    supervisor = acceso.persona(cx, p.supervisor)
    acceso.operador_de_la_empresa(cx, supervisor, p.operador)
    ot = acceso.pedir_ot(cx, supervisor, p.pauta_id)["ot"]
    return servicios.asignar(ot, p.operador, supervisor["id"])


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


# ─── Servicio para clientes: con login, cada empresa ve lo suyo (app/acceso.py) ─
# Se entra con usuario y clave y se manda el token como `Authorization: Bearer <token>`.
# El supervisor pide y asigna OT de su empresa; el operador ve las que tiene asignadas.


@app.post("/auth/entrar")
def entrar(c: Credenciales) -> dict:
    """Devuelve el token, cuándo vence y quién es la persona, con su rol y su empresa. 401 si no calzan."""
    return acceso.entrar(cx, c.usuario, c.clave)


@app.post("/auth/salir", status_code=204)
def salir(authorization: str | None = Header(default=None)) -> None:
    _persona(authorization)
    acceso.salir(cx, _token(authorization))


@app.get("/yo")
def yo(authorization: str | None = Header(default=None)) -> dict:
    """Quién es el dueño del token: su id, nombre, rol y empresa."""
    return _persona(authorization)


@app.get("/cliente/pautas")
def pautas_para_clientes(authorization: str | None = Header(default=None)) -> list[dict]:
    """Las pautas que la empresa puede pedir: habilitadas para ella, aprobadas y con protocolo."""
    return acceso.pautas_habilitadas(cx, _persona(authorization)["cliente"]["id"])


@app.post("/cliente/ots", status_code=201)
def pedir_ot(p: PedidoOt, authorization: str | None = Header(default=None)) -> dict:
    """Un supervisor pide una OT de la última versión aprobada de una pauta habilitada. Sin `ot_id`, el
    servicio le pone uno. La OT queda de su empresa y a su nombre. 403 si no es supervisor o la pauta no
    está habilitada; 409 si la pauta no está lista o el id ya existe."""
    return acceso.pedir_ot(cx, _persona(authorization), p.pauta_id, p.ot_id)


@app.get("/cliente/ots")
def ots_para_clientes(authorization: str | None = Header(default=None)) -> list[dict]:
    """El supervisor ve todas las OT de su empresa; el operador, las que tiene asignadas. Cada una trae su
    `calificacion`, la misma de `GET /cliente/ots/{ot_id}`."""
    ots = acceso.ots_de(cx, _persona(authorization), servicios._ots_en_sesion())
    return [{**o, "calificacion": servicios.calificacion(o["ot"])} for o in ots]


@app.get("/cliente/ots/{ot_id}")
def ot_para_clientes(ot_id: str, authorization: str | None = Header(default=None)) -> dict:
    """Una OT con su avance y su calificación. 404 si no es de su empresa o, para un operador, si no es suya."""
    o = acceso.ot_de(cx, _persona(authorization), ot_id, servicios._ots_en_sesion())
    return {**o, "calificacion": servicios.calificacion(ot_id)}


@app.get("/cliente/ots/{ot_id}/ficha")
def ficha_para_clientes(ot_id: str, authorization: str | None = Header(default=None)) -> dict:
    """Lo que hace falta para ejecutar una OT: su avance, quién la pidió y quién la tiene, de qué protocolos sale
    y cada paso de su pauta con su instrucción y su evidencia, en la versión que la OT ejecuta. 404 como en
    `GET /cliente/ots/{ot_id}`."""
    acceso.ot_de(cx, _persona(authorization), ot_id)
    return acceso.ficha(cx, ot_id, servicios._ots_en_sesion())


@app.post("/cliente/ots/{ot_id}/sesion")
def iniciar_sesion_del_cliente(ot_id: str, s: SesionCliente, authorization: str | None = Header(default=None)) -> dict:
    """El operador que tiene la OT asignada la une a una estación con su token, sin la clave del equipo. El
    `operario` de la sesión es quien entró. Si la estación ejecuta otra OT abierta responde 409 y hay que repetir
    con `tomar` en true; 403 si esa OT es de otra empresa o si quien pide no es operador; 404 si la OT no es suya."""
    p = _persona(authorization)
    acceso.exige_estacion(cx, p, ot_id, s.edge_id, servicios.sesion(s.edge_id), s.tomar)
    return servicios.iniciar_sesion(ot_id, s.edge_id, p["id"])


@app.get("/cliente/operadores")
def operadores_del_cliente(authorization: str | None = Header(default=None)) -> list[dict]:
    """Los operadores de la empresa, para asignarles OT. Solo supervisor."""
    p = _persona(authorization)
    acceso.exige_rol(p, "supervisor")
    return acceso.personas_de(cx, p["cliente"]["id"], "operador")


@app.get("/cliente/personas")
def personas_del_cliente(authorization: str | None = Header(default=None)) -> list[dict]:
    """El `id`, el `nombre` y el `rol` de cada persona de la empresa, para mostrar nombres donde la bitácora
    guarda ids. Lo lee cualquier persona de la empresa, también un operador."""
    return acceso.nombres_de(cx, _persona(authorization)["cliente"]["id"])


@app.post("/cliente/ots/{ot_id}/asignar")
def asignar_ot_del_cliente(ot_id: str, a: AsignacionCliente, authorization: str | None = Header(default=None)) -> dict:
    """El supervisor deja una OT de su empresa en manos de un operador de su empresa. 403 si el operador es de
    otra; 409 si la OT está completa o ya tiene operador."""
    p = _persona(authorization)
    acceso.exige_rol(p, "supervisor")
    acceso.ot_de(cx, p, ot_id)
    acceso.operador_de_la_empresa(cx, p, a.operador)
    return servicios.asignar(ot_id, a.operador, p["id"])


# ─── Ejecutar la OT con login: el actor sale del token, no del cuerpo ───────


def _relevo_entregar(ot_id: str, actor: str) -> dict:
    fila = db.leer_ot(cx, ot_id)
    pauta = db.leer_pauta(cx, fila["pauta_id"], fila["pauta_version"])
    evs = db.eventos(cx, ot_id)
    estado = cerebro.estado_de_ot(pauta, evs)
    resumen = cerebro.redactar_resumen(estado, evs)
    servicios.agregar(Evento(ot_id=ot_id, tipo=TipoEvento.RELEVO_ENTREGADO, ts=db.ahora(), actor=actor, detalle=resumen))
    return {"resumen": resumen, "estado": estado}


def _relevo_recibir(ot_id: str, actor: str) -> dict:
    servicios.agregar(Evento(ot_id=ot_id, tipo=TipoEvento.RELEVO_RECIBIDO, ts=db.ahora(), actor=actor,
                             detalle=f"{actor} confirma que recibió el turno"))
    return {"firmado_por": actor}


def _de_la_empresa(p: dict, ot_id: str) -> dict:
    """La OT de la empresa de quien pide, aunque no la tenga asignada. 404 si es de otra."""
    supervisor = {**p, "rol": "supervisor"}
    return acceso.ot_de(cx, supervisor, ot_id, servicios._ots_en_sesion())


@app.get("/cliente/ots/{ot_id}/pasos")
def pasos_de_la_ot(ot_id: str, authorization: str | None = Header(default=None)) -> dict:
    """Cada paso de la OT en el orden de la pauta, con su estado, la capa y la evidencia que lo cerró, y cuál es el
    paso en curso. Es lo que la interfaz le muestra al operario. 404 si la OT no es suya."""
    acceso.ot_de(cx, _persona(authorization), ot_id)
    fila = db.leer_ot(cx, ot_id)
    return cerebro.estado_de_ot(db.leer_pauta(cx, fila["pauta_id"], fila["pauta_version"]), db.eventos(cx, ot_id))


@app.post("/cliente/ots/{ot_id}/declarar")
def declarar_del_cliente(ot_id: str, d: DeclaracionCliente, authorization: str | None = Header(default=None)) -> dict:
    """El operario que tiene la OT dice que hizo el paso. La evidencia manda: un paso de sensor no se cierra hablando, y
    un paso de cámara se juzga con el último cuadro de su estación. 403 si no es operador; 404 si la OT no es suya;
    409 si la OT ya está completa."""
    p = _persona(authorization)
    acceso.exige_rol(p, "operador")
    acceso.ot_de(cx, p, ot_id)
    return servicios.declarar(ot_id, p["id"], d.texto, d.paso_id)


@app.post("/cliente/ots/{ot_id}/pasos/{paso_id}/confirmar")
def confirmar_del_cliente(ot_id: str, paso_id: str, c: ConfirmacionCliente,
                          authorization: str | None = Header(default=None)) -> dict:
    """El operario que tiene la OT, o el supervisor, confirma el paso en curso aunque su sensor o la cámara no lo
    muestren. Queda quién y por qué, la OT pasa a warning y cuenta como desviación en las métricas. 404 si la OT no es
    suya; 409 si no es el paso en curso o falta el motivo."""
    p = _persona(authorization)
    acceso.ot_de(cx, p, ot_id)
    return servicios.confirmar_por_persona(ot_id, paso_id, p["id"], c.motivo)


@app.post("/cliente/ots/{ot_id}/relevo/entregar")
def entregar_del_cliente(ot_id: str, authorization: str | None = Header(default=None)) -> dict:
    """El operario que tiene la OT entrega el turno: la OT queda sin operador, en `entregada`, con el estado de cada paso
    para quien la reciba. 403 si no es operador; 404 si la OT no es suya; 409 si ya está completa."""
    p = _persona(authorization)
    acceso.exige_rol(p, "operador")
    if acceso.ot_de(cx, p, ot_id)["completa"]:
        raise ReglaDeNegocio(f"la OT {ot_id} ya está completa: no hay turno que entregar")
    return _relevo_entregar(ot_id, p["id"])


@app.post("/cliente/ots/{ot_id}/relevo/recibir")
def recibir_del_cliente(ot_id: str, authorization: str | None = Header(default=None)) -> dict:
    """Un operador de la empresa recibe una OT entregada y queda a su cargo. La firma queda en la bitácora con su nombre.
    403 si no es operador; 404 si la OT es de otra empresa; 409 si nadie la entregó."""
    p = _persona(authorization)
    acceso.exige_rol(p, "operador")
    if _de_la_empresa(p, ot_id)["estado_general"] != "entregada":
        raise ReglaDeNegocio(f"la OT {ot_id} no está entregada: no hay turno que recibir")
    return _relevo_recibir(ot_id, p["id"])


@app.get("/cliente/ots/{ot_id}/eventos")
def bitacora_del_cliente(ot_id: str, authorization: str | None = Header(default=None)) -> list[dict]:
    """La bitácora de la OT, en orden, como la guarda el servidor: solo agrega. 404 si la OT no es suya."""
    acceso.ot_de(cx, _persona(authorization), ot_id)
    return [evento_dict(e) for e in db.eventos(cx, ot_id)]


@app.get("/cliente/ots/{ot_id}/reporte", response_model=None)
def reporte_de_la_ot(ot_id: str, formato: Literal["json", "markdown"] = Query(default="json", description="`markdown` "
                     "devuelve el mismo reporte listo para leer o adjuntar."),
                     authorization: str | None = Header(default=None)) -> dict | PlainTextResponse:
    """El reporte de la OT, armado desde la bitácora por el código y no por un modelo: cada paso con la evidencia que lo
    cerró, su capa, su hora y sus intentos; las desviaciones con su clase y cuánto tardaron en resolverse; las
    confirmaciones por persona con su motivo; las observaciones; los relevos; y lo que quedó pendiente. Cada línea trae
    el `evento` que la sostiene, para citarlo. 404 si la OT no es suya."""
    p = _persona(authorization)
    ot = acceso.ot_de(cx, p, ot_id, servicios._ots_en_sesion())
    nombres = {x["id"]: x["nombre"] for x in acceso.nombres_de(cx, p["cliente"]["id"])}
    r = reporte.armar(cx, ot, servicios.calificacion(ot_id), nombres)
    if formato == "markdown":
        return PlainTextResponse(reporte.markdown(r), media_type="text/markdown; charset=utf-8")
    return r


# ─── Mejora continua y métricas de la empresa (app/mejora.py, app/metricas.py) ─
# Se leen de la bitácora al pedirlas, por pauta, equipo, paso o día, nunca por persona (ADR-0013, ADR-0014).

OrdenGrupos = Literal["desviaciones", "cumplimiento", "ots", "minutos"]
Desde = Query(default=None, description="Desde este día, incluido, según cuándo se abrió la OT (AAAA-MM-DD).")
Hasta = Query(default=None, description="Hasta este día, incluido (AAAA-MM-DD).")
Orden = Query(default="desviaciones", description="`desviaciones`: las más desviadas primero; `cumplimiento`: el peor "
              "primero; `ots`: las más ejecutadas primero; `minutos`: las más lentas primero.")
Limite = Query(default=50, ge=1, le=500, description="Cuántas devolver.")


def _ejecuciones(p: dict, desde: date | None = None, hasta: date | None = None) -> list[metricas.Ejecucion]:
    if desde and hasta and desde > hasta:
        raise HTTPException(422, f"desde ({desde}) es posterior a hasta ({hasta})")
    return metricas.ejecuciones(cx, acceso.ots_de(cx, p, servicios._ots_en_sesion()), desde, hasta)


def _supervisor(authorization: str | None) -> dict:
    p = _persona(authorization)
    acceso.exige_rol(p, "supervisor")
    return p


@app.post("/cliente/ots/{ot_id}/observaciones", status_code=201)
def observar(ot_id: str, o: Observacion, authorization: str | None = Header(default=None)) -> dict:
    """El operario que tiene la OT, o el supervisor de su empresa, deja lo que vio mientras se ejecuta: una pieza
    gastada, un paso que no calza con el equipo. No cierra ningún paso. Queda en la bitácora con quién lo dijo, y las
    de `pauta` y `seguridad` alimentan las propuestas de mejora. 404 si la OT o el paso no son suyos."""
    p = _persona(authorization)
    acceso.ot_de(cx, p, ot_id)
    return evento_dict(servicios.observar(ot_id, p["id"], o.texto, o.categoria, o.paso_id))


@app.get("/cliente/mejoras")
def mejoras_del_cliente(estado: Literal["abierta", "aceptada", "descartada", "aplicada", "superada"] | None = None,
                        authorization: str | None = Header(default=None)) -> list[dict]:
    """Las propuestas para mejorar las pautas de la empresa, las que más pesan primero. Una nace cuando el mismo paso
    de la misma versión tuvo señales en dos o más OT: alertas de orden o de control, conflictos, pasos que confirmó una
    persona porque la evidencia no los vio, y observaciones de los operarios. Cuando hay una versión nueva, `validacion`
    dice si el paso dejó de desviarse. Solo supervisor."""
    p = _supervisor(authorization)
    todas = mejora.propuestas(cx, _ejecuciones(p), p["cliente"]["id"])
    return [m for m in todas if estado is None or m["estado"] == estado]


@app.post("/cliente/mejoras/{propuesta_id}/revision")
def revisar_mejora(propuesta_id: str, r: Revision, authorization: str | None = Header(default=None)) -> dict:
    """El supervisor valida una propuesta: aceptarla la manda al equipo de Factum para la versión siguiente de la pauta;
    descartarla la cierra y pide una nota. Se puede cambiar de opinión: queda la última. 404 si no es de su empresa;
    409 si la pauta ya tiene una versión más nueva."""
    p = _supervisor(authorization)
    return mejora.revisar(cx, _ejecuciones(p), p["cliente"]["id"], propuesta_id, r.decision, r.nota, p["id"])


@app.get("/cliente/metricas")
def metricas_del_cliente(desde: date | None = Desde, hasta: date | None = Hasta,
                         authorization: str | None = Header(default=None)) -> dict:
    """La foto de la empresa: OT por estado, cuántas completas sin desviaciones, con qué evidencia se cerraron los pasos,
    las desviaciones por clase y cuánto tardan en resolverse, el tiempo de ejecución, los relevos, las observaciones y
    las propuestas de mejora. Solo supervisor."""
    p = _supervisor(authorization)
    es = _ejecuciones(p, desde, hasta)
    return {"periodo": {"desde": desde, "hasta": hasta}, **metricas.resumen(es),
            "mejoras": mejora.conteo(mejora.propuestas(cx, _ejecuciones(p), p["cliente"]["id"]))}


@app.get("/cliente/metricas/pautas")
def metricas_por_pauta(desde: date | None = Desde, hasta: date | None = Hasta, orden: OrdenGrupos = Orden,
                       limite: int = Limite, authorization: str | None = Header(default=None)) -> list[dict]:
    """Cada pauta que la empresa ejecutó: cumplimiento, desviaciones por clase, tiempo de ejecución, observaciones y el
    paso que más se desvía. Solo supervisor."""
    return metricas.por_pauta(cx, _ejecuciones(_supervisor(authorization), desde, hasta), orden, limite)


@app.get("/cliente/metricas/pautas/{pauta_id}/pasos")
def metricas_por_paso(pauta_id: str, version: int | None = Query(default=None, description="Sin versión, la última aprobada."),
                      orden: Literal["pauta", "desviaciones"] = Query(default="pauta", description="`pauta`: en el orden "
                      "de la pauta; `desviaciones`: los más desviados primero."),
                      desde: date | None = Desde, hasta: date | None = Hasta,
                      authorization: str | None = Header(default=None)) -> list[dict]:
    """Cada paso de una versión de la pauta: con qué evidencia se cerró, cuántas veces se desvió y qué observaron los
    operarios. Solo las OT de esa versión. 404 si la pauta no está habilitada para la empresa. Solo supervisor."""
    p = _supervisor(authorization)
    if pauta_id not in {x["id"] for x in acceso.pautas_habilitadas(cx, p["cliente"]["id"])}:
        raise db.NoExiste(f"pauta {pauta_id}")
    pauta = db.leer_pauta(cx, pauta_id, version or catalogo.ultima_aprobada(cx, pauta_id))
    return metricas.por_paso(_ejecuciones(p, desde, hasta), pauta, orden)


@app.get("/cliente/metricas/equipos")
def metricas_por_equipo(desde: date | None = Desde, hasta: date | None = Hasta, orden: OrdenGrupos = Orden,
                        limite: int = Limite, authorization: str | None = Header(default=None)) -> list[dict]:
    """Lo mismo por equipo, más lo que los operarios observaron de la máquina (categoría `equipo`). Solo supervisor."""
    return metricas.por_equipo(_ejecuciones(_supervisor(authorization), desde, hasta), orden, limite)


@app.get("/cliente/metricas/serie")
def metricas_en_el_tiempo(intervalo: Literal["dia", "semana"] = "dia", desde: date | None = Desde,
                          hasta: date | None = Hasta, authorization: str | None = Header(default=None)) -> list[dict]:
    """Por día o por semana, sin huecos: OT abiertas y completas, desviaciones, alertas de seguridad y observaciones,
    para graficar. Solo supervisor."""
    return metricas.serie(_ejecuciones(_supervisor(authorization), desde, hasta), intervalo)


# ─── Servicio interno: clientes, personas y qué pautas tiene cada uno ───────


@app.post("/interno/clientes", status_code=201)
def crear_cliente(c: ClienteNuevo, x_clave_equipo: str | None = Header(default=None)) -> dict:
    _solo_equipo(x_clave_equipo)
    return acceso.crear_cliente(cx, c.id, c.nombre, c.industria)


@app.get("/interno/clientes")
def listar_clientes(x_clave_equipo: str | None = Header(default=None)) -> list[dict]:
    _solo_equipo(x_clave_equipo)
    return acceso.listar_clientes(cx)


@app.get("/interno/clientes/{cliente_id}")
def leer_cliente(cliente_id: str, x_clave_equipo: str | None = Header(default=None)) -> dict:
    """El cliente con sus personas y las pautas que tiene habilitadas."""
    _solo_equipo(x_clave_equipo)
    return {**acceso._cliente(cx, cliente_id), "personas": acceso.personas_de(cx, cliente_id),
            "pautas": acceso.pautas_habilitadas(cx, cliente_id)}


@app.post("/interno/clientes/{cliente_id}/personas", status_code=201)
def crear_persona(cliente_id: str, n: PersonaNueva, x_clave_equipo: str | None = Header(default=None)) -> dict:
    """Crea la persona con una clave al azar. La respuesta trae la clave: es la única vez que se ve."""
    _solo_equipo(x_clave_equipo)
    persona, clave = acceso.crear_persona(cx, cliente_id, n.id, n.nombre, n.usuario, n.rol)
    return {"persona": persona, "clave": clave}


@app.post("/interno/personas/{persona_id}/clave")
def cambiar_clave(persona_id: str, x_clave_equipo: str | None = Header(default=None)) -> dict:
    """Una clave nueva al azar, que se ve una sola vez. Cierra las sesiones abiertas de esa persona."""
    _solo_equipo(x_clave_equipo)
    return {"persona": persona_id, "clave": acceso.nueva_clave(cx, persona_id)}


@app.get("/interno/inventario")
def inventario_del_servidor(x_clave_equipo: str | None = Header(default=None)) -> dict:
    """Qué puede comprobar este servidor, leído de la base: cada sensor con su valor actual, los valores que llegaron en la
    bitácora (o su rango, si es numérico), las pautas y pasos que lo usan y las reglas de peligro que lo miran; las clases
    del detector con la confianza con que se vieron y cuántas veces decidieron; y las preguntas visuales con lo que
    respondió la cámara. Es lo que necesita quien escribe una pauta para nombrar solo lo que existe."""
    _solo_equipo(x_clave_equipo)
    return inventario.inventario(cx, detector, servicios.sesiones())


@app.post("/interno/pautas/validar")
def validar_pauta(v: PautaAValidar, x_clave_equipo: str | None = Header(default=None)) -> dict:
    """Valida una pauta sin guardarla. `errores` impide crearla (mal formada o versión equivocada); `hallazgos` dice qué
    le va a fallar a la verificación: un control crítico que no cierra un sensor (V1), un paso que espera el valor de
    reposo de su sensor (V2), una reposición fuera de orden inverso (V3), una capa_minima que no calza (V4), y sensores,
    valores o clases que el servidor no conoce (I1 a I3). Con las comprobaciones de `app/analisis.py`: pasos que se
    cierran solos (A1), reglas de seguridad que disparan en una ejecución correcta (A2), citas que no están literales en
    el protocolo (A3) y pasos que la estación no puede cerrar (A4); y qué análisis vale la pena pedir. 404 si la
    estación o el protocolo no existen."""
    _solo_equipo(x_clave_equipo)
    estacion = inventario.estacion(v.estacion) if v.estacion else None
    return inventario.validar(cx, v.pauta, inventario.inventario(cx, detector, servicios.sesiones()), v.reposo,
                              estacion, v.analisis, v.protocolo_id)


@app.get("/interno/mejoras")
def mejoras_de_todos(estado: Literal["abierta", "aceptada", "descartada", "aplicada", "superada"] | None = "aceptada",
                     x_clave_equipo: str | None = Header(default=None)) -> list[dict]:
    """Las propuestas de mejora de cada empresa, con su `cliente`. Por defecto, las que un supervisor aceptó: son las
    que el equipo lleva a la versión siguiente de la pauta."""
    _solo_equipo(x_clave_equipo)
    salida = []
    for c in acceso.listar_clientes(cx):
        p = {"id": "equipo", "rol": "supervisor", "cliente": c}
        salida += [{**m, "cliente": c} for m in mejora.propuestas(cx, _ejecuciones(p), c["id"])
                   if estado is None or m["estado"] == estado]
    return salida


@app.put("/interno/clientes/{cliente_id}/pautas/{pauta_id}")
def habilitar_pauta(cliente_id: str, pauta_id: str, x_clave_equipo: str | None = Header(default=None)) -> list[dict]:
    _solo_equipo(x_clave_equipo)
    return acceso.habilitar(cx, cliente_id, pauta_id)


@app.delete("/interno/clientes/{cliente_id}/pautas/{pauta_id}", status_code=204)
def deshabilitar_pauta(cliente_id: str, pauta_id: str, x_clave_equipo: str | None = Header(default=None)) -> None:
    _solo_equipo(x_clave_equipo)
    acceso.deshabilitar(cx, cliente_id, pauta_id)


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


@app.get("/ot/{ot_id}/ficha")
def ficha_de_ot(ot_id: str, x_clave_equipo: str | None = Header(default=None)) -> dict:
    """Lo que la estación necesita para ejecutar una OT que ya existe: su avance, su operador, de qué protocolos
    sale y cada paso de su pauta con su instrucción y su evidencia. Con la clave del equipo trae además la
    empresa y los nombres de quien la pidió y de quien la tiene."""
    return acceso.ficha(cx, ot_id, servicios._ots_en_sesion(), con_empresa=_clave_valida(x_clave_equipo))


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


@app.get("/edge/{edge_id}/clases")
def clases_de_edge(edge_id: str) -> dict:
    """Las clases que pide la pauta de la OT en sesión: el edge las consulta y arma su detector con ellas.
    `detector_no_conoce` son las que el modelo del servidor no trae (hay que exportarlo de nuevo); sin
    detector en el servidor va vacío."""
    r = servicios.clases_de_edge(edge_id)
    return {**r, "detector_no_conoce": sorted(set(r["clases"]) - set(detector.clases)) if detector else []}


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
@app.get("/llms-full.txt", include_in_schema=False)
def guia_para_el_agente(request: Request) -> Response:
    """La guía en Markdown para el agente que se conecta: recorrido, WebSocket, errores y endpoints."""
    return Response(texto_de_la_guia(app, str(request.base_url)), media_type="text/markdown; charset=utf-8")


@app.get("/llms.txt", include_in_schema=False)
def indice_para_agentes(request: Request) -> Response:
    """El índice del estándar llms.txt: qué es Factum, cómo se entra, las skills y la documentación."""
    return Response(skills.llms_txt(str(request.base_url)), media_type="text/markdown; charset=utf-8")


@app.get("/skills", include_in_schema=False)
def skills_publicadas(request: Request) -> list[dict]:
    """Las skills de cliente, con su nombre, su descripción y dónde leerlas."""
    return skills.publicadas(str(request.base_url))


@app.get("/skills/{nombre}/SKILL.md", include_in_schema=False)
def skill(nombre: str) -> Response:
    if nombre not in skills.DE_CLIENTE:
        raise db.NoExiste(f"skill {nombre}; hay {', '.join(skills.DE_CLIENTE)}")
    return Response(skills.para_publicar(nombre), media_type="text/markdown; charset=utf-8")


@app.get("/referencia", include_in_schema=False)
def pagina_referencia() -> Response:
    """La referencia de la API para leer y probar, con Scalar: el documento de un cliente y el completo."""
    return referencia.pagina(app.openapi_url)


@app.get("/referencia/clientes.json", include_in_schema=False)
def referencia_para_clientes() -> dict:
    """El OpenAPI con solo lo que usa una empresa cliente."""
    return referencia.para_clientes(app)


@app.get("/camara")
def pagina_camara() -> FileResponse:
    """La cámara del celular del operario como edge de video."""
    return FileResponse(ESTATICO / "camara.html")


@app.get("/monitor")
def pagina_monitor() -> FileResponse:
    """Video, calificación, avisos y bitácora de una OT, en vivo."""
    return FileResponse(ESTATICO / "monitor.html")


@app.get("/analisis")
def pagina_analisis() -> FileResponse:
    """El reporte del supervisor: las métricas y las propuestas de mejora de su empresa (`/cliente/metricas`, `/cliente/mejoras`)."""
    return FileResponse(ESTATICO / "analisis.html")


@app.get("/simulador")
def pagina_simulador() -> FileResponse:
    """El simulador: la ejecución de una OT en 3D con las pautas y los operarios de esta base. Las OT son simuladas."""
    return FileResponse(ESTATICO / "simulador.html")


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
    return _relevo_entregar(ot_id, actor)


@app.post("/ot/{ot_id}/relevo/recibir")
def recibir_turno(ot_id: str, actor: str) -> dict:
    """El traspaso se firma: quién recibió y cuándo queda como evento."""
    return _relevo_recibir(ot_id, actor)


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
