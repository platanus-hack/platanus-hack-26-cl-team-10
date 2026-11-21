"""La lógica de negocio de knowledge/architecture/LOGICA.md.

Este módulo no sabe de HTTP, de base de datos, de cámaras ni de modelos. Recibe
un paso, lo que el operario declaró y el último estado conocido de los sensores,
y devuelve un Veredicto. Por eso se puede probar sin hardware y sin API.

La regla de oro del ADR-0004: la primera capa que puede decidir, decide, y un
modelo nunca contradice a un sensor.
"""

from __future__ import annotations

from collections.abc import Callable, Collection, Mapping, Sequence
from datetime import datetime
from statistics import mean, median

from app.contratos import Capa, Estado, Evento, Paso, Pauta, TipoEvento, TipoEvidencia, Veredicto

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


# Sobre esta parte del tiempo de la pauta, un paso es su cuello de botella.
PARTE_QUE_ES_CUELLO = 0.5


def medidas_por_paso(eventos: Sequence[Evento], minimo: int = 2) -> dict[str, dict]:
    """Lo que el registro dice de cada paso de UNA pauta, sumando sus OT. Agrupa por paso,
    nunca por persona: un paso que se saltan muchos operarios que normalmente cumplen
    apunta a la pauta (REFERENCIAS 33).

    `reintentos` son los veredictos sin verificar antes de que el paso cierre, promediados
    por OT; `segundos`, la mediana de lo que demora en las `mediciones` que hay; `cierres`,
    qué lo cerró (la capa, "declaracion" o "persona"). `nota` dice qué revisar, y solo se llena cuando
    algo se repite en `minimo` OT o más: una desviación suelta no es una propuesta.
    """
    conflicto: dict[str, set[str]] = {}
    persona: dict[str, set[str]] = {}
    fallidos: dict[str, dict[str, int]] = {}  # paso → OT → veredictos sin verificar
    segundos: dict[str, list[float]] = {}
    cierres: dict[str, dict[str, int]] = {}
    cierre: dict[str, datetime] = {}  # OT → cuándo cerró su paso anterior
    cerrados: set[tuple[str, str]] = set()

    for ev in eventos:
        if not ev.paso_id:
            continue
        if ev.estado is Estado.EN_CONFLICTO:
            conflicto.setdefault(ev.paso_id, set()).add(ev.ot_id)
        if ev.tipo is not TipoEvento.VEREDICTO or (ev.ot_id, ev.paso_id) in cerrados:
            continue
        intentos = fallidos.setdefault(ev.paso_id, {})
        intentos.setdefault(ev.ot_id, 0)
        if ev.estado is not Estado.VERIFICADO:
            intentos[ev.ot_id] += 1
            continue
        cerrados.add((ev.ot_id, ev.paso_id))
        # Sin capa y sin persona contra la evidencia: un paso de confirmación, que se cierra declarando.
        por = "persona" if (ev.evidencia or {}).get("tipo") == "persona" else str(ev.capa or "declaracion")
        cierres.setdefault(ev.paso_id, {}).setdefault(por, 0)
        cierres[ev.paso_id][por] += 1
        if por == "persona":
            persona.setdefault(ev.paso_id, set()).add(ev.ot_id)
        # shortcut: nadie emite PASO_INICIADO, así que un paso se mide desde el cierre del
        # anterior y el primero de cada OT queda sin medir; medir desde su inicio cuando exista.
        ts = datetime.fromisoformat(ev.ts)
        if ev.ot_id in cierre:
            segundos.setdefault(ev.paso_id, []).append((ts - cierre[ev.ot_id]).total_seconds())
        cierre[ev.ot_id] = ts

    # La mediana, no el promedio: una OT que quedó a medias de un turno a otro no mueve el número.
    medianas = {p: median(s) for p, s in segundos.items() if len(s) >= minimo}
    # Con menos de tres pasos medidos no hay contra qué comparar: uno siempre sería "la mitad".
    total = sum(medianas.values()) if len(medianas) >= 3 else 0

    medidas = {}
    for paso_id in sorted(conflicto.keys() | fallidos.keys()):
        parte = medianas[paso_id] / total if total and paso_id in medianas else None
        notas = []
        if len(conflicto.get(paso_id, ())) >= minimo:
            notas.append("Revisar la redacción del paso. Si es un paso de seguridad, "
                         "que se salte seguido no lo vuelve prescindible.")
        if len(persona.get(paso_id, ())) >= minimo:
            notas.append("Lo cierra una persona contra la evidencia: revisar el sensor o la "
                         "cámara de este paso antes que a quien lo ejecuta.")
        if parte is not None and parte > PARTE_QUE_ES_CUELLO:
            notas.append("Se lleva más de la mitad del tiempo de la pauta: ver si conviene "
                         "dividirlo o si la evidencia que pide demora.")
        medidas[paso_id] = {
            "paso_id": paso_id,
            "ots": sorted(conflicto.get(paso_id, ())),
            "veces": len(conflicto.get(paso_id, ())),
            "por_persona": len(persona.get(paso_id, ())),
            "reintentos": round(mean(fallidos.get(paso_id, {}).values() or [0]), 1),
            "segundos": median(segundos[paso_id]) if paso_id in segundos else None,
            "mediciones": len(segundos.get(paso_id, ())),
            "parte_del_tiempo": round(parte, 2) if parte is not None else None,
            "cierres": cierres.get(paso_id, {}),
            "nota": " ".join(notas),
        }
    return medidas


def propuesta_de_mejora(eventos: Sequence[Evento], minimo: int = 2) -> list[dict]:
    """Los pasos de UNA pauta que tienen algo que revisar, con sus números."""
    return [m for m in medidas_por_paso(eventos, minimo).values() if m["nota"]]
