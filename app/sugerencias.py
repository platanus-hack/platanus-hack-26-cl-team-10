"""El cambio concreto que propone cada propuesta de mejora, y la versión siguiente que arma Factum con las aceptadas.

Cada propuesta (`app/mejora.py`) trae un borrador: qué pasos agrega, separa o reescribe la versión siguiente de la
pauta. Lo arma el código con reglas fijas, así que funciona sin modelo. Encima, si hay `ANTHROPIC_API_KEY`, un modelo
puede reescribir el título, la instrucción y el porqué de los pasos que el borrador ya cambia, y el código rechaza su
texto si cita una OT que no está en la propuesta o si toca otra cosa (el mismo patrón de app/cerebro.py).

«Aplicar» en la pantalla del supervisor es aceptar la propuesta. La versión la arma el equipo de Factum con todas las
aceptadas de esa pauta (`version_siguiente`), queda sin aprobar, y aprobarla pasa por la regla que no deja sacar un
control crítico (catalogo.aprobar_pauta, ADR-0016). El reporte pasa por Factum (ADR-0018).
"""

from __future__ import annotations

import os
import re
import sqlite3
from collections.abc import Sequence
from dataclasses import replace

from app import analisis, catalogo, cerebro, db, mejora, reglas
from app.catalogo import ReglaDeNegocio
from app.contratos import Paso, Pauta, TipoEvidencia

FRASE = {
    "seguridad": "hacerlo después crea una condición de peligro",
    "orden": "en las OT donde se adelantó, el paso se hizo antes de su turno",
    "control": "en las OT donde se deshizo, el control no se mantuvo hasta el paso que lo retira",
    "conflicto": "en las OT donde se declaró antes, la palabra y la evidencia no coincidieron",
}

SISTEMA = (
    "Reescribes, en español y de tú, el título y la instrucción de pasos de una pauta de mantenimiento industrial, y el "
    "porqué de cada cambio, para que un operario entienda cuándo el paso está hecho. Recibes los cambios que ya decidió "
    "el sistema y las OT que los respaldan. No cambias qué evidencia cierra el paso ni su orden. El porqué cita las OT "
    "por su id y solo las que recibes. Título corto, en infinitivo."
)
ESQUEMA = {
    "type": "object",
    "properties": {"cambios": {"type": "array", "items": {
        "type": "object",
        "properties": {"indice": {"type": "integer"}, "titulo": {"type": "string"}, "instruccion": {"type": "string"},
                       "porque": {"type": "string"}},
        "required": ["indice", "titulo", "instruccion", "porque"], "additionalProperties": False}}},
    "required": ["cambios"], "additionalProperties": False,
}
CAMPOS_DEL_MODELO = {"indice", "titulo", "instruccion", "porque"}
_OT = re.compile(r"\bot-[\w-]+")


# ─── Las piezas ─────────────────────────────────────────────────────────────


def _a_dict(pauta: Pauta) -> dict:
    """La pauta en la forma de datos/ (la misma de db.guardar_pauta)."""
    pasos = []
    for p in pauta.en_orden:
        d = {"id": p.id, "orden": p.orden, "titulo": p.titulo, "instruccion": p.instruccion,
             "tipo_evidencia": str(p.tipo_evidencia), "capa_minima": p.capa_minima, "control_critico": p.control_critico}
        if p.pregunta_visual:
            d["pregunta_visual"] = p.pregunta_visual
        if p.sensor:
            d["sensor"] = {"id": p.sensor.id, "espera": p.sensor.espera}
        if p.deteccion:
            d["deteccion"] = {"clase": p.deteccion.clase, "presente": p.deteccion.presente}
        if p.comparar_con:
            d["comparar_con"] = p.comparar_con
        if p.cumple:
            d["cumple"] = list(p.cumple)
        pasos.append(d)
    return {"id": pauta.id, "nombre": pauta.nombre, "version": pauta.version, "equipo": pauta.equipo, "pasos": pasos}


def _esquema_de_ids(pasos: Sequence[Paso]) -> str | None:
    """El prefijo si los ids son «<prefijo><orden>» (p1, e1, l1); None si la pauta usa otros."""
    m = [re.fullmatch(r"([a-z]+)(\d+)", p.id) for p in pasos]
    if all(m) and len({x.group(1) for x in m}) == 1 and [int(x.group(2)) for x in m] == [p.orden for p in pasos]:
        return m[0].group(1)
    return None


def _confirmacion(nombre: str, exige: str, cumple: str, protocolo: str) -> Paso:
    instruccion = (exige.rstrip(".") + "." if exige else f"{nombre}.") + \
        f" Hazlo y confírmalo antes de seguir: lo exige {protocolo}."
    return Paso(id="__nuevo", orden=0, titulo=nombre, instruccion=instruccion, tipo_evidencia=TipoEvidencia.CONFIRMACION,
                capa_minima=1, control_critico=True, cumple=(cumple,))


def _hecho(p: Paso) -> str:
    if p.sensor:
        return f"{p.sensor.id} marque {p.sensor.espera}"
    if p.tipo_evidencia is TipoEvidencia.CAMARA:
        return "la cámara lo vea hecho"
    return "lo hayas hecho y confirmado"


def _dominante(senales: dict) -> str | None:
    vivas = [s for s in mejora.SENALES if senales.get(s)]
    return max(vivas, key=lambda s: (senales[s], -mejora.SENALES.index(s))) if vivas else None


def _lista(ots: Sequence[str]) -> str:
    ots = list(ots)
    return ots[0] if len(ots) == 1 else ", ".join(ots[:-1]) + f" y {ots[-1]}"


# ─── El borrador de una propuesta ───────────────────────────────────────────


class _Pasos:
    """Los pasos mientras se aplican los cambios, cada uno con una clave que no cambia: su id original, o «+n» si es
    nuevo. Así dos cambios sobre el mismo paso se encadenan, y los ids se renumeran recién al final."""

    def __init__(self, pasos: Sequence[Paso]):
        self.filas: list[list] = [[p.id, p] for p in pasos]
        self._nuevos = 0

    def indice(self, clave: str) -> int:
        return next(i for i, (k, _) in enumerate(self.filas) if k == clave)

    def insertar(self, i: int, paso: Paso) -> str:
        self._nuevos += 1
        clave = f"+{self._nuevos}"
        self.filas.insert(i, [clave, paso])
        return clave

    def paso(self, clave: str) -> Paso:
        return self.filas[self.indice(clave)][1]

    def cambiar(self, clave: str, paso: Paso) -> None:
        self.filas[self.indice(clave)][1] = paso


def _aplicar(cx: sqlite3.Connection, pasos: _Pasos, p: dict) -> list[dict]:
    """Aplica una propuesta sobre los pasos y devuelve sus cambios, cada uno con la clave del paso que toca."""
    if p["tipo"] == "conformidad":
        h = p["conformidad"]
        prot = next(x for x in catalogo.controles_de(cx, p["pauta"]) if x["id"] == h["protocolo"])
        controles = sorted(prot["controles"], key=lambda c: c["orden"])
        if h["tipo"] == "falta":
            c = next(x for x in controles if x["id"] == h["control"])
            donde = 0
            for previo in reversed([x for x in controles if x["orden"] < c["orden"]]):
                marca = f"{prot['id']}:{previo['id']}"
                cumplen = [i for i, (_, s) in enumerate(pasos.filas) if marca in s.cumple]
                if cumplen:
                    donde = cumplen[-1] + 1
                    break
            despues_de = pasos.filas[donde - 1][1].titulo if donde else None
            clave = pasos.insertar(donde, _confirmacion(c["nombre"], c.get("exige", ""), f"{prot['id']}:{c['id']}", prot["id"]))
            return [{"tipo": "agrega", "clave": clave, "antes": None, "despues_de": despues_de, "ots": [],
                     "porque": f"{prot['id']} exige {c['id']} {c['nombre']}, y ningún paso de la versión "
                               f"{p['version']} lo cumple."}]
        if h["tipo"] == "juntos":
            ids = h["control"].split("+")
            juntos = sorted((x for x in controles if x["id"] in ids), key=lambda c: c["orden"])
            marca = f"{prot['id']}:{juntos[0]['id']}"
            clave_original = next(k for k, s in pasos.filas if marca in s.cumple)
            original = pasos.paso(clave_original)
            quitar = {f"{prot['id']}:{c['id']}" for c in juntos[1:]}
            pasos.cambiar(clave_original, replace(original, cumple=tuple(c for c in original.cumple if c not in quitar)))
            cambios = []
            for k, c in enumerate(juntos[1:], 1):
                i = pasos.indice(clave_original) + k
                clave = pasos.insertar(i, _confirmacion(c["nombre"], c.get("exige", ""), f"{prot['id']}:{c['id']}", prot["id"]))
                cambios.append({"tipo": "separa", "clave": clave, "antes": None, "despues_de": original.titulo,
                                "separado_de": original.titulo, "ots": [],
                                "porque": f"{prot['id']} pide {c['id']} {c['nombre']} como un control propio: en un mismo "
                                          f"paso con {juntos[0]['id']} la evidencia no comprueba que se hizo, ni en su orden."})
            return cambios
        return []
    original = pasos.paso(p["paso"])
    clase = _dominante(p["senales"])
    if clase == "seguridad" and original.sensor:
        # El peligro lo arma el propio paso al cerrarse (encender con alguien cerca): reescribirlo no lo evita, falta
        # el paso que deja a la persona a salvo antes. Si la pauta ya lo pide antes, queda la reescritura de abajo.
        i = pasos.indice(p["paso"])
        pedido = {s.sensor.id: s.sensor.espera for _, s in pasos.filas[:i] if s.sensor}  # lo último que pide cada sensor
        faltan = [n for n in reglas.antes_de_cerrar(original.sensor) if pedido.get(n.sensor.id) != n.sensor.espera]
        ots = list(p.get("ots") or [])
        if faltan:
            return [{"tipo": "agrega", "clave": pasos.insertar(pasos.indice(p["paso"]), n), "antes": None,
                     "antes_de": original.titulo, "ots": ots,
                     "porque": f"«{original.titulo}» se hizo sin «{n.titulo}» antes{' en ' + _lista(ots) if ots else ''}: "
                               f"se abrió una alerta de seguridad, y la versión {p['version']} no tiene un paso que lo pida."}
                    for n in faltan]
    frase = f"No sigas al paso siguiente hasta que {_hecho(original)}: {FRASE[clase]}."
    instruccion = original.instruccion if frase in original.instruccion else f"{original.instruccion.rstrip()} {frase}"
    pasos.cambiar(p["paso"], replace(original, instruccion=instruccion))
    ots = list(p.get("ots") or [])
    porque = (f"En {_lista(ots)}, «{original.titulo}» tuvo señales de {clase}: la instrucción no decía cuándo el paso "
              "está hecho ni qué no se hace antes." if ots else f"«{original.titulo}» tuvo señales de {clase}.")
    return [{"tipo": "reescribe", "clave": p["paso"], "antes": {"titulo": original.titulo, "instruccion": original.instruccion},
             "porque": porque, "ots": ots}]


def _comprobacion(cx: sqlite3.Connection, origen: Pauta, nueva: Pauta) -> dict:
    protocolos = catalogo.controles_de(cx, origen.id)
    try:
        catalogo.pauta_desde_dict(_a_dict(nueva))
    except (ReglaDeNegocio, KeyError, ValueError) as e:
        return {"valida": False, "error": str(e), "hallazgos_nuevos": [], "conformidad_despues": None}
    antes = {h["clave"] for h in analisis.conformidad(origen, protocolos)["hallazgos"]}
    despues = analisis.conformidad(nueva, protocolos)
    nuevos = [h for h in despues["hallazgos"] if h["clave"] not in antes]
    return {"valida": not nuevos, "hallazgos_nuevos": nuevos, "conformidad_despues": despues}


def _armar(cx: sqlite3.Connection, origen: Pauta, propuestas: Sequence[dict], version: int) -> tuple[Pauta, list[dict]]:
    pasos = _Pasos(origen.en_orden)
    prefijo = _esquema_de_ids(origen.en_orden)
    crudos = []
    for p in propuestas:
        crudos += [{**c, "propuesta": p["id"]} for c in _aplicar(cx, pasos, p)]
    # ids y orden finales: «<prefijo><n>» si la pauta usa ese esquema; si no, los suyos y «n<k>» para los nuevos
    usados, k, ids = {c for c, _ in pasos.filas if not c.startswith("+")}, 0, {}
    for n, (clave, _) in enumerate(pasos.filas, 1):
        if prefijo:
            ids[clave] = f"{prefijo}{n}"
        elif clave.startswith("+"):
            k += 1
            while f"n{k}" in usados:
                k += 1
            ids[clave] = f"n{k}"
        else:
            ids[clave] = clave
    finales = [replace(s, id=ids[clave], orden=n, comparar_con=ids.get(s.comparar_con, s.comparar_con) if s.comparar_con else None)
               for n, (clave, s) in enumerate(pasos.filas, 1)]
    nueva = replace(origen, version=version, pasos=tuple(finales))
    por_id = {s.id: s for s in finales}
    cambios = []
    for c in crudos:
        paso = por_id[ids[c["clave"]]]
        cambios.append({"tipo": c["tipo"], "paso": paso.id, "antes": c["antes"],
                        "despues": {"titulo": paso.titulo, "instruccion": paso.instruccion,
                                    "tipo_evidencia": str(paso.tipo_evidencia), "cumple": list(paso.cumple)},
                        "porque": c["porque"], "ots": c["ots"], "propuesta": c["propuesta"],
                        "_despues_de": c.get("despues_de"), "_separado_de": c.get("separado_de"),
                        "_antes_de": c.get("antes_de")})
    return nueva, cambios


def _con_modelo(nueva: Pauta, cambios: list[dict], propuestas: Sequence[dict], cliente=None) -> tuple[Pauta, str]:
    """El modelo reescribe título, instrucción y porqué de los pasos que el borrador cambia; si se sale, queda el código."""
    if not cambios or (cliente is None and not cerebro.configurado()):
        return nueva, "codigo"
    ots_validas = {o for p in propuestas for o in (p.get("ots") or [])}
    contenido = {"pauta": nueva.nombre, "cambios": [
        {"indice": i, "tipo": c["tipo"], "antes": c["antes"], "despues": c["despues"], "porque": c["porque"], "ots": c["ots"]}
        for i, c in enumerate(cambios)], "ots_que_puedes_citar": sorted(ots_validas)}
    d = cerebro._pedir(SISTEMA, contenido, ESQUEMA, cliente)
    if not d or not isinstance(d.get("cambios"), list) or len(d["cambios"]) != len(cambios):
        return nueva, "codigo"
    for x in d["cambios"]:
        if set(x) - CAMPOS_DEL_MODELO or not CAMPOS_DEL_MODELO <= set(x) or not isinstance(x["indice"], int):
            return nueva, "codigo"  # trajo algo más que título, instrucción y porqué: no se usa nada
        if not 0 <= x["indice"] < len(cambios) or not x["titulo"].strip() or not x["instruccion"].strip():
            return nueva, "codigo"
        if set(_OT.findall(x["porque"])) - ots_validas:
            return nueva, "codigo"  # cita una OT que no respalda la propuesta
    pasos = {p.id: p for p in nueva.pasos}
    for x in d["cambios"]:
        c = cambios[x["indice"]]
        pasos[c["paso"]] = replace(pasos[c["paso"]], titulo=x["titulo"].strip(), instruccion=x["instruccion"].strip())
        c["despues"] = {**c["despues"], "titulo": x["titulo"].strip(), "instruccion": x["instruccion"].strip()}
        c["porque"] = x["porque"].strip()
    return replace(nueva, pasos=tuple(pasos[p.id] for p in nueva.pasos)), os.environ.get("CEREBRO_MODELO",
                                                                                          cerebro.MODELO_POR_DEFECTO)


def _limpio(cambios: list[dict]) -> list[dict]:
    return [{k: v for k, v in c.items() if not k.startswith("_")} for c in cambios]


def resumen(cambios: Sequence[dict]) -> list[str]:
    """Una línea por cambio, para el reporte."""
    salida = []
    for c in cambios:
        t = c["despues"]["titulo"]
        if c["tipo"] == "agrega" and c.get("_antes_de"):
            salida.append(f"Agrega «{t}» antes de «{c['_antes_de']}»")
        elif c["tipo"] == "agrega":
            salida.append(f"Agrega «{t}» después de «{c['_despues_de']}»" if c.get("_despues_de") else f"Agrega «{t}» al principio")
        elif c["tipo"] == "separa":
            salida.append(f"Separa «{t}» de «{c['_separado_de']}» en un paso propio")
        else:
            salida.append(f"Reescribe «{t}»: dice cuándo el paso está hecho y qué no se hace antes")
    return salida


def _borrador(cx: sqlite3.Connection, propuesta: dict, cliente=None, con_modelo: bool = True) -> tuple[dict, list[dict]]:
    origen = db.leer_pauta(cx, propuesta["pauta"], propuesta["version"])
    siguiente = max(v["version"] for v in catalogo.versiones(cx, origen.id)) + 1
    base = {"propuesta": propuesta["id"], "aplicable": propuesta["aplicable"], "por_que_no": propuesta["por_que_no"],
            "pauta": origen.id, "desde_version": origen.version, "version": siguiente}
    if not propuesta["aplicable"]:
        return {**base, "cambios": [], "redactado_por": "codigo", "comprobacion": None}, []
    nueva, cambios = _armar(cx, origen, [propuesta], siguiente)
    redactado_por = "codigo"
    if con_modelo:
        nueva, redactado_por = _con_modelo(nueva, cambios, [propuesta], cliente)
    return {**base, "cambios": _limpio(cambios), "redactado_por": redactado_por,
            "comprobacion": _comprobacion(cx, origen, nueva)}, cambios


def borrador(cx: sqlite3.Connection, propuesta: dict, cliente=None) -> dict:
    """El cambio que propone una propuesta, sobre la versión en que nació. No guarda nada."""
    return _borrador(cx, propuesta, cliente)[0]


def resumen_de(cx: sqlite3.Connection, propuesta: dict) -> list[str]:
    """El mismo cambio en una línea por paso, para el reporte. Solo el código: el reporte no lo redacta un modelo."""
    return resumen(_borrador(cx, propuesta, con_modelo=False)[1]) if propuesta["aplicable"] else []


# ─── El resumen para el supervisor: una versión siguiente por pauta ─────────


def _por_que_corto(c: dict, propuesta: dict) -> str:
    if c["tipo"] == "agrega" and propuesta["tipo"] == "desviacion":
        r = propuesta.get("recurrencia") or {}
        n, total = r.get("ots_con_senal", propuesta["ots_con_senal"]), r.get("ots", propuesta["ejecuciones"])
        return f"En {n} de {total} OT el paso siguiente se hizo en una condición de peligro: la pauta no pide esto antes."
    if c["tipo"] == "agrega":
        return "El protocolo lo exige y hoy ningún paso de la pauta lo hace."
    if c["tipo"] == "separa":
        return "Va junto con otro control en un mismo paso, y así no se comprueba que se hizo cada uno."
    r = propuesta.get("recurrencia") or {}
    n, total = r.get("ots_con_senal", propuesta["ots_con_senal"]), r.get("ots", propuesta["ejecuciones"])
    return f"Se desvió en {n} de {total} OT: la instrucción no decía cuándo el paso está hecho."


def _sin_cambio(p: dict) -> dict:
    que = f"«{p['titulo']}»" if p["tipo"] == "desviacion" else p["titulo"]
    return {"que": que, "por_que_no": p["por_que_no"], "propuesta": p["id"]}


def _lista_nombres(nombres: Sequence[str]) -> str:
    return " y ".join(f"«{n}»" for n in nombres)


def para_una_persona(p: dict) -> dict:
    """Por qué conviene la mejora y cómo se sabrá si funcionó, con palabras de quien conoce el trabajo, no la estadística."""
    v = p.get("validacion")
    if p["tipo"] == "conformidad":
        c = p["conformidad"] or {}
        nombres = c.get("nombres") or []
        porque = {
            "falta": f"El protocolo de seguridad pide {_lista_nombres(nombres)} y hoy la pauta no tiene ningún paso que lo haga.",
            "juntos": f"El protocolo pide {_lista_nombres(nombres)} por separado, y la pauta los tiene en un mismo paso: así no se "
                      "puede comprobar que se hizo cada uno.",
            "orden": f"La pauta pide {_lista_nombres(nombres[::-1])} en el orden contrario al del protocolo.",
        }.get(c.get("tipo"), "Un paso de la pauta no calza con el protocolo de seguridad.")
        como = ("Se cumple cuando la versión nueva de la pauta tenga ese paso. Antes de usarla, Factum revisa que no se pierda "
                "ningún otro control de seguridad.")
        if v:
            como = ("La versión nueva ya lo tiene." if v["resultado"] == "mejoro"
                    else "La versión nueva todavía no lo arregla.")
        return {"porque": porque, "como_se_mide": como}
    r = p.get("recurrencia") or {}
    n, total = r.get("ots_con_senal", p["ots_con_senal"]), r.get("ots", p["ejecuciones"])
    porque = f"«{p['titulo']}» no se hizo como dice la pauta en {n} de {total} trabajos."
    como = (f"Hoy falla en {n} de {total} trabajos. Con la versión nueva, Factum vuelve a contar: si falla claramente menos, "
            "el cambio sirvió. Si todavía hay pocos trabajos, espera a tener más antes de decirlo, para no confundir suerte "
            "con mejora.")
    if v:
        antes = f"Antes fallaba en {n} de {total} trabajos; con la versión nueva, en {v['ots_con_senal']} de {v['ejecuciones']}."
        como = {"mejoro": f"{antes} Funcionó.",
                "sin_evidencia": f"{antes} Va mejor, pero con tan pocos trabajos todavía puede ser suerte.",
                "se_repite": f"{antes} Sigue fallando: hay que buscar otra causa, no otro texto.",
                "sin_datos": "La versión nueva todavía no se ha usado: no hay con qué comparar."}[v["resultado"]]
    return {"porque": porque, "como_se_mide": como}


def resumen_por_pauta(cx: sqlite3.Connection, propuestas: Sequence[dict]) -> list[dict]:
    """Lo que Factum propone, en pocas líneas: por cada pauta con propuestas abiertas que ya avisó, la versión siguiente
    que armaría con todas juntas, qué cambia y por qué, y lo que no cambia y por qué no. Solo el código; no guarda nada."""
    grupos: dict[tuple[str, int], list[dict]] = {}
    for p in propuestas:
        if p["estado"] == "abierta" and p["detectada"]:
            grupos.setdefault((p["pauta"], p["version"]), []).append(p)
    salida = []
    for (pauta_id, version), ps in grupos.items():
        origen = db.leer_pauta(cx, pauta_id, version)
        siguiente = max(v["version"] for v in catalogo.versiones(cx, pauta_id)) + 1
        aplicables = sorted((p for p in ps if p["aplicable"]), key=lambda p: (p["tipo"] != "conformidad", p["id"]))
        por_id = {p["id"]: p for p in aplicables}
        crudos = _armar(cx, origen, aplicables, siguiente)[1] if aplicables else []
        salida.append({
            "pauta": pauta_id, "nombre": origen.nombre, "desde_version": version, "version": siguiente,
            "cambios": [{"que": linea, "porque": _por_que_corto(c, por_id[c["propuesta"]]), "propuesta": c["propuesta"]}
                        for c, linea in zip(crudos, resumen(crudos))],
            "sin_cambio": [_sin_cambio(p) for p in ps if not p["aplicable"]],
            "propuestas": [p["id"] for p in ps],
        })
    return salida


# ─── La versión siguiente que arma Factum ───────────────────────────────────


def _aceptadas(cx: sqlite3.Connection, pauta_id: str, version: int) -> list[dict]:
    """Las propuestas aceptadas y aplicables de esa versión, de todas las empresas que tienen la pauta."""
    from app import acceso, metricas  # acá adentro: acceso depende de este módulo a través de mejora

    salida = []
    for c in acceso.listar_clientes(cx):
        es = metricas.ejecuciones(cx, acceso.ots_de(cx, {"cliente": {"id": c["id"]}, "rol": "supervisor"}))
        salida += [p for p in mejora.propuestas(cx, es, c["id"])
                   if p["pauta"] == pauta_id and p["version"] == version and p["estado"] == "aceptada" and p["aplicable"]]
    vistas, unicas = set(), []
    for p in salida:  # una de conformidad sale igual en cada empresa que tiene la pauta
        if p["id"] not in vistas:
            vistas.add(p["id"])
            unicas.append(p)
    # primero lo que agrega o separa controles, después lo que reescribe: así un paso agregado ya está al reescribir
    return sorted(unicas, key=lambda p: (p["tipo"] != "conformidad", p["id"]))


def version_siguiente(cx: sqlite3.Connection, pauta_id: str, actor: str, cliente=None) -> dict:
    """Guarda, sin aprobar, la versión siguiente con los cambios de las propuestas aceptadas de la última aprobada."""
    ultima = catalogo.ultima_aprobada(cx, pauta_id)
    if ultima is None:
        raise db.NoExiste(f"pauta {pauta_id} aprobada")
    mayor = max(v["version"] for v in catalogo.versiones(cx, pauta_id))
    if mayor > ultima:
        raise ReglaDeNegocio(f"la pauta {pauta_id} ya tiene la v{mayor} sin aprobar: apruébala o descártala antes de "
                             "armar otra")
    propuestas = _aceptadas(cx, pauta_id, ultima)
    if not propuestas:
        raise ReglaDeNegocio(f"la pauta {pauta_id} v{ultima} no tiene propuestas aceptadas con un cambio que aplicar")
    origen = db.leer_pauta(cx, pauta_id, ultima)
    nueva, cambios = _armar(cx, origen, propuestas, ultima + 1)
    nueva, _ = _con_modelo(nueva, cambios, propuestas, cliente)
    comprobacion = _comprobacion(cx, origen, nueva)
    if not comprobacion["valida"]:
        raise ReglaDeNegocio(f"la versión armada no pasa la comprobación: {comprobacion}")
    protocolos = [p["id"] for p in catalogo.protocolos_de(cx, pauta_id)]
    dueno = catalogo.protocolo_dueno(cx, pauta_id)
    catalogo.crear_pauta_de(cx, protocolos, _a_dict(nueva), actor)
    if dueno:
        catalogo.fijar_duena(cx, pauta_id, dueno, actor)
    return {"pauta": pauta_id, "version": ultima + 1, "desde_version": ultima,
            "propuestas": [p["id"] for p in propuestas], "cambios": _limpio(cambios), "comprobacion": comprobacion}
