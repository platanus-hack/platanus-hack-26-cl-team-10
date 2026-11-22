"""La latencia de capa 1, leída de la bitácora de un servidor: de la lectura en el edge a la alerta escrita.

  uv run python scripts/medir_latencia.py https://servidor [--desde 2026-11-22]

Solo cuentan las lecturas que el edge mandó con `medido_en` (POST /edge/{id}/lecturas). Mide hasta que el evento
queda escrito en el servidor; lo que tarda el aviso en llegar a la pantalla o al parlante va aparte. Si los relojes
del edge y del servidor no están sincronizados por NTP, la diferencia entre ellos entra en cada número.
"""

from __future__ import annotations

import argparse
import json
import statistics
import sys
import urllib.parse
import urllib.request


def _leer(url: str):
    with urllib.request.urlopen(url, timeout=20) as r:  # noqa: S310 - la URL la da quien corre el script
        return json.load(r)


def percentil(valores: list[float], q: float) -> float:
    orden = sorted(valores)
    return orden[min(len(orden) - 1, round(q * (len(orden) - 1)))]


def medir(eventos: list[dict]) -> dict[str, list[int]]:
    """Por clase de evento (alerta de capa 1, veredicto por sensor), los ms de la medición al evento escrito."""
    salida: dict[str, list[int]] = {}
    for e in eventos:
        lectura = (e.get("evidencia") or {}).get("lectura") or {}
        if "ms_hasta_el_evento" not in lectura:
            continue
        if e["tipo"] == "alerta" and e.get("capa") == 1:
            clase = "alerta de capa 1"
        elif e["tipo"] == "veredicto":
            clase = "veredicto por sensor"
        else:
            continue
        salida.setdefault(clase, []).append(lectura["ms_hasta_el_evento"])
    return salida


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("servidor")
    ap.add_argument("--desde", help="solo las OT abiertas desde esta fecha (AAAA-MM-DD)")
    a = ap.parse_args()
    base = a.servidor.rstrip("/")
    eventos = []
    for ot in _leer(f"{base}/ots"):
        if a.desde and ot["abierta_en"][:10] < a.desde:
            continue
        eventos += _leer(f"{base}/ot/{urllib.parse.quote(ot['ot'])}/eventos")
    por_clase = medir(eventos)
    if not por_clase:
        print("Ninguna lectura trae `medido_en`: el edge todavía no manda la hora de la medición.")
        return 1
    print("| Evento | N | Mediana (ms) | p95 (ms) | Máx (ms) |\n|---|---|---|---|---|")
    for clase, ms in sorted(por_clase.items()):
        print(f"| {clase} | {len(ms)} | {statistics.median(ms):.0f} | {percentil(ms, 0.95):.0f} | {max(ms)} |")
    return 0


if __name__ == "__main__":
    sys.exit(main())
