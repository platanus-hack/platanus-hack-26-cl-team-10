"""Enseña al detector un objeto propio con unas pocas fotos (peldaño 3 de la skill solucion-vision).

YOLO-World reconoce bien el objeto en una foto de cerca y mal cuando se ve chico, como en la
cámara de la estación. Entonces: (1) el modelo base encuadra el objeto en cada foto de cerca,
(2) se recorta y se pega, chico y girado, sobre cuadros reales de la cámara, (3) YOLO-World se
afina con esas escenas y (4) se mide contra el base con una foto por clase que no entrenó.

Uso (desde edge/):
  .venv/bin/python entrenar.py --fotos "red soda can=fotos/roja*.jpg" "green soda can=fotos/verde*.jpg"
Deja ../datos/modelos/<nombre>.pt (no va al repo). Después: edge.py --pesos y exportar_onnx.py --pesos.
"""
import argparse
import random
import shutil
from glob import glob
from pathlib import Path

import cv2
import numpy as np

CONF_CIERRA, CONF_PISO = 0.8, 0.25  # los umbrales de app/reglas.por_deteccion


def recortar(img, caja):
    """El objeto de `caja` (x1, y1, x2, y2) sin su fondo: recorte BGR y máscara 0-255."""
    x1, y1, x2, y2 = caja
    m = np.zeros(img.shape[:2], np.uint8)
    cv2.grabCut(img, m, (x1, y1, x2 - x1, y2 - y1), np.zeros((1, 65)), np.zeros((1, 65)), 5, cv2.GC_INIT_WITH_RECT)
    m = np.where((m == cv2.GC_FGD) | (m == cv2.GC_PR_FGD), 255, 0).astype(np.uint8)
    return img[y1:y2, x1:x2], m[y1:y2, x1:x2]


def girar(img, angulo):
    """Gira agrandando el lienzo, para no cortar las esquinas."""
    h, w = img.shape[:2]
    M = cv2.getRotationMatrix2D((w / 2, h / 2), angulo, 1)
    c, s = abs(M[0, 0]), abs(M[0, 1])
    W, H = int(h * s + w * c), int(h * c + w * s)
    M[0, 2] += W / 2 - w / 2
    M[1, 2] += H / 2 - h / 2
    return cv2.warpAffine(img, M, (W, H))


def pegar(fondo, recorte, mascara, largo, angulo, cx, cy):
    """Pega el recorte sobre `fondo` (lo modifica), con su lado mayor de `largo` px y centro en
    (cx, cy). Devuelve la caja YOLO (cx, cy, ancho, alto en 0-1) de lo que quedó a la vista."""
    e = largo / max(recorte.shape[:2])
    tam = (max(1, round(recorte.shape[1] * e)), max(1, round(recorte.shape[0] * e)))
    r, m = girar(cv2.resize(recorte, tam), angulo), girar(cv2.resize(mascara, tam), angulo)
    H, W = fondo.shape[:2]
    x0, y0 = round(cx - r.shape[1] / 2), round(cy - r.shape[0] / 2)
    a, b, c, d = max(x0, 0), max(y0, 0), min(x0 + r.shape[1], W), min(y0 + r.shape[0], H)
    if c <= a or d <= b:
        return None
    r, m = r[b - y0:d - y0, a - x0:c - x0], m[b - y0:d - y0, a - x0:c - x0]
    ys, xs = np.nonzero(m > 127)
    if not len(xs):
        return None
    alfa = cv2.GaussianBlur(m, (5, 5), 0)[..., None] / 255  # borde suave: que no aprenda el recorte
    fondo[b:d, a:c] = (r * alfa + fondo[b:d, a:c] * (1 - alfa)).astype(np.uint8)
    return ((a + xs.min() + a + xs.max() + 1) / 2 / W, (b + ys.min() + b + ys.max() + 1) / 2 / H,
            (xs.max() + 1 - xs.min()) / W, (ys.max() + 1 - ys.min()) / H)


def iou(p, q):
    """Cajas (cx, cy, ancho, alto)."""
    ax, ay, bx, by = max(p[0] - p[2] / 2, q[0] - q[2] / 2), max(p[1] - p[3] / 2, q[1] - q[3] / 2), \
        min(p[0] + p[2] / 2, q[0] + q[2] / 2), min(p[1] + p[3] / 2, q[1] + q[3] / 2)
    inter = max(bx - ax, 0) * max(by - ay, 0)
    return inter / (p[2] * p[3] + q[2] * q[3] - inter)


def armar(a, clases, propias):
    """Escribe las escenas y sus etiquetas en a.datos. Devuelve la ruta del data.yaml."""
    from ultralytics import YOLOWorld

    base = YOLOWorld(a.base)
    base.set_classes(clases)
    recortes = {"train": [], "val": []}  # (índice de clase, recorte, máscara)
    for clase, rutas in propias.items():
        for i, ruta in enumerate(rutas):
            img = cv2.imread(ruta)
            cajas = [b for b in base.predict(img, conf=0.05, verbose=False)[0].boxes if clases[int(b.cls)] == clase]
            if not cajas:
                raise SystemExit(f"El modelo base no encuentra «{clase}» en {ruta}: saca la foto más de cerca y sin tapar")
            caja = [round(v) for v in max(cajas, key=lambda b: float(b.conf)).xyxy[0].tolist()]
            # la última foto de cada clase no entrena: es la que mide
            recortes["val" if i == len(rutas) - 1 and len(rutas) > 1 else "train"].append(
                (clases.index(clase), *recortar(img, caja)))
    if not recortes["val"]:
        raise SystemExit("Hace falta más de una foto por clase: la última se aparta para medir")

    fondos = sorted(glob(f"{a.fondos}/*.jpg"))
    fondos = fondos[::max(1, len(fondos) // a.fondos_max)]
    if not fondos:
        raise SystemExit(f"No hay cuadros de la cámara en {a.fondos}: corre correr_colector.command")
    shutil.rmtree(a.datos, ignore_errors=True)
    azar = random.Random(0)
    for n in range(a.escenas):
        parte = "val" if n % 5 == 4 else "train"
        fondo = cv2.imread(fondos[n % len(fondos)])
        H, W = fondo.shape[:2]
        # lo que el base ya ve bien (mouse, lápiz) se etiqueta con el base, para que no lo desaprenda
        etiquetas = [(int(b.cls), *b.xywhn[0].tolist()) for b in base.predict(fondo, conf=0.5, verbose=False)[0].boxes
                     if clases[int(b.cls)] not in propias]
        for _ in range(azar.choice([0, 1, 1, 2])):  # una de cada cuatro escenas no tiene el objeto
            cls, recorte, mascara = azar.choice(recortes[parte])
            recorte = cv2.convertScaleAbs(recorte, alpha=azar.uniform(0.7, 1.2), beta=azar.uniform(-20, 20))
            caja = pegar(fondo, recorte, mascara, azar.uniform(0.08, 0.4) * H, azar.uniform(0, 360),
                         azar.uniform(0.05, 0.95) * W, azar.uniform(0.05, 0.95) * H)
            if caja:
                etiquetas.append((cls, *caja))
        for sub in ("images", "labels"):
            (a.datos / sub / parte).mkdir(parents=True, exist_ok=True)
        cv2.imwrite(str(a.datos / "images" / parte / f"{n:04}.jpg"), fondo)
        (a.datos / "labels" / parte / f"{n:04}.txt").write_text(
            "".join(f"{c} {x:.5f} {y:.5f} {w:.5f} {h:.5f}\n" for c, x, y, w, h in etiquetas))
    yaml = a.datos / "data.yaml"
    yaml.write_text(f"path: {a.datos.resolve()}\ntrain: images/train\nval: images/val\nnames:\n"
                    + "".join(f"  {i}: {c}\n" for i, c in enumerate(clases)))
    return yaml


def medir(pesos, clases, clase, datos, lado):
    """Sobre las escenas apartadas: cuántas veces `clase` pasa el umbral que cierra un paso, y en
    cuántas escenas sin ella (vacías o con otro objeto) el detector igual la ve."""
    from ultralytics import YOLOWorld

    m = YOLOWorld(pesos)
    m.set_classes(clases)
    k = clases.index(clase)
    confs, sin_objeto, falsas = [], 0, 0
    for img in sorted((datos / "images" / "val").glob("*.jpg")):
        reales = [(int(l[0]), [float(v) for v in l[1:]]) for l in
                  (x.split() for x in (datos / "labels" / "val" / f"{img.stem}.txt").read_text().splitlines())
                  if int(l[0]) == k]
        vistas = [(int(b.cls), float(b.conf), b.xywhn[0].tolist())
                  for b in m.predict(str(img), conf=0.05, imgsz=lado, verbose=False)[0].boxes if int(b.cls) == k]
        for cls, caja in reales:
            confs.append(max((p for c, p, q in vistas if c == cls and iou(caja, q) >= 0.5), default=0.0))
        if not reales:
            sin_objeto += 1
            falsas += any(p >= CONF_PISO for _, p, _ in vistas)
    print(f"  {Path(pesos).name} a {lado} px, {clase}: {sum(c >= CONF_CIERRA for c in confs)} de {len(confs)} "
          f"pasan de {CONF_CIERRA} (mediana {np.median(confs):.2f}, mínimo {min(confs):.2f}); "
          f"{falsas} de {sin_objeto} escenas sin el objeto dan una detección sobre {CONF_PISO}")


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--fotos", nargs="+", required=True, metavar="CLASE=GLOB",
                    help='fotos de cerca de cada objeto, p. ej. "red soda can=fotos/roja*.jpg"')
    ap.add_argument("--fondos", default="data/frames", help="cuadros de la cámara de la estación (los deja el colector)")
    ap.add_argument("--fondos-max", type=int, default=150)
    ap.add_argument("--clases", nargs="+", default=["mouse", "pencil", "soda can"], help="las que el detector ya busca")
    ap.add_argument("--escenas", type=int, default=600)
    ap.add_argument("--epocas", type=int, default=15)
    ap.add_argument("--base", default="yolov8s-worldv2.pt")
    ap.add_argument("--nombre", default="yolo-factum", help="queda en ../datos/modelos/<nombre>.pt")
    ap.add_argument("--datos", type=Path, default=Path("data/entrenamiento"))
    ap.add_argument("--device", default=None, help="mps en un Mac")
    a = ap.parse_args()
    propias = {c: sorted(glob(g)) for c, g in (f.split("=", 1) for f in a.fotos)}
    clases = a.clases + [c for c in propias if c not in a.clases]

    yaml = armar(a, clases, propias)
    from ultralytics import YOLOWorld

    from ultralytics.utils.torch_utils import strip_optimizer

    modelo = YOLOWorld(a.base)
    # la validación de ultralytics aborta el proceso en MPS, también la del final: no se hace, mide medir()
    modelo.add_callback("on_train_start", lambda t: setattr(t, "final_eval", lambda: None))
    modelo.train(data=str(yaml), epochs=a.epocas, imgsz=640, batch=8, plots=False, val=False, device=a.device,
                 project=str(a.datos.resolve()), name="corrida", exist_ok=True)
    destino = Path("../datos/modelos") / f"{a.nombre}.pt"
    destino.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy(a.datos / "corrida" / "weights" / "last.pt", destino)
    strip_optimizer(destino)  # sin el optimizador pesa un tercio
    print("listo:", destino.resolve(), "· clases:", ", ".join(clases))
    for lado in (640, 416):  # el edge detecta a 640 y el servidor a 416
        for pesos in (a.base, destino):
            for clase in propias:
                medir(str(pesos), clases, clase, a.datos, lado)
