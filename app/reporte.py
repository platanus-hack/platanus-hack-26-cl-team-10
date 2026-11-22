"""El reporte de una OT, armado desde su bitácora (PRD de skills, sección 4).

Es la notificación de cierre que hoy un técnico escribe a mano, pero por paso y con evidencia:
qué paso se cerró, con qué y cuándo; qué se desvió y cuánto tardó en resolverse; quién confirmó
contra la evidencia y por qué; qué observaron; qué quedó pendiente. Cada línea trae el `evento`
que la sostiene, para que un modelo que redacte encima cite en vez de inventar (LOGICA, relevo).

Lo arma el código, no un modelo: el reporte no se escribe, se lee. Una OT tiene dueño, así que
este reporte sí nombra a las personas que la ejecutaron, como la notificación de SAP. Las
métricas, que agregan muchas OT, no (ADR-0013).
"""

from __future__ import annotations

import sqlite3

from app import catalogo, db, metricas
from app.contratos import Estado, TipoEvento

CLASES = {"seguridad": "Seguridad", "orden": "Orden invertido", "control": "Control perdido",
          "senal": "Señal fuera de lo normal", "pegado": "Sensor pegado"}


def _evidencia(ev) -> dict:
    e = ev.evidencia or {}
    tipo = e.get("tipo")
    if tipo == "sensor":
        return {"con": "sensor", "sensor": e.get("id"), "leido": e.get("valor"), "esperado": e.get("espera")}
    if tipo == "deteccion":
        return {"con": "detector", "clase": e.get("clase"), "presente": e.get("presente"), "confianza": e.get("confianza")}
    if tipo == "camara":
        return {"con": "camara", "pregunta": e.get("pregunta"), "respuesta": e.get("respuesta"),
                "confianza": e.get("confianza"), "foto": e.get("cuadro")}
    if tipo == "persona":
        return {"con": "persona", "motivo": e.get("motivo"), "contra": e.get("contra")}
    return {"con": "palabra", "declarado": ev.declarado}


def armar(cx: sqlite3.Connection, ot: dict, calificacion: dict, nombres: dict[str, str]) -> dict:
    """`ot` es el resumen de la OT (catalogo); `nombres`, id → nombre de las personas de la empresa."""
    e = metricas.leer(cx, ot)
    eventos = db.eventos(cx, ot["ot"])
    nombre = lambda quien: nombres.get(quien, quien)  # noqa: E731

    abierta = next(ev for ev in eventos if ev.tipo is TipoEvento.OT_ABIERTA)
    declaraciones: dict[str, list] = {}
    for ev in eventos:
        if ev.tipo is TipoEvento.DECLARACION and ev.paso_id:
            declaraciones.setdefault(ev.paso_id, []).append({"quien": nombre(ev.actor), "dijo": ev.declarado,
                                                             "hora": ev.ts, "evento": ev.id})
    pasos = []
    for paso in e.pauta.en_orden:
        vs = e.veredictos.get(paso.id, [])
        cierre = next((v for v in reversed(vs) if v.estado is Estado.VERIFICADO), None)
        ultimo = vs[-1] if vs else None
        pasos.append({
            "paso": paso.id, "orden": paso.orden, "titulo": paso.titulo, "control_critico": paso.control_critico,
            "estado": str(ultimo.estado) if ultimo and ultimo.estado else "no_verificado",
            "cerrado_con": _evidencia(cierre) if cierre else None,
            "capa": metricas._capa(cierre) if cierre else None,
            "hora": cierre.ts if cierre else None,
            "segundos": e.segundos_del_paso(paso.id),
            "intentos": len(vs),
            "detalle": (cierre or ultimo).detalle if (cierre or ultimo) else None,
            "evento": (cierre or ultimo).id if (cierre or ultimo) else None,
            "declaraciones": declaraciones.get(paso.id, []),
        })

    desviaciones, abiertas = [], {}
    for ev in eventos:
        clave = (ev.evidencia or {}).get("clave", "")
        if ev.tipo is TipoEvento.ALERTA:
            clase, _, resto = clave.partition(":")
            d = {"clase": clase, "que": CLASES.get(clase, clase), "paso": resto if clase in ("orden", "control") else None,
                 "detalle": ev.detalle, "abierta": ev.ts, "resuelta": None, "minutos": None,
                 "evento": ev.id, "resuelta_por_evento": None}
            desviaciones.append(d)
            abiertas[ev.id] = d
        elif ev.tipo is TipoEvento.ALERTA_RESUELTA and (d := abiertas.get((ev.evidencia or {}).get("resuelve"))):
            d.update(resuelta=ev.ts, resuelta_por_evento=ev.id,
                     minutos=round((metricas._hora(ev.ts) - metricas._hora(d["abierta"])).total_seconds() / 60, 1))
        elif ev.tipo is TipoEvento.VEREDICTO and ev.estado is Estado.EN_CONFLICTO:
            desviaciones.append({"clase": "conflicto", "que": "La palabra y la evidencia no coinciden", "paso": ev.paso_id,
                                 "detalle": ev.detalle, "abierta": ev.ts, "resuelta": None, "minutos": None,
                                 "evento": ev.id, "resuelta_por_evento": None})
    confirmadas = [{"paso": ev.paso_id, "quien": nombre(ev.actor), "motivo": (ev.evidencia or {}).get("motivo"),
                    "contra": (ev.evidencia or {}).get("contra"), "hora": ev.ts, "evento": ev.id}
                   for vs in e.veredictos.values() for ev in vs if (ev.evidencia or {}).get("tipo") == "persona"]
    observaciones = [{"paso": ev.paso_id, "categoria": (ev.evidencia or {}).get("categoria"), "texto": ev.declarado,
                      "quien": nombre(ev.actor), "hora": ev.ts, "evento": ev.id}
                     for ev in eventos if ev.tipo is TipoEvento.OBSERVACION]
    relevos = [{"que": "entregado" if ev.tipo is TipoEvento.RELEVO_ENTREGADO else "recibido", "quien": nombre(ev.actor),
                "resumen": ev.detalle, "hora": ev.ts, "evento": ev.id}
               for ev in eventos if ev.tipo in (TipoEvento.RELEVO_ENTREGADO, TipoEvento.RELEVO_RECIBIDO)]
    ejecutaron = sorted({nombre(ev.actor) for ev in eventos
                         if ev.tipo in (TipoEvento.DECLARACION, TipoEvento.OBSERVACION, TipoEvento.RELEVO_RECIBIDO)
                         or (ev.tipo is TipoEvento.VEREDICTO and ev.actor != "sistema")})
    de_ejecucion = [d for d in desviaciones if d["clase"] in (*metricas.DE_EJECUCION, "conflicto")]
    return {
        "ot": ot["ot"], "estado": ot["estado_general"], "completa": ot["completa"],
        "pauta": {"id": e.pauta.id, "nombre": e.pauta.nombre, "version": e.pauta.version},
        "protocolos": catalogo.protocolos_de(cx, e.pauta.id), "equipo": ot["equipo"],
        "personas": {"pidio": nombre(abierta.actor), "a_cargo": nombre(ot["operador"]) if ot["operador"] else None,
                     "ejecutaron": ejecutaron},
        "tiempos": {"abierta": ot["abierta_en"], "inicio": e.inicio.isoformat() if e.inicio else None,
                    "fin": e.fin.isoformat() if e.fin else None,
                    "minutos_de_ejecucion": round(e.minutos, 1) if e.minutos is not None else None},
        "resultado": {"pasos_verificados": ot["cerrados"], "pasos": ot["total"],
                      "sin_desviaciones": not e.desviada, "desviaciones": len(de_ejecucion) + len(confirmadas),
                      "confirmados_por_persona": len(confirmadas), "calificacion": calificacion},
        "pasos": pasos,
        "pendientes": [p["paso"] for p in pasos if p["estado"] != "verificado"],
        "desviaciones": desviaciones,
        "confirmados_por_persona": confirmadas,
        "observaciones": observaciones,
        "relevos": relevos,
        "eventos": {"total": len(eventos), "primero": eventos[0].id if eventos else None,
                    "ultimo": eventos[-1].id if eventos else None},
    }


# ─── El mismo reporte, para leer ────────────────────────────────────────────


def _cuando(ts: str | None) -> str:
    return ts.replace("T", " ")[:16] if ts else "—"


def _con(c: dict | None) -> str:
    if not c:
        return "—"
    if c["con"] == "sensor":
        return f"sensor `{c['sensor']}` = {c['leido']}"
    if c["con"] == "detector":
        return f"detector: «{c['clase']}» {'presente' if c['presente'] else 'ausente'} ({c['confianza']:.0%})"
    if c["con"] == "camara":
        return f"cámara: «{c['pregunta']}» → {'sí' if c['respuesta'] else 'no'} ({c['confianza']:.0%})"
    if c["con"] == "persona":
        return f"confirmado por persona: {c['motivo']}"
    return f"declarado: «{c['declarado']}»" if c.get("declarado") else "declarado"


def markdown(r: dict) -> str:
    res, t, gente = r["resultado"], r["tiempos"], r["personas"]
    lineas = [
        f"# OT {r['ot']} · {r['pauta']['nombre']} v{r['pauta']['version']}",
        "",
        f"> {res['pasos_verificados']} de {res['pasos']} pasos verificados · "
        f"{'sin desviaciones' if res['sin_desviaciones'] else str(res['desviaciones']) + ' desviaciones'} · "
        f"calificación {res['calificacion']['nivel']} · estado {r['estado']}",
        "",
        *([f"- **Por qué {res['calificacion']['nivel']}:** " + "; ".join(dict.fromkeys(
            m for a in res["calificacion"].get("avisos", []) for m in a.get("motivos", [])))]
          if res["calificacion"].get("nivel") != "ok" and res["calificacion"].get("avisos") else []),
        f"- **Equipo:** {r['equipo']}",
        f"- **Protocolos:** {', '.join(p['nombre'] for p in r['protocolos']) or '—'}",
        f"- **Pidió:** {gente['pidio']} · **A cargo:** {gente['a_cargo'] or '—'} · "
        f"**Ejecutaron:** {', '.join(gente['ejecutaron']) or '—'}",
        f"- **Abierta:** {_cuando(t['abierta'])} · **Inicio:** {_cuando(t['inicio'])} · **Fin:** {_cuando(t['fin'])}"
        + (f" · **{t['minutos_de_ejecucion']} min de ejecución**" if t["minutos_de_ejecucion"] is not None else ""),
        "",
        "## Pasos",
        "",
        "| # | Paso | Estado | Cerrado con | Hora | Evento |",
        "|---|---|---|---|---|---|",
    ]
    for p in r["pasos"]:
        titulo = f"{p['titulo']}{' · control crítico' if p['control_critico'] else ''}"
        lineas.append(f"| {p['orden']} | {titulo} | {p['estado']} | {_con(p['cerrado_con'])} | "
                      f"{_cuando(p['hora'])[11:]} | {p['evento'] or '—'} |")
    lineas += ["", "## Desviaciones", ""]
    if r["desviaciones"]:
        lineas += [f"- **{d['que']}**{' en ' + d['paso'] if d['paso'] else ''}: {d['detalle']} "
                   f"({_cuando(d['abierta'])[11:]}; "
                   + (f"resuelta en {d['minutos']} min" if d["resuelta"] else "sin resolver")
                   + f"; evento {d['evento']})" for d in r["desviaciones"]]
    else:
        lineas.append("Ninguna.")
    if r["confirmados_por_persona"]:
        lineas += ["", "## Confirmados por una persona contra la evidencia", ""]
        lineas += [f"- {c['paso']}: {c['quien']} — {c['motivo']} (evento {c['evento']})" for c in r["confirmados_por_persona"]]
    if r["observaciones"]:
        lineas += ["", "## Observaciones", ""]
        lineas += [f"- {o['quien']}, {o['categoria']}{' sobre ' + o['paso'] if o['paso'] else ''}: {o['texto']} "
                   f"(evento {o['evento']})" for o in r["observaciones"]]
    if r["relevos"]:
        lineas += ["", "## Relevos", ""]
        lineas += [f"- {x['que'].capitalize()} por {x['quien']}, {_cuando(x['hora'])} (evento {x['evento']})" for x in r["relevos"]]
    if r["pendientes"]:
        lineas += ["", "## Pendiente", "", ", ".join(r["pendientes"])]
    if r.get("mejoras"):
        lineas += ["", "## Mejoras sugeridas", ""]
        for m in r["mejoras"]:
            lineas.append(f"- **{m['cambios_resumen'][0] if m['cambios_resumen'] else m['titulo']}** ({m['estado']})")
            lineas += [f"  - {c}" for c in m["cambios_resumen"][1:]]
            lineas += [f"  - Por qué: {m['porque']}", f"  - Cómo se sabrá si funcionó: {m['como_se_mide']}"]
            if not m["aplicable"] and m["por_que_no"]:
                lineas.append(f"  - No se aplica sola: {m['por_que_no']}")
    lineas += ["", f"Armado desde los eventos {r['eventos']['primero']} a {r['eventos']['ultimo']} de la bitácora "
                   f"({r['eventos']['total']}). Nada de este reporte lo redactó un modelo."]
    return "\n".join(lineas) + "\n"
