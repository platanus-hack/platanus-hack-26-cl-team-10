"""Exporta YOLO-World con clases fijas a ONNX, para correrlo en el servidor sin PyTorch ni CLIP.

Uso (desde edge/):  .venv/bin/python exportar_onnx.py [--clases mouse pencil] [--lado 640]
Deja ../datos/modelos/yolo-<clases>-<lado>.onnx (no va al repo: *.onnx está ignorado).
"""
import argparse
import shutil
from pathlib import Path

from ultralytics import YOLOWorld

ap = argparse.ArgumentParser()
ap.add_argument("--clases", nargs="+", default=["mouse", "pencil"])
ap.add_argument("--lado", type=int, default=640)
a = ap.parse_args()

m = YOLOWorld("yolov8s-worldv2.pt")
m.set_classes(a.clases)
# opset 17: onnxruntime solo garantiza hasta el 21 y ultralytics exporta por defecto en uno más nuevo
ruta = Path(m.export(format="onnx", imgsz=a.lado, simplify=True, opset=17))
destino = Path("../datos/modelos") / f"yolo-{'-'.join(a.clases)}-{a.lado}.onnx"
destino.parent.mkdir(parents=True, exist_ok=True)
shutil.move(ruta, destino)
print("listo:", destino.resolve())
