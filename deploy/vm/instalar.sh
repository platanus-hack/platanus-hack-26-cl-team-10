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
mkdir -p /srv/factum/datos
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
# Capa 3 de cámara: Gemini en Vertex AI con la service account de la VM (sin secretos).
Environment=GOOGLE_GENAI_USE_VERTEXAI=true
Environment=GOOGLE_CLOUD_PROJECT=loyal-venture-448814-f7
Environment=GOOGLE_CLOUD_LOCATION=global
# Secretos u overrides fuera del repo (p. ej. GEMINI_MODELO=...). El "-" lo hace opcional.
EnvironmentFile=-/srv/factum/entorno
ExecStart=/srv/factum/codigo/.venv/bin/uvicorn app.api:app --host 127.0.0.1 --port 8000 --proxy-headers --forwarded-allow-ips 127.0.0.1
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
