#!/bin/zsh
# Cámara + ESP32 en vivo hacia la VM del demo, como workstation. Ctrl+C para parar.
# Modo por defecto: YOLO corre en el servidor; acá solo video y sensores.
# Se corre en Terminal.app (permiso de cámara). La OT se une a workstation con POST /ot/{id}/sesion.
cd "$(dirname "$0")"
.venv/bin/python edge.py --servidor https://34-176-44-192.sslip.io --edge workstation --deteccion servidor
