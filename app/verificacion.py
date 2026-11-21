"""FRENTE 3 — verificación.

La capa 1 ya es real: lee los sensores desde la base y app/reglas.py decide.

Capa 2 de cámara: el modelo del edge (YOLO) decide cuando está seguro
(reglas.por_deteccion). Cuando no le alcanza la certeza, el paso sube acá.

Capa 3 de cámara: un VLM (Claude Haiku 5.5, multimodal y barato) mira el último
cuadro del edge y responde la pregunta visual del paso con (respuesta, confianza).
Se activa con ANTHROPIC_API_KEY; el modelo se cambia con VLM_MODELO. Sin key, o sin
cuadro, queda el stub de ensayo de siempre, para poder ensayar el demo sin red.

La capa 2 de señales todavía no cierra pasos. Detecta anomalías y abre la OT.
"""

from __future__ import annotations

import base64
import json
import logging
import os
import threading

log = logging.getLogger(__name__)

MODELO_POR_DEFECTO = "claude-haiku-5-5"  # multimodal, $0,10 / $0,50 por millón de tokens
TIMEOUT_S = 15.0
# /declarar es público y cada paso de cámara sin certeza llama al modelo: sin tope, cualquiera
# gasta la key. Al agotarse el juez deja de verificar (warning de capa 3) hasta reiniciar.
LLAMADAS_MAX = int(os.environ.get("VLM_MAX_LLAMADAS", "3000"))

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
    "additionalProperties": False,
}

# Permite forzar la respuesta de la cámara durante un ensayo del demo.
_FORZAR: dict[str, bool] = {}
_cliente = None
_llamadas = 0
_candado = threading.Lock()


def forzar_camara(pregunta: str, respuesta: bool) -> None:
    _FORZAR[pregunta] = respuesta


def limpiar_forzados() -> None:
    _FORZAR.clear()


def vlm_configurado() -> bool:
    return bool(os.environ.get("ANTHROPIC_API_KEY"))


def juez_camara(pregunta: str, cuadro: bytes | None = None) -> tuple[bool, float]:
    """Capa 3: (respuesta, confianza) para la pregunta visual del paso sobre `cuadro`.

    El cuadro lo entrega app/servicios.py: es el último que mandó la cámara del edge
    que ejecuta la OT (app/video.py). La firma de reglas.JuezCamara no cambia.

    Si el VLM falla (red, cuota, negativa, respuesta rara) responde (False, 0.0): no
    verifica el paso y queda a la vista como warning de capa 3, nunca lo cierra por error.
    """
    if pregunta in _FORZAR:
        return _FORZAR[pregunta], 0.91
    if cuadro is None or not vlm_configurado():
        return True, 0.55  # stub de ensayo: sin VLM conectado
    if not _queda_presupuesto():
        return False, 0.0
    try:
        return preguntar_claude(pregunta, cuadro)
    except Exception:  # noqa: BLE001 - cualquier falla del VLM se trata igual: no verifica
        log.exception("el VLM no pudo juzgar «%s»", pregunta)
        return False, 0.0


def _queda_presupuesto() -> bool:
    global _llamadas
    with _candado:
        if _llamadas >= LLAMADAS_MAX:
            log.error("el VLM llegó a su tope de %d llamadas por proceso (VLM_MAX_LLAMADAS): no juzga más", LLAMADAS_MAX)
            return False
        _llamadas += 1
        return True


def preguntar_claude(pregunta: str, cuadro: bytes, cliente=None) -> tuple[bool, float]:
    global _cliente
    if cliente is None:
        if _cliente is None:
            import anthropic
            _cliente = anthropic.Anthropic(timeout=TIMEOUT_S, max_retries=1)  # lee ANTHROPIC_API_KEY
        cliente = _cliente
    r = cliente.messages.create(
        model=os.environ.get("VLM_MODELO", MODELO_POR_DEFECTO),
        max_tokens=4000,
        system=INSTRUCCION,
        # esfuerzo bajo: es un sí/no sobre una foto, importa la latencia
        output_config={"effort": "low", "format": {"type": "json_schema", "schema": ESQUEMA}},
        messages=[{"role": "user", "content": [
            {"type": "image", "source": {"type": "base64", "media_type": "image/jpeg",
                                         "data": base64.standard_b64encode(cuadro).decode()}},
            {"type": "text", "text": pregunta},
        ]}],
    )
    if r.stop_reason != "end_turn":  # refusal o max_tokens: no hay respuesta en la que confiar
        log.warning("el VLM terminó con %s para «%s»", r.stop_reason, pregunta)
        return False, 0.0
    d = json.loads(next(b.text for b in r.content if b.type == "text"))
    return bool(d["respuesta"]), min(1.0, max(0.0, float(d["confianza"])))
