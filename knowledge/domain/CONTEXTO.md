# Contexto

> Una página: qué problema resolvemos, para quién, hasta dónde llega y cómo nos van a evaluar.

## El problema

En una operación donde ejecutar mal un procedimiento sale caro, como una faena minera, tres cosas fallan a la vez. El producto sirve a cualquier flujo operacional; el caso de uso es el mantenimiento de maquinaria ([ADR-0009](../decisions/0009-flujo-operacional-verificable-mantenimiento-como-caso-de-uso.md)), y de ahí salen las cifras:

1. **La bitácora no sirve como dato.** Las OT se escriben en texto libre, con criterio de cada técnico. El tiempo medio entre fallas de un mismo equipo puede ir de 97 a 226 días según cómo un analista agrupe las OT (REFERENCIAS 4). `Confirmada`.
2. **La pauta no se cumple y nadie lo ve.** Las mineras ya tienen procedimientos estandarizados, pero no tienen cómo comprobar que se cumplieron: depende solo del operario ([planteamiento del equipo](./fuentes/2026-11-21-planteamiento-del-equipo.md), `Candidata a validar`). Muchas desviaciones nacen de la presión de la jefatura y de pautas mal hechas, no del operario (REFERENCIAS 33). Las guías actuales muestran el paso siguiente, pero no comprueban que el anterior se hizo (REFERENCIAS 18). `Confirmada`.
3. **El error es caro.** La mantención no planificada puede bajar la disponibilidad de la maquinaria minera hasta 37% (REFERENCIAS 24). La minería chilena tuvo 20 muertes en 2025, frente a 11 en 2024 (REFERENCIAS 36, prensa que cita a Sernageomin), y 13 en 2026 al 14 de octubre (REFERENCIAS 43). `Confirmada`. Cuántas de esas muertes ocurrieron en tareas de mantenimiento sigue siendo `Brecha` para Chile, pero la pregunta ya no es la que importa: entre los 26 miembros de ICMM, la **ejecución inefectiva del control** fue la falla más común en los incidentes fatales de 2025, en 19 de 26 (REFERENCIAS 40). `Confirmada`. El control existía y se ejecutó mal, que es justo lo que este flujo verifica. Ver [research → Fatalidades y controles críticos](../projects/research/research.md#fatalidades-y-controles-críticos).

El caso que usa el equipo es la detención no planificada de una correa transportadora. Una parada de planta por problemas en las correas cuesta entre USD 100.000 y 300.000 por hora, según el gerente general de un proveedor chileno de sistemas de transferencia (REFERENCIAS 38). Para cualquier detención no planificada, la prensa cita estimaciones del sector de USD 40.000 a más de 200.000 por hora (REFERENCIAS 39). Ninguna de las dos es un dato de un operador ni de un estudio identificable, y los USD 300.000 son el tope del rango, no el valor típico. `Candidata a validar`.

## La visión

**Un operario aumentado con IA.** La IA acompaña al operario como copiloto mientras ejecuta: comprueba cada paso de la pauta y le avisa en el momento si se salta uno, para que el error se corrija ahí y no después. El resultado es un operario que ejecuta bien, con menos accidentes y con una bitácora confiable, gracias a pautas suficientes y verificables. La bitácora no se escribe: es la lista de pasos verificados con su evidencia. `Confirmada` por el equipo ([planteamiento del 2026-11-21](./fuentes/2026-11-21-planteamiento-del-equipo.md)).

**El pitch: el copiloto de tus operarios.** Como el copiloto está en cada trabajo, todo queda registrado con su evidencia: el reporte no se escribe ni omite nada, el turno siguiente retoma sin depender de quien se fue y la pauta mejora con cada ejecución. La operación sabe que cada trabajo se hizo bien **sin poner un supervisor encima de cada uno**, y los datos salen por API hacia sus sistemas. No se dice que Factum mira la operación todo el tiempo: mira el paso y la pauta, no a la persona. La frase completa, y qué se presenta como construido y qué como visión, están en el [ADR-0013](../decisions/0013-el-pitch-copiloto-del-operario-sin-supervisor-encima.md) ([transcripción](./fuentes/2026-11-21-pitch-del-copiloto.md)). `Candidata a validar`.

**Qué es.** Factum vuelve verificable cualquier flujo operacional: un procedimiento con pasos en el que cada paso declara qué evidencia lo cierra. El objetivo es reducir el impacto de una ejecución mal hecha. El mantenimiento de maquinaria es el caso de uso, elegido por su alto impacto ([ADR-0009](../decisions/0009-flujo-operacional-verificable-mantenimiento-como-caso-de-uso.md)). `Candidata a validar`.

**Cliente objetivo.** Una operación con equipos críticos, de cualquier rubro, que ya tiene procedimientos estandarizados y no tiene cómo verificarlos. A la que no los tiene, el sistema le redacta el primero observando al operario, y desde ahí sigue el mismo flujo. La minería es el caso del demo, no el límite del producto ([ADR-0005](../decisions/0005-producto-general-mineria-como-caso-del-demo.md)). `Candidata a validar`.

**El flujo.** El cliente entrega su protocolo; el sistema lo extrae y lo vuelve una pauta comprobable; de esa pauta se genera la OT cada vez que hay que ejecutar la tarea, sea por calendario, por pedido o por una falla ([ADR-0006](../decisions/0006-la-ot-nace-del-protocolo.md)); cámara, sensores, analítica y modelos de lenguaje guían la ejecución paso a paso.

Lo que entrega, según el planteamiento del equipo. `Candidata a validar`:

1. **Verificación en el momento.** Cámara y sensores (vibración, temperatura y otros) comprueban cada paso. Si el operario se salta uno, recibe el aviso por un auricular.
2. **Relevo de turno.** Cuando un trabajo dura más de un turno, el siguiente lo retoma desde el último paso verificado, sin depender de quien se fue. El formato (resumen, consultas o *briefing*) está por definir.
3. **Mejora de la pauta.** Tras varias ejecuciones del mismo procedimiento, el sistema propone mejoras. Un paso que se saltan muchos operarios que normalmente cumplen apunta a la pauta, no a ellos.
4. **Foco para el supervisor.** Ve en qué áreas y en qué pautas se saltan más pasos, y supervisa en persona solo los trabajos de mayor riesgo. Ve pautas y áreas, no personas ([LOGICA](../architecture/LOGICA.md#cuándo-el-sistema-propone-cambiar-la-pauta)).
5. **Conocimiento del operario.** Como el copiloto lo acompaña, el operario puede dejar lo que observa mientras ejecuta, como una pieza gastada o un paso que no calza con el equipo, y eso alimenta la mejora de la pauta y el reporte. Viene del [pitch del copiloto](./fuentes/2026-11-21-pitch-del-copiloto.md). Cuando el mismo paso se desvía en varias ejecuciones más que el resto de la pauta, el supervisor recibe el aviso con el cambio concreto que propone Factum; si lo aplica, Factum arma y aprueba la versión nueva, y esa versión se comprueba con sus propias OT ([ADR-0014](../decisions/0014-mejora-continua-por-evidencia-y-metricas-por-pauta.md), [ADR-0018](../decisions/0018-la-pauta-tiene-un-protocolo-dueno-y-cada-protocolo-itera-por-separado.md)). Lo que a la pauta le falta respecto de su protocolo se propone sin esperar ninguna OT ([ADR-0016](../decisions/0016-una-pauta-sale-del-protocolo-que-aplica-a-su-tarea.md)).
6. **Datos por API.** La OT, su bitácora y su calificación salen por API hacia los sistemas del cliente, y de ahí, métricas por pauta y por área. El pedido y la lista de OT con login ([ADR-0012](../decisions/0012-login-y-clientes-cada-empresa-ve-lo-suyo.md)) y las métricas por pauta, equipo, paso y día ([ADR-0014](../decisions/0014-mejora-continua-por-evidencia-y-metricas-por-pauta.md)), nunca por persona.

La verificación no depende solo de un modelo de lenguaje: hay sensores y reglas deterministas debajo. Ver [ADR-0004](../decisions/0004-verificacion-por-capas.md).

**Hacia dónde va.** El handoff original del research proponía además cruzar la telemetría con las OT históricas, predecir fallas y abrir OT automáticas. El planteamiento del 2026-11-21 no lo menciona, y la evidencia para predecir es la más débil del flujo. Queda como visión: fuera del alcance del demo y del pitch, salvo como una línea de hacia dónde va ([registro de decisiones](../decisions/decisions.md)). `Candidata a validar`.

La entrada a una operación es *plug & play*: sensores pegados al equipo, la cámara del operario y el archivo exportado de OT, sin tocar el PLC ni pedirle integración a TI. El orden es identificar el proceso, estandarizar, mejorar y recién después predecir. La mayoría de las soluciones de mantenimiento predictivo parten por predecir y chocan con datos malos; nosotros llegamos a predecir como consecuencia. `Candidata a validar`.

Dos cuidados con el *plug & play*. Una faena no deja conectar nada a su red de control sin meses de aprobaciones de ciberseguridad, así que lo creíble es solo lo no invasivo: «funciona el primer día sin pedirle nada a TI». Y la predicción no se promete desde el día uno: detectar anomalías sí, la vida útil remanente necesita semanas o meses de datos por equipo. `Candidata a validar`.

Un ángulo de impacto adicional: capturar el conocimiento de los técnicos senior antes de que se retiren, grabando cómo ejecutan la tarea. `Candidata a validar`.

Tres cuidados con el planteamiento, que salen de la evidencia; el detalle está en [research](../projects/research/research.md#evidencia-frente-al-planteamiento-del-equipo). Un procedimiento redactado tras observar una sola ejecución es un borrador que el experto corrige, no un protocolo. Un aviso por audio con falsas alarmas se termina ignorando. Y si el dato de quién se salta pasos se usa para vigilar personas, puede aumentar la presión que causa parte de las desviaciones (REFERENCIAS 33); por eso el pitch no presenta a Factum como un supervisor que mira todo el tiempo ([ADR-0013](../decisions/0013-el-pitch-copiloto-del-operario-sin-supervisor-encima.md)). `Candidata a validar`.

**Fuera de alcance:** gemelos digitales basados en física.

## Industrias

Lo que une a los posibles clientes no es el rubro sino el tipo de activo: equipos críticos con pautas repetibles. El producto es el mismo en los tres; la minería es el caso del demo. Ver [ADR-0005](../decisions/0005-producto-general-mineria-como-caso-del-demo.md).

| | Minería | Eléctrica | Construcción |
|---|---|---|---|
| Encaje | Alto: equipos críticos, pautas repetibles, detención cara | Alto: subestaciones, transformadores y líneas con pauta | Medio: trabajo por proyecto, salvo la flota de maquinaria |
| Seguridad | Bloqueo y etiquetado en equipos con energía acumulada | El más fuerte: el bloqueo evita la electrocución | Alta, pero ligada a la obra y no al mantenimiento |
| Papers en la revisión IEEE (42) | 1 | 13 | 0 |
| Rol | Caso del demo | Mismo flujo en subestaciones; fuente de métodos | Mismo flujo en la flota de maquinaria |

## Cómo nos evalúan

Track Physical World. Criterios y pesos de la hackathon: `Confirmada`.

| Criterio | Peso | Qué lo sostiene hoy | Qué falta |
|---|---|---|---|
| Aspecto técnico | 25% | El edge con ESP32, cámara y detector, la verificación en tres capas y la API en vivo. El detalle, en [SEGUIMIENTO](../roadmap/SEGUIMIENTO.md) | Medir falsos positivos, falsos negativos y la latencia del aviso |
| Ejecución | 20% | La demo de bloqueo con ESP32 y cámara, desplegada en la VM ([SEGUIMIENTO](../roadmap/SEGUIMIENTO.md)) | Un demo de punta a punta, ensayado, que no se caiga |
| Ambición | 20% | El operario aumentado con IA, un producto que vuelve verificable cualquier flujo operacional y el ciclo de mejora de la pauta | Mostrar el ciclo completo, aunque sea a escala chica |
| Impacto | 20% | La ejecución inefectiva del control, 19 de 26 incidentes fatales de los miembros de ICMM en 2025, de fuente primaria (40); ICMM pide verificar los controles críticos y nombra el aislamiento de energía, que es el paso del demo | Una fuente de operador o de estudio para el costo por hora; hoy es la estimación de un proveedor (38) |
| Originalidad | 15% | Los vacíos de la literatura | Que el vacío se note en el demo, no solo en una lámina |

Lectura del equipo, `Candidata a validar`: ejecución y aspecto técnico suman 45% y se juzgan por lo que funciona en vivo, no por el research. Además, tres de los cuatro pasos del ciclo son software puro. La parte física, la que el jurado del track va a buscar, es verificar con cámara y sensores la ejecución en terreno, y es también el vacío más fuerte de la literatura. Por eso el demo pone esa parte al centro: ver [FLUJO → Demo propuesto](../architecture/FLUJO.md#demo-propuesto).

## Fuentes

- Criterios y pesos de la hackathon, comunicados por el equipo el 2026-11-21. `Confirmada`.
- Handoff de la revisión bibliográfica de Francisco Zúñiga, 2026-11-21: objetivo, alcance y búsquedas. `Confirmada`.
- [Planteamiento del equipo, 2026-11-21](./fuentes/2026-11-21-planteamiento-del-equipo.md): problema, premisa, cliente objetivo, flujo, capas y demo. Transcripción íntegra.
- [Pitch del copiloto, 2026-11-21](./fuentes/2026-11-21-pitch-del-copiloto.md): la propuesta de Francisco para el pitch de venta. Transcripción íntegra.
- Reportes de seguridad de ICMM 2025, fuentes primarias abiertas el 2026-11-21: REFERENCIAS 40 y 41. `Confirmada`.
- Números de referencia: ver [REFERENCIAS](../projects/research/REFERENCIAS.md).
