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
4. Capa 2: si el valor es numérico, se califica contra su historia. La anomalía
   abre una alerta de capa 2 y la vuelta a lo normal la resuelve.
5. Todo lo nuevo, la calificación vigente y los avisos activos salen por el bus.

Qué alertas siguen activas se lee de la bitácora, no de la memoria: una alerta
está activa mientras no haya un `alerta_resuelta` que la apunte. Así un reinicio
del servidor no las pierde.
"""

from __future__ import annotations

import sqlite3
from collections import defaultdict, deque
from collections.abc import Callable
from dataclasses import asdict

from app import catalogo, db, verificacion
from app.bus import Bus, canal_edge, canal_ot
from app.catalogo import ReglaDeNegocio
from app.cerebro import estado_de_ot
from app.contratos import Capa, Estado, Evento, TipoEvento, TipoEvidencia
from app.reglas import estados_desde_eventos, evaluar, paso_actual, reglas_seguridad
from app.scoring import Nivel, avisos, calificar_evento, capa2, peor, vigentes
from app.video import Video

HISTORIA_MAX = 300
SEQ_RECORDADOS = 500

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
        evs = db.eventos(self.cx, ot_id)
        senales = [
            c for ev in self.alertas_activas(ot_id).values()
            if ev.capa == Capa.APRENDIZAJE and (c := calificar_evento(ev)) is not None
        ]
        return vigentes(evs, db.estado_sensores(self.cx), senales)

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

    def declarar(self, ot_id: str, actor: str, texto: str) -> dict:
        """El operario habla; la evidencia manda. Un paso de cámara se juzga con el cuadro actual."""
        fila = db.leer_ot(self.cx, ot_id)
        pauta = db.leer_pauta(self.cx, fila["pauta_id"], fila["pauta_version"])
        paso = paso_actual(pauta, estados_desde_eventos(db.eventos(self.cx, ot_id)))
        if paso is None:
            raise ReglaDeNegocio("la pauta ya está completa")

        self.agregar(Evento(ot_id=ot_id, tipo=TipoEvento.DECLARACION, ts=db.ahora(), actor=actor,
                            paso_id=paso.id, declarado=texto, detalle=f"declara sobre «{paso.titulo}»"))

        cuadro = None
        if paso.tipo_evidencia is TipoEvidencia.CAMARA:
            sesion = self.sesion_de_ot(ot_id)
            cuadro = self.video.ultimo(sesion["edge_id"]) if sesion else None

        v = evaluar(paso, texto, db.estado_sensores(self.cx),
                    lambda pregunta: self.juez(pregunta, cuadro.jpeg if cuadro else None))
        evidencia = dict(v.evidencia) if v.evidencia else None
        if paso.tipo_evidencia is TipoEvidencia.CAMARA and evidencia is not None:
            evidencia["cuadro"] = (
                self.video.guardar_evidencia(cuadro, f"{ot_id}-{paso.id}-{cuadro.n}") if cuadro else None
            )

        ev = self.agregar(Evento(ot_id=ot_id, tipo=TipoEvento.VEREDICTO, ts=db.ahora(), actor="sistema",
                                 paso_id=paso.id, estado=v.estado, capa=v.capa, declarado=texto,
                                 evidencia=evidencia, detalle=v.detalle))
        calificacion = self.publicar_calificacion(ot_id)
        return {"paso": paso.id, "estado": str(v.estado), "capa": v.capa, "detalle": v.detalle,
                "interrumpe": v.interrumpe, "evidencia": evidencia,
                "calificacion": evento_dict(ev)["calificacion"], "calificacion_ot": calificacion}

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
        historia.append(x)

        clave = _clave_senal(sensor_id)
        abierta = self.alertas_activas(ot_id).get(clave)
        if c.nivel is Nivel.WARNING and abierta is None:
            return [self.agregar(Evento(
                ot_id=ot_id, tipo=TipoEvento.ALERTA, ts=db.ahora(), actor="sistema",
                capa=Capa.APRENDIZAJE, detalle=c.motivos[0],
                evidencia={"tipo": "senal", "sensor": sensor_id, "valor": x,
                           "certeza": round(c.certeza, 2), "clave": clave},
            ))]
        if c.nivel is Nivel.OK and abierta is not None:
            return [self._resolver(ot_id, abierta, f"{sensor_id} volvió a lo normal: {x:g}",
                                   {"tipo": "senal", "sensor": sensor_id, "valor": x})]
        return []
