"""Clientes, sus personas y el login (ADR-0012).

Un cliente es una empresa que pide OT. Sus personas entran con usuario y clave y reciben un
token que dura DURACION_SESION; con él, el servicio para clientes sabe quién pide y de qué
empresa es, sin creerle a lo que venga en el cuerpo. Cada cliente ve solo sus OT y solo las
pautas que el equipo le habilitó.

| Rol | Qué puede |
|---|---|
| supervisor | Pedir OT, asignarlas a un operador de su empresa y ver todas las de su empresa |
| operador | Ver las OT que tiene asignadas |

La clave no se guarda: se guarda su derivación PBKDF2-SHA256 con sal propia. El token tampoco:
se guarda su SHA-256. Las claves las genera el sistema y se muestran una sola vez.
"""

from __future__ import annotations

import hashlib
import hmac
import secrets
import sqlite3
from collections.abc import Collection
from datetime import UTC, datetime, timedelta

from app import catalogo, db
from app.catalogo import ReglaDeNegocio
from app.contratos import TipoEvento

ROLES = ("supervisor", "operador")
DURACION_SESION = timedelta(hours=12)
ITERACIONES = 200_000

_ESQUEMA = """
CREATE TABLE IF NOT EXISTS clientes (
    id TEXT PRIMARY KEY, nombre TEXT NOT NULL, industria TEXT NOT NULL, ts TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS personas (
    id TEXT PRIMARY KEY, cliente_id TEXT NOT NULL, nombre TEXT NOT NULL, usuario TEXT NOT NULL UNIQUE,
    rol TEXT NOT NULL, clave TEXT NOT NULL, ts TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS tokens (
    hash TEXT PRIMARY KEY, persona_id TEXT NOT NULL, expira TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS cliente_pautas (
    cliente_id TEXT NOT NULL, pauta_id TEXT NOT NULL, ts TEXT NOT NULL,
    PRIMARY KEY (cliente_id, pauta_id)
);
CREATE TABLE IF NOT EXISTS ot_cliente (
    ot_id TEXT PRIMARY KEY, cliente_id TEXT NOT NULL
);
"""


class NoAutenticado(Exception):
    """Falta el token, no existe o venció: 401."""


class SinPermiso(Exception):
    """La persona entró, pero su rol o su empresa no la dejan: 403."""


def preparar(cx: sqlite3.Connection) -> None:
    catalogo.preparar(cx)
    cx.executescript(_ESQUEMA)


# ─── Claves y tokens ────────────────────────────────────────────────────────


def _derivar(clave: str, sal: bytes, iteraciones: int = ITERACIONES) -> str:
    return hashlib.pbkdf2_hmac("sha256", clave.encode(), sal, iteraciones).hex()


def _guardable(clave: str) -> str:
    sal = secrets.token_bytes(16)
    return f"pbkdf2-sha256${ITERACIONES}${sal.hex()}${_derivar(clave, sal)}"


def _coincide(clave: str, guardada: str) -> bool:
    _, iteraciones, sal, derivada = guardada.split("$")
    return hmac.compare_digest(_derivar(clave, bytes.fromhex(sal), int(iteraciones)), derivada)


def _hash_token(token: str) -> str:
    return hashlib.sha256(token.encode()).hexdigest()


def _ahora() -> datetime:
    return datetime.now(UTC)


# ─── Clientes y personas ────────────────────────────────────────────────────


def _cliente(cx: sqlite3.Connection, cliente_id: str) -> dict:
    f = cx.execute("SELECT * FROM clientes WHERE id = ?", (cliente_id,)).fetchone()
    if f is None:
        raise db.NoExiste(f"cliente {cliente_id}")
    return {"id": f["id"], "nombre": f["nombre"], "industria": f["industria"]}


def crear_cliente(cx: sqlite3.Connection, cliente_id: str, nombre: str, industria: str = "") -> dict:
    if not cliente_id.strip() or not nombre.strip():
        raise ReglaDeNegocio("un cliente necesita id y nombre")
    if cx.execute("SELECT 1 FROM clientes WHERE id = ?", (cliente_id,)).fetchone():
        raise ReglaDeNegocio(f"el cliente {cliente_id} ya existe")
    cx.execute("INSERT INTO clientes (id, nombre, industria, ts) VALUES (?, ?, ?, ?)", (cliente_id, nombre, industria, db.ahora()))
    cx.commit()
    return _cliente(cx, cliente_id)


def listar_clientes(cx: sqlite3.Connection) -> list[dict]:
    return [_cliente(cx, f["id"]) for f in cx.execute("SELECT id FROM clientes ORDER BY id").fetchall()]


def _persona_dict(cx: sqlite3.Connection, f: sqlite3.Row) -> dict:
    return {"id": f["id"], "nombre": f["nombre"], "usuario": f["usuario"], "rol": f["rol"], "cliente": _cliente(cx, f["cliente_id"])}


def persona(cx: sqlite3.Connection, persona_id: str) -> dict:
    f = cx.execute("SELECT * FROM personas WHERE id = ?", (persona_id,)).fetchone()
    if f is None:
        raise db.NoExiste(f"persona {persona_id}")
    return _persona_dict(cx, f)


def crear_persona(cx: sqlite3.Connection, cliente_id: str, persona_id: str, nombre: str, usuario: str, rol: str) -> tuple[dict, str]:
    """Crea la persona con una clave al azar y la devuelve junto a la clave: es la única vez que se ve."""
    _cliente(cx, cliente_id)
    if rol not in ROLES:
        raise ReglaDeNegocio(f"el rol {rol} no existe; hay {', '.join(ROLES)}")
    if not persona_id.strip() or not nombre.strip() or not usuario.strip():
        raise ReglaDeNegocio("una persona necesita id, nombre y usuario")
    if cx.execute("SELECT 1 FROM personas WHERE id = ? OR usuario = ?", (persona_id, usuario.lower())).fetchone():
        raise ReglaDeNegocio(f"ya hay una persona con el id {persona_id} o el usuario {usuario}")
    clave = secrets.token_urlsafe(12)
    cx.execute("INSERT INTO personas (id, cliente_id, nombre, usuario, rol, clave, ts) VALUES (?, ?, ?, ?, ?, ?, ?)",
               (persona_id, cliente_id, nombre, usuario.lower(), rol, _guardable(clave), db.ahora()))
    cx.commit()
    return persona(cx, persona_id), clave


def nueva_clave(cx: sqlite3.Connection, persona_id: str) -> str:
    """Cambia la clave por una nueva al azar y cierra las sesiones abiertas de esa persona."""
    persona(cx, persona_id)
    clave = secrets.token_urlsafe(12)
    cx.execute("UPDATE personas SET clave = ? WHERE id = ?", (_guardable(clave), persona_id))
    cx.execute("DELETE FROM tokens WHERE persona_id = ?", (persona_id,))
    cx.commit()
    return clave


def personas_de(cx: sqlite3.Connection, cliente_id: str, rol: str | None = None) -> list[dict]:
    _cliente(cx, cliente_id)
    filas = cx.execute("SELECT * FROM personas WHERE cliente_id = ? AND (? IS NULL OR rol = ?) ORDER BY id",
                       (cliente_id, rol, rol)).fetchall()
    return [_persona_dict(cx, f) for f in filas]


def nombres_de(cx: sqlite3.Connection, cliente_id: str) -> list[dict]:
    """Lo que una persona puede saber de las demás de su empresa. El usuario no va: es la mitad del login."""
    return [{"id": p["id"], "nombre": p["nombre"], "rol": p["rol"]} for p in personas_de(cx, cliente_id)]


# ─── Entrar, saber quién es y salir ─────────────────────────────────────────


def entrar(cx: sqlite3.Connection, usuario: str, clave: str) -> dict:
    f = cx.execute("SELECT * FROM personas WHERE usuario = ?", ((usuario or "").lower(),)).fetchone()
    if f is None or not _coincide(clave or "", f["clave"]):
        raise NoAutenticado("usuario o clave incorrectos")
    token, expira = secrets.token_urlsafe(32), _ahora() + DURACION_SESION
    cx.execute("DELETE FROM tokens WHERE expira < ?", (_ahora().isoformat(),))
    cx.execute("INSERT INTO tokens (hash, persona_id, expira) VALUES (?, ?, ?)", (_hash_token(token), f["id"], expira.isoformat()))
    cx.commit()
    return {"token": token, "expira": expira.isoformat(timespec="seconds"), "persona": _persona_dict(cx, f)}


def quien(cx: sqlite3.Connection, token: str | None) -> dict:
    if not token:
        raise NoAutenticado("falta el token: entra con POST /auth/entrar y mándalo como Authorization: Bearer <token>")
    f = cx.execute("SELECT persona_id, expira FROM tokens WHERE hash = ?", (_hash_token(token),)).fetchone()
    if f is None or datetime.fromisoformat(f["expira"]) < _ahora():
        raise NoAutenticado("el token no existe o venció: vuelve a entrar")
    return persona(cx, f["persona_id"])


def salir(cx: sqlite3.Connection, token: str) -> None:
    cx.execute("DELETE FROM tokens WHERE hash = ?", (_hash_token(token),))
    cx.commit()


def exige_rol(p: dict, rol: str) -> None:
    if p["rol"] != rol:
        raise SinPermiso(f"eso lo hace un {rol}; {p['id']} es {p['rol']}")


# ─── Qué pautas tiene habilitadas cada cliente ──────────────────────────────


def habilitar(cx: sqlite3.Connection, cliente_id: str, pauta_id: str) -> list[dict]:
    _cliente(cx, cliente_id)
    if not catalogo.versiones(cx, pauta_id):
        raise db.NoExiste(f"pauta {pauta_id}")
    cx.execute("INSERT OR IGNORE INTO cliente_pautas (cliente_id, pauta_id, ts) VALUES (?, ?, ?)", (cliente_id, pauta_id, db.ahora()))
    cx.commit()
    return pautas_habilitadas(cx, cliente_id)


def deshabilitar(cx: sqlite3.Connection, cliente_id: str, pauta_id: str) -> None:
    cx.execute("DELETE FROM cliente_pautas WHERE cliente_id = ? AND pauta_id = ?", (cliente_id, pauta_id))
    cx.commit()


def pautas_habilitadas(cx: sqlite3.Connection, cliente_id: str) -> list[dict]:
    """Las que el cliente puede pedir: habilitadas para él y listas (aprobadas y con protocolo)."""
    suyas = {f["pauta_id"] for f in cx.execute("SELECT pauta_id FROM cliente_pautas WHERE cliente_id = ?", (cliente_id,)).fetchall()}
    return [p for p in catalogo.pautas_disponibles(cx) if p["id"] in suyas]


# ─── Las OT de cada cliente ─────────────────────────────────────────────────


def pedir_ot(cx: sqlite3.Connection, p: dict, pauta_id: str, ot_id: str | None = None) -> dict:
    """Un supervisor pide una OT de una pauta habilitada para su empresa; la OT queda de esa empresa."""
    exige_rol(p, "supervisor")
    cliente_id = p["cliente"]["id"]
    if pauta_id not in {x["id"] for x in pautas_habilitadas(cx, cliente_id)}:
        raise SinPermiso(f"la pauta {pauta_id} no está habilitada para {p['cliente']['nombre']}")
    r = catalogo.generar_ot(cx, pauta_id, p["id"], ot_id)
    vincular_ot(cx, r["ot"], cliente_id)
    return {**r, "cliente": cliente_id}


def vincular_ot(cx: sqlite3.Connection, ot_id: str, cliente_id: str) -> None:
    cx.execute("INSERT OR IGNORE INTO ot_cliente (ot_id, cliente_id) VALUES (?, ?)", (ot_id, cliente_id))
    cx.commit()


def ots_de(cx: sqlite3.Connection, p: dict, en_sesion: Collection[str] = ()) -> list[dict]:
    """El supervisor ve todas las de su empresa; el operador, las que tiene asignadas."""
    suyas = {f["ot_id"] for f in cx.execute("SELECT ot_id FROM ot_cliente WHERE cliente_id = ?", (p["cliente"]["id"],)).fetchall()}
    ots = [o for o in catalogo.listar_ots(cx, en_sesion) if o["ot"] in suyas]
    return ots if p["rol"] == "supervisor" else [o for o in ots if o["operador"] == p["id"]]


def ot_de(cx: sqlite3.Connection, p: dict, ot_id: str, en_sesion: Collection[str] = ()) -> dict:
    """Una OT que no es de su empresa, o que un operador no tiene asignada, no existe para esa persona."""
    o = next((x for x in ots_de(cx, p, en_sesion) if x["ot"] == ot_id), None)
    if o is None:
        raise db.NoExiste(f"OT {ot_id}")
    return o


def ficha(cx: sqlite3.Connection, ot_id: str, en_sesion: Collection[str] = (), con_empresa: bool = True) -> dict:
    """Lo que hace falta para ejecutar una OT que ya existe: su resumen, de qué empresa es, quién la pidió y quién
    la tiene, de qué protocolos sale su pauta y sus pasos completos, en la versión que la OT ejecuta. Sin
    `con_empresa` no salen la empresa ni los nombres de sus personas: es lo que ve quien no entró."""
    o = catalogo.resumen_ot(cx, ot_id, en_sesion)
    f = cx.execute("SELECT cliente_id FROM ot_cliente WHERE ot_id = ?", (ot_id,)).fetchone() if con_empresa else None
    nombres = {p["id"]: p["nombre"] for p in personas_de(cx, f["cliente_id"])} if f else {}
    pedida_por = next((e.actor for e in db.eventos(cx, ot_id) if e.tipo is TipoEvento.OT_ABIERTA), None)
    pauta = catalogo.leer_pauta(cx, o["pauta"], o["version"])
    return {**o, "nombre": pauta["nombre"], "cliente": _cliente(cx, f["cliente_id"]) if f else None,
            "operador_nombre": nombres.get(o["operador"]), "pedida_por": pedida_por,
            "pedida_por_nombre": nombres.get(pedida_por), "protocolos": catalogo.protocolos_de(cx, o["pauta"]),
            "pasos": sorted(pauta["pasos"], key=lambda p: p["orden"])}


def exige_estacion(cx: sqlite3.Connection, p: dict, ot_id: str, edge_id: str, sesion: dict | None, tomar: bool) -> None:
    """Si esta persona puede dejar la estación `edge_id` ejecutando su OT; `sesion` es lo que la estación ejecuta
    ahora. La autoriza quién es, no una clave compartida: el operador que tiene la OT asignada. Una estación
    libre, o con una OT ya completa, se une sin más. Quitársela a una OT abierta hay que pedirlo con `tomar`,
    porque esa OT deja de recibir sus sensores, y nunca se le quita a la OT de otra empresa."""
    exige_rol(p, "operador")
    if ot_de(cx, p, ot_id)["completa"]:
        raise catalogo.ReglaDeNegocio(f"la OT {ot_id} ya está completa")
    if sesion is None or sesion["ot_id"] == ot_id:
        return
    dueno = cx.execute("SELECT cliente_id FROM ot_cliente WHERE ot_id = ?", (sesion["ot_id"],)).fetchone()
    if dueno is not None and dueno["cliente_id"] != p["cliente"]["id"]:
        raise SinPermiso(f"la estación {edge_id} ejecuta la OT de otra empresa")
    try:
        if catalogo.resumen_ot(cx, sesion["ot_id"])["completa"]:
            return
    except db.NoExiste:
        return
    if not tomar:
        raise catalogo.ReglaDeNegocio(f"la estación {edge_id} ejecuta la OT {sesion['ot_id']} desde {sesion['desde']}, con "
                                      f"{sesion['operario']}; para quitársela, repetir con `tomar` en true")


def operador_de_la_empresa(cx: sqlite3.Connection, p: dict, operador: str) -> None:
    if operador not in {x["id"] for x in personas_de(cx, p["cliente"]["id"], "operador")}:
        raise SinPermiso(f"{operador} no es operador de {p['cliente']['nombre']}")
