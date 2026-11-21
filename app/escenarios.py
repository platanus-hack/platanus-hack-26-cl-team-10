"""Escenarios por industria: cómo se comporta cada barrera ante cada forma de ejecutar un paso.

Un escenario es una industria (su pauta y sus sensores) por un patrón de ejecución
(se salta un paso, lo declara antes de hacerlo, el sensor lo ve antes que la palabra,
revierte un control ya verificado...). Cada uno dice qué barrera lo decide y qué se
espera, y se corre en una caja aislada: base en memoria, bus propio, juez de cámara
y reloj inyectados. Así no toca la bitácora real ni los sensores globales del servidor,
y el resultado no depende de qué más esté pasando ahí.

Un escenario con `brecha` describe lo que el producto debería hacer y hoy no hace. El
test exige que siga fallando: si alguien cierra la brecha, el test avisa que hay que
quitar la marca. Ver knowledge/projects/escenarios-por-industria/PRD.md.

Las tres barreras del ADR-0004 se miden distinto. Este módulo prueba la política de
cada una (qué hace el sistema con lo que la barrera dice). La calidad del modelo de
cada barrera se mide aparte: scripts/simular_capa2.py y scripts/evaluar_capa3.py.
"""

from __future__ import annotations

import random
import tempfile
from collections.abc import Callable
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from pathlib import Path

from app import db, protocolos, verificacion
from app.bus import Bus, canal_ot
from app.contratos import Capa, Estado, TipoEvento
from app.protocolos import PAUTA_DEMO
from app.reglas import estados_desde_eventos, paso_actual
from app.scoring import _GRAVEDAD, Nivel, calificar_evento
from app.servicios import Servicios, evento_dict
from app.video import Video

DATOS = PAUTA_DEMO.parent
JPEG = b"\xff\xd8" + b"cuadro de escenario" + b"\xff\xd9"
OT, EDGE, OPERARIO = "ot-escenario", "edge-escenario", "operario:escenario"

BARRERAS = {
    1: "Determinista: sensores y reglas",
    2: "Aprendizaje sobre señales",
    3: "Modelo de visión y lenguaje",
}


# ─── Industrias ─────────────────────────────────────────────────────────────


@dataclass(frozen=True)
class PasoClave:
    sensor: str
    hecho: str
    sin_hacer: str
    dice: str


@dataclass(frozen=True)
class Peligro:
    """Una condición de seguridad de la industria, escrita en reglas.py."""

    regla: str
    lecturas: tuple[tuple[str, str], ...]
    fuente: str


@dataclass(frozen=True)
class Senal:
    sensor: str
    unidad: str
    media: float
    desvio: float
    pico: float
    que_mide: str


@dataclass(frozen=True)
class Industria:
    codigo: str
    nombre: str
    pauta: Path
    tarea: str
    seguro: tuple[tuple[str, str], ...]
    p1: PasoClave
    p2: PasoClave
    hasta_camara: tuple[tuple[str, str], ...]
    paso_camara: str
    dice_camara: str
    peligro: Peligro
    senal: Senal
    fuente_orden: str
    recorrido: tuple[dict, ...] = ()
    trasfondo: tuple[tuple[str, str], ...] = ()
    pruebas: str = ""


MINERIA = Industria(
    codigo="MIN", nombre="Minería", pauta=DATOS / "pauta-correa.json",
    tarea="Cambio de rodillo en la correa CT-01",
    seguro=(("guarda", "cerrada"), ("energia", "cortada"), ("reed_bloqueo", "abierto")),
    p1=PasoClave("reed_bloqueo", "cerrado", "abierto", "bloqueo puesto"),
    p2=PasoClave("guarda", "abierta", "cerrada", "guarda retirada"),
    hasta_camara=(("reed_bloqueo", "cerrado"), ("guarda", "abierta")),
    paso_camara="p3", dice_camara="rodillo cambiado",
    peligro=Peligro("Guarda abierta con energía viva", (("energia", "viva"), ("guarda", "abierta")),
                    "Regla vigente en LOGICA. Mantención solo con la energía cortada y la máquina bloqueada, y guardas puestas "
                    "mientras opera (REFERENCIAS 44, DS 132 art. 52; REFERENCIAS 45, 30 CFR 56.14105 y 56.14112(b))"),
    senal=Senal("vibracion", "mm/s", 2.0, 0.12, 6.5, "vibración del rodillo"),
    fuente_orden=("Bloqueo antes de intervenir y protecciones puestas antes de volver a servicio (REFERENCIAS 44, DS 132 "
                  "art. 52). Ocho muertes en correas desde 2017, todas evitables con bloqueo (REFERENCIAS 46)"),
    recorrido=(
        {"lee": [["reed_bloqueo", "cerrado"], ["guarda", "abierta"]]}, {"cuadro": True}, {"dice": "rodillo cambiado"},
        {"lee": [["guarda", "cerrada"], ["reed_bloqueo", "abierto"], ["energia", "viva"]]},
        {"dice": "la correa paró en dos segundos"},
    ),
    trasfondo=(
        ("La norma", "Antes de mantener se ponen los bloqueos y la advertencia; antes de volver a servicio se reponen "
                     "las protecciones y se prueba el equipo (DS 132 art. 52, REFERENCIAS 44). La correa se mantiene "
                     "totalmente detenida (art. 116). En EE.UU., desenergizar y bloquear antes del trabajo mecánico, y "
                     "el candado lo saca quien lo puso (30 CFR 56.12016, REFERENCIAS 45)."),
        ("Cuando falla", "MSHA contó ocho muertes con correas desde 2017, todas evitables con bloqueo y calzo "
                         "(REFERENCIAS 46). En la de 2025 la mina tenía un procedimiento escrito de bloqueo que no "
                         "aplicó (47). ICMM: la ejecución inefectiva del control explicó 19 de 26 fatales de 2025 (40)."),
        ("Por qué aquí", "Es el caso del demo (ADR-0005): una correa a escala con su candado, su guarda y su energía. "
                         "Una parada de planta no programada cuesta USD 100.000 a 300.000 por hora según un proveedor "
                         "(REFERENCIAS 38, candidata a validar)."),
    ),
    pruebas="tests/test_mineria.py",
)

ELECTRICA = Industria(
    codigo="ELE", nombre="Eléctrica", pauta=DATOS / "pauta-celda-mt.json",
    tarea="Mantenimiento de interruptor en celda de media tensión",
    seguro=(("seccionador", "cerrado"), ("candado_mando", "abierto"), ("tension", "presente"),
            ("tierra", "retirada"), ("puerta_celda", "cerrada")),
    p1=PasoClave("seccionador", "abierto", "cerrado", "seccionador abierto"),
    p2=PasoClave("candado_mando", "cerrado", "abierto", "mando bloqueado"),
    hasta_camara=(("seccionador", "abierto"), ("candado_mando", "cerrado"), ("tension", "ausente"), ("tierra", "puesta")),
    paso_camara="p5", dice_camara="zona señalizada",
    peligro=Peligro("Puesta a tierra con tensión presente", (("tension", "presente"), ("tierra", "puesta")),
                    "Verificar la ausencia de tensión antes de instalar cualquier tierra (REFERENCIAS 50, 29 CFR 1910.269(n)(5); "
                    "REFERENCIAS 48, RD 614/2001 anexo II; REFERENCIAS 49, RPTD N°15 9.1.5)"),
    senal=Senal("temperatura_conexion", "°C", 45.0, 1.5, 80.0, "temperatura de la conexión del interruptor"),
    fuente_orden=("Cinco etapas en orden y ningún trabajo hasta completarlas (REFERENCIAS 48, RD 614/2001 anexo II A.1; "
                  "REFERENCIAS 49, RPTD N°15 9.1.5). Retirar las tierras en el orden equivocado fue el factor principal de "
                  "los accidentes con tierras (REFERENCIAS 51)"),
    recorrido=(
        {"lee": [["seccionador", "abierto"], ["candado_mando", "cerrado"], ["tension", "ausente"], ["tierra", "puesta"]]},
        {"cuadro": True}, {"dice": "zona señalizada"},
        {"lee": [["tierra", "retirada"], ["candado_mando", "abierto"], ["seccionador", "cerrado"], ["tension", "presente"]]},
        {"dice": "celda en servicio, confirmado con el centro de control"},
    ),
    trasfondo=(
        ("La norma", "Cinco etapas en orden: desconectar, prevenir la realimentación, verificar ausencia de tensión, "
                     "poner a tierra y en cortocircuito, y proteger; ningún trabajo hasta completarlas (RD 614/2001, "
                     "REFERENCIAS 48). La misma secuencia en Chile (RPTD N°15 de la SEC, 49). Verificar ausencia de "
                     "tensión antes de cualquier tierra, y no reenergizar con tierras puestas (29 CFR 1910.269, 50)."),
        ("Cuando falla", "Retirar las tierras en el orden equivocado fue el factor principal de los accidentes con "
                         "tierras, con fatales (OSHA citando a IBEW, REFERENCIAS 51). No encontramos una cifra primaria "
                         "que aísle el no verificar ausencia de tensión."),
        ("Por qué aquí", "El bloqueo evita la electrocución y es donde más literatura hay: 13 de los 42 papers de la "
                         "revisión IEEE son de eléctrica (CONTEXTO). El mismo flujo sirve en una subestación."),
    ),
    pruebas="tests/test_electrica.py",
)

CONSTRUCCION = Industria(
    codigo="CON", nombre="Construcción", pauta=DATOS / "pauta-excavadora.json",
    tarea="Cambio de manguera hidráulica en excavadora",
    seguro=(("implementos", "levantados"), ("motor", "encendido"), ("palanca_seguridad", "desbloqueada"),
            ("presion_hidraulica", "con_presion"), ("zona", "libre")),
    p1=PasoClave("implementos", "en_suelo", "levantados", "implementos abajo"),
    p2=PasoClave("motor", "apagado", "encendido", "motor apagado"),
    hasta_camara=(("implementos", "en_suelo"), ("motor", "apagado"), ("palanca_seguridad", "bloqueada"),
                  ("presion_hidraulica", "aliviada")),
    paso_camara="p5", dice_camara="manguera cambiada",
    peligro=Peligro("Persona en la zona con los implementos levantados", (("implementos", "levantados"), ("zona", "ocupada")),
                    "Nadie trabaja bajo una parte levantada que no esté calzada (REFERENCIAS 52, 29 CFR 1926.600(a)(3)(i))"),
    senal=Senal("temperatura_aceite", "°C", 60.0, 2.0, 95.0, "temperatura del aceite hidráulico"),
    fuente_orden=("Implementos abajo o bloqueados, mandos en neutro y motor detenido antes de reparar (REFERENCIAS 52, "
                  "29 CFR 1926.600(a)(3)(i)). Bloquear la palanca y aliviar la presión no tienen norma de construcción: "
                  "vienen del fabricante (1910.147 excluye la construcción)"),
    recorrido=(
        {"lee": [["implementos", "en_suelo"], ["motor", "apagado"], ["palanca_seguridad", "bloqueada"],
                 ["presion_hidraulica", "aliviada"]]},
        {"cuadro": True}, {"dice": "manguera cambiada"},
        {"lee": [["palanca_seguridad", "desbloqueada"], ["motor", "encendido"], ["presion_hidraulica", "con_presion"],
                 ["implementos", "levantados"]]},
        {"dice": "sin fugas en los mandos"},
    ),
    trasfondo=(
        ("La norma", "Cucharones y hojas totalmente abajo o bloqueados al reparar, mandos en neutro, motor detenido y "
                     "frenos puestos; nadie bajo una parte levantada sin calzar (29 CFR 1926.600(a)(3)(i), REFERENCIAS "
                     "52). Si la máquina opera en una mina, 30 CFR 56.14211 (53)."),
        ("Cuando falla", "Quedar atrapado o aplastado explicó 92 de 975 muertes en construcción en 2008, 9 % (OSHA "
                         "Focus Four, REFERENCIAS 54). El bloqueo y etiquetado es la tercera norma más citada por OSHA "
                         "en 2026, en industria general (55)."),
        ("Lo que no es norma", "Bloquear la palanca hidráulica, aliviar la presión y retirar la llave no tienen norma "
                               "de construcción: 29 CFR 1910.147 lo exige, pero excluye la construcción. Vienen del "
                               "fabricante (REFERENCIAS 52)."),
    ),
    pruebas="tests/test_construccion.py",
)

INDUSTRIAS = (MINERIA, ELECTRICA, CONSTRUCCION)


# ─── Patrones de ejecución ──────────────────────────────────────────────────


@dataclass(frozen=True)
class Patron:
    codigo: str
    grupo: str
    nombre: str
    barrera: int
    pregunta: str


GRUPOS = {
    "A": "Cuándo llega la evidencia de un paso",
    "B": "El orden de los pasos",
    "C": "Un control ya verificado se deshace",
    "D": "La lectura del sensor",
    "F": "La cámara",
    "G": "La señal",
}

PATRONES = (
    Patron("A0", "A", "La pauta completa, bien hecha", 1, "¿Las reglas dan alguna falsa alarma?"),
    Patron("A1", "A", "Lo hace y el sensor lo ve, sin hablar", 1, "¿El paso se cierra solo con la lectura?"),
    Patron("A2", "A", "El sensor lo ve y después lo dice", 1, "¿La declaración tardía se confunde con el paso siguiente?"),
    Patron("A3", "A", "Lo dice y después el sensor lo ve", 1, "¿Interrumpe por una diferencia de segundos?"),
    Patron("A4", "A", "Lo dice y el sensor nunca lo confirma", 1, "¿El paso queda en conflicto y a la vista?"),
    Patron("A5", "A", "Dice que hizo el paso siguiente sin hacer este", 1, "¿Se detecta que se lo saltó?"),
    Patron("B1", "B", "Se salta el paso y hace el siguiente", 1, "¿La pauta avanza igual?"),
    Patron("B2", "B", "Se salta el paso, hace el siguiente y vuelve a hacerlo", 1, "¿Queda registro del orden invertido?"),
    Patron("B3", "B", "Se salta el paso y crea la condición de peligro", 1, "¿Suena la alerta de seguridad?"),
    Patron("C1", "C", "Deshace un control crítico ya verificado", 1, "¿Se avisa que el control se perdió?"),
    Patron("C2", "C", "Deshace el control y se crea la condición de peligro", 1, "¿Suena la alerta de seguridad?"),
    Patron("D1", "D", "El sensor repite la misma lectura", 1, "¿Se cuenta una sola vez?"),
    Patron("D3", "D", "El sensor deja de mandar lecturas", 1, "¿Baja la certeza de lo que dice?"),
    Patron("F1", "F", "La cámara confirma con confianza alta", 3, "¿El paso se cierra sin aviso?"),
    Patron("F2", "F", "La cámara confirma con confianza baja", 3, "¿Se cierra pero pide que alguien mire?"),
    Patron("F3", "F", "La cámara contradice al operario", 3, "¿Queda en conflicto sin interrumpir?"),
    Patron("F4", "F", "No hay video y el juez dice que sí", 3, "¿Se acepta un sí sin cuadro?"),
    Patron("F5", "F", "La cámara dice que sí y un sensor marca peligro", 3, "¿Un modelo contradice a un sensor?"),
    Patron("G1", "G", "Un pico aislado", 2, "¿Avisa una vez y se resuelve?"),
    Patron("G2", "G", "Un escalón que se sostiene", 2, "¿El aviso dura lo que dura la falla?"),
    Patron("G3", "G", "Una deriva lenta", 2, "¿Se detecta antes del daño?"),
    Patron("G4", "G", "Ruido normal, sin falla", 2, "¿Da falsas alarmas?"),
    Patron("G5", "G", "Un sensor pegado que se mueve apenas", 2, "¿Confunde un sensor quieto con una falla?"),
)
PATRON = {p.codigo: p for p in PATRONES}


# ─── Escenario ──────────────────────────────────────────────────────────────

Paso = dict  # {"lee": [[sensor, valor], ...]} · {"dice": texto} · {"juez": [sí, confianza] | "stub"} · {"cuadro": True} · {"pasa": s}


@dataclass
class Escenario:
    id: str
    industria: Industria
    patron: Patron
    dado: str
    cuando: str
    entonces: str
    pasos: list[Paso]
    espera: dict
    fuente: str
    brecha: str | None = None
    nota: str | None = None
    inicio: tuple[tuple[str, str], ...] = ()
    juez: object = field(default=(True, 0.9))

    def como_dict(self) -> dict:
        return {
            "id": self.id,
            "industria": {"codigo": self.industria.codigo, "nombre": self.industria.nombre, "tarea": self.industria.tarea},
            "patron": {"codigo": self.patron.codigo, "grupo": self.patron.grupo, "grupo_nombre": GRUPOS[self.patron.grupo],
                       "nombre": self.patron.nombre, "pregunta": self.patron.pregunta},
            "barrera": {"capa": self.patron.barrera, "nombre": BARRERAS[self.patron.barrera]},
            "dado": self.dado, "cuando": self.cuando, "entonces": self.entonces,
            "pasos": self.pasos, "espera": self.espera, "fuente": self.fuente,
            "brecha": self.brecha, "nota": self.nota,
        }


def _lee(*pares: tuple[str, str]) -> Paso:
    return {"lee": [list(p) for p in pares]}


def _serie(s: Senal, n: int, semilla: int) -> list[float]:
    azar = random.Random(semilla)
    return [round(azar.gauss(s.media, s.desvio), 2) for _ in range(n)]


_fuente_reversion = {
    "MIN": "Las protecciones se reponen antes de volver a servicio (REFERENCIAS 44, DS 132 art. 52)",
    "ELE": "No se energiza mientras haya tierras o bloqueos, y se repone en orden inverso (REFERENCIAS 48, RD 614 anexo II A.2; REFERENCIAS 50, 1910.269(m)(3)(xiii))",
    "CON": "Implementos abajo o bloqueados mientras dura la reparación (REFERENCIAS 52, 29 CFR 1926.600(a)(3)(i))",
}


def escenarios_de(i: Industria) -> list[Escenario]:
    p1, p2, s = i.p1, i.p2, i.senal
    base = _serie(s, 12, semilla=7)
    E = lambda codigo, **k: Escenario(id=f"{i.codigo}-{codigo}", industria=i, patron=PATRON[codigo], inicio=i.seguro, **k)  # noqa: E731

    lista = [
        E("A0", dado="la OT abierta y los sensores en estado seguro", cuando="el operario hace cada paso en orden y lo cierra su evidencia",
          entonces="la pauta queda completa sin alertas, sin conflictos y sin interrumpir nunca",
          pasos=list(i.recorrido),
          espera={"paso_actual": None, "alertas_capa1": 0, "conflictos": 0, "interrupciones": 0, "nivel_maximo": "ok"},
          fuente="El control de las reglas: un aviso falso repetido enseña a ignorar el aviso (LOGICA)"),
        E("A1", dado=f"el paso «{p1.sensor}» en curso", cuando=f"llega {p1.sensor} = {p1.hecho} y el operario no dice nada",
          entonces="el paso queda verificado por la capa 1 y la pauta avanza",
          pasos=[_lee((p1.sensor, p1.hecho))],
          espera={"estados": {"p1": "verificado"}, "paso_actual": "p2", "nivel": "ok", "interrupciones": 0},
          fuente="Un paso de sensor lo cierra la lectura (LOGICA; ADR-0004)"),
        E("A2", dado="el sensor ya cerró el paso 1", cuando=f"el operario dice «{p1.dice}» un momento después",
          entonces="la declaración queda registrada y no abre ningún conflicto",
          pasos=[_lee((p1.sensor, p1.hecho)), {"dice": p1.dice, "paso": "p1"}],
          espera={"estados": {"p1": "verificado", "p2": "no_verificado"}, "conflictos": 0, "interrupciones": 0, "nivel_maximo": "ok"},
          fuente="Un paso de sensor nunca se cierra hablando; la palabra se guarda como declarado (LOGICA). La app manda el paso que mostraba"),
        E("A3", dado="el paso 1 en curso", cuando=f"el operario dice «{p1.dice}» y el sensor llega un momento después",
          entonces="el conflicto queda en la bitácora y el paso se verifica al llegar la lectura",
          pasos=[{"dice": p1.dice}, _lee((p1.sensor, p1.hecho))],
          espera={"estados": {"p1": "verificado"}, "conflictos": 1, "interrupciones": 1, "nivel": "ok"},
          fuente="Un paso en conflicto sale del conflicto cuando llega evidencia nueva que lo cierra (LOGICA)",
          nota="Conforme a LOGICA, pero interrumpe al operario por una diferencia de segundos. ¿Hace falta una ventana de gracia? Candidata a validar."),
        E("A4", dado="el paso 1 en curso", cuando=f"el operario dice «{p1.dice}» y {p1.sensor} sigue en {p1.sin_hacer}",
          entonces="el paso queda en conflicto, la OT en error y la pauta no avanza",
          pasos=[_lee((p1.sensor, p1.sin_hacer)), {"dice": p1.dice}],
          espera={"estados": {"p1": "en_conflicto"}, "paso_actual": "p1", "nivel": "error", "interrupciones": 1},
          fuente="Si el operario declara y el sensor dice otra cosa, el paso queda en conflicto y no se cierra (LOGICA)"),
        E("A5", dado="el paso 1 sin hacer", cuando=f"el operario dice «{p2.dice}», que es el paso siguiente",
          entonces="la palabra se evalúa contra el paso 1, que queda en conflicto",
          pasos=[{"dice": p2.dice}],
          espera={"estados": {"p1": "en_conflicto"}, "paso_actual": "p1", "nivel": "error"},
          fuente="La app pregunta por un paso a la vez y evalúa solo el actual (ADR-0002)"),
        E("B1", dado="el paso 1 sin hacer", cuando=f"llega {p2.sensor} = {p2.hecho}, que cierra el paso 2",
          entonces="la pauta no avanza y entra una alerta de orden invertido",
          pasos=[_lee((p2.sensor, p2.hecho))],
          espera={"estados": {"p1": "no_verificado", "p2": "no_verificado"}, "paso_actual": "p1", "desviaciones_de_orden": 1},
          fuente=f"El orden lo impone la aplicación; un VLM detectó 3 de 12 cambios de orden (ADR-0002; REFERENCIAS 9). {i.fuente_orden}"),
        E("B2", dado="el paso 1 sin hacer", cuando=f"el operario hace el paso 2 ({p2.sensor} = {p2.hecho}) y después el 1",
          entonces="la bitácora registra que el orden se invirtió, y la alerta se resuelve al hacer el paso saltado",
          pasos=[_lee((p2.sensor, p2.hecho)), _lee((p1.sensor, p1.hecho))],
          espera={"desviaciones_de_orden": 1, "estados": {"p1": "verificado"}, "alertas_abiertas": 0, "nivel_maximo": "error"},
          fuente=f"El orden lo comprueba la capa 1 con las marcas de tiempo (LOGICA). {i.fuente_orden}"),
        E("B3", dado="el paso 1 sin hacer", cuando=f"se da la condición «{i.peligro.regla.lower()}»",
          entonces="entra una alerta de capa 1 que interrumpe",
          pasos=[_lee(*i.peligro.lecturas)],
          espera={"alertas_seguridad": {"min": 1}, "nivel": "error", "interrupciones": {"min": 1}},
          fuente=i.peligro.fuente),
        E("C1", dado="los pasos 1 y 2 verificados", cuando=f"{p1.sensor} vuelve a {p1.sin_hacer}",
          entonces="entra una alerta de capa 1: el control crítico se perdió, y se resuelve al reponerlo",
          pasos=[_lee((p1.sensor, p1.hecho), (p2.sensor, p2.hecho)), _lee((p1.sensor, p1.sin_hacer)),
                 _lee((p1.sensor, p1.hecho))],
          espera={"controles_deshechos": 1, "desviaciones_de_orden": 0, "nivel_maximo": "error", "alertas_abiertas": 0},
          fuente=(f"El paso es control crítico (LOGICA). La ejecución inefectiva del control explicó 19 de 26 fatales ICMM "
                  f"(REFERENCIAS 40). {_fuente_reversion[i.codigo]}")),
        E("C2", dado="los pasos 1 y 2 verificados", cuando=f"{p1.sensor} vuelve a {p1.sin_hacer} y se da «{i.peligro.regla.lower()}»",
          entonces="entra una alerta de capa 1 que interrumpe",
          pasos=[_lee((p1.sensor, p1.hecho), (p2.sensor, p2.hecho)), _lee((p1.sensor, p1.sin_hacer), *i.peligro.lecturas)],
          espera={"alertas_seguridad": {"min": 1}, "controles_deshechos": 1, "nivel": "error"},
          fuente=i.peligro.fuente),
        E("D1", dado="el paso 1 en curso", cuando=f"llega {p1.sensor} = {p1.hecho} tres veces",
          entonces="hay un solo veredicto",
          pasos=[_lee((p1.sensor, p1.hecho), (p1.sensor, p1.hecho), (p1.sensor, p1.hecho))],
          espera={"verificados_por_paso": {"p1": 1}},
          fuente="La bitácora registra lo que pasó, no cada lectura (ADR-0007)"),
        E("D3", dado="el paso 1 verificado por su sensor", cuando="pasan 8 s sin lecturas",
          entonces="la calificación baja a warning: el sensor puede haberse caído",
          pasos=[_lee((p1.sensor, p1.hecho)), {"pasa": 8}],
          espera={"nivel": "warning"},
          fuente="Capa 1: certeza total mientras la lectura esté fresca, 5 s (scoring.py; ADR-0007). Candidata a validar"),
    ]

    camino = [_lee(*i.hasta_camara), {"cuadro": True}]
    lista += [
        E("F1", dado=f"el paso de cámara {i.paso_camara} en curso, con video", cuando="el juez responde que sí con 90 %",
          entonces="el paso se verifica sin avisos", juez=(True, 0.9),
          pasos=[*camino, {"dice": i.dice_camara}],
          espera={"estados": {i.paso_camara: "verificado"}, "nivel": "ok", "interrupciones": 0},
          fuente="La capa 3 responde la pregunta visual del paso (LOGICA; ADR-0004)"),
        E("F2", dado=f"el paso de cámara {i.paso_camara} en curso, con video", cuando="el juez responde que sí con 60 %",
          entonces="el paso se verifica, la OT queda en warning y no interrumpe", juez=(True, 0.6),
          pasos=[*camino, {"dice": i.dice_camara}],
          espera={"estados": {i.paso_camara: "verificado"}, "nivel": "warning", "interrupciones": 0},
          fuente="Bajo 75 % de confianza conviene que alguien mire (scoring.py). Umbral candidato a validar"),
        E("F3", dado=f"el paso de cámara {i.paso_camara} en curso, con video", cuando=f"el operario dice «{i.dice_camara}» y el juez responde que no",
          entonces="el paso queda en conflicto con warning, sin interrumpir", juez=(False, 0.85),
          pasos=[*camino, {"dice": i.dice_camara}],
          espera={"estados": {i.paso_camara: "en_conflicto"}, "nivel": "warning", "interrupciones": 0},
          fuente="Lo que detecta la cámara se muestra y no suena: un VLM rechazó 5 de 12 ejecuciones correctas (LOGICA; REFERENCIAS 9)"),
        E("F4", dado=f"el paso de cámara {i.paso_camara} en curso, sin video", cuando="el juez de hoy responde",
          entonces="el paso no se verifica: no hubo cuadro que mirar", juez="stub",
          pasos=[_lee(*i.hasta_camara), {"dice": i.dice_camara}],
          espera={"estados": {i.paso_camara: "no_verificado"}, "nivel": "warning"},
          fuente="Un paso de cámara se juzga con el último cuadro del edge (ADR-0007)"),
        E("F5", dado=f"el paso de cámara {i.paso_camara} en curso, con video", cuando=f"el juez dice que sí con 95 % y se da «{i.peligro.regla.lower()}»",
          entonces="la OT queda en error por la capa 1, aunque la cámara diga que todo está bien", juez=(True, 0.95),
          pasos=[*camino, {"dice": i.dice_camara}, _lee(*i.peligro.lecturas)],
          espera={"estados": {i.paso_camara: "verificado"}, "alertas_seguridad": {"min": 1}, "nivel": "error"},
          fuente="Un modelo nunca contradice a un sensor (ADR-0004)"),
    ]

    alto = round(s.media + 8 * s.desvio, 2)
    lista += [
        E("G1", dado=f"12 lecturas normales de {s.que_mide} ({s.media:g} {s.unidad})", cuando=f"llega un pico de {s.pico:g} {s.unidad} y después un valor normal",
          entonces="entra una alerta de capa 2 una vez, se resuelve y la OT nunca pasa de warning",
          pasos=[_lee(*[(s.sensor, str(v)) for v in base]), _lee((s.sensor, str(s.pico))), _lee((s.sensor, str(s.media)))],
          espera={"anomalias": 1, "resueltas": 1, "alertas_abiertas": 0, "nivel": "ok", "nivel_maximo": "warning", "interrupciones": 0},
          fuente="La capa 2 detecta anomalías, se muestra y no interrumpe (ADR-0004; ADR-0007)"),
        E("G2", dado=f"12 lecturas normales de {s.que_mide}", cuando=f"la señal sube a {alto:g} {s.unidad} y se queda ahí 30 lecturas",
          entonces="la alerta sigue abierta mientras la señal no vuelva",
          pasos=[_lee(*[(s.sensor, str(v)) for v in base]),
                 _lee(*[(s.sensor, str(v)) for v in _serie(Senal(s.sensor, s.unidad, alto, s.desvio, 0, ""), 30, 11)])],
          espera={"anomalias": 1, "alertas_abiertas": 1, "nivel": "warning"},
          fuente="Un aviso vive mientras dure su condición (PRD servicios en vivo, O5)"),
        E("G3", dado=f"12 lecturas normales de {s.que_mide}", cuando=f"la señal sube {s.desvio / 2:g} {s.unidad} por lectura durante 40 lecturas",
          entonces="entra una alerta de capa 2 antes de que termine la subida",
          pasos=[_lee(*[(s.sensor, str(v)) for v in base]),
                 _lee(*[(s.sensor, str(round(s.media + (k + 1) * s.desvio / 2, 2))) for k in range(40)])],
          espera={"anomalias": {"min": 1}},
          fuente="Detectar la falla antes del daño es para qué está la capa 2 (ADR-0004). Algoritmo: Brecha"),
        E("G4", dado=f"{s.que_mide} normal", cuando="llegan 60 lecturas con su ruido normal",
          entonces="no entra ninguna alerta",
          pasos=[_lee(*[(s.sensor, str(v)) for v in _serie(s, 60, 23)])],
          espera={"anomalias": 0, "sensores_pegados": 0},
          fuente="Un aviso falso repetido le enseña al operario a ignorar el aviso (LOGICA)"),
        E("G5", dado=f"15 lecturas idénticas de {s.que_mide}", cuando=f"llega una que se mueve {s.desvio / 10:g} {s.unidad}",
          entonces="avisa que el sensor está pegado, no confunde el movimiento mínimo con una falla, y el aviso se va cuando vuelve a variar",
          pasos=[_lee(*[(s.sensor, str(s.media))] * 15), _lee((s.sensor, str(round(s.media + s.desvio / 10, 3))))],
          espera={"anomalias": 0, "sensores_pegados": 1, "alertas_abiertas": 0},
          fuente="Un sensor pegado es una falla del sensor, no del equipo (scoring.py; simulación de capa 2)"),
    ]
    return lista


RAIZ = DATOS.parent

SERVICIOS = {
    "recibir_lectura": ("servicios.recibir_lectura", "atribuye la lectura a la OT de la sesión"),
    "seguridad": ("reglas.reglas_seguridad", "el peligro de la industria, con cada lectura"),
    "paso": ("reglas.evaluar", "¿la lectura cierra el paso actual?"),
    "control": ("reglas.controles_deshechos", "¿se deshizo un control crítico?"),
    "orden": ("reglas.desviacion_de_orden", "¿se saltó un control crítico?"),
    "senal": ("scoring.capa2", "desvío contra la historia normal"),
    "pegado": ("servicios._pegado", "diez lecturas idénticas seguidas"),
    "declarar": ("servicios.declarar", "lo que dice el operario, contra su paso"),
    "juez": ("verificacion.juez_camara", "la pregunta visual, con el último cuadro"),
    "calificacion": ("scoring.calificacion", "ok · warning · error, con motivos"),
    "bus": ("bus.publicar", "lo nuevo sale por el stream de la OT"),
}
CONTROLADORES = {
    "preparar": ["POST /pautas", "POST /ot/{id}/abrir", "POST /ot/{id}/sesion"],
    "lee": ["POST /edge/{id}/lecturas"],
    "dice": ["POST /ot/{id}/declarar"],
    "cuadro": ["POST /edge/{id}/cuadro"],
    "pasa": [],
    "juez": [],
}
TABLAS = {
    "pautas": "la pauta y su versión",
    "ots": "la OT y la versión que ejecuta",
    "sesiones": "qué OT ejecuta cada edge",
    "sensores": "el último valor de cada sensor",
    "eventos": "la bitácora: solo agrega",
    "video": "los últimos 10 s de cuadros, en memoria",
}


# Los nombres de los tests van sin tildes porque son identificadores; en pantalla se leen con ellas.
_TILDES = {
    "bitacora": "bitácora", "camara": "cámara", "despues": "después", "energia": "energía", "escalon": "escalón",
    "perdio": "perdió", "presion": "presión", "reparacion": "reparación", "senalizacion": "señalización",
    "tension": "tensión", "vibracion": "vibración", "video": "video", "solo": "solo", "si": "si",
}


def _legible(nombre: str) -> str:
    return " ".join(_TILDES.get(w, w) for w in nombre.split("_"))


def tests_de(i: Industria) -> list[dict]:
    """Los casos de uso del archivo de tests de la industria, con el escenario que corre cada uno."""
    import re

    ruta = RAIZ / i.pruebas
    if not ruta.exists():
        return []
    texto = ruta.read_text(encoding="utf-8")
    salida = []
    for m in re.finditer(r"def test_(\w+)\(self\):\n(.*?)(?=\n    def |\n\nif __name__|\Z)", texto, re.S):
        nombre, cuerpo = m.group(1), m.group(2)
        base = re.search(r'self\.corre\("(\w+)"(, \w+)?\)', cuerpo)
        propio = re.match(r"([a-g]\d)_", nombre)
        salida.append({
            "nombre": f"test_{nombre}",
            "titulo": _legible(nombre[len(propio.group(0)):] if propio else nombre),
            "patron": propio.group(1).upper() if propio else None,
            "escenario": f"{i.codigo}-{base.group(1)}" if base and not base.group(2) else None,
            "variante_de": f"{i.codigo}-{base.group(1)}" if base and base.group(2) else None,
        })
    return salida


def industria_dict(i: Industria) -> dict:
    from app.reglas import _PELIGROS

    pauta = protocolos.desde_json(i.pauta)
    sensores: dict[str, set[str]] = {}
    for nombre, valor in [*i.seguro, *i.peligro.lecturas]:
        sensores.setdefault(nombre, set()).add(valor)
    for paso in pauta.pasos:
        if paso.sensor:
            sensores.setdefault(paso.sensor.id, set()).add(paso.sensor.espera)
    propios = set(sensores)
    return {
        "codigo": i.codigo, "nombre": i.nombre, "tarea": i.tarea, "equipo": pauta.equipo,
        "pauta": {"id": pauta.id, "nombre": pauta.nombre, "version": pauta.version, "pasos": [
            {"id": p.id, "titulo": p.titulo, "tipo_evidencia": str(p.tipo_evidencia), "control_critico": p.control_critico,
             "sensor": {"id": p.sensor.id, "espera": p.sensor.espera} if p.sensor else None,
             "pregunta_visual": p.pregunta_visual} for p in pauta.en_orden]},
        "sensores": {k: sorted(v) for k, v in sorted(sensores.items())},
        "senal": {"sensor": i.senal.sensor, "unidad": i.senal.unidad, "que_mide": i.senal.que_mide},
        "reglas": [
            *[{"regla": aviso.split(".")[0].capitalize(), "condicion": cond, "fuente": fuente}
              for cond, aviso, fuente in _PELIGROS if set(cond) <= propios],
            {"regla": "Orden invertido", "condicion": "cierra un paso posterior con un control crítico pendiente",
             "fuente": i.fuente_orden},
            {"regla": "Control crítico deshecho", "condicion": "un control crítico verificado vuelve atrás",
             "fuente": _fuente_reversion[i.codigo]},
        ],
        "trasfondo": [{"titulo": t, "texto": x} for t, x in i.trasfondo],
        "pruebas": i.pruebas,
        "tests": tests_de(i),
    }


def arquitectura() -> dict:
    return {
        "controladores": sorted({c for v in CONTROLADORES.values() for c in v} | {"WS /ot/{id}/stream"},
                                key=lambda c: list(CONTROLADORES_ORDEN).index(c) if c in CONTROLADORES_ORDEN else 99),
        "servicios": [{"id": k, "funcion": f, "que": q} for k, (f, q) in SERVICIOS.items()],
        "tablas": [{"id": k, "que": q} for k, q in TABLAS.items()],
    }


CONTROLADORES_ORDEN = ("POST /pautas", "POST /ot/{id}/abrir", "POST /ot/{id}/sesion", "POST /edge/{id}/lecturas",
                       "POST /ot/{id}/declarar", "POST /edge/{id}/cuadro", "WS /ot/{id}/stream")


def catalogo() -> list[Escenario]:
    return [e for i in INDUSTRIAS for e in escenarios_de(i)]


def buscar(escenario_id: str) -> Escenario:
    for e in catalogo():
        if e.id == escenario_id:
            return e
    raise KeyError(f"escenario {escenario_id}")


# ─── La caja aislada ────────────────────────────────────────────────────────


class _Captura(Bus):
    def __init__(self) -> None:
        super().__init__()
        self.mensajes: list[dict] = []

    def publicar(self, canal: str, mensaje: dict) -> None:
        if canal == canal_ot(OT):
            self.mensajes.append(mensaje)


def _peor(a: str, b: str) -> str:
    return a if _GRAVEDAD[Nivel(a)] >= _GRAVEDAD[Nivel(b)] else b


def _cumple(esperado: object, obtenido: object) -> bool:
    if isinstance(esperado, dict) and "min" in esperado:
        return isinstance(obtenido, (int, float)) and obtenido >= esperado["min"]
    if isinstance(esperado, dict):
        return isinstance(obtenido, dict) and all(_cumple(v, obtenido.get(k)) for k, v in esperado.items())
    return esperado == obtenido


def correr(e: Escenario) -> dict:
    cx = db.conectar(":memory:")
    pauta = protocolos.desde_json(e.industria.pauta)
    db.guardar_pauta(cx, pauta)
    db.abrir_ot(cx, OT, pauta, "supervisor:escenario")
    juez_actual: list[object] = [e.juez]

    def juez(pregunta: str, cuadro: bytes | None) -> tuple[bool, float]:
        j = juez_actual[0]
        if j == "stub":
            return verificacion.juez_camara(pregunta, cuadro)
        assert isinstance(j, tuple)
        return j

    with tempfile.TemporaryDirectory() as tmp:
        bus = _Captura()
        s = Servicios(cx, bus, Video(Path(tmp)), juez)
        for sensor, valor in e.inicio:
            db.escribir_sensor(cx, sensor, valor)
        s.iniciar_sesion(OT, EDGE, OPERARIO)
        recorrido = [{
            "accion": "preparar", "texto": f"pauta {pauta.id} aprobada, OT abierta y sesión con el edge",
            "controladores": CONTROLADORES["preparar"], "corren": [], "disparan": [],
            "tablas": ["pautas", "ots", "eventos", "sesiones", "sensores"], "eventos": _nuevos(cx, 0),
            "nivel": s.calificacion(OT)["nivel"],
        }]
        error, seq = None, 0
        try:
            for paso in e.pasos:
                antes = _ultimo_id(cx)
                if "lee" in paso:
                    for sensor, valor in paso["lee"]:
                        seq += 1
                        s.recibir_lectura(EDGE, sensor, str(valor), seq)
                elif "dice" in paso:
                    s.declarar(OT, OPERARIO, paso["dice"], paso.get("paso"))
                elif "juez" in paso:
                    juez_actual[0] = paso["juez"] if paso["juez"] == "stub" else tuple(paso["juez"])
                elif "cuadro" in paso:
                    s.video.recibir(EDGE, JPEG)
                elif "pasa" in paso:
                    _envejecer_sensores(cx, paso["pasa"])
                recorrido.append(_tramo(cx, s, paso, antes))
        except Exception as x:  # noqa: BLE001 — un escenario que revienta se informa, no corta el resto
            error = f"{type(x).__name__}: {x}"
        obtenido = _medir(cx, s, pauta, bus)
        trazas = {
            "bitacora": [evento_dict(ev) for ev in db.eventos(cx, OT)],
            "stream": bus.mensajes,
            "recorrido": recorrido,
        }
        cx.close()

    comparacion = {k: {"esperado": v, "obtenido": obtenido.get(k), "cumple": _cumple(v, obtenido.get(k))}
                   for k, v in e.espera.items()}
    cumple = error is None and all(c["cumple"] for c in comparacion.values())
    if e.brecha:
        sello = "brecha_cerrada" if cumple else "brecha"
    else:
        sello = "pasa" if cumple else "falla"
    return {**e.como_dict(), "cumple": cumple, "sello": sello, "error": error,
            "comparacion": comparacion, "obtenido": obtenido, **trazas}


def _ultimo_id(cx) -> int:
    return cx.execute("SELECT COALESCE(MAX(id), 0) FROM eventos").fetchone()[0]


def _nuevos(cx, desde: int) -> list[dict]:
    salida = []
    for ev in db.eventos(cx, OT):
        if (ev.id or 0) > desde:
            c = calificar_evento(ev)
            salida.append({"id": ev.id, "tipo": str(ev.tipo), "paso_id": ev.paso_id, "capa": ev.capa,
                           "estado": str(ev.estado) if ev.estado else None,
                           "clase": str((ev.evidencia or {}).get("clave", "")).split(":")[0] or None,
                           "detalle": ev.detalle, "nivel": str(c.nivel) if c else None})
    return salida


def _tramo(cx, s: Servicios, paso: Paso, antes: int) -> dict:
    """Por dónde pasó un paso del escenario: controlador, servicios que corrieron y los que dispararon, tablas."""
    eventos = _nuevos(cx, antes)
    accion = next(k for k in ("lee", "dice", "cuadro", "pasa", "juez") if k in paso)
    disparan: list[str] = []
    for ev in eventos:
        clave = ev["clase"]
        if ev["tipo"] in ("alerta", "alerta_resuelta") and clave:
            disparan.append({"senal": "senal"}.get(clave, clave))
        elif ev["tipo"] == "veredicto":
            disparan += ["paso"] if accion == "lee" else ["declarar", *(["juez"] if ev["capa"] == Capa.MODELO else [])]
        elif ev["tipo"] == "declaracion":
            disparan.append("declarar")
    if accion == "lee":
        lecturas = paso["lee"]
        numerica = any(_es_numero(v) for _, v in lecturas)
        corren = ["recibir_lectura", "seguridad", "paso", "control", "orden",
                  *(["senal", "pegado"] if numerica else []), "calificacion", "bus"]
        sensores = sorted({k for k, _ in lecturas})
        texto = (f"{len(lecturas)} lecturas de {', '.join(sensores)}" if len(lecturas) > 4
                 else ", ".join(f"{k} = {v}" for k, v in lecturas))
        tablas = ["sesiones", "sensores", *(["eventos"] if eventos else [])]
    elif accion == "dice":
        corren = ["declarar", "paso", "calificacion", "bus"]
        texto = f"el operario dice «{paso['dice']}»" + (f" sobre {paso['paso']}" if paso.get("paso") else "")
        tablas = ["sensores", "eventos"] + (["video"] if "juez" in disparan else [])
        if "juez" in disparan:
            corren.insert(1, "juez")
    elif accion == "cuadro":
        corren, texto, tablas = [], "llega un cuadro de la cámara", ["video"]
    elif accion == "pasa":
        corren, texto, tablas = ["calificacion"], f"pasan {paso['pasa']} s sin lecturas", ["sensores"]
    else:
        corren, texto, tablas = [], "cambia lo que responde el juez", []
    return {
        "accion": accion, "texto": texto, "controladores": CONTROLADORES[accion],
        "corren": corren, "disparan": list(dict.fromkeys(disparan)), "tablas": tablas,
        "eventos": eventos, "nivel": s.calificacion(OT)["nivel"],
    }


def _es_numero(v: object) -> bool:
    try:
        float(v)
        return True
    except (TypeError, ValueError):
        return False


def _envejecer_sensores(cx, segundos: float) -> None:
    """Solo en la base en memoria de la caja: la lectura parece tener `segundos` más."""
    for f in cx.execute("SELECT id, ts FROM sensores").fetchall():
        ts = datetime.fromisoformat(f["ts"]) - timedelta(seconds=segundos)
        cx.execute("UPDATE sensores SET ts = ? WHERE id = ?", (ts.isoformat(timespec="seconds"), f["id"]))
    cx.commit()


def _medir(cx, s: Servicios, pauta, bus: _Captura) -> dict:
    evs = db.eventos(cx, OT)
    estados = estados_desde_eventos(evs)
    actual = paso_actual(pauta, estados)
    calif = s.calificacion(OT)
    niveles = [m["calificacion"]["nivel"] for m in bus.mensajes if m["tipo"] == "calificacion_ot"] + [calif["nivel"]]
    maximo = "ok"
    for n in niveles:
        maximo = _peor(maximo, n)
    alertas = [ev for ev in evs if ev.tipo is TipoEvento.ALERTA]
    de_clase = lambda clase: sum(1 for a in alertas if str((a.evidencia or {}).get("clave", "")).startswith(clase))  # noqa: E731
    verificados: dict[str, int] = {}
    for ev in evs:
        if ev.tipo is TipoEvento.VEREDICTO and ev.estado is Estado.VERIFICADO and ev.paso_id:
            verificados[ev.paso_id] = verificados.get(ev.paso_id, 0) + 1
    return {
        "estados": {p.id: str(estados.get(p.id, Estado.NO_VERIFICADO)) for p in pauta.en_orden},
        "paso_actual": actual.id if actual else None,
        "nivel": calif["nivel"],
        "nivel_maximo": maximo,
        "avisos": [a["motivos"][0] for a in calif["avisos"]],
        "alertas_capa1": sum(1 for a in alertas if a.capa == Capa.DETERMINISTA),
        "alertas_capa2": sum(1 for a in alertas if a.capa == Capa.APRENDIZAJE),
        "alertas_abiertas": len(s.alertas_activas(OT)),
        "resueltas": sum(1 for ev in evs if ev.tipo is TipoEvento.ALERTA_RESUELTA),
        "alertas_seguridad": de_clase("seguridad:"),
        "desviaciones_de_orden": de_clase("orden:"),
        "controles_deshechos": de_clase("control:"),
        "anomalias": de_clase("senal:"),
        "sensores_pegados": de_clase("pegado:"),
        "conflictos": sum(1 for ev in evs if ev.tipo is TipoEvento.VEREDICTO and ev.estado is Estado.EN_CONFLICTO),
        "interrupciones": sum(1 for ev in evs if (c := calificar_evento(ev)) and c.nivel is Nivel.ERROR
                              and ev.tipo is not TipoEvento.ALERTA_RESUELTA),
        "verificados_por_paso": verificados,
    }


def correr_todos(filtro: Callable[[Escenario], bool] = lambda _: True) -> list[dict]:
    return [correr(e) for e in catalogo() if filtro(e)]
