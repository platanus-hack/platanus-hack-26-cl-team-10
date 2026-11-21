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
| `deteccion` | objeto o nulo | Solo en pasos `camara`: `{clase, presente}`. Qué clase del modelo del edge lo responde en capa 2 (presente o ya retirada). Si el modelo no está seguro, o no busca esa clase, decide el VLM (capa 3). El detector del edge suma a sus clases las que pide la pauta de la OT en sesión |
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

Tipos de evento: `ot_abierta` · `ot_asignada` · `paso_iniciado` · `declaracion` · `veredicto` · `alerta` · `alerta_resuelta` · `relevo_entregado` · `relevo_recibido` · `propuesta_pauta`.

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
| `camara` | Capa 2 si el detector del edge ve con certeza la clase que el paso declara en `deteccion`; si no, capa 3, respondiendo la pregunta visual | Se guarda, y si contradice a la cámara el paso queda `en_conflicto` |
| `confirmacion` | La palabra del operario | Cierra el paso, y el evento deja constancia de que lo cerró una persona |

Cinco consecuencias que importan:

1. **Un paso de sensor nunca se cierra hablando.** Si el operario dice «bloqueo puesto» y el reed switch está abierto, el paso queda `en_conflicto`, no `verificado`. Hablar no lo cierra; **confirmarlo sí**, con la acción explícita de abajo.
2. **El orden no lo juzga el modelo.** Lo impone la aplicación, que pregunta por un paso a la vez, y lo comprueba la capa 1 con las marcas de tiempo: la energía se cortó *antes* de abrir la guarda. Es justo donde un VLM falla (3 de 12 cambios de orden, REFERENCIAS 9).
3. **La capa 2 cierra pasos de cámara, no de señal.** Sobre la imagen, el detector cierra el paso en curso cuando todas sus detecciones recientes son seguras, y nunca abre un conflicto: si duda, el paso sube a la capa 3. Sobre señales, la capa 2 detecta anomalías y avisa, sin cerrar pasos. Qué algoritmo usa ahí es `Brecha`; la [simulación de capa 2](../projects/escenarios-por-industria/capa2-simulacion.md) compara candidatos.
4. **La palabra tardía no se confunde con el paso siguiente.** La app manda el paso que mostraba al operario. Si el sensor ya lo cerró, la declaración se registra y no se evalúa contra el paso que sigue.
5. **Un paso de cámara sin un cuadro reciente no se verifica.** Sin video de los últimos 10 s, la respuesta del juez no es evidencia, aunque diga que sí.

## Cuando la persona y el sensor no coinciden

Un sensor se cae, se descalibra o queda mal montado, y la pauta no puede quedar trabada por eso. Si una persona afirma que el paso está hecho y la evidencia no lo muestra, **se le cree, pero no en silencio**:

- Es una acción aparte de declarar: `POST /ot/{id}/pasos/{paso}/confirmar`, con quién y por qué. Hablar sigue sin cerrar el paso.
- Solo el paso en curso, porque el orden lo impone la app. Un paso de confirmación se cierra declarando, no por acá.
- El paso queda `verificado` por una persona (`capa` nula). El evento guarda quién, el motivo y qué marcaba el sensor en ese momento. El conflicto anterior, si lo hubo, sigue en la bitácora.
- La OT queda en `warning` mientras dure: el registro dice que ese control lo afirmó una persona contra la evidencia. No interrumpe.
- **No apaga la seguridad.** Las reglas de peligro se siguen evaluando con los sensores reales. Si el bloqueo se confirmó a mano y después la guarda se abre con energía viva, la alerta suena igual. Un control cerrado por una persona no cuenta para «control crítico deshecho», porque su sensor nunca lo mostró hecho.

Quién puede confirmar un control crítico (el operario o solo un supervisor) está abierto. `Candidata a validar`.

## Qué puede interrumpir al operario

**Solo la capa 1.** Mientras no se mida la tasa de falsas alarmas de la cámara, lo que detecta la capa 3 se muestra en pantalla pero no suena en el oído. Con 5 rechazos de 12 ejecuciones correctas (REFERENCIAS 9), un aviso falso repetido le enseña al operario a ignorar el aviso.

Y hay reglas de seguridad que **no dependen del paso en curso**: se evalúan con cada lectura de sensor, incluso si el operario va en otro paso o en ninguno. Una por peligro de alta consecuencia de cada industria, con su norma (los números son de [REFERENCIAS](../projects/research/REFERENCIAS.md)):

| Regla | Industria | Dispara | Por qué |
|---|---|---|---|
| Guarda abierta con energía viva | Minería | Alerta crítica, capa 1 | Era el momento del demo de la correa. Mantener solo con la energía cortada y la máquina bloqueada, con guardas puestas mientras opera (44, 45). El aislamiento de energía es uno de los peligros de alta consecuencia que ICMM nombra (40) |
| Puesta a tierra con tensión presente | Eléctrica | Alerta crítica, capa 1 | Se verifica la ausencia de tensión antes de poner cualquier tierra (48, 49, 50) |
| Cierre del seccionador con tierras puestas | Eléctrica | Alerta crítica, capa 1 | No se repone el servicio mientras haya tierras (48, 49, 50) |
| Persona en la zona con los implementos levantados | Construcción | Alerta crítica, capa 1 | Nadie trabaja bajo una parte levantada que no esté calzada (52) |
| Persona en la zona con energía viva | Celda robotizada, el demo | Alerta crítica, capa 1, y el ESP32 corta la energía por su cuenta | Es el momento del demo ([ADR-0010](../decisions/0010-demo-brazo-robotico-en-una-celda-con-corte-local.md)). El corte es local porque una función de seguridad no puede depender de la red. `Candidata a validar`: no está construida y no se buscó su norma |

Y dos reglas que **sí dependen de la pauta**, porque leen qué pasos están cerrados. También son capa 1 e interrumpen:

| Regla | Dispara | Se resuelve | Por qué |
|---|---|---|---|
| Orden invertido | Llega la lectura que cierra un paso posterior mientras el paso en curso, que es control crítico, sigue abierto | Cuando se hace el paso saltado o se deshace lo adelantado | El orden lo comprueba la capa 1 (punto 2 de arriba). Es el bloqueo saltado del demo, y la causa de la muerte que investigó MSHA en 2025: el procedimiento existía y no se aplicó (47). Si el paso pendiente no es crítico no se avisa: cerrar la guarda porque sonó una alerta no vale una interrupción |
| Control crítico deshecho | El sensor de un control crítico ya verificado deja de marcar lo que el paso exige, antes del paso de la pauta que lo deshace | Cuando el sensor vuelve | Las protecciones se reponen antes de volver a servicio y la reposición va en orden inverso (44, 48, 52). Deja de mirar cuando solo quedan pasos de confirmación, que es cuando la pauta devuelve el equipo a servicio |

Agregar una regla de seguridad es una decisión de producto, no un detalle de implementación: va en este documento. Cada una tiene sus escenarios en las tres industrias ([escenarios por industria](../projects/escenarios-por-industria/PRD.md)).

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

Una desviación suelta no es una propuesta. La propuesta nace cuando el **mismo** paso de la misma versión tiene señales en ejecuciones distintas: alertas de orden o de control, conflictos, pasos confirmados por una persona porque la evidencia no los vio, y lo que observaron los operarios. El supervisor la valida, el equipo escribe la versión nueva y la misma propuesta dice después si el paso dejó de desviarse ([ADR-0014](../decisions/0014-mejora-continua-por-evidencia-y-metricas-por-pauta.md)).

La vista del supervisor **agrupa por pauta y por área antes que por persona**: un paso que se saltan muchos operarios que normalmente cumplen apunta a la pauta, no a ellos (REFERENCIAS 33). Y dos cuidados que son regla, no consejo:

- **Un paso de seguridad que se salta seguido no se vuelve prescindible.** Que se repita la desviación es señal de que la pauta está mal escrita o es impracticable, no de que el paso sobre.
- **Si el dato se usa para vigilar personas**, puede aumentar la presión de la jefatura, que es una de las causas de las desviaciones (REFERENCIAS 33). `Candidata a validar`. Por eso el pitch no presenta a Factum como un supervisor que mira todo el tiempo ([ADR-0013](../decisions/0013-el-pitch-copiloto-del-operario-sin-supervisor-encima.md)).

## Lo que esta lógica todavía no resuelve

- Si confirmar un control crítico contra el sensor exige a un supervisor y no al operario. Ver [Cuando la persona y el sensor no coinciden](#cuando-la-persona-y-el-sensor-no-coinciden). `Brecha`.
- Qué fracción de los pasos de una pauta real tiene una señal de sensor disponible sin tocar el PLC. `Brecha`.
- Qué algoritmo usa la capa 2. Para el demo, sin ciclo de trabajo, basta el desvío robusto contra la historia normal. Con un ciclo de carga, como en una subestación o una excavadora, hace falta saber en qué parte del ciclo va el equipo ([simulación](../projects/escenarios-por-industria/capa2-simulacion.md)). `Brecha`.
- La latencia del aviso de punta a punta, y si el auricular convive con la protección auditiva de una planta. `Brecha`.
- Qué evidencia exige una auditoría y cuánto tiempo se guarda. `Brecha`.

## Fuentes

- ADR [0002](../decisions/0002-la-aplicacion-impone-el-orden-de-la-pauta.md), [0003](../decisions/0003-patrones-de-arquitectura-para-el-mvp.md), [0004](../decisions/0004-verificacion-por-capas.md) y [0006](../decisions/0006-la-ot-nace-del-protocolo.md). Todos `proposed`: esta lógica cae si el equipo los rechaza.
- [FLUJO](./FLUJO.md), pasos 2 a 6.
- Números de referencia: ver [REFERENCIAS](../projects/research/REFERENCIAS.md).
