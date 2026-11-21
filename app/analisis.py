"""Lo que se puede saber de una pauta y de sus ejecuciones sin preguntarle a un modelo.

Las skills de `.claude/skills/` reconocen un proceso, proponen su pauta y buscan mejoras
con un agente. Todo lo que ese agente afirma y se puede comprobar, se comprueba acá:
si cada paso cita el protocolo, si la estación puede cerrarlo, y qué análisis vale la
pena correr (ADR-0015). Como app/reglas.py, este módulo no sabe de HTTP ni de la base.

Un borrador es `{"pauta": <Pauta del contrato>, "documento": ruta, "analisis": {...}}`;
su forma está en .claude/skills/reconocer-proceso/SKILL.md.
"""

from __future__ import annotations

import re
from collections.abc import Collection, Mapping, Sequence
from datetime import datetime
from difflib import SequenceMatcher
from statistics import median

from app.contratos import Estado, Evento, Paso, Pauta, TipoEvento, TipoEvidencia
from app.reglas import reglas_seguridad

# ─── El criterio: sus umbrales ──────────────────────────────────────────────
# Un análisis cuesta (tokens, fotos etiquetadas, una persona que revisa). Estos números
# deciden cuándo se paga. Todos son `Candidata a validar`: cambiarlos es cambiar el criterio.

MIN_EJECUCIONES = 5   # bajo esto la historia de una pauta no se analiza: una desviación suelta no es una propuesta (LOGICA)
MIN_REPETICIONES = 2  # la misma desviación en el mismo paso, en OT distintas; el mismo mínimo de reglas.propuesta_de_mejora
PARTE_LENTA = 0.4     # un paso que se lleva esta fracción del tiempo de la pauta se mira


# ─── Lo que dice el protocolo ───────────────────────────────────────────────


def _plano(texto: str) -> str:
    """Sin formato Markdown ni espacios de más: una cita se busca por sus palabras."""
    # las marcas de énfasis se quitan sin dejar espacio: «**candado**, con» es «candado, con»
    return " ".join(re.sub(r"[>#|]", " ", re.sub(r"[*_`]", "", texto)).casefold().split())


def citas_sin_respaldo(borrador: Mapping, texto: str) -> list[str]:
    """Pasos del borrador cuya cita no aparece, literal, en el protocolo.

    Es el freno a que el agente invente un paso: lo que no se puede señalar en el
    documento no entra a la pauta como si viniera de él.
    """
    plano = _plano(texto)
    por_paso = borrador.get("analisis", {}).get("pasos", {})
    return [
        p["id"] for p in borrador["pauta"]["pasos"]
        if not (cita := _plano(por_paso.get(p["id"], {}).get("cita", ""))) or cita not in plano
    ]


# ─── Factibilidad: la pauta contra una estación ─────────────────────────────


def capa_esperada(paso: Paso) -> int:
    if paso.tipo_evidencia is TipoEvidencia.CAMARA:
        return 2 if paso.deteccion else 3
    return 1


def requiere(pauta: Pauta) -> dict:
    """Lo que una estación necesita para ejecutar la pauta, en la forma de datos/estaciones/."""
    sensores: dict[str, list[str]] = {}
    for p in pauta.en_orden:
        if p.sensor and p.sensor.espera not in sensores.setdefault(p.sensor.id, []):
            sensores[p.sensor.id].append(p.sensor.espera)
    return {
        "sensores": sensores,
        "camara": any(p.tipo_evidencia is TipoEvidencia.CAMARA for p in pauta.pasos),
        "clases": sorted({p.deteccion.clase for p in pauta.pasos if p.deteccion}),
    }


def factibilidad(pauta: Pauta, estacion: Mapping) -> list[dict]:
    """Por paso: qué capa puede cerrarlo en esta estación (None = una persona) y qué le falta."""
    sensores, clases = estacion.get("sensores", {}), estacion.get("clases", ())
    salida = []
    for p in pauta.en_orden:
        capa, falta = None, None
        if p.sensor:
            capa = 1
            if p.sensor.id not in sensores:
                falta = f"la estación no tiene el sensor «{p.sensor.id}»"
            elif p.sensor.espera not in sensores[p.sensor.id]:
                falta = f"«{p.sensor.id}» no reporta «{p.sensor.espera}» (reporta {', '.join(sensores[p.sensor.id])})"
        elif p.tipo_evidencia is TipoEvidencia.CAMARA:
            capa = 2 if p.deteccion and p.deteccion.clase in clases else 3
            if not estacion.get("camara"):
                falta = "la estación no tiene cámara"
        salida.append({"paso": p.id, "capa": capa, "falta": falta})
    return salida


def se_cierran_solos(pauta: Pauta) -> list[str]:
    """Pasos de sensor que esperan el valor que un paso anterior ya dejó en ese sensor.

    «Probar que no arranca» con `correa = detenida` después de «Parar la correa»: la
    lectura ya está, así que el paso se verifica sin que nadie haga nada.
    """
    dejado: dict[str, str] = {}
    solos = []
    for p in pauta.en_orden:
        if p.sensor:
            if dejado.get(p.sensor.id) == p.sensor.espera:
                solos.append(p.id)
            dejado[p.sensor.id] = p.sensor.espera
    return solos


def alertas_en_ejecucion_correcta(pauta: Pauta) -> list[dict]:
    """Reglas de seguridad que disparan aunque la pauta se ejecute bien, y en qué paso.

    Las reglas de app/reglas.py son globales y comparan nombres de sensor: una pauta nueva
    que use `energia` o `zona` con otro sentido, o que pida a propósito lo que una regla
    prohíbe, haría sonar la alarma en cada OT. Solo cuenta las lecturas que la propia pauta
    deja; el estado inicial de la estación no se conoce.
    """
    lecturas: dict[str, str] = {}
    vistas: dict[str, str] = {}
    for p in pauta.en_orden:
        if p.sensor:
            lecturas[p.sensor.id] = p.sensor.espera
            for v in reglas_seguridad(lecturas):
                vistas.setdefault(v.detalle, p.id)
    return [{"paso": paso, "aviso": aviso} for aviso, paso in vistas.items()]


# ─── La historia: cómo se ejecutó una versión de la pauta ───────────────────


def historia(pauta: Pauta, ots: Mapping[str, Sequence[Evento]]) -> dict[str, dict]:
    """Por paso, sobre las OT de UNA versión de la pauta. Cuenta OT, nunca personas (LOGICA).

    conflicto: OT donde lo declarado y la evidencia no coincidieron.
    por_persona: OT donde alguien lo confirmó contra el sensor o la cámara.
    alerta: OT donde este paso quedó saltado (orden invertido) o se deshizo (control perdido).
    segundos: mediana desde que se cerró el paso anterior hasta que se cerró este.
    """
    h = {p.id: {"ots": len(ots), "verificado": 0, "conflicto": 0, "por_persona": 0, "alerta": 0, "segundos": []}
         for p in pauta.pasos}
    confirma = {p.id for p in pauta.pasos if p.tipo_evidencia is TipoEvidencia.CONFIRMACION}
    for eventos in ots.values():
        visto: set[tuple[str, str]] = set()
        # shortcut: el primer paso se mide desde que se abrió la OT, que incluye la espera; cuando se
        # registre `paso_iniciado`, medir desde ahí
        anterior = eventos[0].ts if eventos else None

        def contar(paso_id: str | None, que: str) -> bool:
            nuevo = paso_id in h and (paso_id, que) not in visto
            if nuevo:
                visto.add((paso_id, que))
                h[paso_id][que] += 1
            return nuevo

        for ev in eventos:
            if ev.tipo is TipoEvento.ALERTA:
                e = ev.evidencia or {}
                contar(e.get("pendiente") or e.get("paso"), "alerta")
            elif ev.estado is Estado.EN_CONFLICTO:
                contar(ev.paso_id, "conflicto")
            elif ev.estado is Estado.VERIFICADO:
                if ev.capa is None and ev.paso_id not in confirma:
                    contar(ev.paso_id, "por_persona")
                if contar(ev.paso_id, "verificado"):
                    h[ev.paso_id]["segundos"].append(
                        (datetime.fromisoformat(ev.ts) - datetime.fromisoformat(anterior)).total_seconds())
                    anterior = ev.ts
    for d in h.values():
        d["segundos"] = round(median(d["segundos"]), 1) if d["segundos"] else None
    return h


# ─── El criterio: qué se analiza y qué no ───────────────────────────────────


def criterio(
    pauta: Pauta,
    estacion: Mapping | None = None,
    peligros: Sequence[Mapping] = (),
    preguntas_medidas: Collection[str] = (),
) -> list[dict]:
    """Los análisis que vale la pena correr, cada uno con su paso y su razón.

    Lo que no sale de acá no se analiza: un paso que su sensor cierra, que no es
    crítico y que nadie se salta, no necesita a un agente. Cada `analisis` es el
    nombre de una skill de .claude/skills/, salvo `instrumentar`, que es una
    decisión de hardware y la toma una persona.

    peligros: los «no puede pasar» del borrador, cada uno con `que` y `sensores`.
    preguntas_medidas: las preguntas visuales que ya tienen casos en el eval de capa 3.
    """
    salida = []

    def pedir(analisis: str, sobre: str, por_que: str) -> None:
        salida.append({"analisis": analisis, "sobre": sobre, "por_que": por_que})

    capas = {f["paso"]: f for f in factibilidad(pauta, estacion)} if estacion is not None else {}
    for p in pauta.en_orden:
        f = capas.get(p.id, {"capa": capa_esperada(p) if p.tipo_evidencia is not TipoEvidencia.CONFIRMACION else None,
                             "falta": None})
        if f["falta"]:
            pedir("instrumentar", p.id, f"«{p.titulo}» no se puede cerrar: {f['falta']}")
        elif p.control_critico and f["capa"] != 1:
            quien = "la palabra del operario" if f["capa"] is None else "la cámara"
            pedir("instrumentar", p.id, f"«{p.titulo}» es control crítico y lo cierra {quien}: solo la capa 1 interrumpe")
        if f["capa"] == 3 and p.pregunta_visual not in preguntas_medidas:
            pedir("solucion-vision", p.id, f"nadie midió al juez con «{p.pregunta_visual}»")

    disponibles = estacion.get("sensores", {}) if estacion is not None else None
    for pel in peligros:
        condicion = pel.get("sensores") or {}
        if not condicion:
            continue  # un peligro que ningún sensor describe no es una regla: queda en el texto del protocolo
        if reglas_seguridad(condicion):
            continue  # ya hay una regla que dispara con esas lecturas
        faltan = [s for s in condicion if disponibles is not None and s not in disponibles]
        if faltan:
            pedir("instrumentar", pel["que"], f"la regla necesita sensores que la estación no tiene: {', '.join(faltan)}")
        else:
            pedir("regla-programatica", pel["que"], "ninguna regla de seguridad dispara con " +
                  " y ".join(f"{k} = {v}" for k, v in condicion.items()))

    return salida


def criterio_de_historia(pauta: Pauta, hist: Mapping[str, Mapping]) -> list[dict]:
    """Lo mismo, mirando cómo se ejecutó: `hist` es la salida de `historia`. Con poca historia no opina."""
    salida = []
    n = max(d["ots"] for d in hist.values())
    if n < MIN_EJECUCIONES:
        return salida
    total = sum(d["segundos"] or 0 for d in hist.values())
    for p in pauta.en_orden:
        d = hist[p.id]
        if p.tipo_evidencia is TipoEvidencia.CAMARA and not p.deteccion and d["por_persona"] >= MIN_REPETICIONES:
            salida.append({"analisis": "solucion-vision", "sobre": p.id,
                           "por_que": f"la cámara no cerró «{p.titulo}» en {d['por_persona']} de {n} OT: probar un detector"})
        razones = [f"{d[k]} OT con {nombre}" for k, nombre in
                   (("conflicto", "conflicto"), ("por_persona", "cierre por persona"), ("alerta", "alerta"))
                   if d[k] >= MIN_REPETICIONES]
        if total and (d["segundos"] or 0) / total >= PARTE_LENTA:
            razones.append(f"se lleva el {100 * d['segundos'] / total:.0f} % del tiempo")
        if razones:
            salida.append({"analisis": "optimizar-proceso", "sobre": p.id,
                           "por_que": f"«{p.titulo}»: {'; '.join(razones)} (de {n} OT)"})
    return salida


# ─── Medir al que reconoce ──────────────────────────────────────────────────


def comparar(generada: Pauta, referencia: Pauta) -> dict:
    """Cuánto se parece una pauta propuesta a la que escribió una persona.

    Alinea los pasos por la evidencia que los cierra, en orden: los títulos cambian de
    una redacción a otra, pero «energia = cortada antes de bloqueo = puesto» no.
    """
    def firma(p: Paso) -> tuple:
        return (str(p.tipo_evidencia), p.sensor.id if p.sensor else None, p.sensor.espera if p.sensor else None)

    g, r = generada.en_orden, referencia.en_orden
    bloques = SequenceMatcher(None, [firma(p) for p in g], [firma(p) for p in r], autojunk=False).get_matching_blocks()
    pares = [(g[b.a + k], r[b.b + k]) for b in bloques for k in range(b.size)]
    return {
        "pasos_referencia": len(r),
        "pasos_generada": len(g),
        "coinciden": len(pares),
        # un paso de cámara o de confirmación calza con cualquier otro del mismo tipo: solo los de sensor prueban algo
        "coinciden_por_sensor": sum(1 for a, _ in pares if a.sensor),
        "sensor_referencia": sum(1 for p in r if p.sensor),
        "critico_igual": sum(a.control_critico == b.control_critico for a, b in pares),
        "sin_par": [p.id for p in r if p.id not in {b.id for _, b in pares}],
    }
