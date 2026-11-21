"""GET /voz?texto= — el aviso en voz, con ElevenLabs.

El front pide acá el audio del `detalle` de cada evento de nivel error y lo reproduce
(knowledge/architecture/FRONTEND.md §7). La llave vive solo en el servidor:
ELEVENLABS_API_KEY, y opcionalmente ELEVENLABS_VOICE_ID.

La llamada es la que ya funciona en elevenlabs-tts/tts.py, con el modelo de menor
latencia. Cada texto se pide una sola vez: el audio queda en datos/voz/, así que un
aviso que se repite suena sin esperar a ElevenLabs.
"""

from __future__ import annotations

import hashlib
import json
import os
import urllib.error
import urllib.request
from pathlib import Path

from fastapi import APIRouter
from fastapi.responses import FileResponse, JSONResponse, Response

API = "https://api.elevenlabs.io/v1"
MODELO = "eleven_flash_v2_5"
VOZ_POR_DEFECTO = "JBFqnCBsd6RMkjVDRZzb"  # la de tts.py; se cambia con ELEVENLABS_VOICE_ID
MAX_TEXTO = 300
CARPETA = Path(__file__).resolve().parent.parent / "datos" / "voz"

router = APIRouter()


def pedir_audio(texto: str, voice_id: str, llave: str) -> bytes:
    """Una llamada a ElevenLabs; devuelve el MP3 completo."""
    req = urllib.request.Request(
        f"{API}/text-to-speech/{voice_id}?output_format=mp3_44100_128",
        method="POST",
        data=json.dumps({"text": texto, "model_id": MODELO}).encode(),
        headers={"xi-api-key": llave, "Content-Type": "application/json"},
    )
    with urllib.request.urlopen(req, timeout=15) as resp:
        return resp.read()


def _error(status: int, mensaje: str) -> JSONResponse:
    return JSONResponse(status_code=status, content={"voz": mensaje})


@router.get("/voz")
def voz(texto: str) -> Response:
    texto = texto.strip()
    if not texto or len(texto) > MAX_TEXTO:
        return _error(422, f"el texto tiene que tener entre 1 y {MAX_TEXTO} caracteres")

    voice_id = os.environ.get("ELEVENLABS_VOICE_ID") or VOZ_POR_DEFECTO
    clave = hashlib.sha256(f"{voice_id}:{MODELO}:{texto}".encode()).hexdigest()
    guardado = CARPETA / f"{clave}.mp3"
    if guardado.exists():
        return FileResponse(guardado, media_type="audio/mpeg")

    llave = os.environ.get("ELEVENLABS_API_KEY")
    if not llave:
        return _error(503, "falta ELEVENLABS_API_KEY")

    try:
        audio = pedir_audio(texto, voice_id, llave)
    except urllib.error.HTTPError as e:
        return _error(502, f"ElevenLabs respondió {e.code}")
    except urllib.error.URLError:
        return _error(502, "no se pudo llegar a ElevenLabs")

    CARPETA.mkdir(parents=True, exist_ok=True)
    temporal = guardado.with_suffix(".mp3.tmp")
    temporal.write_bytes(audio)
    temporal.replace(guardado)
    return Response(content=audio, media_type="audio/mpeg")
