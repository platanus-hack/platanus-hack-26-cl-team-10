# ADR-0005 — El producto es general y la minería es el caso del demo

> Estado: `proposed` · Fecha: 2026-11-21 · Reemplaza al [ADR-0001](./0001-mineria-como-mercado-de-entrada.md)

## Contexto

El [ADR-0001](./0001-mineria-como-mercado-de-entrada.md) dejó la minería como mercado de entrada, con el demo y el pitch mineros, y la eléctrica y la construcción en una lámina de expansión. Leído así, el producto parece minero.

El [planteamiento del equipo](../domain/fuentes/2026-11-21-planteamiento-del-equipo.md) no describe un producto minero: describe un cliente que ya tiene protocolos estandarizados y no puede verificarlos. La minería aparece como ejemplo, con la detención de una correa transportadora. Lo que une a los posibles clientes es el tipo de operación, no el rubro: equipos críticos y procedimientos repetibles donde un error es caro o peligroso ([CONTEXTO → Industrias](../domain/CONTEXTO.md#industrias)).

## Decisión

El producto es general: sirve a cualquier operación con equipos críticos que ya tiene procedimientos estandarizados y no puede comprobar que se cumplen. Se presenta así en el pitch.

La minería es el **caso del demo**. La correa transportadora a escala es el ejemplo concreto que se muestra, y las cifras chilenas (Sernageomin, costo por hora de detención) sostienen el impacto. La eléctrica y la construcción aparecen como otros casos del mismo flujo, no como una expansión futura.

## Alternativas consideradas

- **A — Mantener el ADR-0001:** el pitch queda enfocado, pero el producto parece de un solo rubro y la ambición se apoya en una lámina de expansión.
- **B — Mostrar tres industrias en el demo:** sube la ambición en el papel y diluye la ejecución, que pesa lo mismo (20%). Es la razón del ADR-0001 y sigue vigente: el demo muestra un solo caso.

## Consecuencias

- La ambición crece sin tocar el demo: el mismo flujo, con otro procedimiento, sirve en una subestación o en una flota de maquinaria.
- Se conserva la originalidad del caso minero: la revisión IEEE tiene un solo paper minero de 42.
- El research y el nombre del knowledge siguen centrados en el mantenimiento. Ir más allá, a cualquier procedimiento operativo, no entra en esta decisión.

## Pendientes y no verificado

- Si el equipo tiene acceso a OT o procedimientos reales de alguna faena. Sin ellos, el corpus sale de MaintIE (REFERENCIAS 6). `Brecha`.
- El costo por hora de detención de un equipo minero crítico, con una fuente de operador o de estudio. `Brecha`.

## Referencias

- [ADR-0001](./0001-mineria-como-mercado-de-entrada.md), al que reemplaza.
- [CONTEXTO → Industrias](../domain/CONTEXTO.md#industrias).
- REFERENCIAS 6, 24, 36, 38 y 39.
