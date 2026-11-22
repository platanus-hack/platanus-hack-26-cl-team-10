"""Las métricas de una empresa cliente, leídas de su bitácora (ADR-0014).

Nada de esto se guarda: cada métrica se calcula al pedirla, leyendo los eventos de las OT de
la empresa, igual que la calificación. Así no hay un número que se desfase de la bitácora.

Agrupan por pauta, por equipo, por paso y por día. Nunca por persona: un paso que se saltan
muchos operarios apunta a la pauta, no a ellos (LOGICA, REFERENCIAS 33), y Factum mira el paso,
no a quien lo ejecuta (ADR-0013).

Qué cuenta como desviación: una alerta de seguridad, de orden o de control perdido; un paso en
conflicto entre la palabra y la evidencia; y un paso que confirmó una persona porque la
evidencia no lo vio. Las alertas de señal y de sensor pegado hablan de los sensores, no de
cómo se ejecutó, y van aparte.
"""

from __future__ import annotations

import sqlite3
from collections import Counter, defaultdict
from dataclasses import dataclass, field
from datetime import date, datetime, timedelta

from app import catalogo, db
from app.contratos import Estado, Evento, Pauta, TipoEvento
from app.scoring import CONFIANZA_CAMARA_MIN

DE_EJECUCION = ("seguridad", "orden", "control")
DE_SENSORES = ("senal", "pegado")
POR_PASO = ("orden", "control", "conflicto", "persona")
EVIDENCIAS = ("sensor", "camara", "persona", "palabra")
ESTADOS_OT = ("sin_asignar", "asignada", "en_ejecucion", "entregada", "completa")


@dataclass
class Alerta:
    clase: str
    paso: str | None
    abierta: datetime
    resuelta: datetime | None = None


@dataclass
class Ejecucion:
    """Lo que dice la bitácora de una OT, ya leído: lo que las métricas y la mejora necesitan."""

    ot: dict
    pauta: Pauta
    abierta: datetime
    inicio: datetime | None = None
    fin: datetime | None = None
    alertas: list[Alerta] = field(default_factory=list)
    verificados: dict[str, str] = field(default_factory=dict)
    por_paso: dict[str, Counter] = field(default_factory=lambda: defaultdict(Counter))
    observaciones: list[dict] = field(default_factory=list)
    operarios: set[str] = field(default_factory=set)
    relevos: Counter = field(default_factory=Counter)
    veredictos: dict[str, list[Evento]] = field(default_factory=lambda: defaultdict(list))
    cierres: dict[str, datetime] = field(default_factory=dict)

    def segundos_del_paso(self, paso_id: str) -> float | None:
        """Desde que se cerró el paso anterior hasta que se cerró este. El primero no tiene: la bitácora no guarda
        cuándo empezó a trabajar el operario, solo cuándo se cerró cada paso."""
        if paso_id not in self.cierres:
            return None
        antes = [t for p, t in self.cierres.items() if t <= self.cierres[paso_id] and p != paso_id]
        return (self.cierres[paso_id] - max(antes)).total_seconds() if antes else None

    @property
    def desviaciones(self) -> Counter:
        c = Counter(a.clase for a in self.alertas if a.clase in DE_EJECUCION)
        for senales in self.por_paso.values():
            c["conflicto"] += senales["conflicto"]
            c["persona"] += senales["persona"]
        return c

    @property
    def desviada(self) -> bool:
        return sum(self.desviaciones.values()) > 0

    @property
    def minutos(self) -> float | None:
        if self.inicio is None or self.fin is None:
            return None
        return (self.fin - self.inicio).total_seconds() / 60


def _hora(ts: str) -> datetime:
    return datetime.fromisoformat(ts)


def _evidencia(ev: Evento) -> str:
    tipo = (ev.evidencia or {}).get("tipo")
    if tipo in ("camara", "deteccion"):
        return "camara"
    return tipo if tipo in ("sensor", "persona") else "palabra"


def leer(cx: sqlite3.Connection, ot: dict) -> Ejecucion:
    pauta = db.leer_pauta(cx, ot["pauta"], ot["version"])
    e = Ejecucion(ot=ot, pauta=pauta, abierta=_hora(ot["abierta_en"]))
    abiertas: dict[int, Alerta] = {}
    ultimo: dict[str, Evento] = {}
    for ev in db.eventos(cx, ot["ot"]):
        if ev.tipo not in (TipoEvento.OT_ABIERTA, TipoEvento.OT_ASIGNADA) and e.inicio is None:
            e.inicio = _hora(ev.ts)
        if ev.tipo is TipoEvento.ALERTA:
            clave = (ev.evidencia or {}).get("clave", "")
            clase, _, resto = clave.partition(":")
            paso = resto if clase in ("orden", "control") else (ev.evidencia or {}).get("paso") if clase == "seguridad" else None
            a = Alerta(clase, paso, _hora(ev.ts))
            e.alertas.append(a)
            abiertas[ev.id] = a
            if a.paso:
                e.por_paso[a.paso][clase] += 1
        elif ev.tipo is TipoEvento.ALERTA_RESUELTA:
            a = abiertas.get((ev.evidencia or {}).get("resuelve"))
            if a is not None:
                a.resuelta = _hora(ev.ts)
        elif ev.tipo is TipoEvento.VEREDICTO and ev.paso_id:
            ultimo[ev.paso_id] = ev
            e.veredictos[ev.paso_id].append(ev)
            if ev.estado is Estado.VERIFICADO:
                e.cierres[ev.paso_id] = _hora(ev.ts)
            if ev.estado is Estado.EN_CONFLICTO:
                e.por_paso[ev.paso_id]["conflicto"] += 1
            if (ev.evidencia or {}).get("tipo") == "persona":
                e.por_paso[ev.paso_id]["persona"] += 1
                e.operarios.add(ev.actor)
        elif ev.tipo is TipoEvento.DECLARACION:
            e.operarios.add(ev.actor)
        elif ev.tipo is TipoEvento.OBSERVACION:
            e.operarios.add(ev.actor)
            e.observaciones.append({"paso": ev.paso_id, "categoria": (ev.evidencia or {}).get("categoria", "otra"),
                                    "texto": ev.declarado, "ts": ev.ts})
        elif ev.tipo in (TipoEvento.RELEVO_ENTREGADO, TipoEvento.RELEVO_RECIBIDO):
            e.relevos[str(ev.tipo)] += 1
    e.verificados = {p: _evidencia(ev) for p, ev in ultimo.items() if ev.estado is Estado.VERIFICADO}
    if ot["completa"]:
        cierres = [ev for ev in ultimo.values() if ev.estado is Estado.VERIFICADO]
        e.fin = max((_hora(ev.ts) for ev in cierres), default=None)
    return e


def ejecuciones(cx: sqlite3.Connection, ots: list[dict], desde: date | None = None, hasta: date | None = None) -> list[Ejecucion]:
    """Las OT abiertas entre `desde` y `hasta`, ambos incluidos."""
    salida = []
    for ot in ots:
        dia = _hora(ot["abierta_en"]).date()
        if (desde and dia < desde) or (hasta and dia > hasta):
            continue
        salida.append(leer(cx, ot))
    return salida


# ─── Cálculos ───────────────────────────────────────────────────────────────


def _pct(parte: int, total: int) -> float | None:
    return round(100 * parte / total, 1) if total else None


def _media(valores: list[float]) -> float | None:
    return round(sum(valores) / len(valores), 1) if valores else None


def _cumplimiento(es: list[Ejecucion]) -> dict:
    completas = [e for e in es if e.ot["completa"]]
    limpias = sum(1 for e in completas if not e.desviada)
    return {"completas": len(completas), "sin_desviaciones": limpias, "porcentaje": _pct(limpias, len(completas))}


def _desviaciones(es: list[Ejecucion]) -> dict:
    por_clase = Counter({c: 0 for c in (*DE_EJECUCION, "conflicto", "persona")})
    for e in es:
        por_clase.update(e.desviaciones)
    alertas = [a for e in es for a in e.alertas if a.clase in DE_EJECUCION]
    resueltas = [(a.resuelta - a.abierta).total_seconds() / 60 for a in alertas if a.resuelta]
    return {"total": sum(por_clase.values()), "por_clase": dict(por_clase),
            "alertas_abiertas": sum(1 for a in alertas if a.resuelta is None),
            "minutos_medios_para_resolver": _media(resueltas)}


def resumen(es: list[Ejecucion]) -> dict:
    """La foto de la empresa: cuánto se ejecutó, cuánto sin desviaciones, con qué evidencia y qué tan rápido."""
    por_estado = Counter({s: 0 for s in ESTADOS_OT})
    por_estado.update(e.ot["estado_general"] for e in es)
    por_evidencia = Counter({k: 0 for k in EVIDENCIAS})
    for e in es:
        por_evidencia.update(e.verificados.values())
    verificados = sum(por_evidencia.values())
    sensores = Counter(a.clase for e in es for a in e.alertas if a.clase in DE_SENSORES)
    observaciones = Counter(o["categoria"] for e in es for o in e.observaciones)
    return {
        "ots": {"total": len(es), "por_estado": dict(por_estado)},
        "cumplimiento": _cumplimiento(es),
        "pasos": {"verificados": verificados, "por_evidencia": dict(por_evidencia),
                  "con_evidencia_objetiva_pct": _pct(por_evidencia["sensor"] + por_evidencia["camara"], verificados)},
        "desviaciones": _desviaciones(es),
        "sensores": {"anomalias": sensores["senal"], "pegados": sensores["pegado"]},
        "minutos_medios_de_ejecucion": _media([m for e in es if (m := e.minutos) is not None]),
        "relevos": {"entregados": sum(e.relevos["relevo_entregado"] for e in es),
                    "recibidos": sum(e.relevos["relevo_recibido"] for e in es)},
        "observaciones": {"total": sum(observaciones.values()), "por_categoria": dict(observaciones)},
    }


def _paso_mas_desviado(es: list[Ejecucion]) -> dict | None:
    conteo: Counter = Counter()
    titulos = {}
    for e in es:
        for paso, senales in e.por_paso.items():
            conteo[paso] += sum(senales[s] for s in POR_PASO)
            try:
                titulos[paso] = e.pauta.paso(paso).titulo
            except KeyError:
                titulos[paso] = paso
    if not conteo or conteo.most_common(1)[0][1] == 0:
        return None
    paso, veces = conteo.most_common(1)[0]
    return {"paso": paso, "titulo": titulos[paso], "desviaciones": veces}


def _grupo(es: list[Ejecucion]) -> dict:
    d = _desviaciones(es)
    return {
        "ots": len(es),
        "cumplimiento": _cumplimiento(es),
        "desviaciones": d["total"],
        "por_clase": d["por_clase"],
        "minutos_medios_de_ejecucion": _media([m for e in es if (m := e.minutos) is not None]),
        "observaciones": sum(len(e.observaciones) for e in es),
        "paso_mas_desviado": _paso_mas_desviado(es),
    }


ORDENES = {
    "desviaciones": (lambda g: (-g["desviaciones"], -g["ots"]), "las más desviadas primero"),
    "cumplimiento": (lambda g: (g["cumplimiento"]["porcentaje"] is None, g["cumplimiento"]["porcentaje"] or 0), "el peor cumplimiento primero"),
    "ots": (lambda g: -g["ots"], "las más ejecutadas primero"),
    "minutos": (lambda g: -(g["minutos_medios_de_ejecucion"] or 0), "las más lentas primero"),
}


def _ordenar(grupos: list[dict], orden: str, limite: int) -> list[dict]:
    return sorted(grupos, key=ORDENES[orden][0])[:limite]


def por_pauta(cx: sqlite3.Connection, es: list[Ejecucion], orden: str = "desviaciones", limite: int = 50) -> list[dict]:
    grupos = defaultdict(list)
    for e in es:
        grupos[e.pauta.id].append(e)
    salida = []
    for pauta_id, del_grupo in grupos.items():
        ultima = max(del_grupo, key=lambda e: e.pauta.version).pauta
        salida.append({"pauta": pauta_id, "nombre": ultima.nombre,
                       "versiones": sorted({e.pauta.version for e in del_grupo}),
                       "protocolos": catalogo.protocolos_de(cx, pauta_id), **_grupo(del_grupo)})
    return _ordenar(salida, orden, limite)


def por_protocolo(cx: sqlite3.Connection, es: list[Ejecucion], orden: str = "desviaciones", limite: int = 50) -> list[dict]:
    """Cada protocolo de la empresa, por las OT de las pautas de las que es dueño (ADR-0018): la unidad en que la
    mejora itera, y la que le sirve al dueño de ese proceso."""
    grupos = defaultdict(list)
    for e in es:
        grupos[catalogo.protocolo_dueno(cx, e.pauta.id) or "sin_dueno"].append(e)
    salida = []
    for protocolo_id, del_grupo in grupos.items():
        nombre = catalogo.leer_protocolo(cx, protocolo_id)["nombre"] if protocolo_id != "sin_dueno" else "Sin protocolo dueño"
        pautas = sorted({e.pauta.id for e in del_grupo})
        salida.append({"protocolo": protocolo_id, "nombre": nombre, "pautas": pautas,
                       "versiones": {p: sorted({e.pauta.version for e in del_grupo if e.pauta.id == p}) for p in pautas},
                       **_grupo(del_grupo)})
    return _ordenar(salida, orden, limite)


def por_equipo(es: list[Ejecucion], orden: str = "desviaciones", limite: int = 50) -> list[dict]:
    grupos = defaultdict(list)
    for e in es:
        grupos[e.ot["equipo"]].append(e)
    salida = []
    for equipo, del_grupo in grupos.items():
        equipo_obs = [o for e in del_grupo for o in e.observaciones if o["categoria"] == "equipo"]
        salida.append({"equipo": equipo, "pautas": sorted({e.pauta.id for e in del_grupo}), **_grupo(del_grupo),
                       "observaciones_del_equipo": [{"texto": o["texto"], "ts": o["ts"]} for o in equipo_obs]})
    return _ordenar(salida, orden, limite)


def por_paso(es: list[Ejecucion], pauta: Pauta, orden: str = "pauta") -> list[dict]:
    """Cada paso de una versión de la pauta: con qué evidencia se cerró, cuántas veces se desvió y qué
    observaron los operarios. Solo las OT que ejecutaron esa versión."""
    es = [e for e in es if e.pauta.id == pauta.id and e.pauta.version == pauta.version]
    salida = []
    for paso in pauta.en_orden:
        senales = Counter({s: 0 for s in POR_PASO})
        evidencia = Counter({k: 0 for k in EVIDENCIAS})
        capas: Counter = Counter()
        confianzas, intentos, segundos, bajo_umbral = [], [], [], 0
        for e in es:
            senales.update(e.por_paso.get(paso.id, Counter()))
            if paso.id in e.verificados:
                evidencia[e.verificados[paso.id]] += 1
                cierre = next(v for v in reversed(e.veredictos[paso.id]) if v.estado is Estado.VERIFICADO)
                capas[_capa(cierre)] += 1
                conf = (cierre.evidencia or {}).get("confianza")
                if conf is not None:
                    confianzas.append(float(conf))
                    bajo_umbral += cierre.capa == 3 and float(conf) < CONFIANZA_CAMARA_MIN
                intentos.append(len(e.veredictos[paso.id]))
                if (s := e.segundos_del_paso(paso.id)) is not None:
                    segundos.append(s)
        salida.append({
            "paso": paso.id, "orden": paso.orden, "titulo": paso.titulo, "control_critico": paso.control_critico,
            "tipo_evidencia": str(paso.tipo_evidencia), "ejecuciones": len(es),
            "verificado": sum(evidencia.values()), "verificado_por": dict(evidencia),
            "capa_minima": paso.capa_minima, "cerrado_en_capa": {str(k): n for k, n in sorted(capas.items(), key=str)},
            "confianza": {"min": min(confianzas), "media": _media(confianzas), "max": max(confianzas),
                          "bajo_el_umbral": bajo_umbral} if confianzas else None,
            "intentos_medios": _media(intentos), "segundos_medios": _media(segundos),
            "desviaciones": sum(senales[s] for s in POR_PASO), "por_clase": {s: senales[s] for s in POR_PASO},
            "observaciones": [{"categoria": o["categoria"], "texto": o["texto"], "ts": o["ts"]}
                              for e in es for o in e.observaciones if o["paso"] == paso.id],
        })
    if orden == "desviaciones":
        salida.sort(key=lambda p: (-p["desviaciones"], p["orden"]))
    return salida


def _capa(ev: Evento) -> int | str:
    """La capa que cerró el paso, o quién: `persona` si lo confirmó contra la evidencia, `palabra` si es de confirmación."""
    if (ev.evidencia or {}).get("tipo") == "persona":
        return "persona"
    return ev.capa if ev.capa is not None else "palabra"


def serie(es: list[Ejecucion], intervalo: str = "dia") -> list[dict]:
    """Por día o por semana (que empieza el lunes), sin huecos entre el primero y el último."""
    def periodo(t: datetime) -> date:
        d = t.date()
        return d - timedelta(days=d.weekday()) if intervalo == "semana" else d

    filas: dict[date, Counter] = defaultdict(Counter)
    for e in es:
        filas[periodo(e.abierta)]["ots_abiertas"] += 1
        if e.fin is not None:
            filas[periodo(e.fin)]["ots_completas"] += 1
        for a in e.alertas:
            if a.clase in DE_EJECUCION:
                filas[periodo(a.abierta)]["desviaciones"] += 1
                filas[periodo(a.abierta)]["alertas_de_seguridad"] += a.clase == "seguridad"
        for o in e.observaciones:
            filas[periodo(_hora(o["ts"]))]["observaciones"] += 1
    if not filas:
        return []
    paso = timedelta(days=7 if intervalo == "semana" else 1)
    salida, d = [], min(filas)
    while d <= max(filas):
        c = filas.get(d, Counter())
        salida.append({"periodo": d.isoformat(), **{k: c[k] for k in
                       ("ots_abiertas", "ots_completas", "desviaciones", "alertas_de_seguridad", "observaciones")}})
        d += paso
    return salida
