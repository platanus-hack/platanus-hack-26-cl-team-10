"""Almacén. La tabla de eventos SOLO admite agregar filas (ADR-0003).

No hay UPDATE ni DELETE sobre eventos en ningún lugar del código, y eso es
deliberado: el estado de una OT se calcula leyendo sus eventos en orden.
"""

from __future__ import annotations

import json
import sqlite3
import threading
from datetime import UTC, datetime
from pathlib import Path

from app.contratos import Estado, Evento, Pauta, Paso, TipoEvento

RUTA = Path(__file__).resolve().parent.parent / "datos" / "bitacora.sqlite3"

_ESQUEMA = """
CREATE TABLE IF NOT EXISTS pautas (
    id TEXT NOT NULL, version INTEGER NOT NULL, json TEXT NOT NULL,
    PRIMARY KEY (id, version)
);
CREATE TABLE IF NOT EXISTS ots (
    id TEXT PRIMARY KEY, pauta_id TEXT NOT NULL, pauta_version INTEGER NOT NULL,
    equipo TEXT NOT NULL, abierta_en TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS eventos (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    ot_id TEXT NOT NULL, paso_id TEXT, ts TEXT NOT NULL, tipo TEXT NOT NULL,
    estado TEXT, actor TEXT NOT NULL, capa INTEGER, declarado TEXT,
    evidencia TEXT, detalle TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS sensores (
    id TEXT PRIMARY KEY, valor TEXT NOT NULL, ts TEXT NOT NULL
);
CREATE INDEX IF NOT EXISTS idx_eventos_ot ON eventos (ot_id, id);
"""


class NoExiste(KeyError):
    """Lo pedido (OT, pauta, evento, paso, sesión) no existe: la API responde 404.

    Hereda de KeyError para quien ya lo atrapaba, pero la API solo traduce a 404 esta
    clase: un KeyError cualquiera es un bug y sale como 500, con su traza.
    """


def ahora() -> str:
    return datetime.now(UTC).isoformat(timespec="seconds")


class _Filas:
    """El resultado de una consulta ya leído entero, para soltar el candado al volver."""

    def __init__(self, cur: sqlite3.Cursor) -> None:
        self._filas, self._i = cur.fetchall(), 0
        self.lastrowid, self.rowcount = cur.lastrowid, cur.rowcount

    def fetchone(self):
        if self._i >= len(self._filas):
            return None
        self._i += 1
        return self._filas[self._i - 1]

    def fetchall(self) -> list:
        resto, self._i = self._filas[self._i:], len(self._filas)
        return resto

    def __iter__(self):
        return iter(self.fetchall())


class ConexionCompartida(sqlite3.Connection):
    """Una conexión que usan a la vez los hilos de los endpoints y el loop de los
    WebSocket. sqlite3 no admite uso concurrente de una misma conexión (InterfaceError
    con 18 detecciones por segundo contra /lecturas): cada operación pasa por un candado
    y devuelve las filas ya leídas."""

    def __init__(self, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)
        self._candado = threading.RLock()

    def execute(self, sql, parametros=(), /):
        with self._candado:
            return _Filas(super().execute(sql, parametros))

    def executescript(self, script, /):
        with self._candado:
            return super().executescript(script)

    def commit(self) -> None:
        with self._candado:
            super().commit()


def conectar(ruta: Path | str | None = None) -> sqlite3.Connection:
    destino = Path(ruta) if ruta else RUTA
    if destino != Path(":memory:"):
        destino.parent.mkdir(parents=True, exist_ok=True)
    cx = sqlite3.connect(destino, check_same_thread=False, factory=ConexionCompartida)
    cx.row_factory = sqlite3.Row
    cx.executescript(_ESQUEMA)
    return cx


# ─── Pautas ─────────────────────────────────────────────────────────────────


def guardar_pauta(cx: sqlite3.Connection, pauta: Pauta) -> None:
    cuerpo = {
        "id": pauta.id,
        "nombre": pauta.nombre,
        "version": pauta.version,
        "equipo": pauta.equipo,
        "pasos": [
            {
                "id": p.id,
                "orden": p.orden,
                "titulo": p.titulo,
                "instruccion": p.instruccion,
                "tipo_evidencia": str(p.tipo_evidencia),
                "capa_minima": p.capa_minima,
                "control_critico": p.control_critico,
                "pregunta_visual": p.pregunta_visual,
                "sensor": {"id": p.sensor.id, "espera": p.sensor.espera} if p.sensor else None,
                "deteccion": ({"clase": p.deteccion.clase, "presente": p.deteccion.presente}
                              if p.deteccion else None),
                "comparar_con": p.comparar_con,
            }
            for p in pauta.en_orden
        ],
    }
    cx.execute(
        "INSERT OR REPLACE INTO pautas (id, version, json) VALUES (?, ?, ?)",
        (pauta.id, pauta.version, json.dumps(cuerpo, ensure_ascii=False)),
    )
    cx.commit()


def leer_pauta(cx: sqlite3.Connection, pauta_id: str, version: int | None = None) -> Pauta:
    if version is None:
        fila = cx.execute(
            "SELECT json FROM pautas WHERE id = ? ORDER BY version DESC LIMIT 1", (pauta_id,)
        ).fetchone()
    else:
        fila = cx.execute(
            "SELECT json FROM pautas WHERE id = ? AND version = ?", (pauta_id, version)
        ).fetchone()
    if fila is None:
        raise NoExiste(f"pauta {pauta_id} v{version}")
    d = json.loads(fila["json"])
    return Pauta(
        id=d["id"],
        nombre=d["nombre"],
        version=d["version"],
        equipo=d["equipo"],
        pasos=tuple(Paso.desde_dict(x) for x in d["pasos"]),
    )


# ─── OT ─────────────────────────────────────────────────────────────────────


def abrir_ot(cx: sqlite3.Connection, ot_id: str, pauta: Pauta, actor: str) -> None:
    """Cada OT guarda qué VERSIÓN de la pauta ejecutó (ADR-0003)."""
    cx.execute(
        "INSERT INTO ots (id, pauta_id, pauta_version, equipo, abierta_en) VALUES (?, ?, ?, ?, ?)",
        (ot_id, pauta.id, pauta.version, pauta.equipo, ahora()),
    )
    cx.commit()
    agregar(
        cx,
        Evento(
            ot_id=ot_id,
            tipo=TipoEvento.OT_ABIERTA,
            ts=ahora(),
            actor=actor,
            detalle=f"OT abierta desde {pauta.nombre} v{pauta.version} sobre {pauta.equipo}",
        ),
    )


def leer_ot(cx: sqlite3.Connection, ot_id: str) -> sqlite3.Row:
    fila = cx.execute("SELECT * FROM ots WHERE id = ?", (ot_id,)).fetchone()
    if fila is None:
        raise NoExiste(f"OT {ot_id}")
    return fila


# ─── Eventos: solo agregar ──────────────────────────────────────────────────


def agregar(cx: sqlite3.Connection, ev: Evento) -> int:
    cur = cx.execute(
        "INSERT INTO eventos (ot_id, paso_id, ts, tipo, estado, actor, capa, declarado,"
        " evidencia, detalle) VALUES (?,?,?,?,?,?,?,?,?,?)",
        (
            ev.ot_id,
            ev.paso_id,
            ev.ts,
            str(ev.tipo),
            str(ev.estado) if ev.estado else None,
            ev.actor,
            int(ev.capa) if ev.capa is not None else None,
            ev.declarado,
            json.dumps(ev.evidencia, ensure_ascii=False) if ev.evidencia else None,
            ev.detalle,
        ),
    )
    cx.commit()
    ev.id = cur.lastrowid
    return cur.lastrowid


def eventos(cx: sqlite3.Connection, ot_id: str) -> list[Evento]:
    filas = cx.execute("SELECT * FROM eventos WHERE ot_id = ? ORDER BY id", (ot_id,)).fetchall()
    return [_fila_a_evento(f) for f in filas]


def todos_los_eventos(cx: sqlite3.Connection) -> list[Evento]:
    filas = cx.execute("SELECT * FROM eventos ORDER BY id").fetchall()
    return [_fila_a_evento(f) for f in filas]


def _fila_a_evento(f: sqlite3.Row) -> Evento:
    return Evento(
        id=f["id"],
        ot_id=f["ot_id"],
        paso_id=f["paso_id"],
        ts=f["ts"],
        tipo=TipoEvento(f["tipo"]),
        estado=Estado(f["estado"]) if f["estado"] else None,
        actor=f["actor"],
        capa=f["capa"],
        declarado=f["declarado"],
        evidencia=json.loads(f["evidencia"]) if f["evidencia"] else None,
        detalle=f["detalle"],
    )


# ─── Sensores ───────────────────────────────────────────────────────────────


def escribir_sensor(cx: sqlite3.Connection, sensor_id: str, valor: str) -> None:
    cx.execute(
        "INSERT OR REPLACE INTO sensores (id, valor, ts) VALUES (?, ?, ?)",
        (sensor_id, valor, ahora()),
    )
    cx.commit()


def estado_sensores(cx: sqlite3.Connection) -> dict[str, str]:
    return {f["id"]: f["valor"] for f in cx.execute("SELECT id, valor FROM sensores").fetchall()}
