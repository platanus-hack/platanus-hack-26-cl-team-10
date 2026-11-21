# ADR-0009 — El producto vuelve verificable cualquier flujo operacional; el mantenimiento es el caso de uso

> Estado: `proposed` · Fecha: 2026-11-21 · Extiende al [ADR-0005](./0005-producto-general-mineria-como-caso-del-demo.md)

## Contexto

El [ADR-0005](./0005-producto-general-mineria-como-caso-del-demo.md) sacó al producto de un solo rubro, pero lo dejó dentro del mantenimiento: «ir más allá, a cualquier procedimiento operativo, no entra en esta decisión». Desde entonces el knowledge, la descripción del proyecto y la API lo nombran «mantenimiento verificado».

Lo construido no verifica mantenimiento. Verifica un paso con la evidencia que lo cierra (un sensor, la cámara o la confirmación de una persona), en el orden de la pauta, con reglas de seguridad encima y una bitácora que solo agrega filas. `app/contratos.py` no nombra el mantenimiento: lo único propio de ese caso son las pautas de `datos/` y las reglas de seguridad por industria de [LOGICA](../architecture/LOGICA.md#qué-puede-interrumpir-al-operario).

El argumento de impacto tampoco es de mantenimiento. La cifra que lo sostiene es la ejecución inefectiva del control, 19 de 26 incidentes fatales de los miembros de ICMM en 2025 (REFERENCIAS 40), y esa cifra no separa el mantenimiento del resto de la operación. Cuántas muertes ocurren en tareas de mantenimiento sigue siendo `Brecha` ([CONTEXTO](../domain/CONTEXTO.md#el-problema)).

Francisco lo planteó así el 2026-11-21: esto no es solo mantenimiento verificable, es volver verificable cualquier flujo operacional para reducir el impacto; el mantenimiento de maquinaria es el caso de uso, y es un caso de alto impacto.

## Decisión

Factum vuelve verificable **cualquier flujo operacional**: un procedimiento con pasos en el que cada paso declara qué evidencia lo cierra. El objetivo es reducir el impacto de una ejecución mal hecha.

El **mantenimiento de maquinaria** es el caso de uso con el que se construye y se muestra, elegido porque su impacto es alto: ahí una mala ejecución cuesta vidas y horas de detención. La minería sigue siendo el caso del demo (ADR-0005).

## Alternativas consideradas

- **A — Seguir en «mantenimiento verificado»:** todo el research lo respalda, pero describe el producto más chico de lo que el código ya hace y apoya la ambición en un solo tipo de tarea.
- **B — Mostrar en el demo un flujo que no sea mantenimiento:** prueba la generalidad y diluye la ejecución, que pesa lo mismo que la ambición (20%). Es la misma razón por la que el demo muestra una sola industria.

## Consecuencias

- Los textos que presentan el producto hablan de flujo operacional, con el mantenimiento como caso de uso: [CONTEXTO](../domain/CONTEXTO.md), [GLOSARIO](../domain/GLOSARIO.md), [INDEX](../INDEX.md), `project-description.md` y el título de la API.
- El vocabulario del código no cambia. `pauta`, `OT`, `paso` y `evento` siguen; la OT se lee como la instancia ejecutable de un flujo. Renombrar es trabajo sin efecto en el demo.
- La evidencia sigue siendo de mantenimiento. El research, las reglas de seguridad por industria y los escenarios cubren ese caso, y la generalización queda `Candidata a validar` hasta que haya evidencia de otro flujo.
- El demo no cambia: un flujo, una industria.

## Pendientes y no verificado

- No se buscó literatura sobre verificar procedimientos operativos fuera del mantenimiento, como arranques y paradas de planta, inspecciones o listas de chequeo de operación. `Brecha`.
- Qué segundo flujo, que no sea mantenimiento, mostraría la generalidad sin tocar el demo. `Brecha`.
- Falta que el equipo lo acepte.

## Referencias

- [ADR-0005](./0005-producto-general-mineria-como-caso-del-demo.md), al que extiende.
- [CONTEXTO](../domain/CONTEXTO.md) y [LOGICA](../architecture/LOGICA.md).
- REFERENCIAS 40.
