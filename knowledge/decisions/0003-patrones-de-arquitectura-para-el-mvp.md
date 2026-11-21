# ADR-0003 — Patrones de arquitectura para el MVP

> Estado: `proposed` · Fecha: 2026-11-21

## Contexto

Al diseñar el flujo se revisó una lista de patrones conocidos: event sourcing, CQRS, sagas, ejecución durable, contextos de DDD, sistemas de varios agentes, búsqueda por palabra clave frente a vectorial e inferencia en el borde. Que un patrón sea conocido no lo hace útil acá. El producto todavía no tiene piloto, y la hackathon premia lo que funciona en vivo.

## Decisión

Usamos tres patrones desde ahora, porque son la tesis del producto o los pide la seguridad:

1. **Registro que solo agrega filas.** La bitácora son los pasos verificados con su evidencia; nada se edita ni se borra.
2. **Aprobación humana antes de un efecto.** Abrir una OT o cambiar una pauta lo confirma una persona.
3. **Pauta versionada.** Cada OT guarda qué versión de la pauta ejecutó.

El resto espera:

| Patrón | Veredicto | Por qué |
|---|---|---|
| Event sourcing completo y CQRS | No | Proyecciones, snapshots y evolución de esquema resuelven problemas que todavía no existen |
| Saga y ejecución durable | No | Una OT avanza al ritmo de una persona y vive en una sola base; una columna de estado alcanza. Se revisa si algún día se escribe de vuelta en SAP PM |
| Contextos de DDD como servicios | No | Sirven como vocabulario, para no mezclar la falla del sensor con la falla de la OT. Una aplicación y una base |
| Varios agentes | No | El flujo es fijo y conocido. Un modelo por tarea, llamado desde código |
| Palabra clave antes que búsqueda vectorial | Probar | Se afirma en general; con jerga minera en español nadie lo ha medido |
| Inferencia en el borde y modelos apilados | Después | Importa en una faena sin conectividad, no en el demo |
| Datos sintéticos | Después | No resuelven nada del primer piloto |

## Alternativas consideradas

- **A — Arquitectura completa desde el inicio:** event sourcing, saga orquestada y contextos separados. Prepara para escala, pero consume el tiempo que necesita el demo.

## Consecuencias

- El MVP es una aplicación, una base y llamadas a modelos desde código.
- Migrar después a event sourcing completo es directo, porque el registro ya solo agrega filas.

## Pendientes y no verificado

- Si la faena exige operar sin conectividad. Si la exige, la inferencia en el borde sube de prioridad. `Brecha`.

## Referencias

- [FLUJO](../architecture/FLUJO.md), apartado «Construcción» de cada paso.
