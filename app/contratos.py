"""Las dos formas del contrato: Paso y Evento.

Esto implementa knowledge/architecture/LOGICA.md. Si los dos se separan, manda
este archivo y el documento se corrige en el mismo commit (CONTRIBUTING, regla 2).

Los cuatro frentes se comunican SOLO por estas dos formas. Agregar un campo acá
es cambiar el contrato: se avisa al equipo.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import IntEnum, StrEnum


class TipoEvidencia(StrEnum):
    """Qué cierra un paso. Es el campo que decide toda la lógica de verificación."""

    SENSOR = "sensor"
    CAMARA = "camara"
    CONFIRMACION = "confirmacion"


class Estado(StrEnum):
    """Los tres estados de un paso. Tres, no dos: ver LOGICA.md."""

    NO_VERIFICADO = "no_verificado"
    VERIFICADO = "verificado"
    EN_CONFLICTO = "en_conflicto"


class TipoEvento(StrEnum):
    OT_ABIERTA = "ot_abierta"
    OT_ASIGNADA = "ot_asignada"
    PASO_INICIADO = "paso_iniciado"
    DECLARACION = "declaracion"
    VEREDICTO = "veredicto"
    ALERTA = "alerta"
    ALERTA_RESUELTA = "alerta_resuelta"
    RELEVO_ENTREGADO = "relevo_entregado"
    RELEVO_RECIBIDO = "relevo_recibido"
    PROPUESTA_PAUTA = "propuesta_pauta"


class Capa(IntEnum):
    """Las tres capas del ADR-0004. La primera que puede decidir, decide."""

    DETERMINISTA = 1
    APRENDIZAJE = 2
    MODELO = 3


@dataclass(frozen=True, slots=True)
class Sensor:
    """Qué sensor cierra el paso y qué valor espera."""

    id: str
    espera: str


@dataclass(frozen=True, slots=True)
class Deteccion:
    """Qué clase del modelo del edge responde un paso de cámara en capa 2.

    presente=True: el paso se cumple cuando el objeto se ve con certeza alta.
    presente=False: se cumple cuando el objeto ya no se ve (p. ej. herramienta retirada).
    """

    clase: str
    presente: bool = True


@dataclass(frozen=True, slots=True)
class Paso:
    id: str
    orden: int
    titulo: str
    instruccion: str
    tipo_evidencia: TipoEvidencia
    capa_minima: int
    control_critico: bool = False
    pregunta_visual: str | None = None
    sensor: Sensor | None = None
    deteccion: Deteccion | None = None
    # id del paso cuya foto es el «antes»: el juez compara esa foto con la de ahora
    comparar_con: str | None = None

    def __post_init__(self) -> None:
        if self.tipo_evidencia is TipoEvidencia.SENSOR and self.sensor is None:
            raise ValueError(f"paso {self.id}: tipo sensor exige el campo sensor")
        if self.tipo_evidencia is TipoEvidencia.CAMARA and not self.pregunta_visual:
            raise ValueError(f"paso {self.id}: tipo camara exige pregunta_visual")
        if self.deteccion is not None and self.tipo_evidencia is not TipoEvidencia.CAMARA:
            raise ValueError(f"paso {self.id}: deteccion solo aplica a pasos de camara")
        if self.comparar_con is not None and self.tipo_evidencia is not TipoEvidencia.CAMARA:
            raise ValueError(f"paso {self.id}: comparar_con solo aplica a pasos de camara")

    @classmethod
    def desde_dict(cls, d: dict) -> Paso:
        s, det = d.get("sensor"), d.get("deteccion")
        return cls(
            id=d["id"],
            orden=d["orden"],
            titulo=d["titulo"],
            instruccion=d["instruccion"],
            tipo_evidencia=TipoEvidencia(d["tipo_evidencia"]),
            capa_minima=d["capa_minima"],
            control_critico=d.get("control_critico", False),
            pregunta_visual=d.get("pregunta_visual"),
            sensor=Sensor(s["id"], s["espera"]) if s else None,
            deteccion=Deteccion(det["clase"], bool(det.get("presente", True))) if det else None,
            comparar_con=d.get("comparar_con"),
        )


@dataclass(frozen=True, slots=True)
class Pauta:
    """La pauta matriz, versionada. Cada OT guarda qué version ejecutó."""

    id: str
    nombre: str
    version: int
    equipo: str
    pasos: tuple[Paso, ...]

    def paso(self, paso_id: str) -> Paso:
        for p in self.pasos:
            if p.id == paso_id:
                return p
        raise KeyError(paso_id)

    @property
    def en_orden(self) -> tuple[Paso, ...]:
        return tuple(sorted(self.pasos, key=lambda p: p.orden))


@dataclass(frozen=True, slots=True)
class Veredicto:
    """El resultado de evaluar un paso. Lo produce app/reglas.py."""

    estado: Estado
    capa: int | None
    detalle: str
    evidencia: dict | None = None
    interrumpe: bool = False


@dataclass(slots=True)
class Evento:
    """Una fila de la bitácora. La tabla solo admite agregar filas."""

    ot_id: str
    tipo: TipoEvento
    ts: str
    actor: str
    detalle: str
    id: int | None = None
    paso_id: str | None = None
    estado: Estado | None = None
    capa: int | None = None
    declarado: str | None = None
    evidencia: dict | None = field(default=None)
