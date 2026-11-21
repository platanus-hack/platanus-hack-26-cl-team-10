"""Exporta YOLO-World con clases fijas a ONNX, para correrlo en el servidor sin PyTorch ni CLIP.

Uso (desde edge/):  .venv/bin/python exportar_onnx.py [--pautas ../datos/borradores/x.json ...] [--lado 640]
Las clases son las que piden las pautas (por defecto, las de ../datos/pauta-*.json); --clases las fija a mano.
Deja ../datos/modelos/yolo-<clases>-<lado>.onnx (no va al repo: *.onnx está ignorado).
"""
import argparse
import json
import shutil
from glob import glob
from pathlib import Path


def clases_de(rutas):
    """Las clases que piden las pautas, o borradores de pauta, de `rutas`."""
    clases = set()
    for r in rutas:
        d = json.loads(Path(r).read_text(encoding="utf-8"))
        clases |= {p["deteccion"]["clase"] for p in d.get("pauta", d)["pasos"] if p.get("deteccion")}
    return sorted(clases)


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--clases", nargs="+", help="por defecto, las que piden las pautas de --pautas")
    ap.add_argument("--pautas", nargs="+", default=sorted(glob("../datos/pauta-*.json")))
    ap.add_argument("--lado", type=int, default=640)
    a = ap.parse_args()
    clases = a.clases or clases_de(a.pautas)
    if not clases:
        raise SystemExit("ninguna de esas pautas pide detector: no hay nada que exportar")

    from ultralytics import YOLOWorld

    m = YOLOWorld("yolov8s-worldv2.pt")
    m.set_classes(clases)
    # opset 17: onnxruntime solo garantiza hasta el 21 y ultralytics exporta por defecto en uno más nuevo
    ruta = Path(m.export(format="onnx", imgsz=a.lado, simplify=True, opset=17))
    # shortcut: el nombre lleva todas las clases, pasar a un hash cuando sean tantas que el nombre no quepa
    destino = Path("../datos/modelos") / f"yolo-{'-'.join(clases).replace(' ', '_')}-{a.lado}.onnx"
    destino.parent.mkdir(parents=True, exist_ok=True)
    shutil.move(ruta, destino)
    print("listo:", destino.resolve(), "· clases:", ", ".join(clases))
