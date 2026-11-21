"""El inventario de lo que el servidor puede comprobar, y el validador de una pauta contra él.

Una pauta nombra sensores, valores, clases del detector y preguntas visuales. Para que una pauta
nueva, la escriba una persona o un modelo, nombre solo lo que existe, hace falta saber qué existe.
Nada de esto se guarda aparte: se lee de lo que ya hay en la base.

- **Las pautas** dicen qué sensores y qué valores se esperan, y qué clases busca el detector.
- **La bitácora** dice qué valores llegaron de verdad: cada veredicto, alerta y resolución guarda
  la lectura que lo produjo, y las de cámara guardan la clase o la respuesta con su confianza.
- **La tabla de sensores** dice el último valor de cada uno y cuándo llegó.
- **Las reglas de peligro** de `app/reglas.py` dicen qué combinaciones interrumpen al operario.
- **El detector**, si corre en el servidor, dice qué clases conoce su modelo.

Los sensores son globales en el servidor, no de una estación: eso es una brecha conocida (pantalla 9
de Factum por dentro), y el inventario lo dice en vez de esconderlo.

El validador (`validar`) junta las reglas que una pauta tiene que cumplir para guardarse y las que
tiene que cumplir para que la verificación funcione: las cuatro de la pantalla 10 de Factum por
dentro y las del inventario.
"""

from __future__ import annotations

import sqlite3
import statistics
from collections import Counter, defaultdict
from datetime import UTC, datetime

from app import catalogo, db
from app.catalogo import ReglaDeNegocio
from app.contratos import Pauta, TipoEvidencia, TipoEvento
from app.reglas import _PELIGROS, CONF_ALTA

NO_SON_SENSORES = {"tipo", "fuente", "clave", "resuelve", "sensores", "certeza", "id", "valor", "espera", "sensor",
                   "adelantado", "pendiente", "paso", "cuadro", "semilla"}


def _numero(valor) -> float | None:
    try:
        return float(valor)
    except (TypeError, ValueError):
        return None


def _lecturas(ev) -> list[tuple[str, str]]:
    """Los pares (sensor, valor) que un evento guardó como evidencia."""
    e = ev.evidencia or {}
    pares = []
    if e.get("tipo") == "sensor" and "id" in e and e.get("valor") is not None:
        pares.append((e["id"], e["valor"]))
    if isinstance(e.get("sensores"), dict):
        pares += [(k, v) for k, v in e["sensores"].items() if v is not None]
    if e.get("sensor") and e.get("valor") is not None:
        pares.append((e["sensor"], e["valor"]))
    if e.get("tipo") == "sensor" and ev.tipo is TipoEvento.ALERTA:
        pares += [(k, v) for k, v in e.items() if k not in NO_SON_SENSORES and isinstance(v, str)]
    return [(s, str(v)) for s, v in pares]


def _pautas_vigentes(cx: sqlite3.Connection) -> list[Pauta]:
    salida = []
    for f in cx.execute("SELECT DISTINCT id FROM pautas ORDER BY id").fetchall():
        version = catalogo.ultima_aprobada(cx, f["id"]) or max(v["version"] for v in catalogo.versiones(cx, f["id"]))
        salida.append(db.leer_pauta(cx, f["id"], version))
    return salida


def inventario(cx: sqlite3.Connection, detector=None, sesiones: list[dict] | None = None) -> dict:
    """Qué sensores, valores, clases y preguntas conoce el servidor, y de dónde sale cada dato."""
    pautas = _pautas_vigentes(cx)
    vistos: dict[str, Counter] = defaultdict(Counter)
    detecciones: dict[str, list[dict]] = defaultdict(list)
    preguntas: dict[tuple[str, str, str], list[dict]] = defaultdict(list)
    version_de = {}
    for f in cx.execute("SELECT id, pauta_id, pauta_version FROM ots").fetchall():
        version_de[f["id"]] = (f["pauta_id"], f["pauta_version"])
    for ev in db.todos_los_eventos(cx):
        for sensor, valor in _lecturas(ev):
            vistos[sensor][valor] += 1
        e = ev.evidencia or {}
        if ev.tipo is TipoEvento.VEREDICTO and e.get("tipo") == "deteccion":
            detecciones[e["clase"]].append({"confianza": e.get("confianza"), "presente": e.get("presente"),
                                            "decidio": ev.estado is not None and str(ev.estado) == "verificado"})
        if ev.tipo is TipoEvento.VEREDICTO and e.get("tipo") == "camara" and ev.paso_id:
            pauta_id, _ = version_de.get(ev.ot_id, ("?", 0))
            preguntas[(pauta_id, ev.paso_id, e.get("pregunta", ""))].append(e)

    actuales = {f["id"]: (f["valor"], f["ts"]) for f in cx.execute("SELECT id, valor, ts FROM sensores").fetchall()}
    usos: dict[str, list[dict]] = defaultdict(list)
    clases_usadas: dict[str, list[dict]] = defaultdict(list)
    for p in pautas:
        for paso in p.en_orden:
            if paso.sensor:
                usos[paso.sensor.id].append({"pauta": p.id, "version": p.version, "paso": paso.id, "titulo": paso.titulo,
                                             "espera": paso.sensor.espera, "control_critico": paso.control_critico})
            if paso.deteccion:
                clases_usadas[paso.deteccion.clase].append({"pauta": p.id, "version": p.version, "paso": paso.id,
                                                            "titulo": paso.titulo, "presente": paso.deteccion.presente})
    peligros: dict[str, list[dict]] = defaultdict(list)
    for condicion, aviso, fuente in _PELIGROS:
        for sensor in condicion:
            peligros[sensor].append({"si": condicion, "aviso": aviso.split(".")[0], "fuente": fuente})

    ahora = datetime.now(UTC)
    sensores = []
    for sid in sorted(set(vistos) | set(actuales) | set(usos) | set(peligros)):
        valores = vistos.get(sid, Counter())
        numeros = [n for v, c in valores.items() if (n := _numero(v)) is not None for _ in range(c)]
        actual = actuales.get(sid)
        sensores.append({
            "id": sid,
            "valor_actual": actual[0] if actual else None,
            "leido_hace_s": round((ahora - datetime.fromisoformat(actual[1])).total_seconds()) if actual else None,
            "numerico": bool(numeros) and len(numeros) == sum(valores.values()),
            "valores_vistos": dict(valores.most_common()) if not numeros or len(numeros) != sum(valores.values()) else None,
            "rango_visto": {"min": min(numeros), "mediana": statistics.median(numeros), "max": max(numeros),
                            "lecturas": len(numeros)} if numeros else None,
            "valores_que_esperan_las_pautas": sorted({u["espera"] for u in usos.get(sid, [])}),
            "pautas": usos.get(sid, []),
            "reglas_de_peligro": peligros.get(sid, []),
        })

    en_modelo = set(getattr(detector, "clases", None) or [])
    clases = []
    for clase in sorted(en_modelo | set(clases_usadas) | set(detecciones)):
        ds = detecciones.get(clase, [])
        confs = [d["confianza"] for d in ds if d["confianza"] is not None]
        clases.append({
            "clase": clase, "en_el_modelo": clase in en_modelo if detector else None,
            "pautas": clases_usadas.get(clase, []),
            "veredictos": len(ds), "decidio_capa_2": sum(1 for d in ds if d["decidio"]),
            "confianza": {"min": min(confs), "mediana": statistics.median(confs), "max": max(confs)} if confs else None,
        })

    visuales = []
    for (pauta_id, paso_id, pregunta), es in sorted(preguntas.items()):
        confs = [e["confianza"] for e in es if e.get("confianza") is not None]
        visuales.append({"pauta": pauta_id, "paso": paso_id, "pregunta": pregunta, "respuestas": len(es),
                         "si": sum(1 for e in es if e.get("respuesta")),
                         "confianza_media": round(sum(confs) / len(confs), 3) if confs else None})

    return {
        "sensores": sensores,
        "detector": {"en_servidor": detector is not None, "modelo": getattr(detector, "modelo", None),
                     "clases": sorted(en_modelo), "certeza_para_decidir": CONF_ALTA},
        "clases": clases,
        "preguntas_visuales": visuales,
        "estaciones_en_sesion": sesiones or [],
        "limites": ["Los sensores son globales en el servidor, no de una estación: dos estaciones con el mismo "
                    "nombre de sensor se mezclan.",
                    "La bitácora guarda la lectura que produjo un veredicto o una alerta, no cada lectura: "
                    "`valores_vistos` cuenta esas, no el total que mandó el edge."],
    }


# ─── El validador ───────────────────────────────────────────────────────────

REGLAS = {
    "V1": "Control crítico que no cierra un sensor",
    "V2": "Un paso espera el valor de reposo de su sensor",
    "V3": "La reposición no va en orden inverso",
    "V4": "capa_minima no coincide con lo que cierra el paso",
    "I1": "Sensor que el servidor no conoce",
    "I2": "Valor que nunca se vio en ese sensor",
    "I3": "Clase que el detector no conoce",
}


def _hallazgo(regla: str, paso: str | None, texto: str) -> dict:
    return {"regla": regla, "titulo": REGLAS[regla], "paso": paso, "texto": texto}


def _reposo(pauta: Pauta, dado: dict[str, str]) -> dict[str, str]:
    """El valor de cada sensor antes de empezar. Si no viene, el que deja el último paso que lo usa:
    una pauta de mantención devuelve el equipo a como estaba."""
    ultimo: dict[str, str] = {}
    veces: Counter = Counter()
    for paso in pauta.en_orden:
        if paso.sensor:
            ultimo[paso.sensor.id] = paso.sensor.espera
            veces[paso.sensor.id] += 1
    return {**{s: v for s, v in ultimo.items() if veces[s] > 1}, **dado}


def validar(cx: sqlite3.Connection, d: dict, inv: dict | None = None, reposo: dict[str, str] | None = None) -> dict:
    """Si la pauta se puede guardar (`errores`) y qué le va a fallar a la verificación (`hallazgos`)."""
    try:
        pauta = catalogo.pauta_desde_dict(d)
    except (ReglaDeNegocio, KeyError, ValueError, TypeError) as e:
        return {"valida": False, "errores": [f"pauta mal formada: {e}"], "hallazgos": [], "reposo": {}}
    errores = []
    versiones = [v["version"] for v in catalogo.versiones(cx, pauta.id)]
    siguiente = (max(versiones) + 1) if versiones else 1
    if pauta.version != siguiente:
        errores.append(f"la pauta {pauta.id} va en la versión {siguiente - 1}; la nueva tiene que ser la {siguiente}")

    hallazgos = []
    pasos = pauta.en_orden
    for paso in pasos:
        if paso.control_critico and paso.tipo_evidencia is not TipoEvidencia.SENSOR:
            como = "la palabra del operario" if paso.tipo_evidencia is TipoEvidencia.CONFIRMACION else "la cámara"
            hallazgos.append(_hallazgo("V1", paso.id, f"«{paso.titulo}» es control crítico y lo cierra {como}: si se "
                                       "deshace, nada avisa, porque «control perdido» solo vigila pasos de sensor"))
        esperada = {TipoEvidencia.SENSOR: 1, TipoEvidencia.CAMARA: 2 if paso.deteccion else 3}.get(paso.tipo_evidencia)
        if esperada is not None and paso.capa_minima != esperada:
            hallazgos.append(_hallazgo("V4", paso.id, f"«{paso.titulo}» dice capa_minima {paso.capa_minima} y lo "
                                       f"cierra la capa {esperada}"))

    en_reposo = _reposo(pauta, reposo or {})
    critico_antes = False
    primero: dict[str, int] = {}
    for paso in pasos:
        if paso.sensor and paso.sensor.id not in primero:
            primero[paso.sensor.id] = paso.orden
            if critico_antes and en_reposo.get(paso.sensor.id) == paso.sensor.espera:
                hallazgos.append(_hallazgo("V2", paso.id, f"«{paso.titulo}» espera {paso.sensor.id} = {paso.sensor.espera}, "
                                           "que es su valor en reposo: la primera lectura del edge abre una alerta de "
                                           "orden apenas empieza la OT"))
        critico_antes = critico_antes or paso.control_critico
    ultimo = {}
    for paso in pasos:
        if paso.sensor:
            ultimo[paso.sensor.id] = paso.orden
    pares = [s for s in primero if ultimo[s] != primero[s]]
    for a in pares:
        for b in pares:
            if primero[a] < primero[b] and ultimo[a] < ultimo[b]:
                hallazgos.append(_hallazgo("V3", None, f"{a} se pone antes que {b} y también se repone antes: lo que se "
                                           "pone en un orden se retira en el contrario (REFERENCIAS 48 y 50)"))

    inv = inv or inventario(cx)
    conocidos = {s["id"]: s for s in inv["sensores"]}
    for paso in pasos:
        if paso.sensor:
            s = conocidos.get(paso.sensor.id)
            if s is None:
                hallazgos.append(_hallazgo("I1", paso.id, f"ningún edge, pauta ni regla nombra el sensor {paso.sensor.id}"))
            else:
                valores = set(s["valores_vistos"] or {}) | set(s["valores_que_esperan_las_pautas"]) | (
                    {s["valor_actual"]} if s["valor_actual"] else set())
                valores |= {v for r in s["reglas_de_peligro"] for k, v in r["si"].items() if k == paso.sensor.id}
                if not s["numerico"] and paso.sensor.espera not in valores:
                    hallazgos.append(_hallazgo("I2", paso.id, f"{paso.sensor.id} = {paso.sensor.espera} nunca se vio; se "
                                               f"conocen {', '.join(sorted(valores)) or 'ninguno'}"))
        if paso.deteccion and inv["detector"]["en_servidor"] and paso.deteccion.clase not in inv["detector"]["clases"]:
            hallazgos.append(_hallazgo("I3", paso.id, f"el detector no conoce «{paso.deteccion.clase}»: el paso irá "
                                       "siempre a la capa 3"))
    return {"valida": not errores, "errores": errores, "hallazgos": hallazgos, "reposo": en_reposo,
            "pauta": catalogo.resumen_pauta(cx, pauta) | {"version": pauta.version}}
