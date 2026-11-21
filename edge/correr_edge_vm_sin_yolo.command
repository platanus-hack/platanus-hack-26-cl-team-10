#!/bin/zsh
# Experimento: YOLO corre en la VM. El edge solo manda video y sensores (edge-mac). Ctrl+C para parar.
cd "$(dirname "$0")"
.venv/bin/python edge.py --servidor https://34-176-44-192.sslip.io --edge edge-mac --sin-yolo
