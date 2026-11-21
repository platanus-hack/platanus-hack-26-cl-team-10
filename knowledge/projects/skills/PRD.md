# PRD — Skills de Factum: del protocolo a la OT, el reporte y la mejora

> **Dueño de la decisión:** Francisco · **Se consulta a:** Jonathan, por las tres capas y el inventario de la estación; Daniel, por lo que la interfaz muestra de cada skill · **Alcance:** cómo se diseñan las skills que un agente usa para extraer un protocolo, generar sus pautas, aterrizarlas en OT, reportar y recomendar mejoras.
>
> **Estado →** [SEGUIMIENTO](../../roadmap/SEGUIMIENTO.md). Este documento no lleva avance. Es diseño: no hay ninguna skill construida.

## 1. Resumen

**Hoy:** del protocolo a la OT, la mitad del camino se hace a mano:

- **Protocolo y pauta, a mano.** El equipo lee el documento del cliente y escribe la pauta en JSON. `protocolos.extraer_pasos` es un stub, y las nueve pautas de `datos/` salieron así de los seis protocolos de la semilla.
- **La OT ya es un servicio.** Existe con login ([ADR-0011](../../decisions/0011-protocolos-y-pautas-por-servicio-interno-ot-por-servicio-al-cliente.md), [ADR-0012](../../decisions/0012-login-y-clientes-cada-empresa-ve-lo-suyo.md)).
- **No hay reporte.** El resumen del relevo (`cerebro.redactar_resumen`) es un stub.
- **La mejora propone, pero no reescribe.** Las propuestas nacen de la evidencia ([ADR-0014](../../decisions/0014-mejora-continua-por-evidencia-y-metricas-por-pauta.md)), pero la versión nueva la escribe una persona. Además, nada recomienda cambiar con qué capa se comprueba un paso.

**Después:** un conjunto de skills, en el formato abierto de Agent Skills (REFERENCIAS 74), que cualquier agente carga y usa contra la API. El trabajo se reparte así:

- **El modelo** lee, redacta y propone.
- **El código** valida y aplica las reglas.
- **Una persona** aprueba. Ninguna skill aprueba una pauta ni cambia una regla de seguridad ([ADR-0003](../../decisions/0003-patrones-de-arquitectura-para-el-mvp.md)).

## 2. Cómo se hace hoy en la industria, y qué cambia

Las skills no inventan un flujo nuevo: siguen el que una planta ya usa y cambian una sola cosa, con qué se cierra cada paso.

| En una planta hoy | Qué es | En Factum | Skill |
|---|---|---|---|
| **El procedimiento de trabajo** | El documento que dice cómo se hace la tarea y qué controles exige. El DS 132 pide bloqueo y advertencia antes de mantener (REFERENCIAS 44, art. 52); las estrategias de controles nombran los controles críticos y cómo se comprueban (56) | Protocolo | `factum-extraer-protocolo` |
| **La lista de tareas** (*task list* de SAP PM) | Las operaciones de la tarea, en orden. El plan de mantenimiento la asigna a cada ítem (REFERENCIAS 76) | Pauta, versionada y aprobada por una persona | `factum-generar-pauta` |
| **El plan de mantenimiento** | En la fecha debida genera la orden y copia en ella las operaciones de la lista (76) | OT, por calendario, pedido o falla ([ADR-0006](../../decisions/0006-la-ot-nace-del-protocolo.md)) | `factum-pedir-ot` |
| **La ejecución** | El técnico sigue la orden; nadie comprueba el paso mientras ocurre | El copiloto comprueba cada paso con la capa que corresponde y avisa | `factum-ejecutar-ot` |
| **La notificación de cierre** | Se confirma cada operación y se escribe lo que pasó (77). El texto libre y los códigos tienen errores sistemáticos (3, 4) | Bitácora con evidencia; el reporte se arma desde ella | `factum-reportar` |
| **La revisión del procedimiento** | Tras un incidente o una auditoría, a criterio | Propuestas desde la evidencia, validadas, más recomendaciones de capa | `factum-mejorar-pauta`, `factum-medir` |

## 3. Las tres capas: lo que una skill decide por cada paso

El sistema de verificación que construyó Jonathan ([ADR-0004](../../decisions/0004-verificacion-por-capas.md), Frente 3) comprueba cada paso con la primera capa que puede decidirlo:

| Capa | Qué es | Dónde está | Decide cuando |
|---|---|---|---|
| 1 · Programática | Sensores y reglas con marca de tiempo | `app/reglas.py` | Un sensor mide el estado final del paso. Es la única que interrumpe al operario |
| 2 · Visión y señales | El detector de objetos (YOLO) y las anomalías de señal | `reglas.por_deteccion`, `scoring.capa2` | El detector ve la clase con 0,8 o más en cada detección reciente, o con menos de 0,25 si el paso espera que ya no esté |
| 3 · Modelo de lenguaje | Un VLM responde la pregunta visual del paso sobre el último cuadro | `app/verificacion.py` | Lo demás que solo se ve. Bajo 0,75 de confianza, su calificación queda en `warning` |

Que cada etapa de una pauta se procese según lo que necesita es exactamente lo que el diseño de una skill tiene que respetar:

- **`factum-generar-pauta` elige la capa más barata que puede decidir cada paso**, según lo que la estación tiene.
- **`factum-mejorar-pauta` mueve un paso de capa** cuando la evidencia de sus ejecuciones muestra que la elegida no le sirve.

**La regla de elección**, en orden:

1. **Sensor.** Si un sensor de la estación mide el estado final del paso, la capa es 1.
2. **Detector.** Si no, y el detector conoce un objeto que aparece o desaparece con el paso, la capa es 2. La skill escribe además la pregunta visual, para que la capa 3 responda cuando el detector no llega a la certeza.
3. **Pregunta visual.** Si solo se ve, la capa es 3, con una pregunta que se responda con sí o no sobre una foto.
4. **Confirmación.** Si nada lo ve, el paso es de confirmación. Un control crítico no puede quedar así sin marcarlo como brecha: es el caso de la comprobación de energía cero, que hoy cierra la palabra del operario (ADR-0011).

## 4. Las skills

Cada skill es una carpeta `skills/<nombre>/` con un `SKILL.md` de menos de 500 líneas. Su encabezado lleva `name` y una `description` que dice qué hace y cuándo usarla, que es lo único que el agente lee antes de activarla (REFERENCIAS 74). Lo largo va en `references/`: el esquema de la pauta, la regla de las capas, las reglas de LOGICA. Lo que se ejecuta va en `scripts/`.

### Internas: las usa el equipo de Factum, con la clave del equipo

| Skill | Entra | Sale | Qué hace el modelo | Qué hace el código | Quién aprueba |
|---|---|---|---|---|---|
| `factum-extraer-protocolo` | El documento del cliente | El protocolo con la estructura de la semilla: alcance, palabras de terreno, lo que no puede pasar (peligro, cómo se evita, cómo se comprueba), antes de empezar y bloques de pasos | Lee, ordena y cita cada parte con su sección o página. Lo que el documento no dice queda como pregunta, no se completa | `POST /interno/protocolos` guarda el texto y su origen | La persona del equipo que lo carga |
| `factum-generar-pauta` | El protocolo y el inventario de la estación | Una pauta borrador: un paso por estado final observable, en orden, con su evidencia y su capa según la sección 3, y los controles críticos que salen de «lo que no puede pasar» | Redacta en palabras de terreno y elige la capa; cada paso cita la parte del protocolo de donde sale | El validador rechaza lo que no se puede ejecutar; `POST /interno/protocolos/{id}/pautas` la guarda sin aprobar | Una persona, en `/interno/pautas/{id}/versiones/{v}/aprobar` |
| `factum-mejorar-pauta` | Las propuestas aceptadas (`GET /interno/mejoras`), las métricas por paso y la pauta vigente | La versión siguiente, con el cambio de cada paso y por qué, más las recomendaciones de capa de la tabla de abajo | Redacta el cambio desde las señales y las observaciones | El validador, y después el ciclo del ADR-0014, que comprueba si el paso dejó de desviarse | Una persona aprueba la versión nueva |

**Las recomendaciones de capa de `factum-mejorar-pauta`.** Es la mejora continua interna con las tres capas:

| Lo que muestra la evidencia de un paso | Qué recomienda |
|---|---|
| Un paso de sensor que una persona confirma seguido | El sensor no ve lo que se hizo: revisar su montaje o pasar el paso a cámara. Primero la estación, no el operario |
| Un paso de cámara que el VLM cierra con poca confianza | Reescribir la pregunta visual, o entrenar al detector en ese objeto para bajarlo a capa 2 |
| Un paso de capa 3 que el detector ya resuelve siempre | Bajarlo a capa 2: decide igual, sin llamar al modelo |
| Un control crítico que cierra la cámara o la palabra | Pedir un sensor. «Control deshecho» solo vigila pasos de sensor (regla V1 del validador) |
| Una alerta de orden repetida en el mismo paso | Revisar el orden o la disposición de la estación. Es el caso de la semilla: el punto de bloqueo queda lejos del tablero |
| Observaciones del operario sobre el paso | Incorporarlas a la instrucción, citándolas |

### De cliente: las usa una empresa con su token

| Skill | Para quién | Qué le enseña al agente |
|---|---|---|
| `factum-pedir-ot` | Supervisor o el planificador del cliente | Entrar, elegir una pauta habilitada, pedir la OT y asignarla. Es lo que llama un calendario o una falla |
| `factum-ejecutar-ot` | Operario, o el agente de voz que lo acompaña | Unir la OT a la estación y tomarla solo si la persona lo pide, seguir el paso en curso, declarar, confirmar por persona con motivo, dejar observaciones y entregar el turno. Las reglas que no se rompen: el orden lo impone la API y un paso de sensor no se cierra hablando |
| `factum-reportar` | Supervisor | El reporte de cierre de una OT y el del relevo, armados desde la bitácora. También el informe del periodo, desde las métricas |
| `factum-medir` | Supervisor | Qué GET responde cada pregunta, cómo leer el cumplimiento, y cómo validar las propuestas de mejora |

### El reporte: el registro manda y el modelo redacta encima

`factum-reportar` sigue la regla de [LOGICA](../../architecture/LOGICA.md#relevo-de-turno): el resumen de un modelo va encima del registro, nunca en su lugar, y el modelo recibe el registro completo de la OT. El reporte tiene dos partes:

1. **El esqueleto, que arma el código y no el modelo.** Lleva cada paso con su estado, la evidencia que lo cerró y su hora; cada desviación con su clase; las confirmaciones por persona con su motivo; las observaciones; y la calificación. Es la notificación de cierre que hoy se escribe a mano, pero por paso y con evidencia.
2. **La redacción del modelo.** Cada afirmación cita el `id` del evento que la sostiene.

Un chequeo sin modelo comprueba dos cosas:

- que cada `id` citado existe y dice lo que el texto afirma;
- que ninguna desviación del esqueleto quedó fuera del texto.

Es lo que el pitch llama «el reporte no omite nada». Como las métricas, el reporte del periodo no nombra personas ([ADR-0013](../../decisions/0013-el-pitch-copiloto-del-operario-sin-supervisor-encima.md)).

## 5. Cómo se prueba cada skill

Una skill que genera pautas se mide como se mide cualquier capa: con casos cuya respuesta se conoce.

| Skill | Contra qué | Qué se mide |
|---|---|---|
| `factum-extraer-protocolo` y `factum-generar-pauta` | Los seis protocolos de la semilla y sus nueve pautas escritas a mano | Pasos recuperados, controles críticos detectados, pares de pasos en el orden correcto, evidencia y capa iguales a las de la pauta a mano, pautas que pasan el validador y citas que existen en el documento |
| `factum-mejorar-pauta` | Casos con el arreglo conocido, empezando por el de la semilla (`pauta-polin-demo` v1, p3) | Si recomienda lo esperado, y si la versión nueva pasa el validador y la matriz de escenarios |
| `factum-reportar` | Las 16 OT de la semilla | Citas que existen, desviaciones omitidas (tiene que ser cero) y personas nombradas en el informe del periodo (tiene que ser cero) |
| Todas | Las rutas de la API | Que cada ruta que nombra una skill exista con ese método. Si alguien cambia la API, la prueba falla en vez de dejar la skill mintiendo |

Antes de medir conviene saber qué esperar. Un VLM sin pauta describió por su cuenta el 54,6 % de las fases de un montaje, y el 68 % con la pauta (REFERENCIAS 9). Lo que salga de `factum-generar-pauta` es un borrador que una persona corrige, no una pauta lista. `Confirmada` para el VLM; `Candidata a validar` para texto.

## 6. Lo que la API les da a las skills, leído de la base

Las skills no leen la base: llaman a la API. Cada ruta de abajo arma su respuesta desde lo que la base ya guarda (las pautas, la bitácora, los sensores, las reglas de peligro y el detector), sin tablas nuevas.

| Ruta | Para qué skill | Qué lee de la base |
|---|---|---|
| `GET /interno/inventario` | `factum-generar-pauta`, `factum-mejorar-pauta` | Cada sensor con su valor actual, los valores que llegaron en la bitácora (o su rango si es numérico), las pautas y los pasos que lo usan y las reglas de peligro que lo miran; las clases del detector con su confianza y cuántas veces decidieron; las preguntas visuales con lo que respondió la cámara |
| `POST /interno/pautas/validar` | `factum-generar-pauta`, `factum-mejorar-pauta` | Si la pauta se puede guardar, y los hallazgos: V1 a V4 de la pantalla 10 de Factum por dentro, y sensores, valores o clases que el inventario no conoce (I1 a I3). En las pautas del repo encuentra los huecos ya anotados: los dos controles críticos de cámara del LOTO y la prueba de energía cero del polín |
| `GET /cliente/metricas/pautas/{id}/pasos` | `factum-mejorar-pauta`, `factum-medir` | Por paso, además de lo de antes: en qué capa cerró, con qué confianza, cuántas veces quedó bajo el umbral, cuántos intentos tomó y cuánto tardó desde el paso anterior |
| `GET /cliente/ots/{id}/reporte` | `factum-reportar` | El esqueleto del reporte de la sección 4, con el `evento` de cada línea. Con `formato=markdown` sale listo para leer, sin modelo |
| `/cliente/ots/{id}/pasos`, `/declarar`, `/pasos/{paso}/confirmar`, `/relevo/entregar`, `/relevo/recibir`, `/eventos` | `factum-ejecutar-ot` | La ejecución con login: quien actúa sale del token |

Lo que todavía falta:

| Falta | Para qué skill | Por qué |
|---|---|---|
| **El inventario por estación** | `factum-generar-pauta` | Los sensores son globales en el servidor: el inventario es del servidor, no de una estación, y lo dice en `limites`. Que el sensor se guarde por edge es una decisión con Jonathan (pantalla 9 de [Factum por dentro](../../architecture/factum-por-dentro.html)) |
| **Las lecturas que no produjeron nada** | `factum-generar-pauta` | La bitácora guarda la lectura que cerró un paso o abrió una alerta, no cada lectura del edge. `valores_vistos` cuenta esas |
| **Cuándo empezó el operario** | `factum-medir`, `factum-reportar` | La bitácora guarda cuándo se cerró cada paso, no cuándo empezó a trabajar: el primer paso no tiene tiempo, y la ejecución se mide desde el primer evento después de asignar |
| **La matriz de escenarios con una pauta cualquiera** | `factum-mejorar-pauta` | `app/escenarios.py` corre las pautas de industria. Una versión nueva tendría que pasar la misma matriz antes de aprobarse |

## 7. Dónde viven y cómo las encuentra un agente

- **En el repo**, en `skills/`, versionadas con el código.
- **En el servidor**, en `/skills/<nombre>/SKILL.md`.
- **En `/llms.txt`**, que pasa a ser el índice que pide el estándar (REFERENCIAS 75): el título, un resumen y listas de enlaces a la guía completa, los dos OpenAPI y las skills.
- **Ninguna skill lleva un secreto.** Las internas leen la clave del equipo de una variable de entorno, y las de cliente, el token de quien entró.

## 8. Criterios de aceptación

- **CA1 —** **Dado** un protocolo de la semilla, **cuando** el equipo corre `factum-extraer-protocolo` y `factum-generar-pauta`, **entonces** la pauta queda sin aprobar, pasa el validador, nombra solo sensores y clases de la estación, y cada paso cita la parte del protocolo de donde sale.
- **CA2 —** **Dado** un control crítico que ningún sensor puede ver, **cuando** se genera la pauta, **entonces** el paso queda marcado como brecha y no se presenta como verificado por un sensor.
- **CA3 —** **Dado** el caso de la semilla (`pauta-polin-demo` v1, p3) aceptado por el supervisor, **cuando** el equipo corre `factum-mejorar-pauta`, **entonces** sale una versión 2 sin aprobar que cambia ese paso y dice por qué, citando la alerta de orden y la observación.
- **CA4 —** **Dado** un paso de sensor confirmado por persona en dos o más OT, **cuando** se corre `factum-mejorar-pauta`, **entonces** recomienda revisar el sensor o pasar el paso a cámara, y no culpa al operario.
- **CA5 —** **Dado** una OT completa con una alerta de seguridad, **cuando** el supervisor pide el reporte, **entonces** la alerta aparece citada por su `id`, y el chequeo sin modelo no encuentra citas falsas ni desviaciones omitidas.
- **CA6 —** **Dado** que alguien renombra una ruta que nombra una skill, **cuando** corren las pruebas, **entonces** fallan.

## 9. Riesgos y decisiones abiertas

| Tema | Impacto | Qué falta decidir | Se consulta a | Decide |
|---|---|---|---|---|
| Publicar las skills internas | medio | ¿Las internas se sirven en `/skills` junto a las de cliente, o solo viven en el repo? No llevan secretos, pero muestran cómo trabaja el equipo | Equipo | Francisco |
| Dónde corre el modelo de las skills | medio | ¿Las corre el agente de quien las usa, o Factum ofrece un endpoint que las corre? Lo primero es más simple; lo segundo cobra por uso | Equipo | Francisco |
| Inventario por estación | alto | ¿El sensor se guarda por edge? Es lo que pide la pantalla 9 de Factum por dentro, y sin eso el inventario no aísla una estación de otra | Jonathan | Francisco |
| Perfil por protocolo | medio | ¿Los umbrales de las capas (0,8, 0,25 y 0,75) y las reglas de peligro viajan con el protocolo? Hoy son constantes del código, iguales para todos | Jonathan | Francisco |
| Una pauta sin protocolo propio | bajo | El cliente que no tiene procedimiento: ¿el borrador sale de grabar a un experto (FLUJO, paso 2), con otra skill? | Equipo | Francisco |
| Cuántas repeticiones para confiar | medio | ¿Cuántas OT de la versión nueva hacen falta para decir «mejoró»? Hoy basta una (ADR-0014) | Equipo | Francisco |

## Fuentes

- [ADR-0003](../../decisions/0003-patrones-de-arquitectura-para-el-mvp.md), [0004](../../decisions/0004-verificacion-por-capas.md), [0006](../../decisions/0006-la-ot-nace-del-protocolo.md), [0011](../../decisions/0011-protocolos-y-pautas-por-servicio-interno-ot-por-servicio-al-cliente.md), [0012](../../decisions/0012-login-y-clientes-cada-empresa-ve-lo-suyo.md), [0013](../../decisions/0013-el-pitch-copiloto-del-operario-sin-supervisor-encima.md) y [0014](../../decisions/0014-mejora-continua-por-evidencia-y-metricas-por-pauta.md).
- [FLUJO](../../architecture/FLUJO.md), pasos 2 a 6, y [LOGICA](../../architecture/LOGICA.md).
- [Factum por dentro](../../architecture/factum-por-dentro.html), pantallas 9 y 10: el inventario de la estación, el validador V1 a V4 y el perfil por protocolo.
- Los seis protocolos de `datos/protocolos/` y sus pautas, que son el caso de prueba.
- REFERENCIAS 3, 4, 9, 44, 56, 74, 75, 76 y 77.
