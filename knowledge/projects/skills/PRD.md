# PRD — Skills de Factum: del protocolo a la OT, el reporte y la mejora

> **Dueño de la decisión:** Francisco · **Se consulta a:** Jonathan, por las tres capas y el inventario de la estación; Daniel, por lo que la interfaz muestra de cada skill · **Alcance:** cómo se diseñan las skills que un agente usa para extraer un protocolo, generar sus pautas, aterrizarlas en OT, reportar y recomendar mejoras.
>
> **Estado →** [SEGUIMIENTO](../../roadmap/SEGUIMIENTO.md). Este documento no lleva avance. Las ocho skills están en `.claude/skills/`: las cuatro internas las construyó Jonathan ([ADR-0015](../../decisions/0015-reconocer-procesos-con-skills-de-agente-y-un-criterio.md)) y las cuatro de cliente salen de este PRD.

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
| **El procedimiento de trabajo** | El documento que dice cómo se hace la tarea y qué controles exige. El DS 132 pide bloqueo y advertencia antes de mantener (REFERENCIAS 44, art. 52); las estrategias de controles nombran los controles críticos y cómo se comprueban (56) | Protocolo | `reconocer-proceso` |
| **La lista de tareas** (*task list* de SAP PM) | Las operaciones de la tarea, en orden. El plan de mantenimiento la asigna a cada ítem (REFERENCIAS 76) | Pauta, versionada y aprobada por una persona | `reconocer-proceso` |
| **El plan de mantenimiento** | En la fecha debida genera la orden y copia en ella las operaciones de la lista (76) | OT, por calendario, pedido o falla ([ADR-0006](../../decisions/0006-la-ot-nace-del-protocolo.md)) | `pedir-ot` |
| **La ejecución** | El técnico sigue la orden; nadie comprueba el paso mientras ocurre | El copiloto comprueba cada paso con la capa que corresponde y avisa | `ejecutar-ot` |
| **La notificación de cierre** | Se confirma cada operación y se escribe lo que pasó (77). El texto libre y los códigos tienen errores sistemáticos (3, 4) | Bitácora con evidencia; el reporte se arma desde ella | `reportar-ot` |
| **La revisión del procedimiento** | Tras un incidente o una auditoría, a criterio | Propuestas desde la evidencia, validadas, más recomendaciones de capa | `optimizar-proceso`, `medir-y-mejorar` |

## 3. Las tres capas: lo que una skill decide por cada paso

El sistema de verificación que construyó Jonathan ([ADR-0004](../../decisions/0004-verificacion-por-capas.md), Frente 3) comprueba cada paso con la primera capa que puede decidirlo:

| Capa | Qué es | Dónde está | Decide cuando |
|---|---|---|---|
| 1 · Programática | Sensores y reglas con marca de tiempo | `app/reglas.py` | Un sensor mide el estado final del paso. Es la única que interrumpe al operario |
| 2 · Visión y señales | El detector de objetos (YOLO) y las anomalías de señal | `reglas.por_deteccion`, `scoring.capa2` | El detector ve la clase con 0,8 o más en cada detección reciente, o con menos de 0,25 si el paso espera que ya no esté |
| 3 · Modelo de lenguaje | Un VLM responde la pregunta visual del paso sobre el último cuadro | `app/verificacion.py` | Lo demás que solo se ve. Bajo 0,75 de confianza, su calificación queda en `warning` |

Que cada etapa de una pauta se procese según lo que necesita es exactamente lo que el diseño de una skill tiene que respetar:

- **`reconocer-proceso` elige la capa más barata que puede decidir cada paso**, según lo que la estación tiene.
- **`optimizar-proceso` mueve un paso de capa** cuando la evidencia de sus ejecuciones muestra que la elegida no le sirve.

**La regla de elección**, en orden:

1. **Sensor.** Si un sensor de la estación mide el estado final del paso, la capa es 1.
2. **Detector.** Si no, y el detector conoce un objeto que aparece o desaparece con el paso, la capa es 2. La skill escribe además la pregunta visual, para que la capa 3 responda cuando el detector no llega a la certeza.
3. **Pregunta visual.** Si solo se ve, la capa es 3, con una pregunta que se responda con sí o no sobre una foto.
4. **Confirmación.** Si nada lo ve, el paso es de confirmación. Un control crítico no puede quedar así sin marcarlo como brecha: es el caso de la comprobación de energía cero, que hoy cierra la palabra del operario (ADR-0011).

## 4. Las skills

Cada skill es una carpeta en `.claude/skills/` con un `SKILL.md` de menos de 500 líneas. Ahí Claude Code las carga solas. Su encabezado lleva `name` y una `description` que dice qué hace y cuándo usarla, que es lo único que el agente lee antes de activarla (REFERENCIAS 74).

### Internas: las usa el equipo de Factum

Las construyó Jonathan. Están descritas, medidas y con sus límites en el [ADR-0015](../../decisions/0015-reconocer-procesos-con-skills-de-agente-y-un-criterio.md). Trabajan sobre el repo y escriben borradores en `datos/borradores/`; nunca cargan ni aprueban. Lo que se puede comprobar lo comprueba `app/analisis.py`, no el agente.

| Skill | Entra | Sale |
|---|---|---|
| `reconocer-proceso` | El protocolo del cliente, o una ejecución grabada, y la estación (`datos/estaciones/`) | Un borrador de pauta: la evidencia y la capa de cada paso según la sección 3, la cita literal de cada uno, los controles críticos, lo que no cabe en una pauta lineal y los sensores que faltan |
| `optimizar-proceso` | La bitácora de una pauta, o contra un servidor, `GET /interno/mejoras` y las métricas por paso | La versión siguiente, con la razón y las OT de cada cambio |
| `regla-programatica` | Un peligro descrito con lecturas de sensores | Una regla de capa 1 en `app/reglas.py`, con su test |
| `solucion-vision` | Un paso de cámara y sus imágenes | La pregunta al VLM o el detector, y los casos que lo miden |

`reconocer-proceso` hace en una sola skill lo que este PRD separaba en dos: extraer el protocolo y generar la pauta. `regla-programatica` y `solucion-vision` no estaban en el diseño: son las que mueven un paso de capa cuando la evidencia lo pide.

**Las recomendaciones de capa.** Las hace `optimizar-proceso` con el criterio de `app/analisis.py`. Es la mejora continua interna con las tres capas:

| Lo que muestra la evidencia de un paso | Qué recomienda |
|---|---|
| Un paso de sensor que una persona confirma seguido | El sensor no ve lo que se hizo: revisar su montaje. Primero la estación, no el operario |
| Un paso de cámara que el VLM cierra con poca confianza, o que no cerró en varias OT | `solucion-vision`: reescribir la pregunta, o bajar el paso a capa 2 con el detector |
| Un control crítico que cierra la cámara o la palabra | `instrumentar`: pedir un sensor. «Control deshecho» solo vigila pasos de sensor (regla V1 del validador) |
| Un peligro que los sensores describen y ninguna regla atrapa | `regla-programatica` |
| Una alerta de orden repetida en el mismo paso | Revisar el orden con quien hace la tarea. Es el caso de la semilla: el punto de bloqueo queda lejos del tablero |
| Observaciones del operario sobre el paso | Incorporarlas a la instrucción, citándolas |

### De cliente: las usa una empresa con su token

Trabajan contra la API, con el login de quien las usa, y el servidor las publica (sección 7).

| Skill | Para quién | Qué le enseña al agente |
|---|---|---|
| `pedir-ot` | Supervisor o el planificador del cliente | Entrar, elegir una pauta habilitada, pedir la OT y asignarla. Es lo que llama un calendario o una falla. Si la pauta no está, se detiene: no crea protocolos ni pautas |
| `ejecutar-ot` | Operario, o el agente de voz que lo acompaña | Unir la OT a la estación (y tomarla solo si la persona lo pide), seguir el paso en curso, declarar, dejar observaciones y entregar el turno. Lo que no hace nunca: saltar el orden, callar un aviso de la capa 1 o confirmar un paso contra la evidencia por su cuenta |
| `reportar-ot` | Supervisor o el operario de la OT | Entregar el reporte que arma el servidor. Si le piden redactar, citar el evento de cada afirmación y no omitir ninguna desviación. El informe del periodo sale de las métricas y no nombra personas |
| `medir-y-mejorar` | Supervisor | Qué GET responde cada pregunta, cómo leer el cumplimiento y las desviaciones, y cómo validar las propuestas de mejora, que decide el supervisor |

### El reporte: el registro manda y el modelo redacta encima

`reportar-ot` sigue la regla de [LOGICA](../../architecture/LOGICA.md#relevo-de-turno): el resumen de un modelo va encima del registro, nunca en su lugar, y el modelo recibe el registro completo de la OT. El reporte tiene dos partes:

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
| `reconocer-proceso` | Los seis protocolos de la semilla y sus nueve pautas escritas a mano | Pasos recuperados, controles críticos detectados, pares de pasos en el orden correcto, evidencia y capa iguales a las de la pauta a mano, pautas que pasan el validador y citas que existen en el documento |
| `optimizar-proceso` | Casos con el arreglo conocido, empezando por el de la semilla (`pauta-polin-demo` v1, p3) | Si recomienda lo esperado, y si la versión nueva pasa el validador y la matriz de escenarios |
| `reportar-ot` | Las OT de la semilla | Citas que existen, desviaciones omitidas (tiene que ser cero) y personas nombradas en el informe del periodo (tiene que ser cero) |
| Todas | Las rutas de la API | Que cada ruta que nombra una skill exista con ese método. Si alguien cambia la API, la prueba falla en vez de dejar la skill mintiendo |

Antes de medir conviene saber qué esperar. Un VLM sin pauta describió por su cuenta el 54,6 % de las fases de un montaje, y el 68 % con la pauta (REFERENCIAS 9). Lo que salga de `reconocer-proceso` es un borrador que una persona corrige, no una pauta lista. `Confirmada` para el VLM; `Candidata a validar` para texto.

## 6. Lo que la API les da a las skills, leído de la base

Las skills no leen la base: llaman a la API. Cada ruta de abajo arma su respuesta desde lo que la base ya guarda (las pautas, la bitácora, los sensores, las reglas de peligro y el detector), sin tablas nuevas.

| Ruta | Para qué skill | Qué lee de la base |
|---|---|---|
| `GET /interno/inventario` | `reconocer-proceso`, `optimizar-proceso` | Las estaciones declaradas en `datos/estaciones/` y qué valores declarados nunca llegaron. Cada sensor con su valor actual, los valores que llegaron en la bitácora (o su rango si es numérico), las pautas y los pasos que lo usan y las reglas de peligro que lo miran; las clases del detector con su confianza y cuántas veces decidieron; las preguntas visuales con lo que respondió la cámara |
| `POST /interno/pautas/validar` | `reconocer-proceso`, `optimizar-proceso` | Si la pauta se puede guardar, y los hallazgos: V1 a V4 de la pantalla 10 de Factum por dentro, sensores, valores o clases que el inventario no conoce (I1 a I3), y las comprobaciones de `app/analisis.py` de Jonathan: pasos que se cierran solos (A1), reglas que disparan en una ejecución correcta (A2), citas que no están en el protocolo (A3) y pasos que la estación declarada no puede cerrar (A4). Es un solo validador para la API y para las skills. En las pautas del repo encuentra los huecos ya anotados: los dos controles críticos de cámara del LOTO y la prueba de energía cero del polín |
| `GET /cliente/metricas/pautas/{id}/pasos` | `optimizar-proceso`, `medir-y-mejorar` | Por paso, además de lo de antes: en qué capa cerró, con qué confianza, cuántas veces quedó bajo el umbral, cuántos intentos tomó y cuánto tardó desde el paso anterior |
| `GET /cliente/ots/{id}/reporte` | `reportar-ot` | El esqueleto del reporte de la sección 4, con el `evento` de cada línea. Con `formato=markdown` sale listo para leer, sin modelo |
| `/cliente/ots/{id}/pasos`, `/declarar`, `/pasos/{paso}/confirmar`, `/relevo/entregar`, `/relevo/recibir`, `/eventos` | `ejecutar-ot` | La ejecución con login: quien actúa sale del token |

Lo que todavía falta:

| Falta | Para qué skill | Por qué |
|---|---|---|
| **El inventario por estación** | `reconocer-proceso` | Los sensores son globales en el servidor: el inventario es del servidor, no de una estación, y lo dice en `limites`. Que el sensor se guarde por edge es una decisión con Jonathan (pantalla 9 de [Factum por dentro](../../architecture/factum-por-dentro.html)) |
| **Las lecturas que no produjeron nada** | `reconocer-proceso` | La bitácora guarda la lectura que cerró un paso o abrió una alerta, no cada lectura del edge. `valores_vistos` cuenta esas |
| **Cuándo empezó el operario** | `medir-y-mejorar`, `reportar-ot` | La bitácora guarda cuándo se cerró cada paso, no cuándo empezó a trabajar: el primer paso no tiene tiempo, y la ejecución se mide desde el primer evento después de asignar |
| **La matriz de escenarios con una pauta cualquiera** | `optimizar-proceso` | `app/escenarios.py` corre las pautas de industria. Una versión nueva tendría que pasar la misma matriz antes de aprobarse |

## 7. Dónde viven y cómo las encuentra un agente

- **En el repo**, en `.claude/skills/`, versionadas con el código. Claude Code las carga solas.
- **En el servidor**, solo las de cliente: `GET /skills` las lista y `GET /skills/<nombre>/SKILL.md` las entrega. Las internas no se publican, porque trabajan sobre el repo y con la clave del equipo.
- **En `/llms.txt`**, el índice que pide el estándar (REFERENCIAS 75): el título, un resumen y listas de enlaces a las skills, la guía completa y los dos OpenAPI. La guía completa está en `/llms-full.txt` y es la misma de `/agente`.
- **Ninguna skill lleva un secreto.** Las de cliente leen el usuario y la clave de `FACTUM_USUARIO` y `FACTUM_CLAVE`, o se los piden a la persona, y nunca los escriben.
- **`tests/test_skills.py`** comprueba el formato de las ocho y que cada ruta que nombran exista en la API con ese método.

## 8. Criterios de aceptación

- **CA1 —** **Dado** un protocolo de la semilla, **cuando** el equipo corre `reconocer-proceso`, **entonces** la pauta queda sin aprobar, pasa el validador, nombra solo sensores y clases de la estación, y cada paso cita la parte del protocolo de donde sale.
- **CA2 —** **Dado** un control crítico que ningún sensor puede ver, **cuando** se genera la pauta, **entonces** el paso queda marcado como brecha y no se presenta como verificado por un sensor.
- **CA3 —** **Dado** el caso de la semilla (`pauta-polin-demo` v1, p3) aceptado por el supervisor, **cuando** el equipo corre `optimizar-proceso`, **entonces** sale una versión 2 sin aprobar que cambia ese paso y dice por qué, citando la alerta de orden y la observación.
- **CA4 —** **Dado** un paso de sensor confirmado por persona en dos o más OT, **cuando** se corre `optimizar-proceso`, **entonces** recomienda revisar el sensor o pasar el paso a cámara, y no culpa al operario.
- **CA5 —** **Dado** una OT completa con una alerta de seguridad, **cuando** el supervisor pide el reporte, **entonces** la alerta aparece citada por su `id`, y el chequeo sin modelo no encuentra citas falsas ni desviaciones omitidas.
- **CA6 —** **Dado** que alguien renombra una ruta que nombra una skill, **cuando** corren las pruebas, **entonces** fallan.

## 9. Riesgos y decisiones abiertas

| Tema | Impacto | Qué falta decidir | Se consulta a | Decide |
|---|---|---|---|---|
| Publicar las skills internas | bajo | Por ahora el servidor publica solo las de cliente. ¿Se publican también las internas? No llevan secretos, pero muestran cómo trabaja el equipo y piden el repo | Equipo | Francisco |
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
