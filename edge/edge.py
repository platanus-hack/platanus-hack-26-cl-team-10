"""Edge en vivo: cámara + ESP32 (+ modelo, según el modo) → servidor (app/), en hilos.

Dos modos de detección (--deteccion):
  servidor  (por defecto) el edge manda solo video y sensores; YOLO corre en la API
            (app/detector.py, ONNX). El edge no necesita GPU ni modelo.
  edge      YOLO-World corre acá, en el Mac, y manda las detecciones. Más rápido
            (~18/s contra ~5/s en la VM) y no carga el servidor.

  video        JPEG a --fps por WS /edge/{id}/video (mensajes binarios)
  detecciones  (modo edge) YOLO-World sobre el último cuadro, por el mismo WS (texto):
               {"tipo": "detecciones", "modelo", "ts", "objetos": [{"clase", "conf", "caja"}]}
               caja = x1, y1, x2, y2 normalizada 0-1. Se manda todo lo que pase --conf:
               qué es "alta certeza" lo decide el servidor. Busca siempre las de --clases,
               más las que pida la pauta de la OT en sesión (GET /edge/{id}/clases, cada 2 s).
  sensores     líneas JSON del ESP32 por serial → POST /edge/{id}/lecturas, con seq

Correr en Terminal.app (permiso de cámara): correr_edge.command, o
  .venv/bin/python edge.py --servidor http://localhost:8000
"""
import argparse, json, os, threading, time
import urllib.request

import cv2
import serial
import websocket

MODELO = "yolov8s-worldv2.pt"
SIN_DATOS_S = 10  # el ESP32 manda 1 línea/s: tanto silencio es un puerto muerto
CLASES_CADA_S = 2  # cada cuánto se pregunta qué clases pide la OT en sesión


class Canal:
    """El WS de video del edge. Si se corta, reconecta; lo que no se pudo mandar se pierde."""

    def __init__(self, url):
        self.url, self.ws, self.lock = url, None, threading.Lock()

    def mandar(self, dato, binario):
        with self.lock:
            try:
                if self.ws is None:
                    self.ws = websocket.create_connection(self.url, timeout=5)
                    threading.Thread(target=self._leer, args=(self.ws,), daemon=True).start()
                    print(f"[ws] conectado a {self.url}")
                (self.ws.send_binary if binario else self.ws.send)(dato)
                return True
            except (OSError, websocket.WebSocketException) as e:
                print(f"[ws] sin conexión ({e}); reintento")
                self.ws = None
                time.sleep(1)
                return False

    @staticmethod
    def _leer(ws):
        """El servidor solo responde si algo llegó mal: se muestra para corregirlo."""
        try:
            while True:
                print(f"[ws] servidor: {ws.recv()}")
        except (OSError, websocket.WebSocketException):
            pass


def objetos_de(r, clases):
    """Resultado de YOLO → lista para el servidor (caja normalizada 0-1)."""
    return [{"clase": clases[int(c)], "conf": round(float(p), 3), "caja": [round(float(v), 4) for v in caja]}
            for c, p, caja in zip(r.boxes.cls, r.boxes.conf, r.boxes.xyxyn)]


def clases_de_la_ot(servidor, edge_id):
    """Las clases que pide la pauta de la OT en sesión en este edge. None si el servidor no responde."""
    try:
        with urllib.request.urlopen(f"{servidor}/edge/{edge_id}/clases", timeout=3) as r:
            return list(json.load(r)["clases"])
    except (OSError, ValueError, KeyError, TypeError):
        return None


def hilo_detecciones(canal, ultimo, base, conf, stats, servidor, edge_id, pesos=MODELO):
    import torch
    from ultralytics import YOLOWorld
    device = "mps" if torch.backends.mps.is_available() else "cpu"
    modelo, clases, visto, t_clases = None, [], None, 0.0
    while True:
        if time.time() - t_clases >= CLASES_CADA_S:
            t_clases = time.time()
            pedidas = clases_de_la_ot(servidor, edge_id)
            # sin respuesta del servidor se sigue con las que había, o con las de siempre al partir
            nuevas = clases if pedidas is None and clases else base + [c for c in pedidas or [] if c not in base]
            if nuevas != clases:
                clases = nuevas
                modelo = YOLOWorld(pesos)  # uno nuevo por lista: set_classes después de predecir falla en MPS
                modelo.set_classes(clases)
                print(f"[detector] clases: {', '.join(clases)}")
        cuadro = ultimo["img"]
        if modelo is None or cuadro is None or cuadro is visto:
            time.sleep(0.01); continue
        visto = cuadro
        r = modelo.predict(cuadro, conf=conf, device=device, imgsz=640, verbose=False)[0]
        msg = {"tipo": "detecciones", "modelo": os.path.basename(pesos), "ts": time.time(), "objetos": objetos_de(r, clases),
               "clases": clases}  # el servidor solo cree "ya no está" de un detector que buscaba la clase
        if canal.mandar(json.dumps(msg), binario=False):
            stats["det"] += 1


def estados(d, dist_previa, dist_max, temp_max):
    """Estados discretos para las pautas: las reglas del servidor comparan igualdad, no rangos.
    operario 'presente' solo si las 2 últimas distancias están cerca (filtra ecos sueltos)."""
    e = {}
    dist = d.get("dist_cm")
    cerca = lambda x: x is not None and x < dist_max
    e["operario"] = "presente" if cerca(dist) and cerca(dist_previa) else "ausente"
    if d.get("temp_c") is not None:
        e["equipo"] = "frio" if d["temp_c"] < temp_max else "caliente"
    if d.get("motor") is not None:
        e["energia"] = "viva" if d["motor"] else "cortada"  # lo que leen la pauta del demo y la regla de peligro
        e["motor"] = "activo" if d["motor"] else "detenido"  # el mismo dato, como se muestra en el dashboard
    return e


def hilo_sensores(servidor, edge_id, puerto, stats, dist_max, temp_max):
    """Si el puerto no se puede abrir (otro proceso aún lo suelta, USB desconectado) o se
    cae, reintenta cada 2 s: un hilo de sensores muerto no avisa a nadie."""
    while True:
        try:
            _leer_y_enviar(servidor, edge_id, puerto, stats, dist_max, temp_max)
        except (serial.SerialException, OSError) as e:
            print(f"[sensores] ESP32 no disponible ({e}); reintento en 2 s")
            time.sleep(2)
        except Exception as e:  # noqa: BLE001 - nada debe matar este hilo: sin él no hay sensores
            print(f"[sensores] error inesperado ({e!r}); reabro el puerto en 2 s")
            time.sleep(2)


def _leer_y_enviar(servidor, edge_id, puerto, stats, dist_max, temp_max):
    url = f"{servidor}/edge/{edge_id}/lecturas"
    seq = int(time.time() * 1000)  # crece entre reinicios: el servidor descarta seq repetidos
    # exclusivo: dos procesos leyendo el mismo CP2102 pueden trabar el adaptador hasta desenchufarlo
    esp = serial.Serial(puerto, 115200, timeout=2, exclusive=True)
    print(f"[sensores] leyendo {puerto}")
    dist_previa, ultimo_dato = None, time.time()
    while True:
        linea = esp.readline()
        if linea:
            ultimo_dato = time.time()
        elif time.time() - ultimo_dato > SIN_DATOS_S:
            # tras desconectar el USB el puerto viejo devuelve vacío para siempre, sin error
            esp.close()
            raise serial.SerialException(f"{SIN_DATOS_S:g} s sin datos del ESP32")
        try:
            d = json.loads(linea.decode(errors="ignore"))
        except ValueError:
            continue  # boot log, línea cortada o vacía
        if not isinstance(d, dict):
            continue  # un pedazo de línea como "5}" se lee como número, no como lectura
        lote = []
        crudos = {k: d[k] for k in ("temp_c", "hum_pct", "dist_cm") if d.get(k) is not None}  # null = sin lectura
        for k, v in {**crudos, **estados(d, dist_previa, dist_max, temp_max)}.items():
            seq += 1
            lote.append({"sensor_id": k, "valor": str(v), "seq": seq})
        dist_previa = d.get("dist_cm")
        if not lote:
            continue
        req = urllib.request.Request(url, json.dumps(lote).encode(), {"Content-Type": "application/json"})
        try:
            urllib.request.urlopen(req, timeout=3).read()
            stats["lect"] += len(lote)
        except OSError as e:  # el servidor no responde: se pierde este lote, el puerto sigue abierto
            print(f"[sensores] no se pudo enviar: {e}")
        except Exception as e:  # noqa: BLE001 - cualquier otra falla del envío no debe matar la lectura
            print(f"[sensores] error al enviar: {e!r}")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--servidor", default="http://localhost:8000")
    ap.add_argument("--edge", default="edge-1")
    ap.add_argument("--camara", type=int, default=0)
    ap.add_argument("--fps", type=float, default=20)
    ap.add_argument("--ancho", type=int, default=960, help="ancho del JPEG enviado (alto en 16:9)")
    ap.add_argument("--calidad", type=int, default=65, help="calidad JPEG 1-100")
    # "soda can" va junto a "red soda can" para que una lata de otro color no caiga en la roja
    ap.add_argument("--clases", nargs="+", default=["mouse", "pencil", "soda can", "red soda can", "green soda can"],
                    help="las que el detector busca siempre; se suman las que pida la pauta de la OT en sesión")
    ap.add_argument("--pesos", default=MODELO, help="modelo afinado con entrenar.py, p. ej. ../datos/modelos/yolo-factum.pt")
    ap.add_argument("--conf", type=float, default=0.25, help="piso para mandar una detección")
    ap.add_argument("--deteccion", choices=["servidor", "edge"], default="servidor",
                    help="dónde corre YOLO: servidor (por defecto, el edge solo manda video y sensores) o edge (acá)")
    ap.add_argument("--puerto", default="/dev/cu.usbserial-0001", help="'' para no leer sensores")
    ap.add_argument("--dist-max", type=float, default=60, help="cm: más cerca = operario presente")
    ap.add_argument("--temp-max", type=float, default=26, help="°C: bajo esto = equipo frío")
    a = ap.parse_args()

    servidor = a.servidor.rstrip("/")
    canal = Canal(servidor.replace("http", "ws", 1) + f"/edge/{a.edge}/video")
    stats = {"video": 0, "det": 0, "lect": 0}
    ultimo = {"img": None}

    cam = cv2.VideoCapture(a.camara)
    cam.set(cv2.CAP_PROP_FRAME_WIDTH, 1280); cam.set(cv2.CAP_PROP_FRAME_HEIGHT, 720)
    if not cam.isOpened():
        raise SystemExit(f"No pude abrir la cámara {a.camara}: corre esto en Terminal.app (permiso de cámara)")

    if a.deteccion == "edge":
        threading.Thread(target=hilo_detecciones, args=(canal, ultimo, a.clases, a.conf, stats, servidor, a.edge, a.pesos),
                         daemon=True).start()
    if a.puerto:
        threading.Thread(target=hilo_sensores, args=(servidor, a.edge, a.puerto, stats, a.dist_max, a.temp_max),
                         daemon=True).start()

    alto = a.ancho * 9 // 16
    periodo, t_stats = 1 / a.fps, time.time()
    print(f"Edge {a.edge} → {servidor}  ({a.fps:g} fps, {a.ancho}x{alto}, detección en {a.deteccion}). Ctrl+C para parar")
    try:
        while True:
            t0 = time.time()
            ok, img = cam.read()
            if ok:
                img = cv2.resize(img, (a.ancho, alto))
                ultimo["img"] = img
                ok, jpg = cv2.imencode(".jpg", img, [cv2.IMWRITE_JPEG_QUALITY, a.calidad])
                if ok and canal.mandar(jpg.tobytes(), binario=True):
                    stats["video"] += 1
            if time.time() - t_stats >= 5:
                dt = time.time() - t_stats
                print(f"video {stats['video'] / dt:.1f} fps · detecciones {stats['det'] / dt:.1f}/s · "
                      f"lecturas {stats['lect']} en {dt:.0f} s")
                stats.update(video=0, det=0, lect=0); t_stats = time.time()
            time.sleep(max(0, periodo - (time.time() - t0)))
    except KeyboardInterrupt:
        pass
    finally:
        cam.release()


if __name__ == "__main__":
    main()
