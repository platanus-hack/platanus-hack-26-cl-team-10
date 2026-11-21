"""Eval de la capa 3: qué tan bien responde el juez de cámara la pregunta visual de cada paso.

Correr:  python3 scripts/evaluar_capa3.py [--juez modulo:funcion] [--casos ruta.jsonl]
Por defecto evalúa app.verificacion:juez_camara, el que corre hoy en el servidor.

Cada caso es una escena de un paso de cámara de una industria, con la respuesta que
debería dar el juez. La imagen va en datos/evals/capa3/imagenes/<id>.jpg, que no se
versiona: puede mostrar a una persona. Un caso sin imagen se le pasa al juez sin
cuadro y se cuenta aparte, porque un juez que contesta sin mirar no prueba nada.

Lo que se mide es lo que importa para la política de LOGICA y del ADR-0004:
- falsa aceptación: dice que sí a un paso mal hecho. Es la que deja pasar un error.
- falso rechazo: dice que no a un paso bien hecho. Es la que enseña a ignorar el aviso;
  Sabetta et al. midieron 5 de 12 en un VLM general (REFERENCIAS 9).
- calibración: si la confianza que declara separa sus aciertos de sus errores, porque
  la calificación usa esa confianza (bajo 75 % pide que alguien mire).
"""

from __future__ import annotations

import argparse
import importlib
import json
import sys
from collections import defaultdict
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app.scoring import CONFIANZA_CAMARA_MIN  # noqa: E402

RAIZ = Path(__file__).resolve().parent.parent
CASOS = RAIZ / "datos" / "evals" / "capa3" / "casos.jsonl"
IMAGENES = CASOS.parent / "imagenes"


def cargar_juez(ruta: str):
    modulo, funcion = ruta.split(":")
    return getattr(importlib.import_module(modulo), funcion)


def evaluar(juez, casos: list[dict]) -> list[dict]:
    salida = []
    for c in casos:
        imagen = IMAGENES / f"{c['id']}.jpg"
        cuadro = imagen.read_bytes() if imagen.exists() else None
        si, confianza = juez(c["pregunta"], cuadro)
        salida.append({**c, "con_imagen": cuadro is not None, "respuesta": bool(si), "confianza": float(confianza),
                       "acierta": bool(si) == c["respuesta_esperada"]})
    return salida


def pct(a: int, b: int) -> str:
    return f"{a}/{b} ({100 * a / b:.0f} %)" if b else "—"


def informe(r: list[dict], juez: str) -> str:
    lineas = [f"# Eval de capa 3 · `{juez}`", ""]
    con = [x for x in r if x["con_imagen"]]
    lineas.append(f"{len(r)} casos, {len(con)} con imagen. "
                  + ("**Ningún caso tiene imagen todavía: lo de abajo mide cómo contesta el juez sin mirar.**"
                     if not con else ""))
    for titulo, grupo in [("Con imagen", con), ("Todos", r)]:
        if not grupo:
            continue
        pos = [x for x in grupo if x["respuesta_esperada"]]
        neg = [x for x in grupo if not x["respuesta_esperada"]]
        fa = sum(1 for x in neg if x["respuesta"])
        fr = sum(1 for x in pos if not x["respuesta"])
        bien = [x["confianza"] for x in grupo if x["acierta"]]
        mal = [x["confianza"] for x in grupo if not x["acierta"]]
        bajo = sum(1 for x in grupo if x["respuesta"] and x["confianza"] < CONFIANZA_CAMARA_MIN)
        prom = lambda v: f"{sum(v) / len(v):.2f}" if v else "—"  # noqa: E731
        lineas += [
            "", f"## {titulo}", "",
            "| Medida | Valor |", "|---|---|",
            f"| Exactitud | {pct(sum(x['acierta'] for x in grupo), len(grupo))} |",
            f"| Falsa aceptación (sí a un paso mal hecho) | {pct(fa, len(neg))} |",
            f"| Falso rechazo (no a un paso bien hecho) | {pct(fr, len(pos))} |",
            f"| Confianza media en aciertos / en errores | {prom(bien)} / {prom(mal)} |",
            f"| Síes que quedan en warning por confianza bajo {CONFIANZA_CAMARA_MIN:.0%} | {pct(bajo, sum(x['respuesta'] for x in grupo))} |",
        ]
        por = defaultdict(lambda: [0, 0])
        for x in grupo:
            por[(x["industria"], x["tipo"])][0] += x["acierta"]
            por[(x["industria"], x["tipo"])][1] += 1
        lineas += ["", "| Industria | Tipo de escena | Aciertos |", "|---|---|---|"]
        lineas += [f"| {i} | {t} | {pct(a, n)} |" for (i, t), (a, n) in sorted(por.items())]
    return "\n".join(lineas)


def main() -> int:
    p = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    p.add_argument("--juez", default="app.verificacion:juez_camara")
    p.add_argument("--casos", default=str(CASOS))
    p.add_argument("--json", action="store_true", help="imprime cada caso con su respuesta en vez del informe")
    a = p.parse_args()
    casos = [json.loads(linea) for linea in Path(a.casos).read_text(encoding="utf-8").splitlines() if linea.strip()]
    r = evaluar(cargar_juez(a.juez), casos)
    print(json.dumps(r, ensure_ascii=False, indent=1) if a.json else informe(r, a.juez))
    return 0


if __name__ == "__main__":
    sys.exit(main())
