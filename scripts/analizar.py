"""Las comprobaciones de app/analisis.py, por línea de comandos. Las usan las skills de .claude/skills/.

  python3 scripts/analizar.py pauta RUTA [--estacion datos/estaciones/X.json]
      RUTA es una pauta (datos/pauta-*.json) o un borrador (datos/borradores/*.json).
      Dice si cumple el contrato, si cada paso cita el protocolo, qué puede cerrar la
      estación y qué análisis vale la pena correr. Sale con 1 si algo no pasa.
  python3 scripts/analizar.py ejecuciones [--db RUTA] [--pauta ID]
      Cómo se ejecutó cada versión de cada pauta, paso por paso, y qué conviene mirar.
  python3 scripts/analizar.py comparar GENERADA REFERENCIA
      Cuánto se parece una pauta propuesta a la que escribió una persona.
  uv run python scripts/analizar.py cuadros VIDEO [--cada 2] [--salida DIR]
      Un JPEG cada tantos segundos, para que el agente mire una ejecución grabada.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app import analisis, catalogo, db  # noqa: E402
from app.contratos import Pauta  # noqa: E402

RAIZ = Path(__file__).resolve().parent.parent
CASOS_CAPA3 = RAIZ / "datos" / "evals" / "capa3" / "casos.jsonl"
CAPA = {1: "sensor", 2: "detector", 3: "VLM", None: "persona"}


def _leer(ruta: str) -> tuple[Pauta, dict]:
    """La pauta y, si la ruta es un borrador, el borrador entero."""
    d = json.loads(Path(ruta).read_text(encoding="utf-8"))
    borrador = d if "pauta" in d else {}
    return catalogo.pauta_desde_dict(d.get("pauta", d)), borrador


def _pedidos(pedidos: list[dict]) -> list[str]:
    if not pedidos:
        return ["Nada que analizar: ningún paso lo pide."]
    return [f"- **{x['analisis']}** · {x['sobre']}: {x['por_que']}" for x in pedidos]


def pauta(a) -> int:
    try:
        p, borrador = _leer(a.ruta)
    except (KeyError, ValueError, catalogo.ReglaDeNegocio) as e:
        print(f"No cumple el contrato: {e}")
        return 1
    fallas = 0
    print(f"# {p.nombre} · {p.id} v{p.version}\n\n{len(p.pasos)} pasos, "
          f"{sum(x.control_critico for x in p.pasos)} controles críticos.\n")

    if borrador:
        doc = borrador.get("documento")
        if not doc:
            print("Citas: el borrador no nombra su `documento`, no se pueden comprobar.\n")
        else:
            sin = analisis.citas_sin_respaldo(borrador, (RAIZ / doc).read_text(encoding="utf-8"))
            fallas += len(sin)
            print(f"Citas: {len(p.pasos) - len(sin)} de {len(p.pasos)} pasos citan `{doc}` literalmente."
                  + (f" **Sin respaldo: {', '.join(sin)}.**" if sin else "") + "\n")
        an = borrador.get("analisis", {})
        for duda in an.get("dudas", []):
            print(f"- Duda para la persona que aprueba: {duda}")
        if an.get("no_cabe"):
            print("\n## Lo que el protocolo pide y la pauta no comprueba\n")
            for x in an["no_cabe"]:
                print(f"- **{x['tipo']}** · {x.get('paso') or 'toda la pauta'}: «{x['cita']}»")
            if len(an["no_cabe"]) >= len(p.pasos):
                print(f"\n**Quedan {len(an['no_cabe'])} cosas fuera para {len(p.pasos)} pasos: este proceso no calza bien con "
                      "una lista en orden.** La pauta sirve de registro, no de verificación. Decídelo antes de instrumentar.")
        if an.get("sensores_que_faltan"):
            print("\n## Sensores que cerrarían lo que hoy cierra una persona o la cámara\n")
            for x in an["sensores_que_faltan"]:
                print(f"- {x['paso']}: `{x['sensor']}` ({' · '.join(x['estados'])}): {x['mide']}")
        print()

    mal = [x.id for x in p.pasos if x.capa_minima != analisis.capa_esperada(x)]
    if mal:
        fallas += len(mal)
        print(f"**`capa_minima` no calza con la evidencia en: {', '.join(mal)}** (sensor y confirmación 1, "
              "cámara 3, cámara con `deteccion` 2).\n")

    solos = analisis.se_cierran_solos(p)
    if solos:
        fallas += len(solos)
        print(f"**Se cierran solos: {', '.join(solos)}.** Esperan la lectura que un paso anterior ya dejó: "
              "si son una prueba que hace el operario, son de confirmación.\n")

    for x in analisis.alertas_en_ejecucion_correcta(p):
        fallas += 1
        print(f"**Una ejecución correcta dispara una regla de seguridad en {x['paso']}:** {x['aviso']} "
              "O el sensor se llama igual que otro y mide otra cosa, o la pauta pide lo que la regla prohíbe.\n")

    estacion = json.loads(Path(a.estacion).read_text(encoding="utf-8")) if a.estacion else None
    if estacion is None:
        print("Sin `--estacion`: no se comprobó contra una estación real. Para ejecutarla hace falta:\n\n```json\n"
              + json.dumps(analisis.requiere(p), ensure_ascii=False, indent=2) + "\n```\n")
    else:
        f = analisis.factibilidad(p, estacion)
        fallas += sum(1 for x in f if x["falta"])
        print(f"## Factibilidad en {Path(a.estacion).stem}\n\n| Paso | Lo cierra | Crítico | Falta |\n|---|---|---|---|")
        for paso, x in zip(p.en_orden, f):
            print(f"| {paso.id} · {paso.titulo} | {CAPA[x['capa']]} | {'sí' if paso.control_critico else ''} | {x['falta'] or ''} |")
        por = {c: sum(1 for x in f if x["capa"] == c and not x["falta"]) for c in CAPA}
        criticos = [x for paso, x in zip(p.en_orden, f) if paso.control_critico]
        print(f"\nCierran: {', '.join(f'{CAPA[c]} {n}' for c, n in por.items() if n)}; "
              f"sin poder cerrarse {sum(1 for x in f if x['falta'])}. "
              f"Controles críticos con sensor disponible: {sum(1 for x in criticos if x['capa'] == 1 and not x['falta'])} de {len(criticos)}.\n")

    medidas = ({json.loads(l)["pregunta"] for l in CASOS_CAPA3.read_text(encoding="utf-8").splitlines() if l.strip()}
               if CASOS_CAPA3.exists() else set())
    print("## Qué vale la pena analizar\n")
    print("\n".join(_pedidos(analisis.criterio(p, estacion, borrador.get("analisis", {}).get("no_puede_pasar", []), medidas))))
    return 1 if fallas else 0


def ejecuciones(a) -> int:
    cx = db.conectar(a.db)
    grupos: dict[tuple[str, int], list[str]] = {}
    for f in cx.execute("SELECT id, pauta_id, pauta_version FROM ots ORDER BY id"):
        if not a.pauta or f["pauta_id"] == a.pauta:
            grupos.setdefault((f["pauta_id"], f["pauta_version"]), []).append(f["id"])
    if not grupos:
        print("No hay OT que analizar.")
        return 0
    for (pauta_id, version), ots in sorted(grupos.items()):
        p = db.leer_pauta(cx, pauta_id, version)
        h = analisis.historia(p, {ot: db.eventos(cx, ot) for ot in ots})
        print(f"# {p.nombre} · {pauta_id} v{version} · {len(ots)} OT\n")
        if len(ots) < analisis.MIN_EJECUCIONES:
            print(f"Menos de {analisis.MIN_EJECUCIONES} OT: se muestra, pero no se propone nada.\n")
        print("| Paso | Verificado | Conflicto | Por persona | Alerta | Mediana (s) |\n|---|---|---|---|---|---|")
        for paso in p.en_orden:
            d = h[paso.id]
            print(f"| {paso.id} · {paso.titulo} | {d['verificado']} | {d['conflicto']} | {d['por_persona']} | {d['alerta']} "
                  f"| {'' if d['segundos'] is None else d['segundos']} |")
        print("\n" + "\n".join(_pedidos(analisis.criterio_de_historia(p, h))) + "\n")
    return 0


def comparar(a) -> int:
    r = analisis.comparar(_leer(a.generada)[0], _leer(a.referencia)[0])
    print(json.dumps(r, ensure_ascii=False, indent=2))
    return 0


def cuadros(a) -> int:
    import cv2  # acá adentro: el resto del script corre con python3 pelado

    video = cv2.VideoCapture(a.video)
    fps = video.get(cv2.CAP_PROP_FPS) or 30
    salida = Path(a.salida or Path(a.video).with_suffix(""))
    salida.mkdir(parents=True, exist_ok=True)
    n = guardados = 0
    while True:
        ok, cuadro = video.read()
        if not ok:
            break
        if n % max(1, round(fps * a.cada)) == 0:
            cv2.imwrite(str(salida / f"{n / fps:07.1f}s.jpg"), cuadro)
            guardados += 1
        n += 1
    print(f"{guardados} cuadros en {salida}, uno cada {a.cada} s; el nombre es el segundo del video")
    return 0 if guardados else 1


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(required=True)
    s = sub.add_parser("pauta"); s.add_argument("ruta"); s.add_argument("--estacion"); s.set_defaults(f=pauta)
    s = sub.add_parser("ejecuciones"); s.add_argument("--db"); s.add_argument("--pauta"); s.set_defaults(f=ejecuciones)
    s = sub.add_parser("comparar"); s.add_argument("generada"); s.add_argument("referencia"); s.set_defaults(f=comparar)
    s = sub.add_parser("cuadros"); s.add_argument("video"); s.add_argument("--cada", type=float, default=2.0)
    s.add_argument("--salida"); s.set_defaults(f=cuadros)
    a = ap.parse_args()
    return a.f(a)


if __name__ == "__main__":
    sys.exit(main())
