"""Cuándo una desviación es recurrente y cuándo un cambio de pauta la bajó de verdad. Sin dependencias.

Contar «el mismo paso en 2 OT» no tiene denominador: con 20 OT, un paso que se desvía al azar el 5 % de las veces
pasa ese mínimo en una de cada cuatro pautas. Acá se compara cada paso contra lo que se desvía el resto de su
pauta, y se corrige por la cantidad de pasos que se prueban a la vez (Holm). La simulación de
`app/simulacion.py` calibra estas pruebas; sus resultados están en
knowledge/projects/mejora-continua/simulacion.md.

Las pruebas son las del NIST/SEMATECH e-Handbook: binomial exacta contra una proporción (7.2.4) y Fisher exacta
para comparar dos proporciones con pocos casos (7.3.3).
"""

from __future__ import annotations

from collections.abc import Mapping
from math import comb

ALFA = 0.05


def cola_binomial(k: int, n: int, p: float) -> float:
    """P(X ≥ k) con X ~ Binomial(n, p)."""
    if k <= 0:
        return 1.0
    return min(1.0, sum(comb(n, i) * p**i * (1 - p) ** (n - i) for i in range(k, n + 1)))


def holm(pvalores: Mapping[str, float], alfa: float = ALFA) -> dict[str, bool]:
    """Qué hipótesis se rechazan controlando la probabilidad de al menos un falso positivo en la familia."""
    orden = sorted(pvalores, key=pvalores.get)
    m, salida, sigue = len(orden), {}, True
    for i, clave in enumerate(orden):
        sigue = sigue and pvalores[clave] <= alfa / (m - i)
        salida[clave] = sigue
    return salida


def recurrentes(con_senal: Mapping[str, int], ots: int, alfa: float = ALFA) -> dict[str, dict]:
    """Por paso: si las OT con señal superan lo que se desvía el resto de la pauta.

    `con_senal` trae todos los pasos de la versión, también los que tuvieron 0. La tasa de referencia de cada paso
    sale de los pasos que no se marcaron, con un prior Beta(1, 1) para que pocas OT sin señales no la dejen en cero
    (con base 0, cualquier señal sería «recurrente»). Se repite sacando de la referencia los pasos marcados, hasta que
    nada cambia: un segundo paso recurrente no debe esconder al primero inflando la base. Sin ningún paso marcado en
    la primera vuelta no hay segunda, así que la probabilidad de un falso positivo en la pauta sigue acotada por Holm.
    """
    marcados: set[str] = set()
    while True:
        normales = [p for p in con_senal if p not in marcados]
        pvalores, salida = {}, {}
        for paso, k in con_senal.items():
            resto = [q for q in normales if q != paso]
            resto_k, resto_n = sum(con_senal[q] for q in resto), ots * len(resto)
            base = (resto_k + 1) / (resto_n + 2)
            pvalores[paso] = cola_binomial(k, ots, base)
            salida[paso] = {"ots_con_senal": k, "ots": ots, "tasa": round(k / ots, 3) if ots else None,
                            "tasa_del_resto": round(base, 3), "p_valor": round(pvalores[paso], 4)}
        rechazos = holm(pvalores, alfa)
        for paso, rechaza in rechazos.items():
            salida[paso]["recurrente"] = rechaza
        nuevos = {p for p, r in rechazos.items() if r}
        if nuevos == marcados or not nuevos:
            return salida
        marcados = nuevos


def fisher_baja(antes: tuple[int, int], despues: tuple[int, int]) -> float:
    """P de ver tan pocas OT con señal después, o menos, si la versión nueva no cambió nada.

    `antes` y `despues` son (OT, OT con señal). Fisher exacta de una cola sobre la tabla 2×2.
    """
    (n1, k1), (n2, k2) = antes, despues
    n, k = n1 + n2, k1 + k2
    total = comb(n, k)
    return min(1.0, sum(comb(n2, i) * comb(n1, k - i) for i in range(0, k2 + 1) if 0 <= k - i <= n1) / total)


def comprobar_cambio(antes: tuple[int, int], despues: tuple[int, int], alfa: float = ALFA) -> dict:
    """«mejoro» solo si la baja no se explica por azar; con pocas OT, una baja es «sin_evidencia», no una mejora."""
    if despues[0] == 0:
        return {"resultado": "sin_datos", "p_valor": None}
    tasa_antes = antes[1] / antes[0] if antes[0] else 0.0
    tasa_despues = despues[1] / despues[0]
    if tasa_despues >= tasa_antes:
        return {"resultado": "se_repite", "p_valor": None}
    p = fisher_baja(antes, despues)
    return {"resultado": "mejoro" if p <= alfa else "sin_evidencia", "p_valor": round(p, 4)}
