"""El reporte para quien decide: qué pasó en las OT de una empresa, pauta por pauta y paso por paso.

No guarda nada: se calcula leyendo la bitácora, igual que el estado de una OT (ADR-0003).
Recibe las OT que la persona puede ver (app/acceso.py), así que cada empresa ve lo suyo.
"""

from __future__ import annotations

import sqlite3
from collections import Counter

from app import db
from app.contratos import Estado, TipoEvento
from app.reglas import medidas_por_paso

_SIN_MEDIR = {"ots": [], "veces": 0, "por_persona": 0, "reintentos": 0, "segundos": None,
              "mediciones": 0, "parte_del_tiempo": None, "cierres": {}, "nota": ""}


def reporte(cx: sqlite3.Connection, ots: list[dict]) -> dict:
    """`ots`: los resúmenes de catalogo.listar_ots, ya filtrados a los de la empresa."""
    por_pauta: dict[tuple[str, int], list[dict]] = {}
    for o in ots:
        por_pauta.setdefault((o["pauta"], o["version"]), []).append(o)

    pautas = []
    for (pauta_id, version), suyas in por_pauta.items():
        pauta = db.leer_pauta(cx, pauta_id, version)
        eventos = [ev for o in suyas for ev in db.eventos(cx, o["ot"])]
        alertas = [ev for ev in eventos if ev.tipo is TipoEvento.ALERTA]
        # Con observaciones: la OT tuvo una alerta, un conflicto o un paso cerrado por una persona.
        observadas = {ev.ot_id for ev in eventos
                      if ev.tipo is TipoEvento.ALERTA or ev.estado is Estado.EN_CONFLICTO
                      or (ev.evidencia or {}).get("tipo") == "persona"}
        medidas = medidas_por_paso(eventos)
        pasos = [{"orden": p.orden, "titulo": p.titulo, "control_critico": p.control_critico,
                  "tipo_evidencia": str(p.tipo_evidencia), **_SIN_MEDIR, "paso_id": p.id, **medidas.get(p.id, {})}
                 for p in pauta.en_orden]
        pautas.append({
            "pauta_id": pauta_id, "version": version, "nombre": pauta.nombre, "equipo": pauta.equipo,
            "ots": len(suyas),
            "completas": sum(o["completa"] for o in suyas),
            "sin_observaciones": sum(o["completa"] and o["ot"] not in observadas for o in suyas),
            # La suma de las medianas de sus pasos: lo que demora una ejecución típica, sin el primer paso.
            "segundos": sum(p["segundos"] or 0 for p in pasos) or None,
            # La clase de una alerta es lo que va antes de «:» en su clave (app/servicios.py).
            "alertas": dict(Counter(str((a.evidencia or {}).get("clave", "otra")).partition(":")[0] for a in alertas)),
            "pasos": pasos,
        })
    pautas.sort(key=lambda p: (-p["ots"], p["nombre"]))

    cierres = Counter()
    for p in pautas:
        for paso in p["pasos"]:
            cierres.update(paso["cierres"])
    return {
        "ots": len(ots),
        "completas": sum(p["completas"] for p in pautas),
        "sin_observaciones": sum(p["sin_observaciones"] for p in pautas),
        "alertas_seguridad": sum(p["alertas"].get("seguridad", 0) for p in pautas),
        "cierres": dict(cierres),
        "propuestas": [{"pauta": p["nombre"], "pauta_id": p["pauta_id"], **paso}
                       for p in pautas for paso in p["pasos"] if paso["nota"]],
        "pautas": pautas,
    }
