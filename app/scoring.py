"""Calificación: OK, WARNING o ERROR, con su certeza y sus motivos.

No reemplaza al Veredicto de app/reglas.py: lo lee. El veredicto dice en qué
quedó un paso; la calificación dice qué tan grave es y cuánto creerle, para que
la UI pinte y la bitácora explique. Se calcula al leer, nunca se guarda: el
registro sigue siendo solo eventos (ADR-0003).

Cada capa del ADR-0004 califica a su manera:

- Capa 1, determinista: certeza total mientras la lectura esté fresca. Es la
  única que llega a ERROR, porque es la única que interrumpe (LOGICA.md).
- Capa 2, señales: anomalía por desvío robusto contra la historia del sensor.
  Llega a lo más a WARNING: no cierra pasos ni interrumpe.
- Capa 3, cámara: la certeza es la confianza del juez. Un conflicto de cámara es
  WARNING, se muestra y no suena.
- Confirmación: la palabra del operario. OK, y el motivo deja dicho que fue una
  persona.

Los motivos son la entrada del LLM que redacta la justificación (frente 4): el
modelo redacta sobre ellos, no los inventa.
"""

from __future__ import annotations

from collections.abc import Iterable, Mapping, Sequence
from dataclasses import dataclass, field
from enum import StrEnum
from statistics import median

from app.contratos import Capa, Estado, Evento, TipoEvento, Veredicto
from app.reglas import reglas_seguridad


class Nivel(StrEnum):
    OK = "ok"
    WARNING = "warning"
    ERROR = "error"


_GRAVEDAD = {Nivel.OK: 0, Nivel.WARNING: 1, Nivel.ERROR: 2}

# Umbrales de partida. Se calibran con el ensayo del demo, no antes.
FRESCURA_S = 5.0
CONFIANZA_CAMARA_MIN = 0.75
HISTORIA_MIN = 10
DESVIO_WARNING = 3.5


@dataclass(frozen=True, slots=True)
class Calificacion:
    nivel: Nivel
    certeza: float
    capa: int | None
    motivos: tuple[str, ...] = field(default_factory=tuple)

    def como_dict(self) -> dict:
        return {
            "nivel": str(self.nivel),
            "certeza": round(self.certeza, 2),
            "capa": self.capa,
            "motivos": list(self.motivos),
        }


def peor(calificaciones: Iterable[Calificacion]) -> Calificacion:
    """La más grave manda. A igual gravedad, la de menor certeza: es la que pide mirar."""
    lista = list(calificaciones)
    if not lista:
        return Calificacion(Nivel.OK, 1.0, None, ("sin nada que calificar",))
    return max(lista, key=lambda c: (_GRAVEDAD[c.nivel], -c.certeza))


# ─── Capa 1 · determinista ──────────────────────────────────────────────────


def capa1(v: Veredicto, edad_lectura_s: float | None = None) -> Calificacion:
    if v.interrumpe or v.estado is Estado.EN_CONFLICTO:
        return Calificacion(Nivel.ERROR, 1.0, Capa.DETERMINISTA, (v.detalle,))

    certeza = _certeza_por_frescura(edad_lectura_s)
    if certeza < 1.0:
        return Calificacion(
            Nivel.WARNING,
            certeza,
            Capa.DETERMINISTA,
            (v.detalle, f"la lectura tiene {edad_lectura_s:.0f} s; el sensor puede haberse caído"),
        )
    return Calificacion(Nivel.OK, 1.0, Capa.DETERMINISTA, (v.detalle,))


def _certeza_por_frescura(edad_s: float | None) -> float:
    if edad_s is None or edad_s <= FRESCURA_S:
        return 1.0
    return max(0.0, 1.0 - (edad_s - FRESCURA_S) / FRESCURA_S)


# ─── Capa 2 · señales ───────────────────────────────────────────────────────


def capa2(sensor_id: str, historia: Sequence[float], valor: float) -> Calificacion:
    """Desvío robusto: (valor - mediana) / MAD escalado. No le afectan los picos sueltos.

    Algoritmo de partida para la Brecha de la capa 2; se reemplaza sin cambiar la firma.
    """
    n = len(historia)
    if n < HISTORIA_MIN:
        return Calificacion(
            Nivel.OK,
            n / HISTORIA_MIN,
            Capa.APRENDIZAJE,
            (f"{sensor_id}: {n} lecturas de historia, faltan para juzgar anomalías",),
        )

    centro = median(historia)
    # Un piso de 1 % de la mediana: con una historia quieta, un movimiento mínimo no es una anomalía.
    mad = max(median(abs(x - centro) for x in historia) * 1.4826, abs(centro) * 0.01, 1e-9)
    desvio = abs(valor - centro) / mad

    certeza = min(1.0, n / (3 * HISTORIA_MIN))
    if desvio >= DESVIO_WARNING:
        return Calificacion(
            Nivel.WARNING,
            certeza,
            Capa.APRENDIZAJE,
            (f"{sensor_id} = {valor:g}, lejos de su mediana {centro:g} ({desvio:.1f} desvíos)",),
        )
    return Calificacion(Nivel.OK, certeza, Capa.APRENDIZAJE, (f"{sensor_id} = {valor:g}, dentro de lo normal",))


def frescura(sensor_id: str, edad_s: float) -> Calificacion | None:
    """Capa 1 sin lecturas recientes: lo que dice el sensor ya no es seguro. El edge reenvía
    cada sensor al menos cada FRESCURA_S segundos, cambie o no."""
    certeza = _certeza_por_frescura(edad_s)
    if certeza >= 1.0:
        return None
    return Calificacion(Nivel.WARNING, certeza, Capa.DETERMINISTA,
                        (f"sin lecturas de {sensor_id} hace {edad_s:.0f} s: el sensor puede haberse caído",))


# ─── Capa 3 · cámara ────────────────────────────────────────────────────────


def capa3(v: Veredicto) -> Calificacion:
    confianza = float((v.evidencia or {}).get("confianza", 0.0))
    if v.evidencia is None:
        return Calificacion(Nivel.WARNING, 0.0, Capa.MODELO, (v.detalle,))
    if v.estado is Estado.EN_CONFLICTO:
        return Calificacion(Nivel.WARNING, confianza, Capa.MODELO, (v.detalle, "se muestra, no interrumpe"))
    if v.estado is Estado.VERIFICADO and confianza < CONFIANZA_CAMARA_MIN:
        return Calificacion(
            Nivel.WARNING,
            confianza,
            Capa.MODELO,
            (v.detalle, f"confianza bajo {CONFIANZA_CAMARA_MIN:.0%}: conviene que alguien mire"),
        )
    return Calificacion(Nivel.OK, confianza, Capa.MODELO, (v.detalle,))


# ─── Un veredicto o un evento, por su capa ──────────────────────────────────


def calificar(v: Veredicto, edad_lectura_s: float | None = None) -> Calificacion:
    match v.capa:
        case Capa.DETERMINISTA:
            return capa1(v, edad_lectura_s)
        case Capa.MODELO:
            return capa3(v)
        case Capa.APRENDIZAJE:
            nivel = Nivel.WARNING if v.estado is Estado.EN_CONFLICTO else Nivel.OK
            return Calificacion(nivel, 1.0, Capa.APRENDIZAJE, (v.detalle,))
        case None:
            return Calificacion(Nivel.OK, 1.0, None, (v.detalle, "lo cerró una persona, no un sensor"))
    raise AssertionError(f"capa no cubierta: {v.capa}")


def calificar_evento(ev: Evento) -> Calificacion | None:
    """Solo los eventos que dicen algo de la ejecución se califican."""
    if ev.tipo is TipoEvento.ALERTA_RESUELTA:
        return Calificacion(Nivel.OK, 1.0, ev.capa, (ev.detalle,))
    if ev.tipo not in (TipoEvento.VEREDICTO, TipoEvento.ALERTA):
        return None
    if ev.tipo is TipoEvento.VEREDICTO and (ev.evidencia or {}).get("tipo") == "persona":
        return Calificacion(Nivel.WARNING, 0.5, None,
                            (ev.detalle, "una persona lo cerró contra la evidencia: conviene revisar el sensor"))
    if ev.tipo is TipoEvento.ALERTA and ev.capa == Capa.APRENDIZAJE:
        certeza = float((ev.evidencia or {}).get("certeza", 1.0))
        return Calificacion(Nivel.WARNING, certeza, Capa.APRENDIZAJE, (ev.detalle,))
    v = Veredicto(
        estado=ev.estado or Estado.NO_VERIFICADO,
        capa=ev.capa,
        detalle=ev.detalle,
        evidencia=ev.evidencia,
        interrumpe=ev.tipo is TipoEvento.ALERTA and ev.capa == Capa.DETERMINISTA,
    )
    return calificar(v)


# ─── La OT completa ─────────────────────────────────────────────────────────


def calificar_ot(
    eventos: Sequence[Evento],
    sensores: Mapping[str, str],
    anomalias: Iterable[Calificacion] = (),
) -> Calificacion:
    return peor(vigentes(eventos, sensores, anomalias))


def vigentes(
    eventos: Sequence[Evento],
    sensores: Mapping[str, str],
    anomalias: Iterable[Calificacion] = (),
) -> list[Calificacion]:
    """El estado vigente de la OT: el último veredicto de cada paso, más la seguridad AHORA.

    Las alertas viejas no pesan: la regla de seguridad se vuelve a evaluar con los
    sensores actuales. Si la guarda ya se cerró, la OT deja de estar en ERROR, y la
    alerta sigue en la bitácora como lo que pasó.
    """
    ultimo: dict[str, Evento] = {}
    for ev in eventos:
        if ev.tipo is TipoEvento.VEREDICTO and ev.paso_id:
            ultimo[ev.paso_id] = ev

    partes = [c for ev in ultimo.values() if (c := calificar_evento(ev)) is not None]
    partes += [calificar(a) for a in reglas_seguridad(sensores)]
    partes += list(anomalias)
    return partes


def avisos(partes: Iterable[Calificacion]) -> list[dict]:
    """Lo que la UI muestra como aviso: todo lo vigente que no es OK, lo más grave primero."""
    return [c.como_dict() for c in sorted(
        (c for c in partes if c.nivel is not Nivel.OK),
        key=lambda c: (-_GRAVEDAD[c.nivel], c.certeza),
    )]
