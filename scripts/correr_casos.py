"""Corre el banco /casos en Chrome sin ventana y dice cuántos casos pasan.

Correr:  uv run python scripts/correr_casos.py [servidor] [--captura ruta.png] [--con-sesiones-ajenas]
Por defecto el servidor es http://localhost:8000. Sale con 0 solo si pasan todos.

El banco se niega a correr si el servidor tiene sesiones que no son suyas, porque los
sensores son globales; `--con-sesiones-ajenas` lo acepta a sabiendas.
Necesita Google Chrome y `websockets`, que ya viene con uvicorn[standard].
"""

import argparse
import base64
import json
import os
import shutil
import subprocess
import sys
import tempfile
import time
import urllib.parse
import urllib.request
from pathlib import Path

from websockets.sync.client import connect

CHROME = os.environ.get("CHROME") or next(
    (c for c in ("/Applications/Google Chrome.app/Contents/MacOS/Google Chrome",
                 shutil.which("google-chrome") or "", shutil.which("chromium") or "") if c and Path(c).exists()),
    None,
)
ESPERA_MAX_S = 180
ALTO_CAPTURA = 2300


class Pestana:
    def __init__(self, ws) -> None:
        self.ws = ws
        self.n = 0

    def pedir(self, metodo: str, **parametros) -> dict:
        self.n += 1
        self.ws.send(json.dumps({"id": self.n, "method": metodo, "params": parametros}))
        while True:
            m = json.loads(self.ws.recv())
            if m.get("id") == self.n:
                return m.get("result", {})

    def evaluar(self, expresion: str):
        r = self.pedir("Runtime.evaluate", expression=expresion, returnByValue=True)
        return r.get("result", {}).get("value")


def correr(pestana: Pestana, servidor: str, url: str, captura: str | None) -> int:
    pestana.pedir("Page.enable")
    pestana.pedir("Page.navigate", url=url)

    limite = time.time() + ESPERA_MAX_S
    estado = {}
    while time.time() < limite:
        time.sleep(0.5)
        estado = pestana.evaluar(
            "document.body && JSON.stringify({...document.body.dataset,"
            " total: typeof CASOS === 'undefined' ? 0 : CASOS.length,"
            " conexion: document.getElementById('conexion')?.textContent,"
            " bloqueado: document.getElementById('todos')?.disabled && !ocupado})"
        )
        estado = json.loads(estado) if estado else {}
        if estado.get("estado") == "terminado" and int(estado.get("corridos", 0)) == estado.get("total"):
            break
        if estado.get("bloqueado") and estado.get("estado") == "listo":
            print(f"{servidor}: el banco no corre porque hay sesiones ajenas. "
                  "Repite con --con-sesiones-ajenas si de verdad quieres.")
            return 3
    else:
        print(f"{servidor}: el banco no terminó en {ESPERA_MAX_S} s. Estado: {estado}")
        return 2

    detalle = json.loads(pestana.evaluar(
        "JSON.stringify(CASOS.map(k => ({id: k.id, sello: document.querySelector('#' + k.id + ' [data-sello]').textContent,"
        " fallas: [...document.querySelectorAll('#' + k.id + ' tr.no')].map(tr => [...tr.cells].slice(0, 3).map(td => td.textContent)),"
        " error: document.querySelector('#' + k.id + ' .fallo-general')?.textContent || null})))"
    ))
    print(f"{servidor} · {estado['conexion']}")
    for k in detalle:
        print(f"  {k['id']:<5} {k['sello']}")
        if k["error"]:
            print(f"        {k['error']}")
        for que, esperado, obtenido in k["fallas"]:
            print(f"        ✗ {que}\n          esperado {esperado}\n          obtenido {obtenido}")
    print(f"{estado['pasan']} de {estado['corridos']} pasan")

    if captura:
        pestana.pedir("Emulation.setDeviceMetricsOverride", width=1360, height=ALTO_CAPTURA, deviceScaleFactor=1, mobile=False)
        pestana.evaluar("window.scrollTo(0, 0)")
        time.sleep(0.3)
        png = pestana.pedir("Page.captureScreenshot", format="png")["data"]
        Path(captura).write_bytes(base64.b64decode(png))
        print(f"captura: {captura}")
    return 0 if int(estado["pasan"]) == estado["total"] else 1


def main() -> int:
    p = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    p.add_argument("servidor", nargs="?", default="http://localhost:8000")
    p.add_argument("--captura", help="guarda una imagen del resumen y las primeras tarjetas al terminar")
    p.add_argument("--con-sesiones-ajenas", action="store_true")
    p.add_argument("--clave", default=os.environ.get("CLAVE_EQUIPO"),
                   help="la clave del equipo, si el servidor la pide (por defecto, CLAVE_EQUIPO)")
    a = p.parse_args()
    if CHROME is None:
        print("No encuentro Chrome; define CHROME con la ruta del ejecutable.")
        return 2

    servidor = a.servidor.rstrip("/")
    url = f"{servidor}/casos?correr=todos" + ("&ajenas=ok" if a.con_sesiones_ajenas else "")
    if a.clave:
        url += "&clave=" + urllib.parse.quote(a.clave)
    perfil = tempfile.mkdtemp(prefix="casos-chrome-")
    chrome = subprocess.Popen(
        [CHROME, "--headless=new", "--remote-debugging-port=0", f"--user-data-dir={perfil}",
         "--no-first-run", "--window-size=1360,1000", "about:blank"],
        stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
    )
    try:
        puerto_en = Path(perfil) / "DevToolsActivePort"
        for _ in range(100):
            if puerto_en.exists() and puerto_en.read_text().strip():
                break
            time.sleep(0.1)
        puerto = puerto_en.read_text().split("\n")[0]
        pestanas = json.load(urllib.request.urlopen(f"http://127.0.0.1:{puerto}/json"))
        with connect(next(t for t in pestanas if t["type"] == "page")["webSocketDebuggerUrl"], max_size=None) as ws:
            return correr(Pestana(ws), servidor, url, a.captura)
    finally:
        chrome.terminate()
        shutil.rmtree(perfil, ignore_errors=True)


if __name__ == "__main__":
    sys.exit(main())
