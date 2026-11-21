# Contexto

> Una página: qué problema resolvemos, para quién, hasta dónde llega y cómo nos van a evaluar.

## El problema

En una operación donde una falla o un error de mantenimiento salen caros, como una faena minera, tres cosas fallan a la vez:

1. **La bitácora no sirve como dato.** Las OT se escriben en texto libre, con criterio de cada técnico. El tiempo medio entre fallas de un mismo equipo puede ir de 97 a 226 días según cómo un analista agrupe las OT (REFERENCIAS 4). `Confirmada`.
2. **La pauta no se cumple y nadie lo ve.** Muchas desviaciones nacen de la presión de la jefatura y de pautas mal hechas, no del operario (REFERENCIAS 33). Las guías actuales muestran el paso siguiente, pero no comprueban que el anterior se hizo (REFERENCIAS 18). `Confirmada`.
3. **El error es caro.** La mantención no planificada puede bajar la disponibilidad de la maquinaria minera hasta 37% (REFERENCIAS 24). La minería chilena tuvo 20 muertes en 2025, frente a 11 en 2024 (REFERENCIAS 36, prensa que cita a Sernageomin). `Confirmada`. Cuántas de esas muertes ocurrieron en tareas de mantenimiento: `Brecha`.

## La visión

Un operario que ejecuta bien, con menos accidentes y con una bitácora confiable, gracias a pautas suficientes y verificables. La bitácora no se escribe: es la lista de pasos verificados con su evidencia. `Confirmada` por el equipo.

El objetivo de largo plazo es un ciclo cerrado con datos reales:

1. Cruzar telemetría IoT con el texto de las OT y bitácoras.
2. Predecir fallas y abrir OT automáticas.
3. Ejecutar con pautas estandarizadas que quedan auditadas y verificadas, incluso con imágenes.
4. Usar lo auditado para actualizar las pautas matriz.

La entrada a una operación es *plug & play*: sensores pegados al equipo, la cámara del operario y el archivo exportado de OT, sin tocar el PLC ni pedirle integración a TI. El orden es identificar el proceso, estandarizar, mejorar y recién después predecir. La mayoría de las soluciones de mantenimiento predictivo parten por predecir y chocan con datos malos; nosotros llegamos a predecir como consecuencia. `Candidata a validar`.

Dos cuidados con el *plug & play*. Una faena no deja conectar nada a su red de control sin meses de aprobaciones de ciberseguridad, así que lo creíble es solo lo no invasivo: «funciona el primer día sin pedirle nada a TI». Y la predicción no se promete desde el día uno: detectar anomalías sí, la vida útil remanente necesita semanas o meses de datos por equipo. `Candidata a validar`.

Un ángulo de impacto adicional: capturar el conocimiento de los técnicos senior antes de que se retiren, grabando cómo ejecutan la tarea. `Candidata a validar`.

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
| Aspecto técnico | 25% | Nada construido | Un sistema que corra en vivo y donde se vea una parte difícil |
| Ejecución | 20% | Nada construido | Un demo de punta a punta que no se caiga |
| Ambición | 20% | La visión del ciclo cerrado | Mostrar el ciclo completo, aunque sea a escala chica |
| Impacto | 20% | La evidencia del problema y el contexto minero chileno | El costo por hora de detención de un equipo crítico, con fuente |
| Originalidad | 15% | Los vacíos de la literatura | Que el vacío se note en el demo, no solo en una lámina |

Lectura del equipo, `Candidata a validar`: ejecución y aspecto técnico suman 45% y se juzgan por lo que funciona en vivo, no por el research. Además, tres de los cuatro pasos del ciclo son software puro. La parte física, la que el jurado del track va a buscar, es verificar con cámara la ejecución en terreno, y es también el vacío más fuerte de la literatura. Por eso el demo pone esa parte al centro: ver [FLUJO → Demo propuesto](../architecture/FLUJO.md#demo-propuesto).

## Fuentes

- Criterios y pesos de la hackathon, comunicados por el equipo el 2026-11-21. `Confirmada`.
- Handoff de la revisión bibliográfica de Francisco Zúñiga, 2026-11-21: objetivo, alcance y búsquedas. `Confirmada`.
- Números de referencia: ver [REFERENCIAS](../projects/research/REFERENCIAS.md).
