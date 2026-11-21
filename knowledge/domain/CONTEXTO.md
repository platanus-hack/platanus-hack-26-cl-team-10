# Contexto

> Una página: qué problema resolvemos, para quién, hasta dónde llega y cómo nos van a evaluar.

## El problema

En una operación donde una falla o un error de mantenimiento salen caros, como una faena minera, tres cosas fallan a la vez:

1. **La bitácora no sirve como dato.** Las OT se escriben en texto libre, con criterio de cada técnico. El tiempo medio entre fallas de un mismo equipo puede ir de 97 a 226 días según cómo un analista agrupe las OT (REFERENCIAS 4). `Confirmada`.
2. **La pauta no se cumple y nadie lo ve.** Las mineras ya tienen procedimientos estandarizados, pero no tienen cómo comprobar que se cumplieron: depende solo del operario ([planteamiento del equipo](./fuentes/2026-11-21-planteamiento-del-equipo.md), `Candidata a validar`). Muchas desviaciones nacen de la presión de la jefatura y de pautas mal hechas, no del operario (REFERENCIAS 33). Las guías actuales muestran el paso siguiente, pero no comprueban que el anterior se hizo (REFERENCIAS 18). `Confirmada`.
3. **El error es caro.** La mantención no planificada puede bajar la disponibilidad de la maquinaria minera hasta 37% (REFERENCIAS 24). La minería chilena tuvo 20 muertes en 2025, frente a 11 en 2024 (REFERENCIAS 36, prensa que cita a Sernageomin). `Confirmada`. Cuántas de esas muertes ocurrieron en tareas de mantenimiento: `Brecha`.

El caso que usa el equipo es la detención no planificada de una correa transportadora. Una parada de planta por problemas en las correas cuesta entre USD 100.000 y 300.000 por hora, según el gerente general de un proveedor chileno de sistemas de transferencia (REFERENCIAS 38). Para cualquier detención no planificada, la prensa cita estimaciones del sector de USD 40.000 a más de 200.000 por hora (REFERENCIAS 39). Ninguna de las dos es un dato de un operador ni de un estudio identificable, y los USD 300.000 son el tope del rango, no el valor típico. `Candidata a validar`.

## La visión

**Un operario aumentado con IA.** La IA acompaña al operario como copiloto mientras ejecuta: comprueba cada paso de la pauta y le avisa en el momento si se salta uno, para que el error se corrija ahí y no después. El resultado es un operario que ejecuta bien, con menos accidentes y con una bitácora confiable, gracias a pautas suficientes y verificables. La bitácora no se escribe: es la lista de pasos verificados con su evidencia. `Confirmada` por el equipo ([planteamiento del 2026-11-21](./fuentes/2026-11-21-planteamiento-del-equipo.md)).

**Cliente objetivo.** Una operación que ya tiene procedimientos estandarizados y no tiene cómo verificarlos. A la que no los tiene, el sistema le redacta el primero observando al operario, y desde ahí sigue el mismo flujo. `Candidata a validar`.

Lo que entrega, según el planteamiento del equipo. `Candidata a validar`:

1. **Verificación en el momento.** Cámara y sensores (vibración, temperatura y otros) comprueban cada paso. Si el operario se salta uno, recibe el aviso por un auricular.
2. **Relevo de turno.** Cuando un trabajo dura más de un turno, el siguiente lo retoma desde el último paso verificado, sin depender de quien se fue. El formato (resumen, consultas o *briefing*) está por definir.
3. **Mejora de la pauta.** Tras varias ejecuciones del mismo procedimiento, el sistema propone mejoras. Un paso que se saltan muchos operarios que normalmente cumplen apunta a la pauta, no a ellos.
4. **Foco para el supervisor.** Ve en qué áreas y en qué pautas se saltan más pasos, y supervisa en persona solo los trabajos de mayor riesgo.

La verificación no depende solo de un modelo de lenguaje: hay sensores y reglas deterministas debajo. Ver [ADR-0004](../decisions/0004-verificacion-por-capas.md).

El objetivo de largo plazo, del handoff original, es un ciclo cerrado con datos reales:

1. Cruzar telemetría IoT con el texto de las OT y bitácoras.
2. Predecir fallas y abrir OT automáticas.
3. Ejecutar con pautas estandarizadas que quedan auditadas y verificadas, incluso con imágenes.
4. Usar lo auditado para actualizar las pautas matriz.

El planteamiento del 2026-11-21 no menciona predecir fallas ni abrir OT automáticas: ahí la OT nace del procedimiento que el cliente ya tiene. Si los pasos 1 y 2 siguen en el alcance del demo está abierto en [SEGUIMIENTO](../roadmap/SEGUIMIENTO.md).

La entrada a una operación es *plug & play*: sensores pegados al equipo, la cámara del operario y el archivo exportado de OT, sin tocar el PLC ni pedirle integración a TI. El orden es identificar el proceso, estandarizar, mejorar y recién después predecir. La mayoría de las soluciones de mantenimiento predictivo parten por predecir y chocan con datos malos; nosotros llegamos a predecir como consecuencia. `Candidata a validar`.

Dos cuidados con el *plug & play*. Una faena no deja conectar nada a su red de control sin meses de aprobaciones de ciberseguridad, así que lo creíble es solo lo no invasivo: «funciona el primer día sin pedirle nada a TI». Y la predicción no se promete desde el día uno: detectar anomalías sí, la vida útil remanente necesita semanas o meses de datos por equipo. `Candidata a validar`.

Un ángulo de impacto adicional: capturar el conocimiento de los técnicos senior antes de que se retiren, grabando cómo ejecutan la tarea. `Candidata a validar`.

Tres cuidados con el planteamiento, que salen de la evidencia; el detalle está en [research](../projects/research/research.md#evidencia-frente-al-planteamiento-del-equipo). Un procedimiento redactado tras observar una sola ejecución es un borrador que el experto corrige, no un protocolo. Un aviso por audio con falsas alarmas se termina ignorando. Y si el dato de quién se salta pasos se usa para vigilar personas, puede aumentar la presión que causa parte de las desviaciones (REFERENCIAS 33). `Candidata a validar`.

**Fuera de alcance:** gemelos digitales basados en física.

## Industrias

Lo que une a los posibles clientes no es el rubro sino el tipo de activo: equipos críticos con pautas repetibles. Ver [ADR-0001](../decisions/0001-mineria-como-mercado-de-entrada.md).

| | Minería | Eléctrica | Construcción |
|---|---|---|---|
| Encaje | Alto: equipos críticos, pautas repetibles, detención cara | Alto: subestaciones, transformadores y líneas con pauta | Medio: trabajo por proyecto, salvo la flota de maquinaria |
| Seguridad | Bloqueo y etiquetado en equipos con energía acumulada | El más fuerte: el bloqueo evita la electrocución | Alta, pero ligada a la obra y no al mantenimiento |
| Papers en la revisión IEEE (42) | 1 | 13 | 0 |
| Rol | Mercado de entrada | Primera expansión y fuente de métodos | Expansión vía maquinaria pesada |

## Cómo nos evalúan

Track Physical World. Criterios y pesos de la hackathon: `Confirmada`.

| Criterio | Peso | Qué lo sostiene hoy | Qué falta |
|---|---|---|---|
| Aspecto técnico | 25% | Nada construido. Hay hardware: Arduino, Raspberry Pi, ESP, sensores y motores | Un sistema que corra en vivo y donde se vea una parte difícil |
| Ejecución | 20% | Nada construido | Un demo de punta a punta que no se caiga |
| Ambición | 20% | El operario aumentado con IA y el ciclo cerrado | Mostrar el ciclo completo, aunque sea a escala chica |
| Impacto | 20% | La evidencia del problema y el contexto minero chileno | Una fuente de operador o de estudio para el costo por hora; hoy es la estimación de un proveedor (38) |
| Originalidad | 15% | Los vacíos de la literatura | Que el vacío se note en el demo, no solo en una lámina |

Lectura del equipo, `Candidata a validar`: ejecución y aspecto técnico suman 45% y se juzgan por lo que funciona en vivo, no por el research. Además, tres de los cuatro pasos del ciclo son software puro. La parte física, la que el jurado del track va a buscar, es verificar con cámara y sensores la ejecución en terreno, y es también el vacío más fuerte de la literatura. Por eso el demo pone esa parte al centro: ver [FLUJO → Demo propuesto](../architecture/FLUJO.md#demo-propuesto).

## Fuentes

- Criterios y pesos de la hackathon, comunicados por el equipo el 2026-11-21. `Confirmada`.
- Handoff de la revisión bibliográfica de Francisco Zúñiga, 2026-11-21: objetivo, alcance y búsquedas. `Confirmada`.
- [Planteamiento del equipo, 2026-11-21](./fuentes/2026-11-21-planteamiento-del-equipo.md): problema, premisa, cliente objetivo, flujo, capas y demo. Transcripción íntegra.
- Números de referencia: ver [REFERENCIAS](../projects/research/REFERENCIAS.md).
