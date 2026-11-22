#!/bin/zsh
# Modo alternativo: YOLO-World corre acá, en el Mac (~18 detecciones/s), y manda las detecciones a la VM.
# Si el servidor tiene su detector activo (DETECTOR_ONNX), ignora estas: apágalo para usar este modo.
cd "$(dirname "$0")"
.venv/bin/python edge.py --servidor https://34-176-44-192.sslip.io --edge edge-1 --deteccion edge
