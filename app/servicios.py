"""Los servicios en vivo: atribuir lo que llega del edge a la OT que se está ejecutando,
revisarlo con las capas, sostener sus avisos mientras duren y repartirlo a la UI.

El edge no sabe de OT: manda lecturas y video de su estación. La OT la elige el
operario en la interfaz, y al empezar abre una sesión que une su OT con ese edge.
Desde ahí cada lectura se atribuye a esa OT y solo a esa.

Por cada lectura atribuida:
1. Se guarda el último valor del sensor (db.sensores).
2. Seguridad: se evalúan las reglas de reglas.py. Una alerta entra a la bitácora
   cuando la condición empieza, y cuando desaparece entra su `alerta_resuelta`.
3. Si el paso actual se cierra con ese sensor, se evalúa y, si quedó verificado,
   entra su veredicto. El orden lo sigue imponiendo la app: solo el paso actual,
   y solo con una lectura de su propio sensor (ADR-0002).
4. Controles: un control crítico ya verificado que se deshace abre una alerta de
   capa 1, que se resuelve cuando el sensor vuelve.
5. Orden: una lectura que cierra un paso posterior al actual abre una alerta de
   capa 1, que se resuelve cuando se hace el paso saltado o se deshace lo adelantado.
6. Capa 2: si el valor es numérico, se califica contra su historia normal. La
   anomalía abre una alerta y la vuelta a lo normal la resuelve; diez lecturas
   idénticas seguidas abren el aviso de sensor pegado.
7. Todo lo nuevo, la calificación vigente y los avisos activos salen por el bus.

Qué alertas siguen activas se lee de la bitácora, no de la memoria: una alerta
está activa mientras no haya un `alerta_resuelta` que la apunte. Así un reinicio
del servidor no las pierde.
"""

from __future__ import annotations

import logging
import sqlite3
import time
from collections import defaultdict, deque
from collections.abc import Callable
from dataclasses import asdict

from app import catalogo, db, verificacion
from app.bus import Bus, canal_edge, canal_ot
from app.catalogo import ReglaDeNegocio
from app.cerebro import estado_de_ot
from app.contratos import Capa, Estado, Evento, TipoEvento, TipoEvidencia
from app.reglas import (
    controles_deshechos,
    desviacion_de_orden,
    estados_desde_eventos,
    evaluar,
    paso_actual,
    por_deteccion,
    reglas_seguridad,
)
from app.contratos import Pauta, Paso, Veredicto
from app.scoring import Nivel, avisos, calificar_evento, capa2, frescura, peor, vigentes
from app.video import SEGUNDOS_GUARDADOS, Video

log = logging.getLogger(__name__)

HISTORIA_MAX = 300
SEQ_RECORDADOS = 500
IGUALES_PEGADO = 10
# Capa 2 de cámara: se juzga con las detecciones del último segundo, y solo si hay
# suficientes (a ~18/s, 5 son ~0,3 s) para que un cuadro suelto no cierre un paso.
VENTANA_DETECCION_S = 1.0
DETECCIONES_MIN = 5
JUICIO_CADA_S = 0.5  # cada cuánto se revisa el paso con lo que llega del edge

# El juez de cámara recibe la pregunta del paso y el cuadro actual (o None si no hay video).
JuezConCuadro = Callable[[str, bytes | None], tuple[bool, float]]

_ESQUEMA = """
CREATE TABLE IF NOT EXISTS sesiones (
    edge_id TEXT PRIMARY KEY, ot_id TEXT NOT NULL, operario TEXT NOT NULL, desde TEXT NOT NULL
);
"""


def evento_dict(ev: Evento) -> dict:
    d = asdict(ev)
    c = calificar_evento(ev)
    d["calificacion"] = c.como_dict() if c else None
    return d


def _clave_seguridad(detalle: str) -> str:
    return f"seguridad:{detalle}"


def _clave_senal(sensor_id: str) -> str:
    return f"senal:{sensor_id}"


def _paso(pauta: Pauta, paso_id: str) -> Paso:
    """El paso que nombró el cliente: si no es de la pauta, es un 404 y no un bug."""
    try:
        return pauta.paso(paso_id)
    except KeyError:
        raise db.NoExiste(f"paso {paso_id} de la pauta {pauta.id}") from None


def _edad_s(ts: str) -> float:
    from datetime import UTC, datetime

    return (datetime.now(UTC) - datetime.fromisoformat(ts)).total_seconds()


class Servicios:
    def __init__(
        self,
        cx: sqlite3.Connection,
        bus: Bus | None = None,
        video: Video | None = None,
        juez: JuezConCuadro | None = None,
    ) -> None:
        self.cx = cx
        self.bus = bus or Bus()
        self.video = video or Video()
        self.juez = juez or verificacion.juez_camara
        cx.executescript(_ESQUEMA)
        catalogo.preparar(cx)
        self._historia: dict[str, deque[float]] = defaultdict(lambda: deque(maxlen=HISTORIA_MAX))
        self._seq: dict[str, deque[int]] = defaultdict(lambda: deque(maxlen=SEQ_RECORDADOS))
        self._iguales: dict[str, tuple[float, int]] = {}
        self._ultimo_juicio: dict[str, float] = defaultdict(float)

    # ─── Sesión: qué OT ejecuta cada edge ──────────────────────────────────

    def iniciar_sesion(self, ot_id: str, edge_id: str, operario: str) -> dict:
        db.leer_ot(self.cx, ot_id)
        self.cx.execute(
            "INSERT OR REPLACE INTO sesiones (edge_id, ot_id, operario, desde) VALUES (?, ?, ?, ?)",
            (edge_id, ot_id, operario, db.ahora()),
        )
        self.cx.commit()
        sesion = self.sesion(edge_id)
        self.bus.publicar(canal_ot(ot_id), {"tipo": "sesion", "sesion": sesion, "video": self._video_de(edge_id)})
        return sesion

    def terminar_sesion(self, edge_id: str) -> None:
        self.cx.execute("DELETE FROM sesiones WHERE edge_id = ?", (edge_id,))
        self.cx.commit()

    def sesion(self, edge_id: str) -> dict | None:
        f = self.cx.execute("SELECT * FROM sesiones WHERE edge_id = ?", (edge_id,)).fetchone()
        return dict(f) if f else None

    def sesiones(self) -> list[dict]:
        return [dict(f) for f in self.cx.execute("SELECT * FROM sesiones ORDER BY desde").fetchall()]

    def sesion_de_ot(self, ot_id: str) -> dict | None:
        f = self.cx.execute("SELECT * FROM sesiones WHERE ot_id = ?", (ot_id,)).fetchone()
        return dict(f) if f else None

    def _video_de(self, edge_id: str) -> dict:
        return {**self.video.estado(edge_id), "url": f"/edge/{edge_id}/video.mjpg"}

    def recibir_detecciones(self, edge_id: str, d: dict) -> dict:
        """Lo que vio el modelo del edge. Va en vivo a la UI; no escribe en la bitácora
        (son varias por segundo): queda como evidencia cuando un paso de cámara se juzga."""
        det = self.video.recibir_detecciones(edge_id, d)
        mensaje = {"tipo": "detecciones", "edge_id": edge_id, **det}
        self.bus.publicar(canal_edge(edge_id), mensaje)
        sesion = self.sesion(edge_id)
        if sesion is not None:
            self.bus.publicar(canal_ot(sesion["ot_id"]), mensaje)
            if det["ts"] - self._ultimo_juicio[edge_id] >= JUICIO_CADA_S:
                self._ultimo_juicio[edge_id] = det["ts"]
                if self._paso_por_deteccion(sesion["ot_id"], edge_id):
                    self.publicar_calificacion(sesion["ot_id"])
        return det

    def _detecciones_para_juzgar(self, edge_id: str) -> list[dict]:
        dets = self.video.detecciones_recientes(edge_id, VENTANA_DETECCION_S)
        return dets if len(dets) >= DETECCIONES_MIN else []

    def _paso_por_deteccion(self, ot_id: str, edge_id: str) -> list[Evento]:
        """Capa 2 de cámara sin que el operario hable: solo el paso actual, solo si es de
        cámara con `deteccion`, y solo si el modelo del edge está seguro (ADR-0002, 0004)."""
        fila = db.leer_ot(self.cx, ot_id)
        pauta = db.leer_pauta(self.cx, fila["pauta_id"], fila["pauta_version"])
        paso = paso_actual(pauta, estados_desde_eventos(db.eventos(self.cx, ot_id)))
        if paso is None or paso.deteccion is None:
            return []
        v = por_deteccion(paso, self._detecciones_para_juzgar(edge_id))
        if v is None:
            return []
        return [self.agregar(Evento(ot_id=ot_id, tipo=TipoEvento.VEREDICTO, ts=db.ahora(), actor="sistema",
                                    paso_id=paso.id, estado=v.estado, capa=v.capa,
                                    evidencia=self._con_cuadro(v.evidencia, ot_id, paso.id, edge_id),
                                    detalle=v.detalle))]

    def _con_cuadro(self, evidencia: dict | None, ot_id: str, paso_id: str, edge_id: str | None) -> dict | None:
        """El cuadro que estaba en pantalla queda en disco como evidencia del veredicto."""
        if evidencia is None:
            return None
        cuadro = self.video.ultimo(edge_id) if edge_id else None
        ruta = None
        if cuadro:
            try:
                ruta = self.video.guardar_evidencia(cuadro, f"{ot_id}-{paso_id}-{cuadro.n}")
            except OSError:  # sin disco o carpeta rota: se pierde la foto, no el veredicto
                log.exception("no se pudo guardar el cuadro de %s %s", ot_id, paso_id)
        return {**evidencia, "cuadro": ruta}

    # ─── Bitácora: agregar y repartir ──────────────────────────────────────

    def agregar(self, ev: Evento) -> Evento:
        """Toda escritura a la bitácora pasa por acá para que la UI la vea al instante."""
        db.agregar(self.cx, ev)
        self.bus.publicar(canal_ot(ev.ot_id), {"tipo": "evento", "evento": evento_dict(ev)})
        return ev

    def alertas_activas(self, ot_id: str) -> dict[str, Evento]:
        """Clave → evento que la abrió, para las alertas que todavía no se resolvieron."""
        activas: dict[str, Evento] = {}
        for ev in db.eventos(self.cx, ot_id):
            clave = (ev.evidencia or {}).get("clave")
            if ev.tipo is TipoEvento.ALERTA and clave:
                activas[clave] = ev
            elif ev.tipo is TipoEvento.ALERTA_RESUELTA:
                resuelve = (ev.evidencia or {}).get("resuelve")
                activas = {k: e for k, e in activas.items() if e.id != resuelve}
        return activas

    def calificacion(self, ot_id: str) -> dict:
        partes = self._vigentes(ot_id)
        return {**peor(partes).como_dict(), "avisos": avisos(partes)}

    def _vigentes(self, ot_id: str):
        """Lo vigente: veredictos, seguridad con los sensores de ahora, y las alertas abiertas
        que no se recalculan de los sensores (orden, control, señal). La seguridad no se suma
        acá porque vigentes() ya la evalúa con los sensores actuales."""
        evs = db.eventos(self.cx, ot_id)
        abiertas = [
            c for clave, ev in self.alertas_activas(ot_id).items()
            if not clave.startswith("seguridad:") and (c := calificar_evento(ev)) is not None
        ]
        return vigentes(evs, db.estado_sensores(self.cx), [*abiertas, *self._frescura(ot_id, evs)])

    def _frescura(self, ot_id: str, evs) -> list:
        """Si el sensor del paso en curso dejó de mandar, lo que dice ya no es seguro."""
        fila = db.leer_ot(self.cx, ot_id)
        pauta = db.leer_pauta(self.cx, fila["pauta_id"], fila["pauta_version"])
        paso = paso_actual(pauta, estados_desde_eventos(evs))
        if paso is None or paso.sensor is None:
            return []
        f = self.cx.execute("SELECT ts FROM sensores WHERE id = ?", (paso.sensor.id,)).fetchone()
        c = frescura(paso.sensor.id, _edad_s(f["ts"])) if f else None
        return [c] if c else []

    def publicar_calificacion(self, ot_id: str) -> dict:
        c = self.calificacion(ot_id)
        self.bus.publicar(canal_ot(ot_id), {"tipo": "calificacion_ot", "calificacion": c})
        return c

    def snapshot(self, ot_id: str, desde: int = 0) -> dict:
        """Lo que la UI necesita al conectarse: estado, calificación, avisos, video y bitácora."""
        fila = db.leer_ot(self.cx, ot_id)
        pauta = db.leer_pauta(self.cx, fila["pauta_id"], fila["pauta_version"])
        evs = db.eventos(self.cx, ot_id)
        sesion = self.sesion_de_ot(ot_id)
        return {
            "tipo": "snapshot",
            "ot": ot_id,
            "estado": estado_de_ot(pauta, evs),
            "calificacion": self.calificacion(ot_id),
            "alertas_activas": [evento_dict(e) for e in self.alertas_activas(ot_id).values()],
            "sesion": sesion,
            "video": self._video_de(sesion["edge_id"]) if sesion else None,
            "sensores": db.estado_sensores(self.cx),
            "bitacora": [evento_dict(e) for e in evs if (e.id or 0) > desde],
        }

    # ─── Lo que dice el operario ───────────────────────────────────────────

    def declarar(self, ot_id: str, actor: str, texto: str, paso_id: str | None = None) -> dict:
        """El operario habla; la evidencia manda. Un paso de cámara se juzga con el cuadro actual.

        `paso_id` es el paso que la app le mostraba. Si su sensor ya lo cerró, la palabra
        llegó tarde: se registra y no se evalúa contra el paso siguiente. En cualquier otro
        caso se evalúa el paso actual, porque el orden lo impone la app (ADR-0002).
        """
        fila = db.leer_ot(self.cx, ot_id)
        pauta = db.leer_pauta(self.cx, fila["pauta_id"], fila["pauta_version"])
        estados = estados_desde_eventos(db.eventos(self.cx, ot_id))
        if paso_id is not None:
            nombrado = _paso(pauta, paso_id)
            if estados.get(paso_id) is Estado.VERIFICADO:
                self.agregar(Evento(ot_id=ot_id, tipo=TipoEvento.DECLARACION, ts=db.ahora(), actor=actor,
                                    paso_id=paso_id, declarado=texto,
                                    detalle=f"confirma «{nombrado.titulo}», que su evidencia ya había cerrado"))
                calificacion = self.publicar_calificacion(ot_id)
                return {"paso": paso_id, "estado": str(Estado.VERIFICADO), "capa": None,
                        "detalle": "la evidencia ya había cerrado este paso; la declaración queda registrada",
                        "interrumpe": False, "evidencia": None, "calificacion": None, "calificacion_ot": calificacion}
        paso = paso_actual(pauta, estados)
        if paso is None:
            raise ReglaDeNegocio("la pauta ya está completa")

        self.agregar(Evento(ot_id=ot_id, tipo=TipoEvento.DECLARACION, ts=db.ahora(), actor=actor,
                            paso_id=paso.id, declarado=texto, detalle=f"declara sobre «{paso.titulo}»"))

        cuadro, edge_id, v = None, None, None
        if paso.tipo_evidencia is TipoEvidencia.CAMARA:
            sesion = self.sesion_de_ot(ot_id)
            edge_id = sesion["edge_id"] if sesion else None
            cuadro = self.video.ultimo(edge_id) if edge_id else None
            if cuadro is not None and time.time() - cuadro.ts > SEGUNDOS_GUARDADOS:
                cuadro = None
            # Capa 2 primero: si el modelo del edge está seguro, decide él; si no, el juez (capa 3).
            v = por_deteccion(paso, self._detecciones_para_juzgar(edge_id)) if edge_id else None
            if v is None and cuadro is None:
                # Sin un cuadro reciente el juez no tiene qué mirar: su respuesta no es evidencia.
                v = Veredicto(Estado.NO_VERIFICADO, Capa.MODELO,
                              f"sin video reciente del edge: no hay cuadro para responder «{paso.pregunta_visual}»")

        if v is None:
            v = evaluar(paso, texto, db.estado_sensores(self.cx),
                        lambda pregunta: self.juez(pregunta, cuadro.jpeg if cuadro else None))
        evidencia = dict(v.evidencia) if v.evidencia else None
        if paso.tipo_evidencia is TipoEvidencia.CAMARA:
            evidencia = self._con_cuadro(evidencia, ot_id, paso.id, edge_id)

        ev = self.agregar(Evento(ot_id=ot_id, tipo=TipoEvento.VEREDICTO, ts=db.ahora(), actor="sistema",
                                 paso_id=paso.id, estado=v.estado, capa=v.capa, declarado=texto,
                                 evidencia=evidencia, detalle=v.detalle))
        calificacion = self.publicar_calificacion(ot_id)
        return {"paso": paso.id, "estado": str(v.estado), "capa": v.capa, "detalle": v.detalle,
                "interrumpe": v.interrumpe, "evidencia": evidencia,
                "calificacion": evento_dict(ev)["calificacion"], "calificacion_ot": calificacion}

    def confirmar_por_persona(self, ot_id: str, paso_id: str, actor: str, motivo: str) -> dict:
        """Una persona afirma que el paso en curso está hecho aunque la evidencia no lo muestre.

        Se le cree, pero no en silencio (LOGICA): queda quién, el motivo y qué marcaba
        el sensor, la OT queda en warning y la seguridad se sigue evaluando con los
        sensores reales. Solo el paso en curso, y no un paso de confirmación.
        """
        pauta, estados = self._pauta_y_estados(ot_id)
        paso = _paso(pauta, paso_id)
        actual = paso_actual(pauta, estados)
        if actual is None:
            raise ReglaDeNegocio("la pauta ya está completa")
        if paso.id != actual.id:
            raise ReglaDeNegocio(f"solo se confirma el paso en curso ({actual.id}): el orden lo impone la app")
        if paso.tipo_evidencia is TipoEvidencia.CONFIRMACION:
            raise ReglaDeNegocio(f"«{paso.titulo}» es de confirmación: se cierra declarando")
        if not actor or actor == "sistema":
            raise ReglaDeNegocio("un paso lo confirma una persona, no el sistema")
        if not motivo.strip():
            raise ReglaDeNegocio("confirmar contra la evidencia necesita un motivo")

        valor = db.estado_sensores(self.cx).get(paso.sensor.id) if paso.sensor else None
        contra = ({"sensor": paso.sensor.id, "valor": valor, "espera": paso.sensor.espera} if paso.sensor
                  else {"camara": paso.pregunta_visual})
        que = (f"{paso.sensor.id} = {valor}, se esperaba {paso.sensor.espera}" if paso.sensor
               else "la cámara no lo confirmó")
        ev = self.agregar(Evento(
            ot_id=ot_id, tipo=TipoEvento.VEREDICTO, ts=db.ahora(), actor=actor, paso_id=paso.id,
            estado=Estado.VERIFICADO, capa=None, declarado=motivo,
            evidencia={"tipo": "persona", "motivo": motivo, "contra": contra},
            detalle=f"{actor} confirma «{paso.titulo}» contra la evidencia ({que}): {motivo}",
        ))
        self._resolver_orden(ot_id, f"lo confirmó {actor}")
        calificacion = self.publicar_calificacion(ot_id)
        d = evento_dict(ev)
        return {"paso": paso.id, "estado": str(Estado.VERIFICADO), "capa": None, "detalle": ev.detalle,
                "interrumpe": False, "evidencia": ev.evidencia, "calificacion": d["calificacion"],
                "calificacion_ot": calificacion}

    def _por_persona(self, ot_id: str) -> set[str]:
        """Pasos cuyo último veredicto lo puso una persona contra la evidencia."""
        ultimo: dict[str, Evento] = {}
        for ev in db.eventos(self.cx, ot_id):
            if ev.tipo is TipoEvento.VEREDICTO and ev.paso_id:
                ultimo[ev.paso_id] = ev
        return {p for p, ev in ultimo.items() if (ev.evidencia or {}).get("tipo") == "persona"}

    # ─── Lo que llega del edge ─────────────────────────────────────────────

    def recibir_lectura(
        self, edge_id: str, sensor_id: str, valor: str, seq: int | None = None
    ) -> dict:
        if seq is not None:
            if seq in self._seq[edge_id]:
                return {"duplicada": True, "ot": None, "eventos": []}
            self._seq[edge_id].append(seq)

        db.escribir_sensor(self.cx, sensor_id, valor)
        lectura = {"tipo": "lectura", "edge_id": edge_id, "sensor_id": sensor_id, "valor": valor, "ts": db.ahora()}
        self.bus.publicar(canal_edge(edge_id), lectura)

        sesion = self.sesion(edge_id)
        if sesion is None:
            return {"duplicada": False, "ot": None, "eventos": []}

        ot_id = sesion["ot_id"]
        self.bus.publicar(canal_ot(ot_id), lectura)
        nuevos = [
            *self._seguridad(ot_id, sensor_id, valor),
            *self._paso_por_sensor(ot_id, sensor_id),
            *self._controles(ot_id, sensor_id, valor),
            *self._orden(ot_id, sensor_id, valor),
            *self._senal(ot_id, sensor_id, valor),
        ]
        calificacion = self.publicar_calificacion(ot_id)
        return {
            "duplicada": False,
            "ot": ot_id,
            "eventos": [evento_dict(e) for e in nuevos],
            "calificacion": calificacion,
        }

    def _resolver(self, ot_id: str, abierta: Evento, detalle: str, evidencia: dict) -> Evento:
        return self.agregar(Evento(
            ot_id=ot_id, tipo=TipoEvento.ALERTA_RESUELTA, ts=db.ahora(), actor="sistema",
            capa=abierta.capa, detalle=detalle,
            evidencia={"resuelve": abierta.id, "clave": (abierta.evidencia or {}).get("clave"), **evidencia},
        ))

    def _seguridad(self, ot_id: str, sensor_id: str, valor: str) -> list[Evento]:
        sensores = db.estado_sensores(self.cx)
        alertas = {_clave_seguridad(a.detalle): a for a in reglas_seguridad(sensores)}
        activas = {k: e for k, e in self.alertas_activas(ot_id).items() if k.startswith("seguridad:")}
        nuevos = [
            self.agregar(Evento(ot_id=ot_id, tipo=TipoEvento.ALERTA, ts=db.ahora(), actor="sistema",
                                estado=a.estado, capa=a.capa, detalle=a.detalle,
                                evidencia={**(a.evidencia or {}), "clave": clave}))
            for clave, a in alertas.items() if clave not in activas
        ]
        nuevos += [
            self._resolver(ot_id, abierta, f"Se normalizó con {sensor_id} = {valor}: {abierta.detalle}",
                           {"tipo": "sensor", "sensores": sensores})
            for clave, abierta in activas.items() if clave not in alertas
        ]
        return nuevos

    def _abrir(self, ot_id: str, v: Veredicto, clave: str) -> Evento:
        return self.agregar(Evento(ot_id=ot_id, tipo=TipoEvento.ALERTA, ts=db.ahora(), actor="sistema",
                                   estado=v.estado, capa=v.capa, detalle=v.detalle,
                                   evidencia={**(v.evidencia or {}), "clave": clave}))

    def _pauta_y_estados(self, ot_id: str):
        fila = db.leer_ot(self.cx, ot_id)
        pauta = db.leer_pauta(self.cx, fila["pauta_id"], fila["pauta_version"])
        return pauta, estados_desde_eventos(db.eventos(self.cx, ot_id))

    def _controles(self, ot_id: str, sensor_id: str, valor: str) -> list[Evento]:
        pauta, estados = self._pauta_y_estados(ot_id)
        sensores = db.estado_sensores(self.cx)
        ahora = {f"control:{v.evidencia['paso']}": v
                 for v in controles_deshechos(pauta, estados, sensores, self._por_persona(ot_id))}
        activas = {k: e for k, e in self.alertas_activas(ot_id).items() if k.startswith("control:")}
        nuevos = [self._abrir(ot_id, v, clave) for clave, v in ahora.items() if clave not in activas]
        nuevos += [
            self._resolver(ot_id, abierta, f"Control repuesto con {sensor_id} = {valor}: {abierta.detalle}",
                           {"tipo": "control", "sensor": sensor_id, "valor": valor})
            for clave, abierta in activas.items() if clave not in ahora
        ]
        return nuevos

    def _resolver_orden(self, ot_id: str, por: str = "") -> list[Evento]:
        """Cierra las alertas de orden cuyo paso saltado ya se hizo o cuyo adelanto se deshizo."""
        _, estados = self._pauta_y_estados(ot_id)
        sensores = db.estado_sensores(self.cx)
        nuevos = []
        for clave, abierta in self.alertas_activas(ot_id).items():
            if not clave.startswith("orden:"):
                continue
            ev = abierta.evidencia or {}
            if estados.get(ev.get("pendiente")) is Estado.VERIFICADO:
                motivo = f"se hizo el paso saltado ({ev.get('pendiente')}{', ' + por if por else ''})"
            elif sensores.get(ev.get("sensor")) != ev.get("valor"):
                motivo = f"se deshizo lo adelantado ({ev.get('sensor')} = {sensores.get(ev.get('sensor'))})"
            else:
                continue
            nuevos.append(self._resolver(ot_id, abierta, f"Orden resuelto: {motivo}. {abierta.detalle}",
                                         {"tipo": "orden", "sensor": ev.get("sensor"),
                                          "valor": sensores.get(ev.get("sensor"))}))
        return nuevos

    def _orden(self, ot_id: str, sensor_id: str, valor: str) -> list[Evento]:
        pauta, estados = self._pauta_y_estados(ot_id)
        nuevos = self._resolver_orden(ot_id)
        # Deshacer un control ya cuenta como control perdido: no se avisa dos veces lo mismo.
        perdido = any(k.startswith("control:") and (e.evidencia or {}).get("sensor") == sensor_id
                      for k, e in self.alertas_activas(ot_id).items())
        v = None if perdido else desviacion_de_orden(pauta, estados, sensor_id, valor)
        if v is not None and (clave := f"orden:{v.evidencia['adelantado']}") not in self.alertas_activas(ot_id):
            nuevos.append(self._abrir(ot_id, v, clave))
        return nuevos

    def _paso_por_sensor(self, ot_id: str, sensor_id: str) -> list[Evento]:
        fila = db.leer_ot(self.cx, ot_id)
        pauta = db.leer_pauta(self.cx, fila["pauta_id"], fila["pauta_version"])
        estados = estados_desde_eventos(db.eventos(self.cx, ot_id))
        paso = paso_actual(pauta, estados)
        if (
            paso is None
            or paso.tipo_evidencia is not TipoEvidencia.SENSOR
            or paso.sensor is None
            or paso.sensor.id != sensor_id
        ):
            return []
        v = evaluar(paso, None, db.estado_sensores(self.cx))
        if v.estado is not Estado.VERIFICADO:
            return []
        return [
            self.agregar(Evento(ot_id=ot_id, tipo=TipoEvento.VEREDICTO, ts=db.ahora(), actor="sistema",
                                paso_id=paso.id, estado=v.estado, capa=v.capa,
                                evidencia=v.evidencia, detalle=v.detalle))
        ]

    def _senal(self, ot_id: str, sensor_id: str, valor: str) -> list[Evento]:
        try:
            x = float(valor)
        except ValueError:
            return []
        historia = self._historia[sensor_id]
        c = capa2(sensor_id, list(historia), x)
        if c.nivel is Nivel.OK:
            # La historia es la de lo normal: una falla que se sostiene no pasa a ser la referencia.
            historia.append(x)

        nuevos = self._pegado(ot_id, sensor_id, x)
        clave = _clave_senal(sensor_id)
        abierta = self.alertas_activas(ot_id).get(clave)
        if c.nivel is Nivel.WARNING and abierta is None:
            return nuevos + [self.agregar(Evento(
                ot_id=ot_id, tipo=TipoEvento.ALERTA, ts=db.ahora(), actor="sistema",
                capa=Capa.APRENDIZAJE, detalle=c.motivos[0],
                evidencia={"tipo": "senal", "sensor": sensor_id, "valor": x,
                           "certeza": round(c.certeza, 2), "clave": clave},
            ))]
        if c.nivel is Nivel.OK and abierta is not None:
            return nuevos + [self._resolver(ot_id, abierta, f"{sensor_id} volvió a lo normal: {x:g}",
                                            {"tipo": "senal", "sensor": sensor_id, "valor": x})]
        return nuevos

    def _pegado(self, ot_id: str, sensor_id: str, x: float) -> list[Evento]:
        """Diez lecturas idénticas seguidas: falla del sensor, no del equipo. Capa 2, no interrumpe."""
        previo, n = self._iguales.get(sensor_id, (None, 0))
        n = n + 1 if x == previo else 1
        self._iguales[sensor_id] = (x, n)
        clave = f"pegado:{sensor_id}"
        abierta = self.alertas_activas(ot_id).get(clave)
        if n >= IGUALES_PEGADO and abierta is None:
            return [self.agregar(Evento(
                ot_id=ot_id, tipo=TipoEvento.ALERTA, ts=db.ahora(), actor="sistema", capa=Capa.APRENDIZAJE,
                detalle=f"{sensor_id} lleva {n} lecturas idénticas ({x:g}): el sensor puede estar pegado",
                evidencia={"tipo": "pegado", "sensor": sensor_id, "valor": x, "certeza": 0.5, "clave": clave},
            ))]
        if n == 1 and abierta is not None:
            return [self._resolver(ot_id, abierta, f"{sensor_id} volvió a variar: {x:g}",
                                   {"tipo": "pegado", "sensor": sensor_id, "valor": x})]
        return []
