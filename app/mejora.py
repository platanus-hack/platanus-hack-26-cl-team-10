"""La mejora continua de las pautas, desde la evidencia validada de cada ejecución (ADR-0014).

El ciclo:

1. **Señal.** Cada OT deja en su bitácora lo que pasó en cada paso: una alerta de orden o de control
   perdido, un conflicto entre la palabra y la evidencia, un paso que confirmó una persona porque la
   evidencia no lo vio, y lo que observaron los operarios (`pauta` o `seguridad`).
2. **Propuesta.** Cuando el MISMO paso de la MISMA versión tiene señales en al menos MINIMO OT
   distintas, nace una propuesta. Una desviación suelta no es una propuesta (LOGICA).
3. **Validación.** El supervisor de la empresa la acepta o la descarta, con una nota. Queda quién y
   cuándo, y nada se borra: una revisión nueva se agrega encima de la anterior.
4. **Versión nueva.** El equipo de Factum escribe y aprueba la versión siguiente de la pauta
   (`/interno`), a partir de las aceptadas. La propuesta pasa a `aplicada`.
5. **Comprobación.** Con las OT de la versión nueva se mide si el paso dejó de desviarse.

Agrupa por paso y por pauta, nunca por persona: de los operarios solo se cuenta cuántos distintos
dieron señales, para distinguir un paso que se salta uno de un paso que se saltan muchos.
"""

from __future__ import annotations

import sqlite3
from collections import Counter, defaultdict

from app import catalogo, db
from app.catalogo import ReglaDeNegocio
from app.metricas import Ejecucion

MINIMO = 2
DECISIONES = {"aceptar": "aceptada", "descartar": "descartada"}
ALIMENTAN = ("pauta", "seguridad")
SENALES = ("orden", "control", "conflicto", "persona", "observacion")

_ESQUEMA = """
CREATE TABLE IF NOT EXISTS mejora_revisiones (
    id INTEGER PRIMARY KEY AUTOINCREMENT, cliente_id TEXT NOT NULL, propuesta_id TEXT NOT NULL,
    decision TEXT NOT NULL, nota TEXT NOT NULL, actor TEXT NOT NULL, ts TEXT NOT NULL
);
"""

SUGERENCIAS = {
    "orden": "El paso se hace antes de su turno: revisar si el orden de la pauta calza con cómo se trabaja en el "
             "equipo, o si el paso anterior se puede cumplir antes.",
    "control": "Un control se deshizo antes de tiempo: revisar si la pauta deja claro hasta cuándo se mantiene.",
    "persona": "La evidencia no vio el paso y una persona lo confirmó: revisar el sensor o la pregunta de la "
               "cámara de este paso antes que a quien lo ejecuta.",
    "conflicto": "La palabra del operario y la evidencia no coinciden: revisar cómo está escrito el paso.",
    "observacion": "Los operarios dejaron observaciones sobre este paso: leerlas antes de escribir la versión siguiente.",
}
CONTROL_CRITICO = "Es un control crítico: que se desvíe seguido no lo vuelve prescindible."


def preparar(cx: sqlite3.Connection) -> None:
    cx.executescript(_ESQUEMA)


def _id(pauta_id: str, version: int, paso_id: str) -> str:
    return f"{pauta_id}:v{version}:{paso_id}"


def _senales(e: Ejecucion) -> dict[str, Counter]:
    """Las señales de cada paso en una OT."""
    por_paso: dict[str, Counter] = defaultdict(Counter)
    for paso, senales in e.por_paso.items():
        por_paso[paso].update({s: n for s, n in senales.items() if n})
    for o in e.observaciones:
        if o["paso"] and o["categoria"] in ALIMENTAN:
            por_paso[o["paso"]]["observacion"] += 1
    return por_paso


def _revisiones(cx: sqlite3.Connection, cliente_id: str) -> dict[str, dict]:
    filas = cx.execute("SELECT * FROM mejora_revisiones WHERE cliente_id = ? ORDER BY id", (cliente_id,)).fetchall()
    return {f["propuesta_id"]: {"decision": f["decision"], "nota": f["nota"], "por": f["actor"], "ts": f["ts"]} for f in filas}


def _validacion(es: list[Ejecucion], pauta_id: str, version: int, paso_id: str, antes: tuple[int, int], nueva: int) -> dict:
    # Solo cuentan las OT que ya pasaron por el paso: una OT que nadie ejecutó no prueba que el paso mejoró.
    despues = [e for e in es if e.pauta.id == pauta_id and e.pauta.version == nueva
               and (paso_id in e.verificados or _senales(e).get(paso_id))]
    con_senal = sum(1 for e in despues if _senales(e).get(paso_id))
    tasa_antes = antes[1] / antes[0] if antes[0] else 0
    if not despues:
        resultado = "sin_datos"
    elif con_senal / len(despues) < tasa_antes:
        resultado = "mejoro"
    else:
        resultado = "se_repite"
    return {"version_nueva": nueva, "ejecuciones": len(despues), "ots_con_senal": con_senal, "resultado": resultado}


def propuestas(cx: sqlite3.Connection, es: list[Ejecucion], cliente_id: str) -> list[dict]:
    """Las propuestas de la empresa, las que más pesan primero: más OT con señal, control crítico antes."""
    revisiones = _revisiones(cx, cliente_id)
    grupos: dict[tuple[str, int, str], list[tuple[Ejecucion, Counter]]] = defaultdict(list)
    ejecuciones_por_version: Counter = Counter()
    for e in es:
        ejecuciones_por_version[(e.pauta.id, e.pauta.version)] += 1
        for paso, senales in _senales(e).items():
            grupos[(e.pauta.id, e.pauta.version, paso)].append((e, senales))

    salida = []
    for (pauta_id, version, paso_id), del_paso in grupos.items():
        if len(del_paso) < MINIMO:
            continue
        pauta = del_paso[0][0].pauta
        try:
            paso = pauta.paso(paso_id)
        except KeyError:
            continue
        senales = Counter({s: 0 for s in SENALES})
        for _, s in del_paso:
            senales.update(s)
        operarios = set().union(*(e.operarios for e, _ in del_paso))
        dominantes = [s for s, n in senales.most_common() if n]
        sugerencia = " ".join([SUGERENCIAS[s] for s in dominantes] + ([CONTROL_CRITICO] if paso.control_critico else []))
        pid = _id(pauta_id, version, paso_id)
        ejecuciones = ejecuciones_por_version[(pauta_id, version)]
        revision = revisiones.get(pid)
        estado = DECISIONES.get(revision["decision"]) if revision else "abierta"
        ultima = catalogo.ultima_aprobada(cx, pauta_id)
        validacion = None
        if ultima is not None and ultima > version:
            estado = "aplicada" if estado == "aceptada" else "superada"
            validacion = _validacion(es, pauta_id, version, paso_id, (ejecuciones, len(del_paso)), ultima)
        salida.append({
            "id": pid, "pauta": pauta_id, "nombre": pauta.nombre, "version": version,
            "protocolos": catalogo.protocolos_de(cx, pauta_id),
            "paso": paso_id, "titulo": paso.titulo, "control_critico": paso.control_critico,
            "ejecuciones": ejecuciones, "ots_con_senal": len(del_paso), "operarios_distintos": len(operarios),
            "senales": dict(senales),
            "observaciones": [{"categoria": o["categoria"], "texto": o["texto"]}
                              for e, _ in del_paso for o in e.observaciones
                              if o["paso"] == paso_id and o["categoria"] in ALIMENTAN],
            "motivo": f"«{paso.titulo}» tuvo señales en {len(del_paso)} de {ejecuciones} OT de la versión {version}, "
                      f"con {len(operarios)} operarios distintos",
            "sugerencia": sugerencia,
            "estado": estado, "revision": revision, "validacion": validacion,
        })
    salida.sort(key=lambda p: (-p["ots_con_senal"], not p["control_critico"], p["id"]))
    return salida


def revisar(cx: sqlite3.Connection, es: list[Ejecucion], cliente_id: str, propuesta_id: str,
            decision: str, nota: str, actor: str) -> dict:
    """El supervisor valida una propuesta de su empresa. Descartar pide un motivo."""
    if decision not in DECISIONES:
        raise ReglaDeNegocio(f"la decisión {decision} no existe; hay {', '.join(DECISIONES)}")
    nota = (nota or "").strip()
    if decision == "descartar" and not nota:
        raise ReglaDeNegocio("descartar una propuesta necesita una nota que diga por qué")
    propuesta = next((p for p in propuestas(cx, es, cliente_id) if p["id"] == propuesta_id), None)
    if propuesta is None:
        raise db.NoExiste(f"propuesta {propuesta_id}")
    if propuesta["estado"] in ("aplicada", "superada"):
        raise ReglaDeNegocio(f"la pauta {propuesta['pauta']} ya tiene una versión aprobada más nueva que la v{propuesta['version']}")
    cx.execute("INSERT INTO mejora_revisiones (cliente_id, propuesta_id, decision, nota, actor, ts) VALUES (?, ?, ?, ?, ?, ?)",
               (cliente_id, propuesta_id, decision, nota, actor, db.ahora()))
    cx.commit()
    return next(p for p in propuestas(cx, es, cliente_id) if p["id"] == propuesta_id)


def conteo(propuestas_: list[dict]) -> dict:
    c = Counter(p["estado"] for p in propuestas_)
    return {e: c[e] for e in ("abierta", "aceptada", "descartada", "aplicada", "superada")}
