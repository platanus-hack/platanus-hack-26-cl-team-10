"""FRENTE 4 — registro, relevo de turno y vista del supervisor.

El relevo es una LECTURA de los eventos, no un documento aparte. El resumen que
redacta un modelo va encima del registro, no en su lugar.

El modelo recibe el registro COMPLETO de la OT: sin recuperación y sin base
vectorial, porque una OT entera cabe en el contexto y omitir un evento al
responder «¿se puso el bloqueo?» es inaceptable. Cada frase que escribe cita los
eventos que la sostienen, y el código lo comprueba antes de usarla: que los
eventos existan en esta OT, que cada paso en conflicto esté citado y que, si hubo
alertas, se cite al menos una. Si algo no calza, o no hay ANTHROPIC_API_KEY, queda
el texto determinista, que es además la fuente de verdad.
"""

from __future__ import annotations

import json
import logging
import os
import threading
from collections.abc import Sequence

from app.contratos import Estado, Evento, Pauta, TipoEvento
from app.reglas import estados_desde_eventos, paso_actual

log = logging.getLogger(__name__)

MODELO_POR_DEFECTO = "claude-opus-5-5"
TIMEOUT_S = 30.0
# /ot/{id}/relevo/entregar y /preguntar son públicos: sin tope, cualquiera gasta la key.
LLAMADAS_MAX = int(os.environ.get("CEREBRO_MAX_LLAMADAS", "500"))

SISTEMA_RELEVO = (
    "Redactas el relevo de turno de una orden de trabajo de mantenimiento industrial, para el operario que la "
    "recibe. Recibes los hechos que calculó el sistema y la bitácora completa de la OT. Escribe en español, de "
    "tú, como mucho seis frases cortas: qué quedó hecho, qué quedó en conflicto y por qué, qué alertas hubo y "
    "desde qué paso se retoma. Cada frase cita los `id` de los eventos que la sostienen. No digas nada que la "
    "bitácora no muestre. Un paso en conflicto se hereda como conflicto: nunca lo des por cerrado."
)
SISTEMA_PREGUNTA = (
    "Respondes preguntas sobre una orden de trabajo de mantenimiento industrial usando solo su bitácora. "
    "Responde en español, en una o dos frases, y en `evento` pon el `id` del evento que sostiene la respuesta. "
    "Si la bitácora no lo dice, dilo y deja `evento` en null: no supongas."
)
ESQUEMA_RELEVO = {
    "type": "object",
    "properties": {"frases": {"type": "array", "items": {
        "type": "object",
        "properties": {"texto": {"type": "string"}, "eventos": {"type": "array", "items": {"type": "integer"}}},
        "required": ["texto", "eventos"], "additionalProperties": False}}},
    "required": ["frases"], "additionalProperties": False,
}
ESQUEMA_PREGUNTA = {
    "type": "object",
    "properties": {"respuesta": {"type": "string"}, "evento": {"type": ["integer", "null"]}},
    "required": ["respuesta", "evento"], "additionalProperties": False,
}

_cliente = None
_llamadas = 0
_candado = threading.Lock()


def configurado() -> bool:
    return bool(os.environ.get("ANTHROPIC_API_KEY"))


def _queda_presupuesto() -> bool:
    global _llamadas
    with _candado:
        if _llamadas >= LLAMADAS_MAX:
            log.error("el cerebro llegó a su tope de %d llamadas (CEREBRO_MAX_LLAMADAS): redacta el código", LLAMADAS_MAX)
            return False
        _llamadas += 1
        return True


def _bitacora(eventos: Sequence[Evento]) -> list[dict]:
    return [{"id": e.id, "ts": e.ts, "tipo": str(e.tipo), "actor": e.actor, "paso": e.paso_id,
             "estado": str(e.estado) if e.estado else None, "capa": e.capa, "declarado": e.declarado,
             "detalle": e.detalle} for e in eventos]


def _pedir(sistema: str, contenido: dict, esquema: dict, cliente=None) -> dict | None:
    """Una llamada con salida JSON validada por esquema. None si no hay key, presupuesto o respuesta usable."""
    global _cliente
    if cliente is None:
        if not configurado() or not _queda_presupuesto():
            return None
        if _cliente is None:
            import anthropic
            _cliente = anthropic.Anthropic(timeout=TIMEOUT_S, max_retries=1)
        cliente = _cliente
    try:
        r = cliente.beta.messages.create(
            model=os.environ.get("CEREBRO_MODELO", MODELO_POR_DEFECTO),
            max_tokens=4000,
            system=sistema,
            betas=["server-side-fallback-2026-07-01"],
            fallbacks="default",
            # esfuerzo bajo: es redactar sobre hechos ya calculados, importa la latencia
            output_config={"effort": "low", "format": {"type": "json_schema", "schema": esquema}},
            messages=[{"role": "user", "content": json.dumps(contenido, ensure_ascii=False)}],
        )
    except Exception:  # noqa: BLE001 - cualquier falla del modelo deja el texto del código
        log.exception("el cerebro no pudo redactar")
        return None
    if r.stop_reason != "end_turn":
        log.warning("el cerebro terminó con %s", r.stop_reason)
        return None
    return json.loads(next(b.text for b in r.content if b.type == "text"))


def citas_validas(frases: Sequence[dict], estado: dict, eventos: Sequence[Evento]) -> bool:
    """Lo que el código exige a un relevo redactado por el modelo antes de usarlo."""
    por_id = {e.id: e for e in eventos}
    citados = [por_id.get(i) for f in frases for i in f["eventos"]]
    if not frases or any(not f["eventos"] for f in frases) or None in citados:
        return False
    pasos_citados = {e.paso_id for e in citados}
    if not set(estado["en_conflicto"]) <= pasos_citados:
        return False
    hubo_alertas = any(e.tipo is TipoEvento.ALERTA for e in eventos)
    return not hubo_alertas or any(e.tipo is TipoEvento.ALERTA for e in citados)


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


def resumen_determinista(estado: dict, eventos: Sequence[Evento]) -> str:
    """El relevo que arma el código: el respaldo, y la fuente de verdad contra la que se lee el del modelo."""
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


def redactar_resumen(estado: dict, eventos: Sequence[Evento], cliente=None) -> tuple[str, dict]:
    """(texto, evidencia). La evidencia dice quién lo redactó y qué eventos cita cada frase."""
    respaldo = resumen_determinista(estado, eventos)
    if any(e.id is None for e in eventos):
        return respaldo, {"redactado_por": "codigo"}
    d = _pedir(SISTEMA_RELEVO, {"hechos": estado, "bitacora": _bitacora(eventos)}, ESQUEMA_RELEVO, cliente)
    if d is None:
        return respaldo, {"redactado_por": "codigo"}
    if not citas_validas(d["frases"], estado, eventos):
        log.warning("el relevo del modelo no pasó las citas: queda el del código")
        return respaldo, {"redactado_por": "codigo", "rechazado": d["frases"]}
    texto = " ".join(f"{f['texto'].strip()} [{', '.join(f'#{i}' for i in f['eventos'])}]" for f in d["frases"])
    return texto, {"redactado_por": os.environ.get("CEREBRO_MODELO", MODELO_POR_DEFECTO),
                   "frases": d["frases"], "respaldo": respaldo}


def responder(pregunta: str, pauta: Pauta, eventos: Sequence[Evento], cliente=None) -> dict:
    """Una respuesta SIEMPRE viaja con su evidencia y su hora, y las dos salen de la bitácora, no del modelo.

    El modelo lee el registro completo y nombra el evento que responde; si ese evento no existe en la OT,
    o no hay modelo, responde el código: busca por prefijo («bloqueo» ↔ «bloquear») sobre título e
    instrucción, y entre los pasos que calzan gana el que ya tiene veredicto, porque la pregunta del
    relevo es por lo que pasó, no por lo que falta.
    """
    if all(e.id is not None for e in eventos):
        d = _pedir(SISTEMA_PREGUNTA, {"pregunta": pregunta, "bitacora": _bitacora(eventos)}, ESQUEMA_PREGUNTA, cliente)
        ev = next((e for e in eventos if d and e.id == d["evento"]), None)
        if d is not None and ev is not None:
            return {"respuesta": d["respuesta"], "evidencia": ev.evidencia, "ts": ev.ts, "capa": ev.capa,
                    "evento": ev.id, "redactado_por": os.environ.get("CEREBRO_MODELO", MODELO_POR_DEFECTO)}
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
