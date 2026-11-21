"""Demo: verificación paso a paso de un bloqueo LOTO con cámara + sensores.

Lee lo que deja colector.py (data/sensores.jsonl y data/frames/), detecta la tarjeta
y la herramienta con YOLO-World, avanza el protocolo y avisa (texto + voz) si se salta
un paso. Al cerrar guarda la evidencia de la orden de trabajo en data/ot/<id>/.

Uso: .venv/bin/python loto.py [--temp-max 26] [--dist-max 60]
"""
import argparse, json, subprocess, time
from collections import deque
from datetime import datetime
from pathlib import Path

# prompts de YOLO-World: [0] = dispositivo de bloqueo (hace de tarjeta LOTO), [1] = herramienta
CLASES = ["mouse", "pencil"]
BLOQUEO, HERRAMIENTA = "mouse", "lápiz"  # nombres en pantalla
PASOS = [
    "Operario llega al equipo",                      # HC-SR04
    f"Bloqueo puesto ({BLOQUEO})",                   # visión
    "Energía cero: equipo frío",                     # DHT22
    f"Intervención: {HERRAMIENTA} en zona",          # visión
    f"{HERRAMIENTA.capitalize()} retirado",          # visión
    f"Bloqueo retirado ({BLOQUEO}): OT cerrada",     # visión
]
FIN = len(PASOS)


def avanzar(paso, o, temp_max=26.0, dist_max=60.0):
    """(paso, observación) -> (paso siguiente, alerta o None).
    o = {"dist": cm|None, "temp": °C|None, "tarjeta": bool, "herramienta": bool}"""
    if paso < FIN and o["herramienta"] and not o["tarjeta"]:
        if paso >= 4:
            return paso, "Bloqueo retirado con herramientas en la zona"
        return paso, "Intervención sin bloqueo"
    frio = o["temp"] is not None and o["temp"] < temp_max
    if paso == 2 and o["herramienta"] and not frio:
        return paso, "Intervención antes de verificar energía cero"

    listo = [
        o["dist"] is not None and o["dist"] < dist_max,
        o["tarjeta"],
        frio,
        o["herramienta"] and o["tarjeta"],
        o["tarjeta"] and not o["herramienta"],
        not o["tarjeta"],
    ]
    return (paso + 1 if paso < FIN and listo[paso] else paso), None


def ultimas_lecturas(n=2):
    """Últimas n lecturas del ESP32 (la más nueva al final)."""
    try:
        with open("data/sensores.jsonl", "rb") as f:
            f.seek(0, 2); f.seek(max(0, f.tell() - 1024))
            return [json.loads(l) for l in f.read().splitlines()[-n:]]
    except (OSError, ValueError):
        return []


def mostrar(paso, alerta, o):
    print("\033[2J\033[H🔒  Protocolo LOTO — verificación en vivo\n")
    for i, p in enumerate(PASOS):
        print(f"  {'✅' if i < paso else '👉' if i == paso else '⬜'}  {i + 1}. {p}")
    print(f"\n  dist={o['dist']} cm  temp={o['temp']} °C  "
          f"{BLOQUEO}={'sí' if o['tarjeta'] else 'no'}  {HERRAMIENTA}={'sí' if o['herramienta'] else 'no'}")
    if alerta:
        print(f"\n  🚨  {alerta.upper()}")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--temp-max", type=float, default=26.0)
    ap.add_argument("--dist-max", type=float, default=60.0)
    ap.add_argument("--conf", type=float, default=0.5)
    ap.add_argument("--estable", type=int, default=3, help="fotos seguidas que deben coincidir para cambiar de estado")
    a = ap.parse_args()

    import torch
    from ultralytics import YOLOWorld
    modelo = YOLOWorld("yolov8s-worldv2.pt")
    modelo.set_classes(CLASES)
    device = "mps" if torch.backends.mps.is_available() else "cpu"

    ot = Path("data/ot") / datetime.now().strftime("OT-%Y%m%d-%H%M%S")
    ot.mkdir(parents=True)
    paso, alerta_previa, ultimo_frame, r = 0, None, None, None
    o = {"dist": None, "temp": None, "tarjeta": False, "herramienta": False}
    evidencia = []
    historial = {k: deque(maxlen=a.estable) for k in ("tarjeta", "herramienta")}

    while paso < FIN:
        frames = sorted(Path("data/frames").glob("*.jpg"))
        if frames and frames[-1] != ultimo_frame:
            ultimo_frame = frames[-1]
            res = modelo.predict(str(ultimo_frame), conf=a.conf, device=device, verbose=False)
            if res:  # vacío si el colector aún está escribiendo la foto: se usa la siguiente
                r = res[0]
                vistos = {int(b.cls) for b in r.boxes}
                historial["tarjeta"].append(0 in vistos)
                historial["herramienta"].append(1 in vistos)
                for k, h in historial.items():  # cambia solo si las últimas N fotos coinciden
                    if len(h) == a.estable and len(set(h)) == 1:
                        o[k] = h[0]
        lecturas = ultimas_lecturas(2)
        s = lecturas[-1] if lecturas else {}
        dists = [x.get("dist_cm") for x in lecturas]
        # operario "cerca" solo si las 2 últimas lecturas lo ven (filtra ecos sueltos)
        o["dist"] = max(dists) if len(dists) == 2 and None not in dists else None
        o["temp"] = s.get("temp_c")

        nuevo, alerta = avanzar(paso, o, a.temp_max, a.dist_max)
        if nuevo > paso:
            foto = ot / f"paso{nuevo}.jpg"
            if r is not None:
                r.save(filename=str(foto))
            evidencia.append({"paso": PASOS[paso], "ts": datetime.now().isoformat(timespec="seconds"),
                              "sensores": s, "foto": foto.name if r is not None else None})
            paso = nuevo
        if alerta and alerta != alerta_previa:
            print("\a", end="")
            subprocess.Popen(["say", "-v", "Paulina", alerta])  # voz en español de macOS
        alerta_previa = alerta
        mostrar(paso, alerta, o)
        ventana(r, paso, alerta, 200)

    (ot / "evidencia.json").write_text(json.dumps(evidencia, indent=2, ensure_ascii=False))
    subprocess.Popen(["say", "-v", "Paulina", "Orden de trabajo cerrada"])
    print(f"\n  ✅  OT cerrada. Evidencia en {ot}/")
    ventana(r, paso, None, 4000)


def ventana(r, paso, alerta, ms):
    """Muestra la última foto anotada con el paso actual; espera ms milisegundos."""
    import cv2, unicodedata
    if r is None:
        time.sleep(ms / 1000); return
    img = r.plot()
    sin_tildes = lambda t: unicodedata.normalize("NFKD", t).encode("ascii", "ignore").decode()  # putText no dibuja tildes
    titulo = "OT CERRADA" if paso >= FIN else f"Paso {paso + 1}/{FIN}: {PASOS[paso]}"
    cv2.rectangle(img, (0, 0), (img.shape[1], 70), (40, 40, 40), -1)
    cv2.putText(img, sin_tildes(titulo), (20, 48), cv2.FONT_HERSHEY_SIMPLEX, 1.4,
                (0, 200, 0) if paso >= FIN else (255, 255, 255), 3)
    if alerta:
        cv2.rectangle(img, (0, 70), (img.shape[1], 140), (0, 0, 220), -1)
        cv2.putText(img, sin_tildes(alerta.upper()), (20, 118), cv2.FONT_HERSHEY_SIMPLEX, 1.3, (255, 255, 255), 3)
    cv2.imshow("LOTO - camara", cv2.resize(img, (img.shape[1] // 2, img.shape[0] // 2)))
    cv2.waitKey(ms)


def autotest():
    """Self-check de la lógica del protocolo."""
    def obs(dist=None, temp=25.0, tarjeta=False, herramienta=False):
        return {"dist": dist, "temp": temp, "tarjeta": tarjeta, "herramienta": herramienta}
    p = 0
    for x in [obs(dist=40), obs(dist=40, tarjeta=True), obs(tarjeta=True),
              obs(tarjeta=True, herramienta=True), obs(tarjeta=True), obs()]:
        p, al = avanzar(p, x); assert al is None, al
    assert p == FIN
    assert avanzar(1, obs(herramienta=True)) == (1, "Intervención sin bloqueo")
    assert avanzar(2, obs(temp=40, tarjeta=True, herramienta=True))[1] == "Intervención antes de verificar energía cero"
    assert avanzar(4, obs(herramienta=True)) == (4, "Bloqueo retirado con herramientas en la zona")
    assert avanzar(2, obs(temp=40, tarjeta=True)) == (2, None)  # no avanza con equipo caliente
    assert avanzar(2, obs(temp=25, tarjeta=True, herramienta=True)) == (3, None)  # frío: herramienta ok


if __name__ == "__main__":
    autotest()
    main()
