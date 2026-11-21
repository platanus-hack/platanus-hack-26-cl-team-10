"""Simulación de la capa 2: qué detector de anomalías aguanta qué patrón de falla, por industria.

Correr:  python3 scripts/simular_capa2.py [--semillas 40] [--md ruta.md]
Sin dependencias. Las señales son SINTÉTICAS: sirven para descartar detectores que
fallan en patrones conocidos (un escalón que se absorbe, una deriva que no se ve, un
ciclo de carga que dispara falsas alarmas), no para calibrar umbrales. Calibrar pide
datos reales del ensayo. Ver knowledge/projects/escenarios-por-industria/PRD.md.

Cada detector recibe una lectura a la vez y dice si la alarma está encendida, igual
que el servicio: la alarma se abre cuando el detector marca y se cierra cuando deja
de marcar.
"""

from __future__ import annotations

import argparse
import math
import random
import sys
from dataclasses import dataclass
from datetime import date
from pathlib import Path
from statistics import median

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app.scoring import DESVIO_WARNING, Nivel, capa2  # noqa: E402

LARGO = 800
HISTORIA_MAX = 300


@dataclass(frozen=True)
class Senal:
    industria: str
    que: str
    unidad: str
    media: float
    desvio: float
    ciclo_amplitud: float
    ciclo_periodo: int

    @property
    def calibracion(self) -> int:
        """La línea base tiene que cubrir al menos dos ciclos de trabajo, o el ciclo parece falla."""
        return max(60, 2 * self.ciclo_periodo if self.ciclo_amplitud else 0)


SENALES = (
    Senal("Minería", "vibración del rodillo", "mm/s", 2.0, 0.12, 0.0, 1),
    Senal("Eléctrica", "temperatura de la conexión", "°C", 45.0, 1.5, 4.5, 120),
    Senal("Construcción", "temperatura del aceite hidráulico", "°C", 60.0, 2.0, 4.0, 40),
)

FALLAS = {
    "sin_falla": "Sin falla: solo ruido y el ciclo de trabajo",
    "pico": "Pico aislado de 8 desvíos",
    "escalon": "Escalón de 8 desvíos que se sostiene 200 lecturas, hasta que alguien lo repara",
    "deriva": "Deriva de 0,1 desvíos por lectura durante 80 lecturas",
    "pegado": "Sensor pegado en un valor 40 lecturas (falla del sensor, no del equipo)",
}


def generar(s: Senal, falla: str, azar: random.Random) -> tuple[list[float], range]:
    x = [s.media + s.ciclo_amplitud * math.sin(2 * math.pi * t / s.ciclo_periodo) + azar.gauss(0, s.desvio)
         for t in range(LARGO)]
    inicio = azar.randint(s.calibracion + 60, s.calibracion + 260)
    if falla == "pico":
        x[inicio] += 8 * s.desvio
        return x, range(inicio, inicio + 1)
    if falla == "escalon":
        for t in range(inicio, inicio + 200):
            x[t] += 8 * s.desvio
        return x, range(inicio, inicio + 200)
    if falla == "deriva":
        for k, t in enumerate(range(inicio, inicio + 80)):
            x[t] += 0.1 * s.desvio * (k + 1)
        return x, range(inicio, inicio + 80)
    if falla == "pegado":
        for t in range(inicio, inicio + 40):
            x[t] = round(x[inicio], 1)
        return x, range(inicio, inicio + 40)
    return x, range(0)


# ─── Detectores ─────────────────────────────────────────────────────────────


class Detector:
    nombre = ""
    explicacion = ""

    def marca(self, x: float) -> bool:
        raise NotImplementedError


class MADActual(Detector):
    nombre = "MAD con historia móvil (hoy)"
    explicacion = "scoring.capa2 tal cual corre en servicios.py: compara contra las últimas 300 lecturas, falla incluida"

    def __init__(self, s: Senal) -> None:
        self.h: list[float] = []

    def marca(self, x: float) -> bool:
        c = capa2("s", self.h, x)
        self.h.append(x)
        self.h = self.h[-HISTORIA_MAX:]
        return c.nivel is Nivel.WARNING


class _ConLineaBase(Detector):
    def __init__(self, s: Senal) -> None:
        self.base: list[float] = []
        self.calibracion = s.calibracion

    def marca(self, x: float) -> bool:
        if len(self.base) < self.calibracion:
            self.base.append(x)
            if len(self.base) == self.calibracion:
                self.calibrar()
            return False
        return self.paso(x)

    def calibrar(self) -> None:
        self.centro = median(self.base)
        self.escala = (median(abs(v - self.centro) for v in self.base) * 1.4826) or 1e-9

    def paso(self, x: float) -> bool:
        raise NotImplementedError


class MADCongelada(_ConLineaBase):
    nombre = "MAD con línea base fija"
    explicacion = "la misma fórmula, pero la línea base se toma al calibrar y no se mueve"

    def paso(self, x: float) -> bool:
        return abs(x - self.centro) / self.escala >= DESVIO_WARNING


class EWMA(_ConLineaBase):
    nombre = "EWMA (λ 0,2 · L 3)"
    explicacion = "media móvil exponencial contra su límite de control; suaviza el ruido y ve cambios chicos sostenidos"

    def calibrar(self) -> None:
        super().calibrar()
        self.z, self.lam = self.centro, 0.2
        self.limite = 3 * self.escala * math.sqrt(self.lam / (2 - self.lam))

    def paso(self, x: float) -> bool:
        self.z = self.lam * x + (1 - self.lam) * self.z
        return abs(self.z - self.centro) >= self.limite


class CUSUM(_ConLineaBase):
    nombre = "CUSUM (k 0,5 · h 5)"
    explicacion = "suma acumulada de desvíos; el clásico para detectar un corrimiento sostenido de la media"

    def calibrar(self) -> None:
        super().calibrar()
        self.alto = self.bajo = 0.0

    def paso(self, x: float) -> bool:
        d = (x - self.centro) / self.escala
        self.alto = max(0.0, self.alto + d - 0.5)
        self.bajo = max(0.0, self.bajo - d - 0.5)
        return self.alto > 5 or self.bajo > 5


class UmbralFijo(Detector):
    nombre = "Umbral fijo"
    explicacion = "un límite tipo fabricante: media nominal más 6 desvíos, sin aprender nada"

    def __init__(self, s: Senal) -> None:
        self.limite = s.media + 6 * s.desvio

    def marca(self, x: float) -> bool:
        return x > self.limite


class CUSUMSinCiclo(Detector):
    nombre = "CUSUM sobre el residuo del ciclo"
    explicacion = ("el mismo CUSUM, pero contra lo esperado en ese momento del ciclo de trabajo. Necesita saber en "
                   "qué parte del ciclo va la máquina: en terreno, otra señal como la corriente o la carga")

    def __init__(self, s: Senal) -> None:
        self.s, self.t, self.base = s, 0, []

    def marca(self, x: float) -> bool:
        s, t = self.s, self.t
        self.t += 1
        if t < s.calibracion:
            self.base.append(x)
            if t + 1 == s.calibracion:
                p = s.ciclo_periodo if s.ciclo_amplitud else 1
                fases = [[v for k, v in enumerate(self.base) if k % p == f] for f in range(p)]
                medias = [sum(f) / len(f) for f in fases]
                # Con dos ciclos hay dos muestras por fase: se suaviza con las fases vecinas.
                vecinas = range(-3, 4) if p > 1 else range(1)
                self.esperado = [sum(medias[(f + d) % p] for d in vecinas) / len(vecinas) for f in range(p)]
                residuo = [v - self.esperado[k % p] for k, v in enumerate(self.base)]
                c = median(residuo)
                self.escala = (median(abs(r - c) for r in residuo) * 1.4826) or 1e-9
                self.p, self.alto, self.bajo = p, 0.0, 0.0
            return False
        d = (x - self.esperado[t % self.p]) / self.escala
        self.alto = max(0.0, self.alto + d - 0.5)
        self.bajo = max(0.0, self.bajo - d - 0.5)
        return self.alto > 5 or self.bajo > 5


def detectores(s: Senal) -> list[Detector]:
    return [MADActual(s), MADCongelada(s), EWMA(s), CUSUM(s), CUSUMSinCiclo(s), UmbralFijo(s)]


class Pegado(Detector):
    nombre = "Sensor pegado"
    explicacion = "aparte de los demás: 10 lecturas idénticas seguidas son una falla del sensor"

    def __init__(self, s: Senal) -> None:
        self.ultimo, self.iguales = None, 0

    def marca(self, x: float) -> bool:
        self.iguales = self.iguales + 1 if x == self.ultimo else 0
        self.ultimo = x
        return self.iguales >= 9


# ─── Medir ──────────────────────────────────────────────────────────────────


@dataclass
class Medida:
    detectadas: int = 0
    corridas: int = 0
    retardos: list[int] | None = None
    cobertura: list[float] | None = None
    falsas: int = 0
    lecturas_fuera: int = 0

    def __post_init__(self) -> None:
        self.retardos, self.cobertura = [], []


def correr(s: Senal, falla: str, crear, semillas: int) -> Medida:
    m = Medida()
    for semilla in range(semillas):
        azar = random.Random(f"{s.industria}-{falla}-{semilla}")
        x, ventana = generar(s, falla, azar)
        det = crear()
        alarma = [det.marca(v) for v in x]
        m.corridas += 1
        # La calibración de los detectores con línea base no cuenta para nadie.
        for t in range(s.calibracion, LARGO):
            if t in ventana:
                continue
            m.lecturas_fuera += 1
            if alarma[t] and not alarma[t - 1] and (t - 1) not in ventana:
                m.falsas += 1
        if ventana:
            # Para el pico, la alarma vale si llega en la lectura del pico o la siguiente.
            mirar = range(ventana.start, ventana.stop + (1 if falla == "pico" else 0))
            primera = next((t for t in mirar if alarma[t]), None)
            if primera is not None:
                m.detectadas += 1
                m.retardos.append(primera - ventana.start)
            m.cobertura.append(sum(alarma[t] for t in ventana) / len(ventana))
    return m


def tabla(semillas: int) -> tuple[str, dict]:
    salida, resumen = [], {}
    for s in SENALES:
        ciclo = f", con un ciclo de ±{s.ciclo_amplitud:g} {s.unidad} cada {s.ciclo_periodo} lecturas" if s.ciclo_amplitud else ", sin ciclo"
        salida.append(f"\n### {s.industria} · {s.que}\n\nMedia {s.media:g} {s.unidad}, ruido {s.desvio:g}{ciclo}. "
                      f"Línea base: {s.calibracion} lecturas.\n")
        salida.append("| Detector | Falsas alarmas / 1.000 lecturas | Pico | Escalón: detecta · retardo · cubre | Deriva: detecta · retardo | Alarma por sensor pegado |")
        salida.append("|---|---|---|---|---|---|")
        for base in detectores(s):
            crear = lambda b=base, s=s: type(b)(s)  # noqa: E731
            r = {f: correr(s, f, crear, semillas) for f in FALLAS}
            fuera = sum(r[f].lecturas_fuera for f in FALLAS)
            falsas = 1000 * sum(r[f].falsas for f in FALLAS) / fuera
            pct = lambda m: f"{100 * m.detectadas / m.corridas:.0f} %"  # noqa: E731
            ret = lambda m: f"{median(m.retardos):.0f}" if m.retardos else "—"  # noqa: E731
            cub = f"{100 * sum(r['escalon'].cobertura) / len(r['escalon'].cobertura):.0f} %"
            pegado = r["pegado"]
            salida.append(f"| {base.nombre} | {falsas:.1f} | {pct(r['pico'])} | {pct(r['escalon'])} · {ret(r['escalon'])} · {cub} "
                          f"| {pct(r['deriva'])} · {ret(r['deriva'])} | {pct(pegado)} |")
            resumen[(s.industria, base.nombre)] = {
                "falsas": falsas, "escalon": r["escalon"].detectadas / r["escalon"].corridas,
                "cubre": sum(r["escalon"].cobertura) / len(r["escalon"].cobertura),
                "deriva": r["deriva"].detectadas / r["deriva"].corridas,
            }
        r = {f: correr(s, f, lambda s=s: Pegado(s), semillas) for f in FALLAS}
        fuera = sum(r[f].lecturas_fuera for f in FALLAS)
        salida.append(f"\nEl detector de sensor pegado encontró el pegado en {100 * r['pegado'].detectadas / r['pegado'].corridas:.0f} % "
                      f"de las corridas, con {1000 * sum(r[f].falsas for f in FALLAS) / fuera:.1f} falsas alarmas por 1.000 lecturas.")
    return "\n".join(salida), resumen


def main() -> None:
    p = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    p.add_argument("--semillas", type=int, default=40)
    p.add_argument("--md", help="escribe el resultado en este archivo Markdown")
    a = p.parse_args()
    cuerpo, _ = tabla(a.semillas)
    detalle = "\n".join(f"- **{d.nombre}**: {d.explicacion}." for d in [*detectores(SENALES[0]), Pegado(SENALES[0])])
    texto = f"""# Simulación de la capa 2

> Generado por `scripts/simular_capa2.py --semillas {a.semillas}` el {date.today().isoformat()}. Señales **sintéticas**:
> descartan detectores que fallan en patrones conocidos; no calibran umbrales. Se regenera, no se edita a mano.

Cada corrida tiene {LARGO} lecturas. Los detectores con línea base fija la toman al principio, de al menos
dos ciclos de trabajo, y la falla empieza entre 60 y 260 lecturas después. **Detecta** es la fracción de corridas en que la alarma se
encendió durante la falla; **retardo**, la mediana de lecturas entre el inicio de la falla y la alarma;
**cubre**, qué fracción de la falla la alarma estuvo encendida. Una falsa alarma es una alarma que se
enciende fuera de la falla.

## Detectores

{detalle}

## Resultados
{cuerpo}
"""
    if a.md:
        Path(a.md).write_text(texto, encoding="utf-8")
        print(f"escrito: {a.md}")
    else:
        print(texto)


if __name__ == "__main__":
    main()
