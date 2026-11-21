#!/bin/bash
set -euo pipefail
DOMINIO=${DOMINIO:?falta DOMINIO}
export DEBIAN_FRONTEND=noninteractive
apt-get update -qq
apt-get install -y -qq curl ca-certificates debian-keyring debian-archive-keyring apt-transport-https gnupg >/dev/null
if ! command -v caddy >/dev/null; then
  curl -1sLf https://dl.cloudsmith.io/public/caddy/stable/gpg.key | gpg --dearmor -o /usr/share/keyrings/caddy-stable-archive-keyring.gpg
  curl -1sLf https://dl.cloudsmith.io/public/caddy/stable/debian.deb.txt > /etc/apt/sources.list.d/caddy-stable.list
  apt-get update -qq && apt-get install -y -qq caddy >/dev/null
fi
id factum >/dev/null 2>&1 || useradd --system --create-home --home-dir /srv/factum --shell /usr/sbin/nologin factum
if ! command -v uv >/dev/null; then curl -LsSf https://astral.sh/uv/install.sh | env UV_INSTALL_DIR=/usr/local/bin sh >/dev/null; fi
mkdir -p /srv/factum/app-nueva && tar xzf /tmp/factum.tgz -C /srv/factum/app-nueva
rm -rf /srv/factum/codigo && mv /srv/factum/app-nueva /srv/factum/codigo
mkdir -p /srv/factum/datos/evidencias /srv/factum/datos/modelos  # destino del enlace datos/evidencias: sin esto queda roto y guardar_evidencia falla
ln -sfn /srv/factum/datos/bitacora.sqlite3 /srv/factum/codigo/datos/bitacora.sqlite3
ln -sfn /srv/factum/datos/evidencias /srv/factum/codigo/datos/evidencias
chown -R factum:factum /srv/factum
sudo -u factum env HOME=/srv/factum UV_PYTHON_INSTALL_DIR=/srv/factum/.python bash -c 'cd /srv/factum/codigo && uv sync --frozen --no-dev -q'
cat > /etc/systemd/system/factum.service <<UNIDAD
[Unit]
Description=Factum API
After=network-online.target
[Service]
User=factum
WorkingDirectory=/srv/factum/codigo
# Modo de detección por defecto: YOLO en el servidor (app/detector.py). Para volver a
# YOLO en el edge, DETECTOR_ONNX= (vacío) en /srv/factum/entorno y el edge con --deteccion edge.
Environment=DETECTOR_ONNX=/srv/factum/datos/modelos/yolo-mouse-pencil-416.onnx
Environment=VENTANA_DETECCION_S=1.5
# Secretos y overrides fuera del repo: ANTHROPIC_API_KEY=... (capa 3 de cámara). El "-" lo hace opcional.
EnvironmentFile=-/srv/factum/entorno
ExecStart=/srv/factum/codigo/.venv/bin/uvicorn app.api:app --host 127.0.0.1 --port 8000 --proxy-headers --forwarded-allow-ips 127.0.0.1 --timeout-graceful-shutdown 3
Restart=always
RestartSec=2
[Install]
WantedBy=multi-user.target
UNIDAD
cat > /etc/caddy/Caddyfile <<CADDY
$DOMINIO {
	reverse_proxy 127.0.0.1:8000
}
CADDY
systemctl daemon-reload
systemctl enable --now factum >/dev/null 2>&1
systemctl restart factum caddy
sleep 3
systemctl is-active factum caddy
curl -s -o /dev/null -w "local %{http_code}\n" http://127.0.0.1:8000/agente
