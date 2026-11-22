"""Exporta YOLO-World con clases fijas a ONNX, para correrlo en el servidor sin PyTorch ni CLIP.

Uso (desde edge/):  .venv/bin/python exportar_onnx.py [--pautas ../datos/borradores/x.json ...] [--lado 640] [--pesos ../datos/modelos/yolo-factum.pt]
Exporta las clases de --clases más las que pidan las pautas de --pautas (por defecto, ../datos/pauta-*.json).
Deja ../datos/modelos/yolo-<clases>-<lado>.onnx (no va al repo: *.onnx está ignorado).
"""
import argparse
import json
import shutil
from glob import glob
from pathlib import Path

BASE = "yolov8s-worldv2.pt"


def clases_de(rutas):
    """Las clases que piden las pautas, o borradores de pauta, de `rutas`."""
    clases = set()
    for r in rutas:
        d = json.loads(Path(r).read_text(encoding="utf-8"))
        clases |= {c for p in d.get("pauta", d)["pasos"] if p.get("deteccion")
                   for c in (p["deteccion"]["clase"], p["deteccion"].get("en_su_lugar")) if c}
    return sorted(clases)


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    # "soda can" va junto a "red soda can" para que una lata de otro color no caiga en la roja
    ap.add_argument("--clases", nargs="+", default=["mouse", "pencil", "soda can", "red soda can", "green soda can"],
                    help="las que se exportan siempre; se suman las que pidan las pautas")
    ap.add_argument("--pautas", nargs="*", default=sorted(glob("../datos/pauta-*.json")))
    ap.add_argument("--lado", type=int, default=640)
    ap.add_argument("--pesos", default=BASE, help="modelo afinado con entrenar.py; por defecto, YOLO-World sin entrenar")
    a = ap.parse_args()
    clases = a.clases + [c for c in clases_de(a.pautas) if c not in a.clases]

    from ultralytics import YOLOWorld

    m = YOLOWorld(a.pesos)
    m.set_classes(clases)
    # opset 17: onnxruntime solo garantiza hasta el 21 y ultralytics exporta por defecto en uno más nuevo
    ruta = Path(m.export(format="onnx", imgsz=a.lado, simplify=True, opset=17))
    # shortcut: el nombre lleva todas las clases, pasar a un hash cuando sean tantas que el nombre no quepa
    destino = Path("../datos/modelos") / f"{'yolo' if a.pesos == BASE else Path(a.pesos).stem}-{'-'.join(clases).replace(' ', '_')}-{a.lado}.onnx"
    destino.parent.mkdir(parents=True, exist_ok=True)
    shutil.move(ruta, destino)
    print("listo:", destino.resolve(), "· clases:", ", ".join(clases))
