#!/bin/bash
# Despliega el front a producción en Vercel. Sube lo que está en `main` (origin/main), no lo que
# haya en esta carpeta: el trabajo en curso vive en su rama y no llega a producción por accidente.
# Uso: deploy/vercel/desplegar.sh   (o `npm run desplegar` desde web/)
# Una vez por máquina: `vercel login` y, en web/, `vercel link`.
set -euo pipefail
raiz=$(cd "$(dirname "$0")/../.." && pwd)
enlace="$raiz/web/.vercel/project.json"
[ -f "$enlace" ] || { echo "Falta el enlace al proyecto de Vercel: corre \`vercel link\` en web/." >&2; exit 1; }

# main en una copia aparte: así no importa en qué rama esté esta carpeta ni qué tenga a medias.
git -C "$raiz" fetch --quiet origin main
copia=$(mktemp -d)
trap 'git -C "$raiz" worktree remove --force "$copia" >/dev/null 2>&1 || rm -rf "$copia"' EXIT
git -C "$raiz" worktree add --quiet --detach "$copia" origin/main
echo "Desplegando main: $(git -C "$copia" log -1 --format='%h %s')"

mkdir -p "$copia/web/.vercel"
cp "$enlace" "$copia/web/.vercel/"
cd "$copia/web"
echo "Instalando dependencias…"
npm ci --silent
npm run --silent build:funcion
vercel pull --yes --environment=production >/dev/null
vercel build --prod
vercel deploy --prebuilt --prod
