"""El CRUD de lo que las reglas de negocio piden guardar, con esas reglas adentro.

No todo admite las cuatro letras, y eso es deliberado:

| Recurso   | Crear | Leer | Cambiar                    | Borrar |
|-----------|-------|------|----------------------------|--------|
| Pauta     | sí    | sí   | una versión nueva, nunca encima de otra (ADR-0003) | no: hay OT que la ejecutaron |
| Aprobación| sí    | sí   | no                         | no     |
| OT        | sí, solo desde una pauta aprobada (ADR-0003, 0006) | sí | su estado se calcula de los eventos | no |
| Evento    | solo por las acciones del flujo | sí | no: la bitácora solo agrega | no |
| Sesión    | sí    | sí   | se reemplaza al abrir otra en el mismo edge | sí, al terminar |
| Sensor    | sí (lectura) | sí | cada lectura pisa la anterior | no |
"""

from __future__ import annotations

import json
import sqlite3

from app import db
from app.contratos import Pauta, Paso
from app.reglas import estados_desde_eventos, paso_actual

_ESQUEMA = """
CREATE TABLE IF NOT EXISTS aprobaciones (
    pauta_id TEXT NOT NULL, version INTEGER NOT NULL, aprobada_por TEXT NOT NULL, ts TEXT NOT NULL,
    PRIMARY KEY (pauta_id, version)
);
"""


class ReglaDeNegocio(Exception):
    """Lo pedido choca con una regla del negocio. La API lo devuelve como 409."""


def preparar(cx: sqlite3.Connection) -> None:
    cx.executescript(_ESQUEMA)


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


def aprobar_pauta(cx: sqlite3.Connection, pauta_id: str, version: int, actor: str) -> dict:
    """Una persona aprueba antes de que la pauta se use (ADR-0003)."""
    pauta = db.leer_pauta(cx, pauta_id, version)
    if not actor or actor == "sistema":
        raise ReglaDeNegocio("una pauta la aprueba una persona, no el sistema")
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
        raise KeyError(f"pauta {pauta_id}" + (f" v{version}" if version is not None else ""))
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


def listar_ots(cx: sqlite3.Connection) -> list[dict]:
    salida = []
    for f in cx.execute("SELECT * FROM ots ORDER BY abierta_en, id").fetchall():
        pauta = db.leer_pauta(cx, f["pauta_id"], f["pauta_version"])
        actual = paso_actual(pauta, estados_desde_eventos(db.eventos(cx, f["id"])))
        salida.append({
            "ot": f["id"],
            "pauta": f["pauta_id"],
            "version": f["pauta_version"],
            "equipo": f["equipo"],
            "abierta_en": f["abierta_en"],
            "paso_actual": actual.id if actual else None,
            "completa": actual is None,
        })
    return salida


# ─── Eventos: solo lectura desde acá ────────────────────────────────────────


def leer_evento(cx: sqlite3.Connection, evento_id: int):
    f = cx.execute("SELECT ot_id FROM eventos WHERE id = ?", (evento_id,)).fetchone()
    if f is None:
        raise KeyError(f"evento {evento_id}")
    return next(e for e in db.eventos(cx, f["ot_id"]) if e.id == evento_id)
