#!/bin/zsh
# Se abre en Terminal.app (que sí puede pedir permiso de cámara).
# Prueba índices 0-2 y guarda una foto de cada uno en data/prueba_camara_N.jpg
cd "$(dirname "$0")"
mkdir -p data
.venv/bin/python -I -c "
import cv2
for i in range(3):
    c = cv2.VideoCapture(i)
    ok, img = c.read() if c.isOpened() else (False, None)
    if ok:
        cv2.imwrite(f'data/prueba_camara_{i}.jpg', img)
    print(i, 'ok' if ok else 'no', int(c.get(3)), 'x', int(c.get(4)))
    c.release()
" 2>&1 | grep -v WARN | tee data/camaras.txt
echo "Listo. Puedes cerrar esta ventana."
