"""Junta sensores (ESP32 por serial) y cámara en data/.

  data/sensores.jsonl  una lectura por línea, con timestamp del Mac
  data/frames/*.jpg    una foto cada --cada segundos

Uso: .venv/bin/python colector.py [--puerto /dev/cu.usbserial-0001] [--camara 0] [--cada 5]
"""
import argparse, json, time
from datetime import datetime
from pathlib import Path

import cv2
import serial


def parsear(linea: bytes):
    """Línea JSON del ESP32 -> dict con ts, o None si viene basura (boot log, ruido)."""
    try:
        d = json.loads(linea.decode(errors="ignore").strip())
    except ValueError:
        return None
    if not isinstance(d, dict):
        return None
    d["ts"] = datetime.now().isoformat(timespec="milliseconds")
    return d


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--puerto", default="/dev/cu.usbserial-0001")
    ap.add_argument("--camara", type=int, default=0, help="-1 para no usar cámara")
    ap.add_argument("--cada", type=float, default=5.0, help="segundos entre fotos")
    a = ap.parse_args()

    frames = Path("data/frames"); frames.mkdir(parents=True, exist_ok=True)
    log = open("data/sensores.jsonl", "a", buffering=1)
    # exclusivo, igual que edge.py: dos procesos leyendo el mismo CP2102 lo traban hasta desenchufarlo
    esp = serial.Serial(a.puerto, 115200, timeout=0.2, exclusive=True)
    cam = cv2.VideoCapture(a.camara) if a.camara >= 0 else None
    if cam is not None and not cam.isOpened():
        raise SystemExit(f"No pude abrir la cámara {a.camara} (¿permiso de cámara para la terminal?)")

    ultima_foto = 0.0
    print("Colectando… Ctrl+C para parar")
    try:
        while True:
            # solo leer si hay bytes: un readline vacío bloquearía el ciclo de la cámara
            d = parsear(esp.readline()) if esp.in_waiting else None
            if d is None:
                time.sleep(0.01)
            if d:
                log.write(json.dumps(d) + "\n")
                print(d)
            if cam is not None and time.time() - ultima_foto >= a.cada:
                ultima_foto = time.time()  # medir desde el inicio: guardar la foto no alarga el intervalo
                ok, img = cam.read()
                if ok:
                    cv2.imwrite(str(frames / f"{datetime.now():%Y%m%d-%H%M%S-%f}.jpg"), img)  # µs: varias fotos por segundo
    except KeyboardInterrupt:
        pass
    finally:
        esp.close(); log.close()
        if cam is not None: cam.release()


if __name__ == "__main__":
    assert parsear(b'{"ms":1,"temp_c":null,"dist_cm":12.5}\n')["dist_cm"] == 12.5
    assert parsear(b"ets Jun  8 2016 rst:0x1") is None and parsear(b"42") is None
    main()
