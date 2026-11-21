"""Prueba el juez de capa 3 (Claude) con el cuadro actual de la cámara del edge.

Necesita ANTHROPIC_API_KEY en el entorno. Para no dejar la key en el historial:
  read -s ANTHROPIC_API_KEY && export ANTHROPIC_API_KEY
  uv run python scripts/probar_vlm.py [--servidor http://localhost:8000] [--edge edge-1]
"""

import argparse
import os
import sys
import time
import urllib.request

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from app import verificacion  # noqa: E402

ap = argparse.ArgumentParser()
ap.add_argument("--servidor", default="http://localhost:8000")
ap.add_argument("--edge", default="edge-1")
ap.add_argument("preguntas", nargs="*", default=["¿Hay un mouse de computador sobre la mesa?",
                                                  "¿Hay un lápiz sobre la mesa?",
                                                  "¿Hay una taza de café sobre la mesa?"])
a = ap.parse_args()

if not verificacion.vlm_configurado():
    sys.exit("Falta ANTHROPIC_API_KEY: read -s ANTHROPIC_API_KEY && export ANTHROPIC_API_KEY")
cuadro = urllib.request.urlopen(f"{a.servidor.rstrip('/')}/edge/{a.edge}/cuadro.jpg", timeout=5).read()
print(f"cuadro de {a.edge}: {len(cuadro)} bytes · modelo {os.environ.get('VLM_MODELO', verificacion.MODELO_POR_DEFECTO)}")
for p in a.preguntas:
    t = time.time()
    r = verificacion.preguntar_claude(p, cuadro)
    print(f"  {p:45s} → {'sí' if r[0] else 'no'} ({r[1]:.0%})  {time.time() - t:.1f} s")
