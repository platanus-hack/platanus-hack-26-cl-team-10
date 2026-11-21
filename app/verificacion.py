"""FRENTE 3 — verificación.

La capa 1 ya es real: lee los sensores desde la base y app/reglas.py decide.

Capa 2 de cámara: el modelo del edge (YOLO) decide cuando está seguro
(reglas.por_deteccion). Cuando no le alcanza la certeza, el paso sube acá.

Capa 3 de cámara: un VLM (Gemini) mira el último cuadro del edge y responde la
pregunta visual del paso con (respuesta, confianza). Se activa con la variable
GEMINI_API_KEY; el modelo se cambia con GEMINI_MODELO. Sin key, o sin cuadro,
queda el stub de ensayo de siempre, para poder ensayar el demo sin red.

La capa 2 de señales todavía no cierra pasos. Detecta anomalías y abre la OT.
"""

from __future__ import annotations

import json
import logging
import os

log = logging.getLogger(__name__)

# Estable, el más rápido y barato de la familia 3.5 (docs de modelos de Gemini, nov 2026).
MODELO_POR_DEFECTO = "gemini-3.5-flash-lite"
TIMEOUT_MS = 15_000

INSTRUCCION = (
    "Eres el verificador visual de un procedimiento de mantenimiento industrial. "
    "Recibes una foto de la cámara de la estación y una pregunta de sí o no sobre ella. "
    "Responde solo lo que la foto muestra: si no se ve con claridad, la respuesta es no. "
    "La confianza va de 0 a 1 y dice cuán seguro estás de tu respuesta."
)
ESQUEMA = {
    "type": "object",
    "properties": {
        "respuesta": {"type": "boolean"},
        "confianza": {"type": "number"},
    },
    "required": ["respuesta", "confianza"],
}

# Permite forzar la respuesta de la cámara durante un ensayo del demo.
_FORZAR: dict[str, bool] = {}
_cliente = None


def forzar_camara(pregunta: str, respuesta: bool) -> None:
    _FORZAR[pregunta] = respuesta


def limpiar_forzados() -> None:
    _FORZAR.clear()


def juez_camara(pregunta: str, cuadro: bytes | None = None) -> tuple[bool, float]:
    """Capa 3: (respuesta, confianza) para la pregunta visual del paso sobre `cuadro`.

    El cuadro lo entrega app/servicios.py: es el último que mandó la cámara del edge
    que ejecuta la OT (app/video.py). La firma de reglas.JuezCamara no cambia.

    Si el VLM falla (red, cuota, respuesta rara) responde (False, 0.0): no verifica el
    paso y queda a la vista como warning de capa 3, nunca lo cierra por error.
    """
    if pregunta in _FORZAR:
        return _FORZAR[pregunta], 0.91
    if cuadro is None or not os.environ.get("GEMINI_API_KEY"):
        return True, 0.55  # stub de ensayo: sin VLM conectado
    try:
        return preguntar_gemini(pregunta, cuadro)
    except Exception:  # noqa: BLE001 - cualquier falla del VLM se trata igual: no verifica
        log.exception("el VLM no pudo juzgar «%s»", pregunta)
        return False, 0.0


def preguntar_gemini(pregunta: str, cuadro: bytes, cliente=None) -> tuple[bool, float]:
    from google.genai import types

    global _cliente
    if cliente is None:
        if _cliente is None:
            from google import genai
            _cliente = genai.Client(http_options=types.HttpOptions(timeout=TIMEOUT_MS))  # lee GEMINI_API_KEY
        cliente = _cliente
    r = cliente.models.generate_content(
        model=os.environ.get("GEMINI_MODELO", MODELO_POR_DEFECTO),
        contents=[types.Part.from_bytes(data=cuadro, mime_type="image/jpeg"), pregunta],
        config=types.GenerateContentConfig(
            system_instruction=INSTRUCCION,
            response_mime_type="application/json",
            response_json_schema=ESQUEMA,
        ),
    )
    d = json.loads(r.text)
    return bool(d["respuesta"]), min(1.0, max(0.0, float(d["confianza"])))
