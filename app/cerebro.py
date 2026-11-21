"""FRENTE 4 — registro, relevo de turno y vista del supervisor.

El relevo es una LECTURA de los eventos, no un documento aparte. El resumen que
redacta un modelo va encima del registro, no en su lugar.

Lo que hay que construir acá: reemplazar redactar_resumen y responder por
llamadas a un modelo, entregándole el registro COMPLETO de la OT. Sin
recuperación y sin base vectorial: una OT entera cabe en el contexto, y omitir
un evento al responder «¿se puso el bloqueo?» es inaceptable.
"""

from __future__ import annotations

from collections.abc import Sequence

from app.contratos import Estado, Evento, Pauta
from app.reglas import estados_desde_eventos, paso_actual


def estado_de_ot(pauta: Pauta, eventos: Sequence[Evento]) -> dict:
    """Lo que el turno siguiente necesita saber, calculado desde los eventos."""
    estados = estados_desde_eventos(eventos)
    actual = paso_actual(pauta, estados)

    def vista(paso):
        est = estados.get(paso.id, Estado.NO_VERIFICADO)
        ultimo = next(
            (e for e in reversed(eventos) if e.paso_id == paso.id and e.estado is not None), None
        )
        return {
            "id": paso.id,
            "orden": paso.orden,
            "titulo": paso.titulo,
            "instruccion": paso.instruccion,
            "tipo_evidencia": str(paso.tipo_evidencia),
            "sensor": {"id": paso.sensor.id, "espera": paso.sensor.espera} if paso.sensor else None,
            "pregunta_visual": paso.pregunta_visual,
            "estado": str(est),
            "control_critico": paso.control_critico,
            "capa": ultimo.capa if ultimo else None,
            "evidencia": ultimo.evidencia if ultimo else None,
            "detalle": ultimo.detalle if ultimo else None,
        }

    pasos = [vista(p) for p in pauta.en_orden]
    return {
        "pauta": f"{pauta.nombre} v{pauta.version}",
        "equipo": pauta.equipo,
        "paso_actual": actual.id if actual else None,
        "completa": actual is None,
        "pasos": pasos,
        "verificados": [p["id"] for p in pasos if p["estado"] == Estado.VERIFICADO],
        "en_conflicto": [p["id"] for p in pasos if p["estado"] == Estado.EN_CONFLICTO],
        "pendientes": [p["id"] for p in pasos if p["estado"] == Estado.NO_VERIFICADO],
    }


def redactar_resumen(estado: dict, eventos: Sequence[Evento]) -> str:
    """TODO frente 4: entregar `eventos` completos a un modelo y pedirle esto.

    El texto determinista de abajo es el respaldo, y además es la fuente de
    verdad: si el modelo dice algo que no está acá, el modelo se equivocó.
    """
    lineas = [f"{estado['pauta']} sobre {estado['equipo']}."]
    if estado["verificados"]:
        lineas.append(f"Verificados: {', '.join(estado['verificados'])}.")
    if estado["en_conflicto"]:
        lineas.append(
            f"EN CONFLICTO, no cerrados: {', '.join(estado['en_conflicto'])}. "
            "Se heredan como conflicto, no se limpian al cambiar de turno."
        )
    if estado["pendientes"]:
        lineas.append(f"Sin iniciar: {', '.join(estado['pendientes'])}.")
    if estado["paso_actual"]:
        lineas.append(f"Retomar desde {estado['paso_actual']}.")
    else:
        lineas.append("La pauta está completa.")
    alertas = [e for e in eventos if str(e.tipo) == "alerta"]
    if alertas:
        lineas.append(f"Hubo {len(alertas)} alerta(s) de seguridad durante el trabajo.")
    return " ".join(lineas)


def responder(pregunta: str, pauta: Pauta, eventos: Sequence[Evento]) -> dict:
    """Una respuesta SIEMPRE viaja con su evidencia y su hora.

    TODO frente 4: acá va el modelo, con el registro completo. El stub matchea
    por prefijo («bloqueo» ↔ «bloquear») sobre título e instrucción, y entre los
    pasos que calzan gana el que ya tiene veredicto: la pregunta del relevo es
    por lo que pasó, no por lo que falta.
    """
    raices = {w[:5] for w in pregunta.lower().split() if len(w) > 4}
    candidatos = []
    for paso in pauta.en_orden:
        texto = f"{paso.titulo} {paso.instruccion}".lower()
        puntaje = sum(1 for r in raices if r in texto)
        if puntaje:
            ev = next(
                (e for e in reversed(eventos) if e.paso_id == paso.id and e.estado is not None),
                None,
            )
            candidatos.append((ev is None, -puntaje, paso.orden, paso, ev))
    if not candidatos:
        return {"respuesta": "No encuentro ese paso en la pauta.", "evidencia": None, "ts": None}

    candidatos.sort(key=lambda c: c[:3])
    _, _, _, paso, ev = candidatos[0]
    if ev is None:
        return {
            "respuesta": f"«{paso.titulo}» todavía no tiene veredicto.",
            "evidencia": None,
            "ts": None,
        }
    return {
        "respuesta": f"«{paso.titulo}»: {ev.estado}. {ev.detalle}",
        "evidencia": ev.evidencia,
        "ts": ev.ts,
        "capa": ev.capa,
    }
