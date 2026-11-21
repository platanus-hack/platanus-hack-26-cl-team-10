# Lógica de negocio

> Documento vivo. Las reglas que gobiernan el flujo, sin código: qué es un paso, qué es un evento, quién decide que un paso está hecho, qué puede interrumpir al operario y cómo se traspasa un turno.
>
> **Es la dependencia dura del reparto.** Los cuatro frentes se comunican solo por las dos formas de aquí abajo, así que se acuerdan antes de escribir código y se cambian avisando. Estado del conjunto: `Candidata a validar`; sale de los ADR [0002](../decisions/0002-la-aplicacion-impone-el-orden-de-la-pauta.md), [0003](../decisions/0003-patrones-de-arquitectura-para-el-mvp.md), [0004](../decisions/0004-verificacion-por-capas.md) y [0006](../decisions/0006-la-ot-nace-del-protocolo.md), y del [FLUJO](./FLUJO.md).

## Las dos formas

### Paso

Una unidad de la pauta que se puede cerrar con evidencia. Sale de convertir el protocolo que el cliente ya tiene.

| Campo | Valores | Para qué |
|---|---|---|
| `id` | texto | Único dentro de la pauta |
| `orden` | entero | El orden que impone la aplicación, no el modelo |
| `titulo` | texto | Lo que se le muestra y se le dice al operario |
| `instruccion` | texto | El detalle, tal como lo dice el protocolo |
| `tipo_evidencia` | `sensor` · `camara` · `confirmacion` | **Qué cierra el paso.** Es el campo que decide todo lo demás |
| `pregunta_visual` | texto o nulo | La pregunta concreta para la cámara, si el tipo es `camara` |
| `sensor` | objeto o nulo | Qué sensor y qué valor se espera, si el tipo es `sensor` |
| `deteccion` | objeto o nulo | Solo en pasos `camara`: `{clase, presente}`. Qué clase del modelo del edge lo responde en capa 2 (presente o ya retirada). Si el modelo no está seguro, decide el VLM (capa 3) |
| `control_critico` | sí · no | Si su falla permite un evento de alta consecuencia |
| `capa_minima` | 1 · 2 · 3 | La capa más baja que puede cerrarlo |

### Evento

El evento **es** la bitácora. La tabla solo admite agregar filas: nada se edita ni se borra, y el estado de una OT se calcula leyendo sus eventos en orden.

| Campo | Valores | Para qué |
|---|---|---|
| `id` | entero | Autoincremental. Es el orden real de lo que pasó |
| `ot_id` | texto | A qué orden de trabajo pertenece |
| `paso_id` | texto o nulo | Nulo cuando el evento es de la OT y no de un paso |
| `ts` | ISO 8601 | Cuándo |
| `tipo` | ver abajo | Qué ocurrió |
| `estado` | `verificado` · `no_verificado` · `en_conflicto` | En qué quedó el paso |
| `actor` | `operario:A` · `sistema` · `supervisor:X` | Quién |
| `capa` | 1 · 2 · 3 o nulo | Qué capa decidió |
| `declarado` | texto o nulo | Lo que dijo el operario, literal |
| `evidencia` | objeto o nulo | El valor del sensor o la foto, con su hora |
| `detalle` | texto | Por qué se decidió así, legible por una persona |

Tipos de evento: `ot_abierta` · `paso_iniciado` · `declaracion` · `veredicto` · `alerta` · `alerta_resuelta` · `relevo_entregado` · `relevo_recibido` · `propuesta_pauta`.

Una alerta no se borra cuando su condición desaparece: entra un `alerta_resuelta` que apunta a ella (`evidencia.resuelve`) con la lectura que la normalizó. Así la bitácora muestra cuándo empezó y cuándo terminó, y la UI saca el aviso en vivo. Ver [ADR-0007](../decisions/0007-servicios-en-vivo-sesion-stream-y-calificacion.md).

## Los tres estados de un paso

Tres, no dos. El tercero existe porque la capa determinista puede contradecir lo que el operario declaró, y en ese caso el sistema no resuelve en silencio.

- **`no_verificado`**: todavía no hay evidencia, o la evidencia dice que no está hecho. Es el estado inicial de todo paso.
- **`verificado`**: la evidencia que el paso exige lo cierra.
- **`en_conflicto`**: el operario declaró una cosa y la evidencia muestra otra. **El paso no se cierra** y queda a la vista del supervisor.

Un paso `en_conflicto` no vuelve atrás solo. Sale del conflicto cuando llega evidencia nueva que lo cierra, y el conflicto **queda en el registro** igual: es una fila más, no se borra.

## Quién decide que un paso está hecho

La regla de oro del [ADR-0004](../decisions/0004-verificacion-por-capas.md): **la primera capa que puede decidir, decide, y un modelo nunca contradice a un sensor.**

| `tipo_evidencia` | Quién cierra el paso | Qué pasa con lo que diga el operario |
|---|---|---|
| `sensor` | Capa 1, con la lectura del sensor | Se guarda como `declarado`, pero **no cierra el paso** |
| `camara` | Capa 3, respondiendo la pregunta visual | Se guarda, y si contradice a la cámara el paso queda `en_conflicto` |
| `confirmacion` | La palabra del operario | Cierra el paso, y el evento deja constancia de que lo cerró una persona |

Tres consecuencias que importan:

1. **Un paso de sensor nunca se cierra hablando.** Si el operario dice «bloqueo puesto» y el reed switch está abierto, el paso queda `en_conflicto`, no `verificado`.
2. **El orden no lo juzga el modelo.** Lo impone la aplicación, que pregunta por un paso a la vez, y lo comprueba la capa 1 con las marcas de tiempo: la energía se cortó *antes* de abrir la guarda. Es justo donde un VLM falla (3 de 12 cambios de orden, REFERENCIAS 9).
3. **La capa 2 todavía no cierra pasos.** Detecta anomalías en la señal y abre la OT. Qué algoritmo usa es `Brecha`.

## Qué puede interrumpir al operario

**Solo la capa 1.** Mientras no se mida la tasa de falsas alarmas de la cámara, lo que detecta la capa 3 se muestra en pantalla pero no suena en el oído. Con 5 rechazos de 12 ejecuciones correctas (REFERENCIAS 9), un aviso falso repetido le enseña al operario a ignorar el aviso.

Y hay reglas de seguridad que **no dependen del paso en curso**: se evalúan con cada lectura de sensor, incluso si el operario va en otro paso o en ninguno.

| Regla | Dispara | Por qué |
|---|---|---|
| Guarda abierta con energía viva | Alerta crítica, capa 1 | Es el momento del demo, y el aislamiento de energía es uno de los peligros de alta consecuencia que ICMM nombra (REFERENCIAS 40) |

Esa es la única regla definida hoy. Agregar una regla de seguridad es una decisión de producto, no un detalle de implementación: va en este documento.

## Dónde una persona tiene que aprobar

Del [ADR-0003](../decisions/0003-patrones-de-arquitectura-para-el-mvp.md): nada de esto ocurre solo.

1. **Convertir el protocolo en pauta.** El sistema propone los pasos y su tipo de evidencia; una persona los aprueba antes de que la pauta se use.
2. **Abrir la OT.** El sistema la propone, una persona la confirma.
3. **Cambiar la pauta matriz.** El sistema propone, el supervisor aprueba o rechaza.

Cada OT guarda **qué versión de la pauta ejecutó**. Sin eso, una propuesta de mejora no se puede evaluar contra lo que realmente se corrió.

## Relevo de turno

El relevo es una **lectura de los eventos**, no un documento aparte: qué pasos están cerrados, con qué evidencia, y cuál sigue. El turno que llega retoma desde el último paso `verificado`.

- Un paso `en_conflicto` **se hereda como conflicto**. No se limpia al cambiar de turno.
- El resumen que redacta un modelo va **encima** del registro, no en su lugar. Ante «¿se puso el bloqueo?» la respuesta viaja con la foto o el valor del sensor y su hora.
- Se le entrega al modelo el registro **completo** de la OT, sin recuperación ni base vectorial: una OT entera cabe en el contexto, y omitir un evento al responder una pregunta de seguridad es inaceptable. `Candidata a validar`. Esto responde la fila «Formato del relevo de turno» de [SEGUIMIENTO](../roadmap/SEGUIMIENTO.md).
- El traspaso **se firma**: el que llega confirma que lo recibió, y eso es un evento (`relevo_recibido`) con su nombre y su hora.

Límite conocido y aceptado: esto funciona mientras el registro de una OT quepa en el contexto del modelo. Una tarea de varios días no cabe. `Brecha`.

## Cuándo el sistema propone cambiar la pauta

Una desviación suelta no es una propuesta. La propuesta nace cuando la **misma** desviación se repite en el mismo paso, en ejecuciones distintas.

La vista del supervisor **agrupa por pauta y por área antes que por persona**: un paso que se saltan muchos operarios que normalmente cumplen apunta a la pauta, no a ellos (REFERENCIAS 33). Y dos cuidados que son regla, no consejo:

- **Un paso de seguridad que se salta seguido no se vuelve prescindible.** Que se repita la desviación es señal de que la pauta está mal escrita o es impracticable, no de que el paso sobre.
- **Si el dato se usa para vigilar personas**, puede aumentar la presión de la jefatura, que es una de las causas de las desviaciones (REFERENCIAS 33). `Candidata a validar`.

## Lo que esta lógica todavía no resuelve

- Qué pasa con un paso `en_conflicto` cuando el operario insiste. ¿Se escala a un supervisor? `Brecha`.
- Qué fracción de los pasos de una pauta real tiene una señal de sensor disponible sin tocar el PLC. `Brecha`.
- Qué algoritmo usa la capa 2. Para el demo basta un umbral. `Brecha`.
- La latencia del aviso de punta a punta, y si el auricular convive con la protección auditiva de una planta. `Brecha`.
- Qué evidencia exige una auditoría y cuánto tiempo se guarda. `Brecha`.

## Fuentes

- ADR [0002](../decisions/0002-la-aplicacion-impone-el-orden-de-la-pauta.md), [0003](../decisions/0003-patrones-de-arquitectura-para-el-mvp.md), [0004](../decisions/0004-verificacion-por-capas.md) y [0006](../decisions/0006-la-ot-nace-del-protocolo.md). Todos `proposed`: esta lógica cae si el equipo los rechaza.
- [FLUJO](./FLUJO.md), pasos 2 a 6.
- Números de referencia: ver [REFERENCIAS](../projects/research/REFERENCIAS.md). La (40), de ICMM, entra con el PR #7; si ese PR no se mergea, las dos menciones a controles críticos de alta consecuencia quedan sin fuente numerada.
