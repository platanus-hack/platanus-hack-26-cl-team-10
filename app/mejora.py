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

import math
import sqlite3
from collections import Counter, defaultdict

from app import catalogo, db, recurrencia
from app.catalogo import ReglaDeNegocio
from app.metricas import Ejecucion

MINIMO = 2
# Lo que se decide mirando una y otra vez los mismos datos (el aviso al supervisor, la versión que escribe Factum, la
# escalada) reparte su α entre las miradas: la k-ésima OT de una versión gasta ALFA_VIDA·6/(π²k²), y como esa serie suma
# ALFA_VIDA, la probabilidad de un aviso falso en toda la vida de una versión no pasa de ALFA_VIDA, por muchas OT que se
# ejecuten. Con un α fijo, mirar sin fin termina dando un falso positivo seguro y la mejora no converge
# (simulacion.md, «El aviso en vivo» y «Convergencia»).
ALFA_VIDA = 0.05


def alfa_en_vivo(ots: int) -> float:
    return ALFA_VIDA * 6 / (math.pi ** 2 * max(1, ots) ** 2)
DECISIONES = {"aceptar": "aceptada", "descartar": "descartada"}
ALIMENTAN = ("pauta", "seguridad")
SENALES = ("seguridad", "orden", "control", "conflicto", "persona", "observacion")

_ESQUEMA = """
CREATE TABLE IF NOT EXISTS mejora_revisiones (
    id INTEGER PRIMARY KEY AUTOINCREMENT, cliente_id TEXT NOT NULL, propuesta_id TEXT NOT NULL,
    decision TEXT NOT NULL, nota TEXT NOT NULL, actor TEXT NOT NULL, ts TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS mejora_escaladas (
    cliente_id TEXT NOT NULL, propuesta_id TEXT NOT NULL, ts TEXT NOT NULL, PRIMARY KEY (cliente_id, propuesta_id)
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

    Se avisa por recurrencia con el α repartido de `alfa_en_vivo`, no por MINIMO: lo que suena en la pantalla del supervisor tiene que
    distinguirse del ruido aunque se pruebe después de cada OT (knowledge/projects/mejora-continua/simulacion.md)."""
    ya = avisos(cx, cliente_id)
    return [p for p in propuestas(cx, es, cliente_id)
            if p["tipo"] == "desviacion" and p["pauta"] == pauta_id and p["version"] == version and p["estado"] == "abierta"
            and (p["recurrencia"] or {}).get("en_vivo") and p["id"] not in ya]


def registrar_escaladas(cx: sqlite3.Connection, propuestas_: list[dict], cliente_id: str) -> None:
    for p in propuestas_:
        if p.get("escalar"):
            cx.execute("INSERT OR IGNORE INTO mejora_escaladas (cliente_id, propuesta_id, ts) VALUES (?, ?, ?)",
                       (cliente_id, p["id"], db.ahora()))
    cx.commit()


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
            con_senal = {p.id: len(grupos.get((*clave, p.id), [])) for p in e.pauta.pasos}
            pruebas[clave] = recurrencia.recurrentes(con_senal, ejecuciones_por_version[clave])
            # `en_vivo`: con el α del aviso. Es el que usa todo lo que se decide mirando una y otra vez los mismos datos:
            # el aviso al supervisor, la versión que escribe Factum y la escalada (simulacion.md, «Convergencia»)
            for paso_id, d in recurrencia.recurrentes(con_senal, ejecuciones_por_version[clave],
                                                             alfa_en_vivo(ejecuciones_por_version[clave])).items():
                pruebas[clave][paso_id]["en_vivo"] = d["recurrente"]

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
            "id": pid, "tipo": "desviacion", "pauta": pauta_id, "nombre": pauta.nombre, "version": version,
            "protocolos": catalogo.protocolos_de(cx, pauta_id),
            "paso": paso_id, "titulo": paso.titulo, "control_critico": paso.control_critico,
            "ejecuciones": ejecuciones, "ots_con_senal": len(del_paso), "operarios_distintos": len(operarios),
            "ots": sorted({e.ot["ot"] for e, _ in del_paso}),
            "senales": dict(senales),
            "observaciones": [{"categoria": o["categoria"], "texto": o["texto"]}
                              for e, _ in del_paso for o in e.observaciones
                              if o["paso"] == paso_id and o["categoria"] in ALIMENTAN],
            "motivo": f"«{paso.titulo}» tuvo señales en {len(del_paso)} de {ejecuciones} OT de la versión {version}, "
                      f"con {len(operarios)} operarios distintos",
            "sugerencia": sugerencia,
            "recurrencia": pruebas[(pauta_id, version)].get(paso_id),
            "detectada": avisadas.get(pid),
            "conformidad": None,
            "estado": estado, "revision": revision, "validacion": validacion,
        })
    _escalar(salida)
    # una escalada queda firme: la validación sobre datos que se acumulan oscila cerca de su umbral, y si la escalada
    # se recalculara en cada mirada aparecería y desaparecería (simulacion.md, «Convergencia»)
    firmes = {f["propuesta_id"] for f in cx.execute(
        "SELECT propuesta_id FROM mejora_escaladas WHERE cliente_id = ?", (cliente_id,)).fetchall()}
    for p in salida:
        if p["id"] in firmes and not p.get("escalar"):
            p["escalar"] = True
            p["sugerencia"] = f"{ESCALAR} {p['sugerencia']}"
    salida += _de_conformidad(cx, ejecuciones_por_version, cliente_id, revisiones)
    for p in salida:
        p["protocolo_dueno"] = catalogo.protocolo_dueno(cx, p["pauta"])
        p.setdefault("escalar", False)
        p["aplicable"], p["por_que_no"] = aplicabilidad(p)
    salida.sort(key=lambda p: (p["tipo"] != "conformidad", -p["ots_con_senal"], not p["control_critico"], p["id"]))
    return salida


NO_APLICABLE = {
    "persona": "La evidencia no vio el paso y lo confirmó una persona: se revisa el sensor o la pregunta de la cámara, no "
               "la pauta.",
    "observacion": "Lo que pesa son observaciones de los operarios: se leen antes de cambiar la pauta, no se aplican solas.",
    "orden": "Los controles van en otro orden que el del protocolo: reordenarlos lo decide el equipo con quien hace la "
             "tarea, no se aplica solo.",
    "desconocido": "Un paso dice cumplir un control que el protocolo no declara: se corrige la marca o el protocolo.",
}


def aplicabilidad(p: dict) -> tuple[bool, str | None]:
    """Si la propuesta trae un cambio de pauta que proponer (app/sugerencias.py) y, si no, por qué."""
    if p["estado"] not in ("abierta", "aceptada"):
        return False, f"La propuesta está {p['estado']}: ya no cambia la pauta."
    if p.get("escalar"):
        return False, "Se escaló: un cambio anterior a este paso no lo bajó, así que la causa no es la pauta."
    if p["tipo"] == "conformidad":
        t = p["conformidad"]["tipo"]
        return (False, NO_APLICABLE[t]) if t in NO_APLICABLE else (True, None)
    vivas = [s for s in SENALES if p["senales"].get(s)]
    dominante = max(vivas, key=lambda s: (p["senales"][s], -SENALES.index(s))) if vivas else None
    if dominante in (None, "persona", "observacion"):
        return False, NO_APLICABLE.get(dominante or "observacion")
    return True, None


ESCALAR = ("Una versión anterior ya cambió este paso, no lo bajó, y en la versión nueva se sigue desviando de forma "
           "recurrente: la pauta no es la causa. Antes de otra versión, revisar con la supervisión si es presión de tiempo o el equipo.")


def _escalar(salida: list[dict]) -> None:
    """La regla que hace converger la mejora (ADR-0018): si un paso vuelve a ser recurrente en la versión nueva después
    de que se aplicó un cambio sobre él, y ese cambio no lo bajó (la validación no dice «mejoro»), no se propone otra
    versión: se escala. Si el cambio lo bajó y queda un resto, otra vuelta sí tiene sentido. Sin esto, una causa que el texto no
    arregla (la presión, el equipo) produce versiones sin fin (knowledge/projects/mejora-continua/simulacion.md)."""
    por_paso: dict[tuple[str, str], list[dict]] = defaultdict(list)
    for p in salida:
        por_paso[(p["pauta"], p["paso"])].append(p)
    for propuestas_ in por_paso.values():
        propuestas_.sort(key=lambda p: p["version"])
        for antes, ahora in zip(propuestas_, propuestas_[1:]):
            no_bajo = (antes["validacion"] or {}).get("resultado") != "mejoro"
            if antes["estado"] == "aplicada" and no_bajo and (ahora["recurrencia"] or {}).get("en_vivo"):
                ahora["escalar"] = True
                ahora["sugerencia"] = f"{ESCALAR} {ahora['sugerencia']}"


SUGERENCIA_CONFORMIDAD = {
    "falta": "El protocolo exige este control y ningún paso de la pauta lo cumple: la versión siguiente lo agrega como "
             "un paso propio, con su evidencia.",
    "juntos": "Dos controles van en un solo paso: la versión siguiente los separa, para que la evidencia compruebe cada "
              "uno y su orden.",
    "orden": "Los controles van en otro orden que el del protocolo: la versión siguiente los ordena como lo pide.",
    "desconocido": "Un paso dice cumplir un control que el protocolo no declara: corregir la marca o el protocolo.",
}


def _de_conformidad(cx: sqlite3.Connection, ejecuciones: Counter, cliente_id: str, revisiones: dict) -> list[dict]:
    """Los hallazgos de conformidad de las pautas habilitadas para la empresa, como propuestas de tipo «conformidad»
    (ADR-0016). Nacen de la pauta misma, no de las OT: están desde que se aprueba la versión. Con una versión aprobada
    más nueva, `validacion` dice si el hallazgo se cerró."""
    habilitadas = [f["pauta_id"] for f in cx.execute(
        "SELECT pauta_id FROM cliente_pautas WHERE cliente_id = ? ORDER BY pauta_id", (cliente_id,)).fetchall()]
    salida = []
    for pauta_id in habilitadas:
        aprobadas = [f["version"] for f in cx.execute(
            "SELECT version FROM aprobaciones WHERE pauta_id = ? ORDER BY version", (pauta_id,)).fetchall()]
        if not aprobadas:
            continue
        ultima = aprobadas[-1]
        de_la_ultima = {h["clave"] for h in catalogo.hallazgos_de_conformidad(cx, db.leer_pauta(cx, pauta_id, ultima))}
        for version in aprobadas:
            pauta = db.leer_pauta(cx, pauta_id, version)
            aprobada_en = cx.execute("SELECT ts FROM aprobaciones WHERE pauta_id = ? AND version = ?",
                                     (pauta_id, version)).fetchone()["ts"]
            for h in catalogo.hallazgos_de_conformidad(cx, pauta):
                pid = f"conformidad:{pauta_id}@{version}:{h['clave']}"
                revision = revisiones.get(pid)
                estado = DECISIONES.get(revision["decision"]) if revision else "abierta"
                validacion = None
                if version < ultima:
                    estado = "aplicada" if estado == "aceptada" else "superada"
                    validacion = {"version_nueva": ultima, "ejecuciones": 0, "ots_con_senal": 0, "p_valor": None,
                                  "resultado": "se_repite" if h["clave"] in de_la_ultima else "mejoro"}
                paso = pauta.paso(h["pasos"][0]) if h["pasos"] else None
                salida.append({
                    "id": pid, "tipo": "conformidad", "pauta": pauta_id, "nombre": pauta.nombre, "version": version,
                    "protocolos": catalogo.protocolos_de(cx, pauta_id),
                    "paso": paso.id if paso else None, "titulo": h["detalle"][0].upper() + h["detalle"][1:],
                    "control_critico": True, "ejecuciones": ejecuciones[(pauta_id, version)], "ots_con_senal": 0,
                    "operarios_distintos": 0, "ots": [], "senales": {s: 0 for s in SENALES}, "observaciones": [],
                    "motivo": f"{h['protocolo']}: {h['detalle']}. Lo dice la pauta misma, sin esperar ninguna OT.",
                    "sugerencia": SUGERENCIA_CONFORMIDAD[h["tipo"]], "recurrencia": None,
                    "detectada": {"ot": None, "evento": None, "ts": aprobada_en},
                    "conformidad": {k: h[k] for k in ("protocolo", "control", "tipo", "detalle", "pasos")},
                    "estado": estado, "revision": revision, "validacion": validacion,
                })
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
