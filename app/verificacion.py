"""FRENTE 3 — verificación.

La capa 1 ya es real: lee los sensores desde la base y app/reglas.py decide.
La capa 3 es un stub conmutable, para poder ensayar el demo sin cámara.

Lo que hay que construir acá: reemplazar juez_camara por una llamada a un VLM
que reciba el cuadro de la cámara y la pregunta visual del paso. El resto del
sistema no cambia: la firma devuelve (respuesta, confianza).

La capa 2, aprendizaje sobre señales, todavía no cierra pasos. Detecta anomalías
y abre la OT. Qué algoritmo usa es una Brecha abierta.
"""

from __future__ import annotations

# Permite forzar la respuesta de la cámara durante un ensayo del demo.
# El frente 3 lo borra cuando conecte el modelo.
_FORZAR: dict[str, bool] = {}


def forzar_camara(pregunta: str, respuesta: bool) -> None:
    _FORZAR[pregunta] = respuesta


def limpiar_forzados() -> None:
    _FORZAR.clear()


def juez_camara(pregunta: str) -> tuple[bool, float]:
    """TODO frente 3: llamar al VLM con el cuadro actual y esta pregunta.

    Mientras no exista, responde lo que se haya forzado, y si no se forzó nada
    responde que sí con confianza baja, para que el flujo avance en los ensayos.
    """
    if pregunta in _FORZAR:
        return _FORZAR[pregunta], 0.91
    return True, 0.55
