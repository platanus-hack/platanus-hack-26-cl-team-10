# ADR-0006 — La OT nace del protocolo, no de la falla

> Estado: `proposed` · Fecha: 2026-11-21

## Contexto

El [FLUJO](../architecture/FLUJO.md) heredó del handoff original del research un paso 3 en el que la OT se abre cuando el equipo se detiene o un sensor sale de rango. Así el producto queda en el mantenimiento correctivo, y la OT depende de detectar una falla.

En el [planteamiento del equipo](../domain/fuentes/2026-11-21-planteamiento-del-equipo.md), la OT sale del protocolo que el cliente ya tiene: «entre un protocolo que ya existe, a través de AI esto genera una OT». No hace falta una falla para que exista.

## Decisión

La OT es la instancia ejecutable de la pauta vigente: la tarea, el equipo, los pasos en orden, la evidencia que cierra cada uno y la versión de la pauta. El sistema la genera desde la pauta cuando hay que ejecutar la tarea, y una persona la confirma.

El disparo puede ser cualquiera: el calendario de una mantención preventiva, el pedido de alguien o una falla del equipo. La falla es un caso más, no la definición.

En el demo se mantiene la detención de la correa como disparo, porque es la escena que pone en pantalla el costo de cada hora detenida.

## Alternativas consideradas

- **A — La OT nace de la falla, como estaba:** da un demo dramático, pero deja fuera las mantenciones preventivas y las tareas programadas, que son donde más se repite una misma pauta.
- **B — La OT nace de una predicción:** depende de historia limpia por equipo, que no existe el primer día. Queda como visión; ver el [registro](./decisions.md).

## Consecuencias

- El producto funciona desde el primer día sin detectar nada: basta con el procedimiento del cliente.
- La detección de fallas deja de ser un requisito del flujo y pasa a ser un disparo opcional.
- La OT guarda la versión de la pauta que ejecutó, como ya pedía el [ADR-0003](./0003-patrones-de-arquitectura-para-el-mvp.md).

## Pendientes y no verificado

- Si una OT disparada por falla necesita pasos de diagnóstico que la pauta no trae. `Brecha`.
- Quién confirma la OT antes de ejecutarla: el supervisor o el propio operario. `Brecha`.

## Referencias

- [Planteamiento del equipo, 2026-11-21](../domain/fuentes/2026-11-21-planteamiento-del-equipo.md).
- [FLUJO → 3. Generar la OT](../architecture/FLUJO.md#3-generar-la-ot).
- REFERENCIAS 25.
