"""La lógica de negocio de knowledge/architecture/LOGICA.md.

Este módulo no sabe de HTTP, de base de datos, de cámaras ni de modelos. Recibe
un paso, lo que el operario declaró y el último estado conocido de los sensores,
y devuelve un Veredicto. Por eso se puede probar sin hardware y sin API.

La regla de oro del ADR-0004: la primera capa que puede decidir, decide, y un
modelo nunca contradice a un sensor.
"""

from __future__ import annotations

from collections.abc import Callable, Mapping, Sequence

from app.contratos import Capa, Estado, Evento, Paso, Pauta, TipoEvidencia, Veredicto

# Un juez de capa 3 recibe la pregunta visual y devuelve (respuesta, confianza).
# El frente 3 reemplaza el stub por una llamada real a un VLM.
JuezCamara = Callable[[str], tuple[bool, float]]


def paso_actual(pauta: Pauta, estados: Mapping[str, Estado]) -> Paso | None:
    """El paso por el que la aplicación va a preguntar.

    El orden lo impone la aplicación, no el modelo (ADR-0002): es el primer paso
    en orden que todavía no está verificado. Un paso en conflicto sigue siendo el
    paso actual, porque no se cierra hasta que llegue evidencia que lo cierre.
    """
    for paso in pauta.en_orden:
        if estados.get(paso.id, Estado.NO_VERIFICADO) is not Estado.VERIFICADO:
            return paso
    return None


def fuera_de_orden(pauta: Pauta, estados: Mapping[str, Estado], paso_id: str) -> bool:
    """Si se intenta avanzar un paso sin cerrar los anteriores."""
    actual = paso_actual(pauta, estados)
    return actual is not None and actual.id != paso_id


def evaluar(
    paso: Paso,
    declarado: str | None,
    sensores: Mapping[str, str],
    juez_camara: JuezCamara | None = None,
) -> Veredicto:
    """Decide en qué queda un paso. Es el corazón de la lógica."""
    match paso.tipo_evidencia:
        case TipoEvidencia.SENSOR:
            return _por_sensor(paso, declarado, sensores)
        case TipoEvidencia.CAMARA:
            return _por_camara(paso, declarado, juez_camara)
        case TipoEvidencia.CONFIRMACION:
            return _por_confirmacion(declarado)
    raise AssertionError(f"tipo de evidencia no cubierto: {paso.tipo_evidencia}")


def _por_sensor(paso: Paso, declarado: str | None, sensores: Mapping[str, str]) -> Veredicto:
    """Capa 1. Un paso de sensor NUNCA se cierra hablando."""
    assert paso.sensor is not None
    leido = sensores.get(paso.sensor.id)
    evidencia = {"tipo": "sensor", "id": paso.sensor.id, "valor": leido, "espera": paso.sensor.espera}

    if leido is None:
        return Veredicto(
            Estado.NO_VERIFICADO,
            Capa.DETERMINISTA,
            f"sin lectura de {paso.sensor.id}",
            evidencia,
        )
    if leido == paso.sensor.espera:
        return Veredicto(
            Estado.VERIFICADO,
            Capa.DETERMINISTA,
            f"{paso.sensor.id} = {leido}, que es lo que el paso exige",
            evidencia,
        )
    if declarado:
        # El operario dijo que lo hizo y el sensor dice que no. No se resuelve en
        # silencio y no se cierra: queda a la vista. Interrumpe, porque es capa 1.
        return Veredicto(
            Estado.EN_CONFLICTO,
            Capa.DETERMINISTA,
            f"el operario declaró «{declarado}» y {paso.sensor.id} = {leido}, "
            f"se esperaba {paso.sensor.espera}",
            evidencia,
            interrumpe=True,
        )
    return Veredicto(
        Estado.NO_VERIFICADO,
        Capa.DETERMINISTA,
        f"{paso.sensor.id} = {leido}, se espera {paso.sensor.espera}",
        evidencia,
    )


def _por_camara(paso: Paso, declarado: str | None, juez: JuezCamara | None) -> Veredicto:
    """Capa 3. Nunca interrumpe: se muestra, no suena.

    Con 5 rechazos de 12 ejecuciones correctas (REFERENCIAS 9), un aviso falso
    repetido le enseña al operario a ignorar el aviso.
    """
    assert paso.pregunta_visual is not None
    if juez is None:
        return Veredicto(Estado.NO_VERIFICADO, Capa.MODELO, "sin juez de cámara conectado")

    respuesta, confianza = juez(paso.pregunta_visual)
    evidencia = {
        "tipo": "camara",
        "pregunta": paso.pregunta_visual,
        "respuesta": respuesta,
        "confianza": confianza,
    }
    if respuesta:
        return Veredicto(
            Estado.VERIFICADO, Capa.MODELO, f"la cámara responde que sí ({confianza:.0%})", evidencia
        )
    if declarado:
        return Veredicto(
            Estado.EN_CONFLICTO,
            Capa.MODELO,
            f"el operario declaró «{declarado}» y la cámara responde que no ({confianza:.0%})",
            evidencia,
        )
    return Veredicto(
        Estado.NO_VERIFICADO, Capa.MODELO, f"la cámara responde que no ({confianza:.0%})", evidencia
    )


CONF_ALTA = 0.8   # capa 2 de cámara decide "se ve" solo con esta certeza en cada detección
CONF_PISO = 0.25  # y decide "ya no se ve" solo si ninguna detección llega a esto


def por_deteccion(paso: Paso, detecciones: Sequence[Mapping]) -> Veredicto | None:
    """Capa 2 de un paso de cámara: el modelo del edge (YOLO) decide si está seguro.

    Recibe las detecciones recientes del edge, de la más vieja a la más nueva. Decide
    solo si TODAS coinciden con certeza (un cuadro dudoso basta para no decidir), y
    solo puede verificar: nunca abre un conflicto. Si no puede decidir devuelve None,
    y el paso sube a la capa 3 (VLM) cuando el operario declara (ADR-0004: la primera
    capa que puede decidir, decide).
    """
    if paso.deteccion is None or not detecciones:
        return None
    clase, presente = paso.deteccion.clase, paso.deteccion.presente
    confs = [max((o["conf"] for o in d["objetos"] if o["clase"] == clase), default=0.0) for d in detecciones]
    if presente and min(confs) >= CONF_ALTA:
        confianza, detalle = min(confs), f"el modelo del edge ve {clase} en {len(confs)} cuadros seguidos (mín. {min(confs):.0%})"
    elif not presente and max(confs) < CONF_PISO:
        confianza, detalle = 1 - max(confs), f"el modelo del edge ya no ve {clase} en {len(confs)} cuadros seguidos"
    else:
        return None
    evidencia = {"tipo": "deteccion", "clase": clase, "presente": presente, "confianza": round(confianza, 3),
                 "cuadros": len(confs), "modelo": detecciones[-1].get("modelo"),
                 "objetos": detecciones[-1]["objetos"]}
    return Veredicto(Estado.VERIFICADO, Capa.APRENDIZAJE, detalle, evidencia)


def _por_confirmacion(declarado: str | None) -> Veredicto:
    """La palabra del operario cierra el paso, y el evento deja constancia."""
    if declarado:
        return Veredicto(
            Estado.VERIFICADO, None, f"lo cerró una persona declarando «{declarado}»"
        )
    return Veredicto(Estado.NO_VERIFICADO, None, "sin confirmación del operario")


# ─── Reglas de seguridad ────────────────────────────────────────────────────
# No dependen del paso en curso: se evalúan con CADA lectura de sensor, incluso
# si el operario va en otro paso o en ninguno. Agregar una regla acá es una
# decisión de producto: va también en LOGICA.md.


def reglas_seguridad(sensores: Mapping[str, str]) -> list[Veredicto]:
    """Devuelve las alertas que disparan las lecturas actuales. Todas capa 1."""
    alertas: list[Veredicto] = []

    if sensores.get("guarda") == "abierta" and sensores.get("energia") == "viva":
        alertas.append(
            Veredicto(
                Estado.EN_CONFLICTO,
                Capa.DETERMINISTA,
                "GUARDA ABIERTA CON ENERGÍA VIVA. Detener y aislar la energía antes de continuar.",
                {"tipo": "sensor", "guarda": "abierta", "energia": "viva"},
                interrumpe=True,
            )
        )
    return alertas


# ─── Lectura del registro ───────────────────────────────────────────────────
# El estado de una OT no se guarda: se calcula leyendo sus eventos en orden.


def estados_desde_eventos(eventos: Sequence[Evento]) -> dict[str, Estado]:
    """Proyecta el estado de cada paso. El último veredicto de cada paso manda."""
    estados: dict[str, Estado] = {}
    for ev in eventos:
        if ev.estado is not None and ev.paso_id:
            estados[ev.paso_id] = ev.estado
    return estados


def propuesta_de_mejora(eventos: Sequence[Evento], minimo: int = 2) -> list[dict]:
    """Una desviación suelta no es una propuesta.

    La propuesta nace cuando el MISMO paso entra en conflicto en ejecuciones
    distintas. Agrupa por paso, nunca por persona: un paso que se saltan muchos
    operarios que normalmente cumplen apunta a la pauta (REFERENCIAS 33).
    """
    por_paso: dict[str, set[str]] = {}
    for ev in eventos:
        if ev.estado is Estado.EN_CONFLICTO and ev.paso_id:
            por_paso.setdefault(ev.paso_id, set()).add(ev.ot_id)

    return [
        {
            "paso_id": paso_id,
            "ots": sorted(ots),
            "veces": len(ots),
            "nota": "Revisar la redacción del paso. Si es un paso de seguridad, "
            "que se salte seguido no lo vuelve prescindible.",
        }
        for paso_id, ots in sorted(por_paso.items())
        if len(ots) >= minimo
    ]
