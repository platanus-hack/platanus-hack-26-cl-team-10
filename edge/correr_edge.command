#!/bin/zsh
# Cámara + modelo + ESP32 en vivo hacia el servidor. Ctrl+C para parar.
# Se corre en Terminal.app porque Claude Code no tiene permiso de cámara.
# Servidor por defecto: local. Para la VM: SERVIDOR=https://34-176-44-192.sslip.io ./correr_edge.command
cd "$(dirname "$0")"
.venv/bin/python edge.py --servidor "${SERVIDOR:-http://localhost:8000}"
