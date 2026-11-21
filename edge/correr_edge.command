#!/bin/zsh
# Cámara + ESP32 (+ YOLO según el modo) en vivo hacia el servidor. Ctrl+C para parar.
# Se corre en Terminal.app porque Claude Code no tiene permiso de cámara.
# Servidor por defecto: local. Para la VM: SERVIDOR=https://34-176-44-192.sslip.io ./correr_edge.command
# Detección por defecto en el servidor (necesita DETECTOR_ONNX allá); con YOLO acá: DETECCION=edge
cd "$(dirname "$0")"
.venv/bin/python edge.py --servidor "${SERVIDOR:-http://localhost:8000}" --deteccion "${DETECCION:-servidor}"
