#!/bin/zsh
# Sensores (ESP32) + cámara UGREEN (índice 0). Ctrl+C para parar.
# Se corre en Terminal.app porque Claude Code no tiene permiso de cámara.
cd "$(dirname "$0")"
.venv/bin/python colector.py --camara 0 --cada 0.5
