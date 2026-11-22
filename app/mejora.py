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
5. **Comprobación.** Con las OT de la versión nueva se mide si el paso dejó de desviarse. «mejoro» pide que la
   baja no se explique por azar (Fisher exacta, app/recurrencia.py); con pocas OT es «sin_evidencia».

Cada propuesta trae además `recurrencia`: si las OT con señal de ese paso superan lo que se desvía el resto de su
pauta, corregido por cuántos pasos se prueban a la vez. MINIMO decide que la propuesta nazca, como pide el
ADR-0014; `recurrencia.recurrente` dice si se distingue del ruido. La simulación de app/simulacion.py mide los dos.

Agrupa por paso y por pauta, nunca por persona: de los operarios solo se cuenta cuántos distintos
dieron señales, para distinguir un paso que se salta uno de un paso que se saltan muchos.
"""

from __future__ import annotations

import sqlite3
from collections import Counter, defaultdict

from app import catalogo, db, recurrencia
from app.catalogo import ReglaDeNegocio
from app.metricas import Ejecucion

MINIMO = 2
# El aviso en vivo prueba después de cada señal, y mirar muchas veces infla los falsos avisos: con α = 0,05 y 50 OT
# de solo ruido, el 17 % de las pautas daba un aviso falso; con 0,005, el 4,5 % (simulacion.md, «El aviso en vivo»).
ALFA_AVISO = 0.005
DECISIONES = {"aceptar": "aceptada", "descartar": "descartada"}
ALIMENTAN = ("pauta", "seguridad")
SENALES = ("seguridad", "orden", "control", "conflicto", "persona", "observacion")

_ESQUEMA = """
CREATE TABLE IF NOT EXISTS mejora_revisiones (
    id INTEGER PRIMARY KEY AUTOINCREMENT, cliente_id TEXT NOT NULL, propuesta_id TEXT NOT NULL,
    decision TEXT NOT NULL, nota TEXT NOT NULL, actor TEXT NOT NULL, ts TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS mejora_avisos (
    cliente_id TEXT NOT NULL, propuesta_id TEXT NOT NULL, ot_id TEXT NOT NULL, evento_id INTEGER, ts TEXT NOT NULL,
    PRIMARY KEY (cliente_id, propuesta_id)
);
"""

SUGERENCIAS = {
    "seguridad": "Con este paso todavía abierto se dio una condición de peligro: se hizo lo que viene antes de "
                 "terminarlo. Revisar con quien hace la tarea por qué se salta, y si la pauta deja claro que sin este "
                 "paso no se avanza.",
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


def avisos(cx: sqlite3.Connection, cliente_id: str) -> dict[str, dict]:
    """Las propuestas que ya se le avisaron al supervisor: cuándo y en qué OT se detectó el patrón."""
    filas = cx.execute("SELECT * FROM mejora_avisos WHERE cliente_id = ?", (cliente_id,)).fetchall()
    return {f["propuesta_id"]: {"ot": f["ot_id"], "evento": f["evento_id"], "ts": f["ts"]} for f in filas}


def por_avisar(cx: sqlite3.Connection, es: list[Ejecucion], cliente_id: str, pauta_id: str, version: int) -> list[dict]:
    """Las propuestas de esa versión que acaban de volverse recurrentes y nadie avisó todavía.

    Se avisa por recurrencia con ALFA_AVISO, no por MINIMO: lo que suena en la pantalla del supervisor tiene que
    distinguirse del ruido aunque se pruebe después de cada OT (knowledge/projects/mejora-continua/simulacion.md)."""
    ya = avisos(cx, cliente_id)
    de_la_version = [e for e in es if e.pauta.id == pauta_id and e.pauta.version == version]
    if not de_la_version:
        return []
    pasos = de_la_version[0].pauta.pasos
    con_senal = {p.id: sum(1 for e in de_la_version if _senales(e).get(p.id)) for p in pasos}
    en_vivo = recurrencia.recurrentes(con_senal, len(de_la_version), ALFA_AVISO)
    return [p for p in propuestas(cx, es, cliente_id)
            if p["pauta"] == pauta_id and p["version"] == version and p["estado"] == "abierta"
            and en_vivo.get(p["paso"], {}).get("recurrente") and p["id"] not in ya]


def registrar_aviso(cx: sqlite3.Connection, cliente_id: str, propuesta_id: str, ot_id: str, evento_id: int | None, ts: str) -> None:
    cx.execute("INSERT OR IGNORE INTO mejora_avisos (cliente_id, propuesta_id, ot_id, evento_id, ts) VALUES (?, ?, ?, ?, ?)",
               (cliente_id, propuesta_id, ot_id, evento_id, ts))
    cx.commit()


def texto_del_aviso(p: dict) -> str:
    r = p["recurrencia"]
    return (f"Factum encontró un patrón en «{p['titulo']}»: señales en {r['ots_con_senal']} de {r['ots']} OT de la "
            f"versión {p['version']}, con {p['operarios_distintos']} operarios distintos. {p['sugerencia']}")


def _validacion(es: list[Ejecucion], pauta_id: str, version: int, paso_id: str, antes: tuple[int, int], nueva: int) -> dict:
    # Solo cuentan las OT que ya pasaron por el paso: una OT que nadie ejecutó no prueba que el paso mejoró.
    despues = [e for e in es if e.pauta.id == pauta_id and e.pauta.version == nueva
               and (paso_id in e.verificados or _senales(e).get(paso_id))]
    con_senal = sum(1 for e in despues if _senales(e).get(paso_id))
    c = recurrencia.comprobar_cambio(antes, (len(despues), con_senal))
    return {"version_nueva": nueva, "ejecuciones": len(despues), "ots_con_senal": con_senal, **c}


def propuestas(cx: sqlite3.Connection, es: list[Ejecucion], cliente_id: str) -> list[dict]:
    """Las propuestas de la empresa, las que más pesan primero: más OT con señal, control crítico antes."""
    revisiones = _revisiones(cx, cliente_id)
    avisadas = avisos(cx, cliente_id)
    grupos: dict[tuple[str, int, str], list[tuple[Ejecucion, Counter]]] = defaultdict(list)
    ejecuciones_por_version: Counter = Counter()
    for e in es:
        ejecuciones_por_version[(e.pauta.id, e.pauta.version)] += 1
        for paso, senales in _senales(e).items():
            grupos[(e.pauta.id, e.pauta.version, paso)].append((e, senales))

    pruebas: dict[tuple[str, int], dict[str, dict]] = {}
    for e in es:
        clave = (e.pauta.id, e.pauta.version)
        if clave not in pruebas:
            pruebas[clave] = recurrencia.recurrentes(
                {p.id: len(grupos.get((*clave, p.id), [])) for p in e.pauta.pasos}, ejecuciones_por_version[clave])

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
            "recurrencia": pruebas[(pauta_id, version)].get(paso_id),
            "detectada": avisadas.get(pid),
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
