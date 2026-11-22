"""El CRUD de lo que las reglas de negocio piden guardar, con esas reglas adentro.

No todo admite las cuatro letras, y eso es deliberado:

| Recurso   | Crear | Leer | Cambiar                    | Borrar |
|-----------|-------|------|----------------------------|--------|
| Protocolo | sí, una persona | sí | nombre, industria, origen y texto | solo si no tiene pautas atribuidas |
| Atribución| sí    | sí   | no                         | sí, salvo la última de una pauta que ya tiene OT |
| Pauta     | sí    | sí   | una versión nueva, nunca encima de otra (ADR-0003) | no: hay OT que la ejecutaron |
| Aprobación| sí    | sí   | no                         | no     |
| OT        | sí, solo desde una pauta aprobada (ADR-0003, 0006) | sí | su estado y su operador se calculan de los eventos | no |
| Evento    | solo por las acciones del flujo | sí | no: la bitácora solo agrega | no |
| Sesión    | sí    | sí   | se reemplaza al abrir otra en el mismo edge | sí, al terminar |
| Sensor    | sí (lectura) | sí | cada lectura pisa la anterior | no |
"""

from __future__ import annotations

import json
import sqlite3
from collections.abc import Collection, Iterable, Sequence

from app import db
from app.contratos import Estado, Evento, Pauta, Paso, TipoEvento
from app.reglas import estados_desde_eventos, paso_actual

OPERADORES = ("operario:1", "operario:2")  # los del demo: no hay tabla de personas

_ESQUEMA = """
CREATE TABLE IF NOT EXISTS aprobaciones (
    pauta_id TEXT NOT NULL, version INTEGER NOT NULL, aprobada_por TEXT NOT NULL, ts TEXT NOT NULL,
    PRIMARY KEY (pauta_id, version)
);
CREATE TABLE IF NOT EXISTS protocolos (
    id TEXT PRIMARY KEY, nombre TEXT NOT NULL, industria TEXT NOT NULL, origen TEXT NOT NULL,
    texto TEXT NOT NULL, creado_por TEXT NOT NULL, ts TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS pauta_protocolo (
    pauta_id TEXT NOT NULL, protocolo_id TEXT NOT NULL, atribuida_por TEXT NOT NULL, ts TEXT NOT NULL,
    PRIMARY KEY (pauta_id, protocolo_id)
);
-- El protocolo dueño de la pauta: uno solo, el de la tarea que ejecuta. Sus versiones, sus OT, sus propuestas y sus
-- métricas se iteran en ese protocolo (ADR-0018). Los demás protocolos de pauta_protocolo solo «aplican» (ADR-0016).
CREATE TABLE IF NOT EXISTS pauta_duena (
    pauta_id TEXT PRIMARY KEY, protocolo_id TEXT NOT NULL, por TEXT NOT NULL, ts TEXT NOT NULL
);
"""


class ReglaDeNegocio(Exception):
    """Lo pedido choca con una regla del negocio. La API lo devuelve como 409."""


def preparar(cx: sqlite3.Connection) -> None:
    cx.executescript(_ESQUEMA)
    # Los controles críticos de cada protocolo, como datos (ADR-0016). Una base anterior no tiene las columnas.
    columnas = {f["name"] for f in cx.execute("PRAGMA table_info(protocolos)").fetchall()}
    for columna, tipo in (("controles", "TEXT NOT NULL DEFAULT '[]'"), ("controles_por", "TEXT"), ("controles_en", "TEXT"),
                          ("cliente_id", "TEXT")):  # sin cliente: de la biblioteca de Factum (ADR-0018)
        if columna not in columnas:
            cx.execute(f"ALTER TABLE protocolos ADD COLUMN {columna} {tipo}")  # columna y tipo son constantes de acá
    cx.commit()


# ─── Pautas ─────────────────────────────────────────────────────────────────


def pauta_desde_dict(d: dict) -> Pauta:
    pasos = tuple(Paso.desde_dict(x) for x in d["pasos"])
    if not pasos:
        raise ReglaDeNegocio("una pauta sin pasos no se puede ejecutar")
    ordenes = [p.orden for p in pasos]
    if len(set(ordenes)) != len(ordenes):
        raise ReglaDeNegocio("dos pasos con el mismo orden: el orden lo impone la app y debe ser único")
    ids = [p.id for p in pasos]
    if len(set(ids)) != len(ids):
        raise ReglaDeNegocio("dos pasos con el mismo id")
    return Pauta(id=d["id"], nombre=d["nombre"], version=d["version"], equipo=d["equipo"], pasos=pasos)


def versiones(cx: sqlite3.Connection, pauta_id: str) -> list[dict]:
    filas = cx.execute(
        "SELECT p.version, a.aprobada_por, a.ts FROM pautas p LEFT JOIN aprobaciones a"
        " ON a.pauta_id = p.id AND a.version = p.version WHERE p.id = ? ORDER BY p.version",
        (pauta_id,),
    ).fetchall()
    return [{"version": f["version"], "aprobada_por": f["aprobada_por"], "aprobada_en": f["ts"]} for f in filas]


def crear_pauta(cx: sqlite3.Connection, d: dict) -> dict:
    """Crear y «cambiar» son lo mismo: una versión nueva, la siguiente a la última."""
    pauta = pauta_desde_dict(d)
    existentes = [v["version"] for v in versiones(cx, pauta.id)]
    siguiente = (max(existentes) + 1) if existentes else 1
    if pauta.version != siguiente:
        raise ReglaDeNegocio(
            f"la pauta {pauta.id} va en la versión {siguiente - 1}; la nueva tiene que ser la {siguiente}"
        )
    db.guardar_pauta(cx, pauta)
    return resumen_pauta(cx, pauta)


def hallazgos_de_conformidad(cx: sqlite3.Connection, pauta: Pauta) -> list[dict]:
    from app import analisis  # acá adentro: analisis no depende del catálogo

    return analisis.conformidad(pauta, controles_de(cx, pauta.id))["hallazgos"]


def aprobar_pauta(cx: sqlite3.Connection, pauta_id: str, version: int, actor: str) -> dict:
    """Una persona aprueba antes de que la pauta se use (ADR-0003).

    Una versión nueva no se aprueba si le falta un control crítico que la versión aprobada anterior cumplía: la mejora
    continua puede reescribir un paso, nunca sacar o juntar un control (ADR-0016). Lo que ya le faltaba a la anterior
    no bloquea: es un hallazgo abierto, que se revisa en las mejoras."""
    pauta = db.leer_pauta(cx, pauta_id, version)
    if not actor or actor == "sistema":
        raise ReglaDeNegocio("una pauta la aprueba una persona, no el sistema")
    anterior = ultima_aprobada(cx, pauta_id)
    if anterior is not None and anterior < version:
        previa = db.leer_pauta(cx, pauta_id, anterior)
        anotados = {c.split(":")[0] for p in previa.pasos for c in p.cumple}  # una versión sin `cumple` no se compara
        antes = {h["clave"] for h in hallazgos_de_conformidad(cx, previa)}
        nuevos = [h for h in hallazgos_de_conformidad(cx, pauta) if h["clave"] not in antes and h["protocolo"] in anotados]
        if nuevos:
            raise ReglaDeNegocio(f"la pauta {pauta_id} v{version} pierde controles críticos que la v{anterior} cumplía: "
                                 + "; ".join(h["detalle"] for h in nuevos))
    try:
        cx.execute(
            "INSERT INTO aprobaciones (pauta_id, version, aprobada_por, ts) VALUES (?, ?, ?, ?)",
            (pauta_id, version, actor, db.ahora()),
        )
        cx.commit()
    except sqlite3.IntegrityError as e:
        raise ReglaDeNegocio(f"la pauta {pauta_id} v{version} ya está aprobada") from e
    return resumen_pauta(cx, pauta)


def aprobada(cx: sqlite3.Connection, pauta_id: str, version: int) -> bool:
    return cx.execute(
        "SELECT 1 FROM aprobaciones WHERE pauta_id = ? AND version = ?", (pauta_id, version)
    ).fetchone() is not None


def resumen_pauta(cx: sqlite3.Connection, pauta: Pauta) -> dict:
    return {
        "id": pauta.id,
        "nombre": pauta.nombre,
        "version": pauta.version,
        "equipo": pauta.equipo,
        "pasos": len(pauta.pasos),
        "aprobada": aprobada(cx, pauta.id, pauta.version),
    }


def listar_pautas(cx: sqlite3.Connection) -> list[dict]:
    """Una fila por pauta, en su última versión."""
    ids = [f["id"] for f in cx.execute("SELECT DISTINCT id FROM pautas ORDER BY id").fetchall()]
    return [resumen_pauta(cx, db.leer_pauta(cx, i)) for i in ids]


def leer_pauta(cx: sqlite3.Connection, pauta_id: str, version: int | None = None) -> dict:
    fila = cx.execute(
        "SELECT json FROM pautas WHERE id = ? AND version = ?"
        if version is not None
        else "SELECT json FROM pautas WHERE id = ? ORDER BY version DESC LIMIT 1",
        (pauta_id, version) if version is not None else (pauta_id,),
    ).fetchone()
    if fila is None:
        raise db.NoExiste(f"pauta {pauta_id}" + (f" v{version}" if version is not None else ""))
    d = json.loads(fila["json"])
    d["aprobada"] = aprobada(cx, d["id"], d["version"])
    return d


# ─── OT ─────────────────────────────────────────────────────────────────────


def abrir_ot(
    cx: sqlite3.Connection, ot_id: str, pauta_id: str, actor: str, version: int | None = None
) -> dict:
    """La OT nace de una pauta aprobada (ADR-0006) y guarda qué versión ejecuta."""
    pauta = db.leer_pauta(cx, pauta_id, version)
    if not aprobada(cx, pauta.id, pauta.version):
        raise ReglaDeNegocio(f"la pauta {pauta.id} v{pauta.version} no está aprobada; nadie la puede ejecutar")
    if cx.execute("SELECT 1 FROM ots WHERE id = ?", (ot_id,)).fetchone():
        raise ReglaDeNegocio(f"la OT {ot_id} ya existe")
    db.abrir_ot(cx, ot_id, pauta, actor)
    return {"ot": ot_id, "pauta": pauta.id, "version": pauta.version, "nombre": pauta.nombre}


def operador_de(eventos: Sequence[Evento]) -> str | None:
    """Quién tiene la OT. Lo dice el último evento que la mueve de manos: la asignación la
    deja en su operador, recibir el turno en quien firma, y entregarlo en nadie."""
    for ev in reversed(eventos):
        if ev.tipo is TipoEvento.OT_ASIGNADA:
            return (ev.evidencia or {}).get("operador")
        if ev.tipo is TipoEvento.RELEVO_RECIBIDO:
            return ev.actor
        if ev.tipo is TipoEvento.RELEVO_ENTREGADO:
            return None
    return None


def _resumen(cx: sqlite3.Connection, f: sqlite3.Row, en_sesion: Collection[str]) -> dict:
    pauta = db.leer_pauta(cx, f["pauta_id"], f["pauta_version"])
    evs = db.eventos(cx, f["id"])
    estados = estados_desde_eventos(evs)
    actual = paso_actual(pauta, estados)
    operador = operador_de(evs)
    entrega = next((e for e in reversed(evs) if e.tipo in (TipoEvento.RELEVO_ENTREGADO, TipoEvento.RELEVO_RECIBIDO)), None)
    entregada = operador is None and entrega is not None and entrega.tipo is TipoEvento.RELEVO_ENTREGADO
    if actual is None:
        estado_general = "completa"
    elif entregada:
        estado_general = "entregada"
    elif operador is None:
        estado_general = "sin_asignar"
    elif f["id"] in en_sesion or any(e.tipo is TipoEvento.VEREDICTO for e in evs):
        estado_general = "en_ejecucion"
    else:
        estado_general = "asignada"
    return {
        "ot": f["id"],
        "pauta": f["pauta_id"],
        "version": f["pauta_version"],
        "equipo": f["equipo"],
        "abierta_en": f["abierta_en"],
        "paso_actual": actual.id if actual else None,
        "completa": actual is None,
        "operador": operador,
        "estado_general": estado_general,
        "entregada_por": entrega.actor if entregada else None,
        "cerrados": sum(1 for p in pauta.pasos if estados.get(p.id) is Estado.VERIFICADO),
        "total": len(pauta.pasos),
    }


def listar_ots(cx: sqlite3.Connection, en_sesion: Collection[str] = ()) -> list[dict]:
    """`en_sesion`: las OT que algún edge está ejecutando ahora (las sesiones viven en servicios)."""
    return [_resumen(cx, f, en_sesion) for f in cx.execute("SELECT * FROM ots ORDER BY abierta_en, id").fetchall()]


def resumen_ot(cx: sqlite3.Connection, ot_id: str, en_sesion: Collection[str] = ()) -> dict:
    return _resumen(cx, db.leer_ot(cx, ot_id), en_sesion)


def _es_operador(cx: sqlite3.Connection, operador: str) -> bool:
    """Los dos del demo, o una persona con rol operador de algún cliente (app/acceso.py)."""
    if operador in OPERADORES:
        return True
    if not cx.execute("SELECT 1 FROM sqlite_master WHERE type = 'table' AND name = 'personas'").fetchone():
        return False
    return cx.execute("SELECT 1 FROM personas WHERE id = ? AND rol = 'operador'", (operador,)).fetchone() is not None


def _rol_de(cx: sqlite3.Connection, persona: str) -> str | None:
    if not cx.execute("SELECT 1 FROM sqlite_master WHERE type = 'table' AND name = 'personas'").fetchone():
        return None
    f = cx.execute("SELECT rol FROM personas WHERE id = ?", (persona,)).fetchone()
    return f["rol"] if f else None


def asignacion(cx: sqlite3.Connection, ot_id: str, operador: str, actor: str) -> Evento:
    """El evento que asigna la OT, si las reglas lo dejan: la asigna un supervisor, solo a un operador
    conocido y solo una OT sin operador (nunca asignada, o entregada en un relevo que nadie recibió).

    Un actor que es una persona de la base tiene que tener rol supervisor; uno que no lo es (los del
    demo y las pruebas) tiene que decirlo en su id: `supervisor` o `supervisor:<algo>`."""
    rol = _rol_de(cx, actor)
    if rol != "supervisor" and (rol is not None or not (actor == "supervisor" or actor.startswith("supervisor:"))):
        raise ReglaDeNegocio(f"solo un supervisor asigna una OT; {actor} es {rol or 'alguien sin rol de supervisor'}")
    actual = resumen_ot(cx, ot_id)
    if not _es_operador(cx, operador):
        raise ReglaDeNegocio(f"el operador {operador} no existe; hay {', '.join(OPERADORES)} y los operadores de cada cliente")
    if actual["completa"]:
        raise ReglaDeNegocio(f"la OT {ot_id} ya está completa")
    if actual["operador"]:
        raise ReglaDeNegocio(f"la OT {ot_id} ya tiene operador: {actual['operador']}")
    return Evento(ot_id=ot_id, tipo=TipoEvento.OT_ASIGNADA, ts=db.ahora(), actor=actor,
                  evidencia={"operador": operador}, detalle=f"OT asignada a {operador}")


# ─── Protocolos: el documento del cliente del que salen las pautas ──────────
# Un protocolo da una o más pautas, y una pauta puede salir de más de un protocolo: el
# procedimiento del equipo y el estándar de aislamiento del sitio, por ejemplo. La
# atribución es a la pauta, no a una versión: todas sus versiones salen del mismo documento.

CAMPOS_PROTOCOLO = ("nombre", "industria", "origen", "texto")


def _fila_protocolo(cx: sqlite3.Connection, protocolo_id: str) -> sqlite3.Row:
    f = cx.execute("SELECT * FROM protocolos WHERE id = ?", (protocolo_id,)).fetchone()
    if f is None:
        raise db.NoExiste(f"protocolo {protocolo_id}")
    return f


def _exige_pauta(cx: sqlite3.Connection, pauta_id: str) -> None:
    if cx.execute("SELECT 1 FROM pautas WHERE id = ?", (pauta_id,)).fetchone() is None:
        raise db.NoExiste(f"pauta {pauta_id}")


def _exige_persona(actor: str, que: str) -> None:
    if not actor or actor == "sistema":
        raise ReglaDeNegocio(f"{que} lo hace una persona, no el sistema")


def protocolos_de(cx: sqlite3.Connection, pauta_id: str) -> list[dict]:
    """Los protocolos de los que sale una pauta."""
    filas = cx.execute(
        "SELECT p.id, p.nombre FROM pauta_protocolo a JOIN protocolos p ON p.id = a.protocolo_id"
        " WHERE a.pauta_id = ? ORDER BY p.id", (pauta_id,)).fetchall()
    return [{"id": f["id"], "nombre": f["nombre"]} for f in filas]


def pautas_de(cx: sqlite3.Connection, protocolo_id: str) -> list[dict]:
    """Las pautas que salen de un protocolo, cada una en su última versión."""
    ids = [f["pauta_id"] for f in cx.execute(
        "SELECT pauta_id FROM pauta_protocolo WHERE protocolo_id = ? ORDER BY pauta_id", (protocolo_id,)).fetchall()]
    return [resumen_pauta(cx, db.leer_pauta(cx, i)) for i in ids]


def _protocolo_dict(cx: sqlite3.Connection, f: sqlite3.Row, con_texto: bool) -> dict:
    d = {"id": f["id"], "nombre": f["nombre"], "industria": f["industria"], "origen": f["origen"],
         "creado_por": f["creado_por"], "creado_en": f["ts"], "pautas": pautas_de(cx, f["id"]),
         "controles": json.loads(f["controles"] or "[]"), "cliente": f["cliente_id"],
         "propias": [r["pauta_id"] for r in cx.execute(
             "SELECT pauta_id FROM pauta_duena WHERE protocolo_id = ? ORDER BY pauta_id", (f["id"],)).fetchall()],
         "controles_aprobados": {"por": f["controles_por"], "en": f["controles_en"]} if f["controles_por"] else None}
    if con_texto:
        d["texto"] = f["texto"]
    return d


def crear_protocolo(cx: sqlite3.Connection, d: dict, actor: str) -> dict:
    """Carga el documento de un cliente. `pautas` lo deja atribuido a pautas que ya existen."""
    protocolo_id, nombre = str(d.get("id") or "").strip(), str(d.get("nombre") or "").strip()
    if not protocolo_id or not nombre:
        raise ReglaDeNegocio("un protocolo necesita id y nombre")
    _exige_persona(actor, "cargar un protocolo")
    if cx.execute("SELECT 1 FROM protocolos WHERE id = ?", (protocolo_id,)).fetchone():
        raise ReglaDeNegocio(f"el protocolo {protocolo_id} ya existe")
    pautas = list(d.get("pautas") or [])
    for pauta_id in pautas:
        _exige_pauta(cx, pauta_id)
    cx.execute(
        "INSERT INTO protocolos (id, nombre, industria, origen, texto, creado_por, ts) VALUES (?, ?, ?, ?, ?, ?, ?)",
        (protocolo_id, nombre, d.get("industria") or "", d.get("origen") or "", d.get("texto") or "", actor, db.ahora()))
    cx.commit()
    for pauta_id in pautas:
        atribuir(cx, pauta_id, protocolo_id, actor)
    if d.get("controles"):
        fijar_controles(cx, protocolo_id, d["controles"], actor)
    return leer_protocolo(cx, protocolo_id)


def _controles_validos(controles: Sequence[dict]) -> list[dict]:
    salida, ids = [], set()
    for c in controles:
        cid, nombre = str(c.get("id") or "").strip(), str(c.get("nombre") or "").strip()
        if not cid or not nombre or ":" in cid:
            raise ReglaDeNegocio("cada control necesita id (sin «:») y nombre")
        if cid in ids:
            raise ReglaDeNegocio(f"el control {cid} está dos veces")
        if not isinstance(c.get("orden"), int):
            raise ReglaDeNegocio(f"el control {cid} necesita su orden, un entero")
        ids.add(cid)
        salida.append({"id": cid, "nombre": nombre, "orden": c["orden"], "exige": str(c.get("exige") or ""),
                       "evidencia": str(c.get("evidencia") or "")})
    return sorted(salida, key=lambda c: c["orden"])


def fijar_controles(cx: sqlite3.Connection, protocolo_id: str, controles: Sequence[dict], actor: str) -> dict:
    """Los controles críticos del protocolo, con su orden. Los propone la skill que lee el protocolo y los aprueba una
    persona del equipo (ADR-0016): queda quién y cuándo. Cambiarlos cambia lo que el validador le exige a cada pauta.

    shortcut: los protocolos todavía no tienen versiones; cuando las tengan, los controles van por versión."""
    _fila_protocolo(cx, protocolo_id)
    _exige_persona(actor, "aprobar los controles de un protocolo")
    validos = _controles_validos(controles)
    cx.execute("UPDATE protocolos SET controles = ?, controles_por = ?, controles_en = ? WHERE id = ?",
               (json.dumps(validos, ensure_ascii=False), actor, db.ahora(), protocolo_id))
    cx.commit()
    return leer_protocolo(cx, protocolo_id)


def fijar_duena(cx: sqlite3.Connection, pauta_id: str, protocolo_id: str, actor: str) -> None:
    """El protocolo dueño de la pauta. Tiene que aplicarle: se atribuye si no lo estaba."""
    _exige_persona(actor, "darle un protocolo dueño a una pauta")
    atribuir(cx, pauta_id, protocolo_id, actor)
    cx.execute("INSERT OR REPLACE INTO pauta_duena (pauta_id, protocolo_id, por, ts) VALUES (?, ?, ?, ?)",
               (pauta_id, protocolo_id, actor, db.ahora()))
    cx.commit()


def protocolo_dueno(cx: sqlite3.Connection, pauta_id: str) -> str | None:
    f = cx.execute("SELECT protocolo_id FROM pauta_duena WHERE pauta_id = ?", (pauta_id,)).fetchone()
    return f["protocolo_id"] if f else None


def _copiar_protocolo(cx: sqlite3.Connection, base: dict, nuevo_id: str, cliente_id: str, actor: str) -> None:
    cx.execute("INSERT INTO protocolos (id, nombre, industria, origen, texto, creado_por, ts, cliente_id) "
               "VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
               (nuevo_id, base["nombre"], base["industria"], f"adaptado de {base['id']}", base["texto"], actor, db.ahora(),
                cliente_id))
    cx.commit()
    if base["controles"]:
        fijar_controles(cx, nuevo_id, base["controles"], actor)


def instanciar(cx: sqlite3.Connection, base_id: str, cliente_id: str, actor: str, sufijo: str | None = None) -> dict:
    """El protocolo de una empresa, copiado de la biblioteca de Factum, con una copia de cada pauta que el de la
    biblioteca tiene como propia (ADR-0018). Desde acá cada copia itera sola: sus versiones, OT, propuestas y métricas no
    tocan las de otro protocolo, de esta empresa o de otra.

    `sufijo` distingue dos protocolos del mismo tipo en una empresa (una planta, un área). Los protocolos que además le
    aplican a la pauta, como el de aislamiento, se copian una vez por empresa y se comparten dentro de ella."""
    from app import acceso  # acá adentro: acceso depende del catálogo

    _exige_persona(actor, "cargar el protocolo de una empresa")
    base = leer_protocolo(cx, base_id)
    if base["cliente"]:
        raise ReglaDeNegocio(f"{base_id} es de la empresa {base['cliente']}: se copia desde la biblioteca, no desde otra empresa")
    if not cx.execute("SELECT 1 FROM clientes WHERE id = ?", (cliente_id,)).fetchone():
        raise db.NoExiste(f"cliente {cliente_id}")
    marca = f"{cliente_id}--{sufijo}" if sufijo else cliente_id
    if "--" in cliente_id or (sufijo and ("--" in sufijo or ":" in sufijo)):
        raise ReglaDeNegocio("el cliente y el sufijo no pueden llevar «--» ni «:»")
    nuevo_id = f"{base_id}--{marca}"
    if cx.execute("SELECT 1 FROM protocolos WHERE id = ?", (nuevo_id,)).fetchone():
        raise ReglaDeNegocio(f"el protocolo {nuevo_id} ya existe")
    _copiar_protocolo(cx, base, nuevo_id, cliente_id, actor)
    copias = {base_id: nuevo_id}
    pautas = []
    for pauta_id in base["propias"]:
        version = ultima_aprobada(cx, pauta_id)
        if version is None:
            continue
        original = db.leer_pauta(cx, pauta_id, version)
        for otro in [p["id"] for p in protocolos_de(cx, pauta_id)]:
            if otro not in copias:
                copia = f"{otro}--{cliente_id}"
                if not cx.execute("SELECT 1 FROM protocolos WHERE id = ?", (copia,)).fetchone():
                    _copiar_protocolo(cx, leer_protocolo(cx, otro), copia, cliente_id, actor)
                copias[otro] = copia
        cumple = lambda cs: tuple(f"{copias.get(c.split(':')[0], c.split(':')[0])}:{c.split(':')[1]}" for c in cs)  # noqa: E731
        from dataclasses import replace

        pauta = replace(original, id=f"{pauta_id}--{marca}", version=1,
                        pasos=tuple(replace(p, cumple=cumple(p.cumple)) for p in original.pasos))
        db.guardar_pauta(cx, pauta)
        for otro in [p["id"] for p in protocolos_de(cx, pauta_id)]:
            atribuir(cx, pauta.id, copias[otro], actor)
        fijar_duena(cx, pauta.id, nuevo_id, actor)
        aprobar_pauta(cx, pauta.id, 1, actor)
        acceso.habilitar(cx, cliente_id, pauta.id)
        pautas.append({"id": pauta.id, "de": f"{pauta_id} v{version}"})
    return {"protocolo": leer_protocolo(cx, nuevo_id), "pautas": pautas,
            "tambien_aplican": sorted(v for k, v in copias.items() if k != base_id)}


def controles_de(cx: sqlite3.Connection, pauta_id: str) -> list[dict]:
    """Los protocolos que aplican a la pauta, cada uno con sus controles críticos aprobados."""
    filas = cx.execute(
        "SELECT p.id, p.nombre, p.controles FROM pauta_protocolo a JOIN protocolos p ON p.id = a.protocolo_id"
        " WHERE a.pauta_id = ? ORDER BY p.id", (pauta_id,)).fetchall()
    return [{"id": f["id"], "nombre": f["nombre"], "controles": json.loads(f["controles"] or "[]")} for f in filas]


def leer_protocolo(cx: sqlite3.Connection, protocolo_id: str) -> dict:
    return _protocolo_dict(cx, _fila_protocolo(cx, protocolo_id), con_texto=True)


def listar_protocolos(cx: sqlite3.Connection) -> list[dict]:
    """Sin el texto, para que la lista pese poco."""
    return [_protocolo_dict(cx, f, con_texto=False) for f in cx.execute("SELECT * FROM protocolos ORDER BY id").fetchall()]


def cambiar_protocolo(cx: sqlite3.Connection, protocolo_id: str, cambios: dict) -> dict:
    """Corrige sus datos. El id no cambia: las pautas apuntan a él."""
    _fila_protocolo(cx, protocolo_id)
    ajenos = sorted(set(cambios) - set(CAMPOS_PROTOCOLO))
    if ajenos:
        raise ReglaDeNegocio(f"de un protocolo solo se cambia {', '.join(CAMPOS_PROTOCOLO)}; no {', '.join(ajenos)}")
    if "nombre" in cambios and not str(cambios["nombre"] or "").strip():
        raise ReglaDeNegocio("un protocolo necesita nombre")
    for campo, valor in cambios.items():
        cx.execute(f"UPDATE protocolos SET {campo} = ? WHERE id = ?", (valor or "", protocolo_id))  # campo viene de CAMPOS_PROTOCOLO
    cx.commit()
    return leer_protocolo(cx, protocolo_id)


def borrar_protocolo(cx: sqlite3.Connection, protocolo_id: str) -> None:
    _fila_protocolo(cx, protocolo_id)
    n = len(pautas_de(cx, protocolo_id))
    if n:
        raise ReglaDeNegocio(f"el protocolo {protocolo_id} tiene {n} pauta(s) atribuida(s); quítalas antes de borrarlo")
    cx.execute("DELETE FROM protocolos WHERE id = ?", (protocolo_id,))
    cx.commit()


def atribuir(cx: sqlite3.Connection, pauta_id: str, protocolo_id: str, actor: str) -> dict:
    """Deja dicho que la pauta sale de ese protocolo. Repetirlo no cambia nada."""
    _exige_pauta(cx, pauta_id)
    _fila_protocolo(cx, protocolo_id)
    _exige_persona(actor, "atribuir una pauta a un protocolo")
    cx.execute("INSERT OR IGNORE INTO pauta_protocolo (pauta_id, protocolo_id, atribuida_por, ts) VALUES (?, ?, ?, ?)",
               (pauta_id, protocolo_id, actor, db.ahora()))
    cx.commit()
    return {"pauta": pauta_id, "protocolos": protocolos_de(cx, pauta_id)}


def quitar_atribucion(cx: sqlite3.Connection, pauta_id: str, protocolo_id: str) -> None:
    """Una pauta que ya tiene OT no puede quedar sin protocolo: esas OT dejarían de tener origen."""
    actuales = [p["id"] for p in protocolos_de(cx, pauta_id)]
    if protocolo_id not in actuales:
        raise db.NoExiste(f"atribución de la pauta {pauta_id} al protocolo {protocolo_id}")
    if len(actuales) == 1 and cx.execute("SELECT 1 FROM ots WHERE pauta_id = ?", (pauta_id,)).fetchone():
        raise ReglaDeNegocio(f"la pauta {pauta_id} ya tiene OT y este es su único protocolo: no puede quedar sin ninguno")
    cx.execute("DELETE FROM pauta_protocolo WHERE pauta_id = ? AND protocolo_id = ?", (pauta_id, protocolo_id))
    cx.commit()


def crear_pauta_de(cx: sqlite3.Connection, protocolos: Iterable[str], d: dict, actor: str) -> dict:
    """Crea la versión siguiente de una pauta y la deja atribuida a sus protocolos. Nace sin aprobar."""
    protocolos = list(dict.fromkeys(protocolos))
    if not protocolos:
        raise ReglaDeNegocio("una pauta sale de al menos un protocolo")
    for protocolo_id in protocolos:
        _fila_protocolo(cx, protocolo_id)
    _exige_persona(actor, "crear una pauta")
    r = crear_pauta(cx, d)
    for protocolo_id in protocolos:
        atribuir(cx, r["id"], protocolo_id, actor)
    return {**r, "protocolos": protocolos_de(cx, r["id"])}


# ─── Lo que ve el cliente: pautas listas y OT ───────────────────────────────


def ultima_aprobada(cx: sqlite3.Connection, pauta_id: str) -> int | None:
    f = cx.execute("SELECT MAX(version) AS v FROM aprobaciones WHERE pauta_id = ?", (pauta_id,)).fetchone()
    return f["v"] if f else None


def pautas_disponibles(cx: sqlite3.Connection) -> list[dict]:
    """Lo que un cliente puede pedir: pautas con una versión aprobada y al menos un protocolo.

    De cada una, su última versión aprobada: una versión nueva que nadie aprobó todavía no la esconde.
    """
    salida = []
    for f in cx.execute("SELECT DISTINCT id FROM pautas ORDER BY id").fetchall():
        version, protocolos = ultima_aprobada(cx, f["id"]), protocolos_de(cx, f["id"])
        if version is None or not protocolos:
            continue
        pauta = db.leer_pauta(cx, f["id"], version)
        salida.append({"id": pauta.id, "nombre": pauta.nombre, "version": pauta.version, "equipo": pauta.equipo,
                       "pasos": len(pauta.pasos), "protocolos": protocolos})
    return salida


def _id_de_ot(cx: sqlite3.Connection) -> str:
    """La siguiente después de la más alta bajo ot-1000 (las de la semilla), para no volver atrás si se borran OT."""
    altas = [int(f["id"][3:]) for f in cx.execute("SELECT id FROM ots WHERE id GLOB 'ot-0[0-9][0-9][0-9]'").fetchall()]
    n = max([cx.execute("SELECT COUNT(*) AS n FROM ots").fetchone()["n"], *altas]) + 1
    while cx.execute("SELECT 1 FROM ots WHERE id = ?", (f"ot-{n:04d}",)).fetchone():
        n += 1
    return f"ot-{n:04d}"


def generar_ot(cx: sqlite3.Connection, pauta_id: str, solicitante: str, ot_id: str | None = None) -> dict:
    """La OT que pide un cliente: de la última versión aprobada de una pauta atribuida a un protocolo."""
    _exige_pauta(cx, pauta_id)
    if not str(solicitante or "").strip():
        raise ReglaDeNegocio("una OT la pide alguien: falta el solicitante")
    version = ultima_aprobada(cx, pauta_id)
    if version is None:
        raise ReglaDeNegocio(f"la pauta {pauta_id} no tiene ninguna versión aprobada; nadie la puede ejecutar")
    protocolos = protocolos_de(cx, pauta_id)
    if not protocolos:
        raise ReglaDeNegocio(f"la pauta {pauta_id} no está atribuida a ningún protocolo; no se ofrece a clientes")
    r = abrir_ot(cx, ot_id or _id_de_ot(cx), pauta_id, solicitante, version)
    return {**r, "protocolos": protocolos}


# ─── Eventos: solo lectura desde acá ────────────────────────────────────────


def leer_evento(cx: sqlite3.Connection, evento_id: int):
    f = cx.execute("SELECT ot_id FROM eventos WHERE id = ?", (evento_id,)).fetchone()
    if f is None:
        raise db.NoExiste(f"evento {evento_id}")
    return next(e for e in db.eventos(cx, f["ot_id"]) if e.id == evento_id)
