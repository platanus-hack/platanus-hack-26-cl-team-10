"""Detecta objetos por texto (YOLO-World, sin entrenar) en la última foto del colector.

Uso: .venv/bin/python detectar.py [--clases "soda can" "bottle"] [--foto ruta.jpg] [--conf 0.15] [--pesos ../datos/modelos/yolo-factum.pt]
Guarda la foto anotada en data/detecciones/.
"""
import argparse
from pathlib import Path

from ultralytics import YOLOWorld


def ultima_foto():
    fotos = sorted(Path("data/frames").glob("*.jpg"))
    if not fotos:
        raise SystemExit("No hay fotos en data/frames: ¿está corriendo correr_colector.command?")
    return fotos[-1]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--clases", nargs="+", default=["soda can"])
    ap.add_argument("--foto", type=Path)
    ap.add_argument("--conf", type=float, default=0.15)
    ap.add_argument("--pesos", default="yolov8s-worldv2.pt", help="o el modelo afinado con entrenar.py")
    a = ap.parse_args()

    foto = a.foto or ultima_foto()
    modelo = YOLOWorld(a.pesos)  # el base se descarga la primera vez (~25 MB)
    modelo.set_classes(a.clases)
    r = modelo.predict(str(foto), conf=a.conf, verbose=False)[0]

    salida = Path("data/detecciones"); salida.mkdir(parents=True, exist_ok=True)
    r.save(filename=str(salida / foto.name))
    print(f"{foto.name}: {len(r.boxes)} detección(es)")
    for b in r.boxes:
        print(f"  {a.clases[int(b.cls)]}  conf={float(b.conf):.2f}  caja={[round(v) for v in b.xyxy[0].tolist()]}")


if __name__ == "__main__":
    main()
