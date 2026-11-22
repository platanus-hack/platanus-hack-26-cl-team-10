"""La lógica de negocio de knowledge/architecture/LOGICA.md.

Este módulo no sabe de HTTP, de base de datos, de cámaras ni de modelos. Recibe
un paso, lo que el operario declaró y el último estado conocido de los sensores,
y devuelve un Veredicto. Por eso se puede probar sin hardware y sin API.

La regla de oro del ADR-0004: la primera capa que puede decidir, decide, y un
modelo nunca contradice a un sensor.
"""

from __future__ import annotations

from collections.abc import Callable, Collection, Mapping, Sequence

from app.contratos import Capa, Estado, Evento, Paso, Pauta, Sensor, TipoEvidencia, Veredicto

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
    solo puede verificar: nunca abre un conflicto. "Ya no se ve" solo lo decide un detector
    que buscaba esa clase (`clases` de cada detección): si no la conoce, no verla no dice
    nada. Si no puede decidir devuelve None,
    y el paso sube a la capa 3 (VLM) cuando el operario declara (ADR-0004: la primera
    capa que puede decidir, decide).
    """
    if paso.deteccion is None or not detecciones:
        return None
    clase, presente, otra = paso.deteccion.clase, paso.deteccion.presente, paso.deteccion.en_su_lugar

    def confs_de(c: str) -> list[float]:
        return [max((o["conf"] for o in d["objetos"] if o["clase"] == c), default=0.0) for d in detecciones]

    confs = confs_de(clase)
    if presente and min(confs) >= CONF_ALTA:
        confianza, detalle = min(confs), f"el modelo del edge ve {clase} en {len(confs)} cuadros seguidos (mín. {min(confs):.0%})"
    elif not presente and max(confs) < CONF_PISO and all(clase in (d.get("clases") or ()) for d in detecciones):
        confianza, detalle = 1 - max(confs), f"el modelo del edge ya no ve {clase} en {len(confs)} cuadros seguidos"
        if otra:
            # shortcut: basta con ver una «otra» cualquiera, no cuenta cuántas hay; si la cámara ve más
            # de un polín a la vez, comparar con las que había cuando se vio la clase que salió.
            if min(confs_de(otra)) < CONF_ALTA:
                return None
            confianza, detalle = min(confianza, min(confs_de(otra))), f"{detalle}, y ve {otra} en su lugar"
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


_PELIGROS: tuple[tuple[dict[str, str], str, str], ...] = (
    # (condición sobre sensores, aviso, fuente en REFERENCIAS)
    ({"guarda": "abierta", "energia": "viva"},
     "GUARDA ABIERTA CON ENERGÍA VIVA. Detener y aislar la energía antes de continuar.",
     "Minería: DS 132 art. 52 (44); 30 CFR 56.14105 y 56.14112(b) (45)"),
    ({"tierra": "puesta", "tension": "presente"},
     "PUESTA A TIERRA CON TENSIÓN PRESENTE. Retirar y verificar ausencia de tensión antes de volver a poner tierra.",
     "Eléctrica: 29 CFR 1910.269(n)(5) (50); RD 614/2001 anexo II (48); RPTD N°15 9.1.5 (49)"),
    ({"tierra": "puesta", "seccionador": "cerrado"},
     "CIERRE CON TIERRAS PUESTAS. Abrir el seccionador: no se repone el servicio mientras haya tierras.",
     "Eléctrica: 29 CFR 1910.269(m)(3)(xiii) (50); RD 614/2001 anexo II A.2 (48); RPTD N°15 9.1.7 (49)"),
    ({"zona": "ocupada", "implementos": "levantados"},
     "PERSONA BAJO LOS IMPLEMENTOS LEVANTADOS. Salir de la zona o bajar y calzar los implementos.",
     "Construcción: 29 CFR 1926.600(a)(3)(i) (52)"),
    ({"operario": "presente", "energia": "viva"},
     "PERSONA JUNTO A LA MÁQUINA CON EL MOTOR ENCENDIDO. Alejarse; cortar la corriente y poner el candado antes de acercarse.",
     "Minería: DS 132 art. 52 (44); estrategia de controles de correas, control crítico 1 (56)"),
)


def reglas_seguridad(sensores: Mapping[str, str]) -> list[Veredicto]:
    """Devuelve las alertas que disparan las lecturas actuales. Todas capa 1.

    Una regla por peligro de alta consecuencia de cada industria, con su norma. Cada
    una mira sensores propios de su equipo, así que en una estación solo puede
    disparar la de su industria.
    """
    return [
        Veredicto(
            Estado.EN_CONFLICTO,
            Capa.DETERMINISTA,
            aviso,
            {"tipo": "sensor", **condicion, "fuente": fuente},
            interrumpe=True,
        )
        for condicion, aviso, fuente in _PELIGROS
        if all(sensores.get(k) == v for k, v in condicion.items())
    ]


# Cómo sale una persona de un peligro con un gesto que el sensor ve: (sensor, valor peligroso) → valor a salvo, y el
# título y la instrucción del paso que lo pide. Con esto la mejora continua propone el paso que le falta a una pauta
# (app/sugerencias.py). Un peligro que no está acá no se arregla agregando un paso solo.
_SALIDAS: dict[tuple[str, str], tuple[str, str, str]] = {
    ("operario", "presente"): ("ausente", "Alejarte del equipo",
                               "Aléjate del equipo hasta que el sensor deje de verte."),
}


def antes_de_cerrar(sensor: Sensor) -> list[Paso]:
    """Los pasos que tienen que estar hechos antes de uno que se cierra con `sensor`, para que al cerrarse no arme un
    peligro de _PELIGROS: antes de dejar `energia = viva`, `operario = ausente`."""
    return [
        Paso(id="__nuevo", orden=0, titulo=titulo, instruccion=instruccion, tipo_evidencia=TipoEvidencia.SENSOR,
             capa_minima=1, control_critico=True, sensor=Sensor(otro, a_salvo))
        for condicion, _, _ in _PELIGROS if condicion.get(sensor.id) == sensor.espera
        for otro, valor in condicion.items() if (otro, valor) in _SALIDAS
        for a_salvo, titulo, instruccion in [_SALIDAS[otro, valor]]
    ]


def desviacion_de_orden(pauta: Pauta, estados: Mapping[str, Estado], sensor_id: str, valor: str) -> Veredicto | None:
    """El orden lo comprueba la capa 1 (ADR-0002, LOGICA): una lectura que cierra un paso
    posterior mientras el actual, un control crítico, sigue abierto, es un control saltado,
    aunque después se haga. Si el paso pendiente no es crítico no se avisa: cerrar la guarda
    porque sonó una alerta no es una desviación que valga una interrupción.

    Se mira el primer paso sin verificar que usa ese sensor: con eso, la guarda cerrada
    del inicio no se confunde con «reinstalar la guarda», que viene después de abrirla.
    """
    actual = paso_actual(pauta, estados)
    if actual is None or not actual.control_critico:
        return None
    adelantado = next(
        (p for p in pauta.en_orden
         if p.sensor and p.sensor.id == sensor_id and estados.get(p.id) is not Estado.VERIFICADO),
        None,
    )
    if adelantado is None or adelantado.orden <= actual.orden or adelantado.sensor.espera != valor:
        return None
    return Veredicto(
        Estado.EN_CONFLICTO,
        Capa.DETERMINISTA,
        f"ORDEN INVERTIDO: «{adelantado.titulo}» ({sensor_id} = {valor}) antes de «{actual.titulo}».",
        {"tipo": "orden", "adelantado": adelantado.id, "pendiente": actual.id, "sensor": sensor_id, "valor": valor},
        interrumpe=True,
    )


def controles_deshechos(
    pauta: Pauta, estados: Mapping[str, Estado], sensores: Mapping[str, str], por_persona: Collection[str] = ()
) -> list[Veredicto]:
    """Un control crítico ya verificado que se deshace antes de tiempo (LOGICA).

    Para cada sensor cuenta el último paso verificado que lo usa: si es control
    crítico y el sensor ya no marca lo que ese paso exige, el control se perdió. El
    paso de la pauta que lo deshace a propósito queda verificado antes de llegar acá,
    así que no cuenta. Deja de mirar cuando solo quedan pasos de confirmación, que es
    cuando la pauta devuelve el equipo a servicio.

    Un paso que confirmó una persona contra su sensor (`por_persona`) no cuenta: su
    sensor nunca lo mostró hecho, así que no se puede «deshacer».
    """
    actual = paso_actual(pauta, estados)
    if actual is None or all(
        p.tipo_evidencia is TipoEvidencia.CONFIRMACION for p in pauta.en_orden if p.orden >= actual.orden
    ):
        return []
    ultimo: dict[str, Paso] = {}
    for p in pauta.en_orden:
        if p.sensor and estados.get(p.id) is Estado.VERIFICADO:
            ultimo[p.sensor.id] = p
    ultimo = {k: p for k, p in ultimo.items() if p.id not in por_persona}
    return [
        Veredicto(
            Estado.EN_CONFLICTO,
            Capa.DETERMINISTA,
            f"CONTROL PERDIDO: «{p.titulo}» se deshizo ({sensor_id} = {sensores.get(sensor_id)}, "
            f"exige {p.sensor.espera}).",
            {"tipo": "control", "paso": p.id, "sensor": sensor_id, "valor": sensores.get(sensor_id),
             "espera": p.sensor.espera},
            interrumpe=True,
        )
        for sensor_id, p in ultimo.items()
        if p.control_critico and sensores.get(sensor_id) not in (None, p.sensor.espera)
    ]


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
