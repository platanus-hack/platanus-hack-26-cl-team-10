#!/bin/bash
# Sube la rama actual a la VM del demo y la reinicia. La bitácora vive en /srv/factum/datos y sobrevive.
# Uso: deploy/vm/desplegar.sh
set -euo pipefail
cd "$(dirname "$0")/../.."
PROYECTO=${PROYECTO:-loyal-venture-448814-f7}
ZONA=${ZONA:-southamerica-west1-a}
VM=${VM:-factum-vm}
DOMINIO=${DOMINIO:-34-176-44-192.sslip.io}
CUENTA=${CUENTA:-$(gcloud config get-value account 2>/dev/null)}
G="--zone=$ZONA --project=$PROYECTO --account=$CUENTA --quiet"

paquete=$(mktemp -d)/factum.tgz
COPYFILE_DISABLE=1 tar czf "$paquete" pyproject.toml uv.lock app datos/pauta-*.json tests/test_mineria.py tests/test_electrica.py tests/test_construccion.py
# /tmp es compartido: lo que dejó el deploy de otro usuario no se puede sobrescribir
gcloud compute ssh "$VM" $G --command="sudo rm -f /tmp/factum.tgz /tmp/instalar.sh"
gcloud compute scp "$paquete" deploy/vm/instalar.sh "$VM":/tmp/ $G
gcloud compute ssh "$VM" $G --command="sudo DOMINIO=$DOMINIO bash /tmp/instalar.sh"
echo "Listo: https://$DOMINIO/agente"
