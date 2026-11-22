"""Simular OT con conductas erróneas recurrentes y ver si la mejora continua las encuentra, sin engañarse.

Modela la CAUSA de cada desviación, no solo la conducta (Reason y Hobbs, REFERENCIAS 34; Peres et al., 33): cada
perfil dice si un cambio de pauta ataca esa causa y, si la ataca, con qué efecto publicado. Así que la versión 2 sirva
o no lo decide la tabla de perfiles, declarada antes de correr, y no el operario simulado.

Las OT pasan por el `Servicios` real, en una base en memoria: lecturas inyectadas, el juez de cámara simulado, y la
bitácora, las métricas y las propuestas son las de siempre. La conducta simulada queda en `Corrida.verdad`, aparte
de la bitácora, para medir qué propuestas acertaron (Sommers et al. 2025: inyectar en el modelo, no en el registro).

Lo que esto prueba y lo que no está en knowledge/projects/mejora-continua/simulacion.md, que genera
scripts/simular_mejora.py.
"""

from __future__ import annotations

import random
import sqlite3
import time
from collections.abc import Mapping, Sequence
from dataclasses import dataclass, field

from app import acceso, catalogo, db, mejora, metricas
from app.bus import Bus
from app.contratos import Pauta, Paso, TipoEvidencia
from app.reglas import reglas_seguridad
from app.servicios import Servicios
from app.video import Cuadro, Video

MODOS = ("saltar", "declarar_sin_hacer", "sensor_falla")


@dataclass(frozen=True)
class Perfil:
    nombre: str
    causa: str
    modo: str
    arreglable: bool          # si un cambio de pauta ataca la causa
    remedio: str
    efecto_v2: float | None   # factor sobre la tasa si la versión nueva aplica el remedio; None = no hay dato publicado
    fuente: str


PERFILES: dict[str, Perfil] = {p.nombre: p for p in (
    Perfil("olvido", "lapso de memoria tras una interrupción", "saltar", True,
           "agregar la verificación explícita del paso", 0.3,
           "THERP, NUREG/CR-1278 tabla 20-7: omisión 0,01 sin casilla de verificación y 0,003 con ella"),
    Perfil("impracticable", "la pauta no calza con cómo se hace el trabajo (violación situacional)", "saltar", True,
           "reescribir el paso con quien hace la tarea", None,
           "Peres et al. 2020 (33); Mendoza et al. 2024: desviación autodeclarada media 30,8 %. Sin efecto publicado"),
    Perfil("presion", "presión de tiempo o del supervisor (violación por optimización)", "saltar", False,
           "ninguno en la pauta: hablar con la supervisión; nunca relajar el control", 1.0,
           "Peres et al. 2020: 7 de 16 se desvían para ahorrar tiempo; HEART: ×11 por falta de tiempo"),
    Perfil("apuro", "declara el paso antes de terminarlo", "declarar_sin_hacer", True,
           "reescribir cuándo el paso está hecho", None,
           "Tabla de síntomas de la skill optimizar-proceso. Sin efecto publicado"),
    Perfil("equipo", "el sensor no ve el paso", "sensor_falla", False,
           "revisar el sensor, no la pauta", 1.0, "Peres et al. 2020: equipo que falla, 5 de 16"),
    Perfil("ruido", "deslices sueltos, en cualquier paso", "declarar_sin_hacer", False,
           "ninguno: no es un patrón", 1.0, "IndustReal (13): 38 de 762 pasos mal completados, ~5 %"),
)}


@dataclass(frozen=True)
class Patron:
    """Una causa recurrente sobre un paso, con la probabilidad de que aparezca en cada OT."""

    perfil: str
    paso: str
    tasa: float


def _estado_antes(pauta: Pauta, i: int, sin: str | None = None) -> dict[str, str]:
    """Los sensores justo antes del paso i de una ejecución en orden; `sin` es un sensor que nunca reportó."""
    estado = reposo(pauta)
    for q in pauta.en_orden[:i]:
        if q.sensor and q.sensor.id != sin:
            estado[q.sensor.id] = q.sensor.espera
    return estado


def _peligros(estado: Mapping[str, str]) -> set[str]:
    return {v.detalle for v in reglas_seguridad(estado)}


def senales_esperadas(pauta: Pauta, paso_id: str, modo: str) -> list[tuple[str, str]]:
    """Las (paso, señal) que la conducta deja en la bitácora; vacío si la evidencia no la distingue.

    Saltarse un paso deja «orden» en el paso que se adelantó, y solo si el saltado es un control crítico
    (reglas.desviacion_de_orden); si adelantarlo deshace un control ya verificado, deja «control» en ese control.
    Si adelantarlo crea una condición de peligro, deja «seguridad» en el paso saltado, que es el que estaba en curso.
    Declarar sin hacer deja «conflicto» si hay sensor o cámara que contradiga. Un sensor que falla deja «persona», y
    si su lectura de reposo crea un peligro más adelante, «seguridad» en el paso en curso en ese momento.
    """
    pasos = pauta.en_orden
    i = next(j for j, p in enumerate(pasos) if p.id == paso_id)
    p = pasos[i]
    if modo == "saltar":
        siguiente = pasos[i + 1] if i + 1 < len(pasos) else None
        if not (p.sensor and siguiente is not None and siguiente.sensor):
            return []
        salida = []
        # Si adelantar el paso siguiente deshace un control ya verificado (sacar el candado antes de alejarse), la
        # alerta es de control perdido sobre ese control, y no se avisa además el orden (servicios._orden).
        deshecho = next((q for q in reversed(pasos[:i]) if q.sensor and q.sensor.id == siguiente.sensor.id), None)
        if deshecho is not None and deshecho.control_critico and deshecho.sensor.espera != siguiente.sensor.espera:
            salida.append((deshecho.id, "control"))
        elif p.control_critico:
            salida.append((siguiente.id, "orden"))
        antes = _estado_antes(pauta, i)
        if _peligros({**antes, siguiente.sensor.id: siguiente.sensor.espera}) - _peligros(antes):
            salida.append((p.id, "seguridad"))
        return salida
    if modo == "declarar_sin_hacer":
        return [(p.id, "conflicto")] if p.tipo_evidencia is not TipoEvidencia.CONFIRMACION else []
    if modo == "sensor_falla":
        if not p.sensor:
            return []
        salida, activos = [(p.id, "persona")], _peligros(_estado_antes(pauta, i))
        for j in range(i + 1, len(pasos)):
            if pasos[j].sensor and pasos[j].sensor.id != p.sensor.id:
                ahora = _peligros({**_estado_antes(pauta, j, sin=p.sensor.id), pasos[j].sensor.id: pasos[j].sensor.espera})
                if ahora - activos:
                    salida.append((pasos[j].id, "seguridad"))
                activos = ahora
        return salida
    raise ValueError(f"modo desconocido: {modo}")


def senal_esperada(pauta: Pauta, paso_id: str, modo: str) -> tuple[str, str] | None:
    """La primera de `senales_esperadas`, o None si la evidencia no distingue la conducta."""
    senales = senales_esperadas(pauta, paso_id, modo)
    return senales[0] if senales else None


def reposo(pauta: Pauta) -> dict[str, str]:
    """El estado de cada sensor antes de empezar: el que deja el último paso que lo usa (la pauta deja el equipo como lo
    encontró). Un sensor que solo se usa una vez arranca en un valor que no es el que el paso espera."""
    salida: dict[str, str] = {}
    for p in pauta.en_orden:
        if p.sensor:
            salida[p.sensor.id] = p.sensor.espera
    primera = {}
    for p in pauta.en_orden:
        if p.sensor and p.sensor.id not in primera:
            primera[p.sensor.id] = p.sensor.espera
    return {s: (v if v != primera[s] else f"sin_{v}") for s, v in salida.items()}


class _Video(Video):
    """Siempre hay un cuadro fresco: el juez simulado no lo mira."""

    def ultimo(self, edge_id: str) -> Cuadro | None:
        return Cuadro(0, time.time(), b"")


class _Servicios(Servicios):
    def _con_cuadro(self, evidencia, ot_id, paso_id, edge_id):
        return {**evidencia, "cuadro": None, "simulado": True} if evidencia else None

    def _cuadro_de_paso(self, ot_id, paso_id):
        return b""


@dataclass
class Corrida:
    cx: sqlite3.Connection
    pauta: Pauta
    ots: list[str] = field(default_factory=list)
    verdad: list[dict] = field(default_factory=list)  # una fila por desviación simulada
    cliente: str = "simulacion"

    def ejecuciones(self, version: int | None = None) -> list[metricas.Ejecucion]:
        filas = [o for o in catalogo.listar_ots(self.cx) if version is None or o["version"] == version]
        return metricas.ejecuciones(self.cx, filas)

    def propuestas(self) -> list[dict]:
        return mejora.propuestas(self.cx, self.ejecuciones(), self.cliente)

    def avisos(self) -> list[dict]:
        """Las recomendaciones que le llegaron al supervisor: en qué OT (su número en la corrida) y sobre qué paso."""
        orden = {ot: i + 1 for i, ot in enumerate(self.ots)}
        filas = self.cx.execute("SELECT ot_id, paso_id, evidencia FROM eventos WHERE tipo = 'propuesta_pauta' ORDER BY id").fetchall()
        return [{"ot": f["ot_id"], "numero": orden.get(f["ot_id"]), "paso": f["paso_id"]} for f in filas]

    def senales(self, version: int | None = None) -> dict[str, dict[str, set[str]]]:
        """OT → paso → señales, como las lee la mejora continua."""
        return {e.ot["ot"]: {p: set(c) for p, c in mejora._senales(e).items()} for e in self.ejecuciones(version)}


class Simulador:
    """Ejecuta OT de una pauta contra los servicios reales, en una base propia."""

    OPERARIOS = ("operario:sim-1", "operario:sim-2", "operario:sim-3", "operario:sim-4")

    def __init__(self, pauta: Pauta, cx: sqlite3.Connection | None = None, cliente: str | None = None):
        """Con `cliente`, cada OT queda de esa empresa: así corre también el aviso al supervisor."""
        self.cx = cx or db.conectar(":memory:")
        self.cliente = cliente
        self.camara_ok = True
        self.s = _Servicios(self.cx, Bus(), _Video(), juez=lambda pregunta, cuadro, antes=None: (self.camara_ok, 0.9))
        mejora.preparar(self.cx)
        if cliente and not self.cx.execute("SELECT 1 FROM clientes WHERE id = ?", (cliente,)).fetchone():
            acceso.crear_cliente(self.cx, cliente, f"Empresa simulada {cliente}", "mineria")
        self.corrida = Corrida(self.cx, pauta, cliente=cliente or "simulacion")
        self.versionar(pauta)

    def versionar(self, pauta: Pauta) -> None:
        """Guarda y aprueba una versión: la de la corrida es la última que se ejecuta."""
        if pauta.version not in {v["version"] for v in catalogo.versiones(self.cx, pauta.id)}:
            db.guardar_pauta(self.cx, pauta)
            catalogo.aprobar_pauta(self.cx, pauta.id, pauta.version, "supervisor:simulacion")
        self.corrida.pauta = pauta

    def correr(self, n_ots: int, patrones: Sequence[Patron] = (), ruido: float = 0.0, semilla: int = 0,
               factores: Mapping[str, float] | None = None) -> Corrida:
        """`factores`: por perfil, cuánto se multiplica su tasa en esta versión (el efecto declarado del cambio).

        Los números al azar se sacan siempre en el mismo orden, así que la misma semilla con otros factores es la
        misma OT con la conducta cambiada solo donde el factor la cambia: un contrafactual pareado.
        """
        pauta = self.corrida.pauta
        for patron in patrones:
            if senal_esperada(pauta, patron.paso, PERFILES[patron.perfil].modo) is None:
                raise ValueError(f"«{patron.perfil}» en {patron.paso}: la evidencia de esa pauta no lo distingue")
        rng = random.Random(semilla)
        for i in range(n_ots):
            plan: dict[str, tuple[str, str]] = {}
            for patron in patrones:
                u = rng.random()
                if u < patron.tasa * (factores or {}).get(patron.perfil, 1.0):
                    plan.setdefault(patron.paso, (PERFILES[patron.perfil].modo, patron.perfil))
            # el paso que se adelanta al saltarse otro se ejecuta junto con él: no lleva conducta propia
            ocupados = set(plan) | {self._siguiente(pauta, paso) for paso, (modo, _) in plan.items() if modo == "saltar"}
            for p in pauta.en_orden:
                u = rng.random()
                if u < ruido and p.id not in ocupados and senal_esperada(pauta, p.id, "declarar_sin_hacer"):
                    plan[p.id] = ("declarar_sin_hacer", "ruido")
            operario = self.OPERARIOS[rng.randrange(len(self.OPERARIOS))]
            self._una_ot(f"sim-v{pauta.version}-s{semilla}-{i:03d}", pauta, plan, operario)
        return self.corrida

    @staticmethod
    def _siguiente(pauta: Pauta, paso_id: str) -> str:
        pasos = pauta.en_orden
        return pasos[next(i for i, p in enumerate(pasos) if p.id == paso_id) + 1].id

    def _una_ot(self, ot_id: str, pauta: Pauta, plan: dict[str, tuple[str, str]], operario: str) -> None:
        edge = f"edge-{ot_id}"
        db.abrir_ot(self.cx, ot_id, pauta, "supervisor:simulacion")
        if self.cliente:
            acceso.vincular_ot(self.cx, ot_id, self.cliente)
        for sensor, valor in reposo(pauta).items():
            self.s.recibir_lectura(edge, sensor, valor)
        self.s.iniciar_sesion(ot_id, edge, operario)
        self.corrida.ots.append(ot_id)
        pasos = pauta.en_orden
        i = 0
        while i < len(pasos):
            p = pasos[i]
            modo, perfil = plan.get(p.id, (None, None))
            if modo:
                senales = senales_esperadas(pauta, p.id, modo)
                if modo == "declarar_sin_hacer" and p.sensor and db.estado_sensores(self.cx).get(p.sensor.id) == p.sensor.espera:
                    senales = []  # el sensor ya marca lo que el paso espera (otro sensor falló antes): no hay qué contradecir
                self.corrida.verdad.append({"ot": ot_id, "paso": p.id, "perfil": perfil, "modo": modo, "senales": senales})
            if modo == "saltar":
                siguiente = pasos[i + 1]
                self._leer(edge, siguiente)
                self._hacer(ot_id, edge, p, None, operario)
                self._leer(edge, siguiente)
                i += 2
                continue
            self._hacer(ot_id, edge, p, modo, operario)
            i += 1
        self.s.terminar_sesion(edge)

    def _leer(self, edge: str, p: Paso) -> None:
        self.s.recibir_lectura(edge, p.sensor.id, p.sensor.espera)

    def _hacer(self, ot_id: str, edge: str, p: Paso, modo: str | None, operario: str) -> None:
        if p.sensor:
            if modo in ("declarar_sin_hacer", "sensor_falla"):
                self.s.declarar(ot_id, operario, f"listo: {p.titulo}", p.id)
            if modo == "sensor_falla":
                self.s.confirmar_por_persona(ot_id, p.id, "supervisor:simulacion", "el sensor no lo vio")
            else:
                self._leer(edge, p)
        elif p.tipo_evidencia is TipoEvidencia.CAMARA:
            if modo == "declarar_sin_hacer":
                self.camara_ok = False
                self.s.declarar(ot_id, operario, f"listo: {p.titulo}", p.id)
            self.camara_ok = True
            self.s.declarar(ot_id, operario, f"listo: {p.titulo}", p.id)
        else:
            self.s.declarar(ot_id, operario, f"listo: {p.titulo}", p.id)


def fidelidad(corrida: Corrida) -> dict:
    """Si cada desviación simulada dejó exactamente la señal esperada, y ninguna señal apareció sin desviación."""
    leidas = corrida.senales()
    esperadas = {(v["ot"], paso, senal) for v in corrida.verdad for paso, senal in v["senales"]}
    vistas = {(ot, paso, s) for ot, por_paso in leidas.items() for paso, senales in por_paso.items() for s in senales
              if s != "conflicto" or (ot, paso, "persona") not in esperadas}
    return {"esperadas": len(esperadas), "vistas": len(vistas),
            "faltan": sorted(esperadas - vistas), "sobran": sorted(vistas - esperadas)}


# ─── Monte Carlo sobre las señales: miles de pautas en segundos ─────────────
# Simula directo la matriz «OT × paso con señal» que lee la mejora continua. `fidelidad` y el eval de
# scripts/simular_mejora.py comprueban contra el pipeline real que esa matriz es la que dejan las OT simuladas.


def _regla_minimo(con_senal: Mapping[str, int]) -> set[str]:
    return {p for p, k in con_senal.items() if k >= mejora.MINIMO}


def _regla_recurrencia(con_senal: Mapping[str, int], ots: int) -> set[str]:
    from app import recurrencia

    return {p for p, d in recurrencia.recurrentes(con_senal, ots).items() if d["recurrente"]}


def montecarlo_criterio(pasos: int, ots: int, base: float, recurrente: float | None = None,
                        repeticiones: int = 1000, semilla: int = 0) -> dict:
    """Con `pasos` pasos que se desvían al azar con `base` y, si se da, el primero con `recurrente`:
    cuántas veces cada regla marca algún paso sin patrón (falsa propuesta) y cuántas marca el que lo tiene."""
    rng = random.Random(semilla)
    cuentas = {"minimo": [0, 0], "recurrencia": [0, 0]}
    for _ in range(repeticiones):
        con_senal = {f"p{j}": sum(rng.random() < (recurrente if j == 0 and recurrente is not None else base)
                                  for _ in range(ots)) for j in range(pasos)}
        for nombre, marcados in (("minimo", _regla_minimo(con_senal)), ("recurrencia", _regla_recurrencia(con_senal, ots))):
            cuentas[nombre][0] += bool(marcados - ({"p0"} if recurrente is not None else set()))
            cuentas[nombre][1] += "p0" in marcados
    salida = {}
    for nombre, (falsas, detecta) in cuentas.items():
        salida[nombre] = {"falsa_propuesta": falsas / repeticiones,
                          "detecta": detecta / repeticiones if recurrente is not None else None}
    return salida


def montecarlo_validacion(ots: int, tasa: float, factor: float, repeticiones: int = 1000, semilla: int = 0) -> dict:
    """La v1 y la v2 con OT distintas, la v2 con `tasa × factor`: cuántas veces cada regla dice «mejoró».

    `ingenua` es la que tenía mejora.py hasta el 2026-11-21: mejoró si la tasa de la v2 es menor. Con factor 1 todo
    «mejoró» es falso."""
    from app import recurrencia

    rng = random.Random(semilla)
    ingenua = fisher = 0
    for _ in range(repeticiones):
        k1 = sum(rng.random() < tasa for _ in range(ots))
        k2 = sum(rng.random() < tasa * factor for _ in range(ots))
        ingenua += k2 / ots < k1 / ots
        fisher += recurrencia.comprobar_cambio((ots, k1), (ots, k2))["resultado"] == "mejoro"
    return {"ingenua": ingenua / repeticiones, "fisher": fisher / repeticiones}


def montecarlo_peor_paso(pasos: int, ots: int, base: float, repeticiones: int = 1000, semilla: int = 0) -> dict:
    """Regresión a la media: se elige el paso que más se desvió en la v1 y se vuelve a medir sin cambiar nada."""
    from app import recurrencia

    rng = random.Random(semilla)
    ingenua = fisher = 0
    for _ in range(repeticiones):
        v1 = [sum(rng.random() < base for _ in range(ots)) for _ in range(pasos)]
        k1 = max(v1)
        k2 = sum(rng.random() < base for _ in range(ots))
        ingenua += k2 < k1
        fisher += recurrencia.comprobar_cambio((ots, k1), (ots, k2))["resultado"] == "mejoro"
    return {"ingenua": ingenua / repeticiones, "fisher": fisher / repeticiones}


def montecarlo_aviso(pasos: int, ots: int, base: float, recurrente: float | None, alfa: float,
                     repeticiones: int = 500, semilla: int = 0) -> dict:
    """El aviso en vivo: se prueba después de cada OT, como hace servicios._vigilar_patrones.

    `falso_aviso`: pautas donde en algún momento de las `ots` se marcó un paso sin patrón. `detecta_en`: la mediana
    de la OT en que se marcó el paso con patrón, y `detecta_antes_de`: la fracción que lo marcó dentro de las `ots`."""
    from app import recurrencia

    rng = random.Random(semilla)
    falsos, cuando = 0, []
    for _ in range(repeticiones):
        cuenta, primero, falso = [0] * pasos, None, False
        for t in range(1, ots + 1):
            for j in range(pasos):
                cuenta[j] += rng.random() < (recurrente if j == 0 and recurrente is not None else base)
            r = recurrencia.recurrentes({f"p{j}": cuenta[j] for j in range(pasos)}, t, alfa)
            marcados = {k for k, d in r.items() if d["recurrente"]}
            falso = falso or bool(marcados - ({"p0"} if recurrente is not None else set()))
            if recurrente is not None and primero is None and "p0" in marcados:
                primero = t
        falsos += falso
        if primero is not None:
            cuando.append(primero)
    cuando.sort()
    return {"falso_aviso": falsos / repeticiones,
            "detecta_antes_de": len(cuando) / repeticiones if recurrente is not None else None,
            "detecta_en": cuando[len(cuando) // 2] if cuando else None}
