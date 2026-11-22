# ADR-0018 — La pauta tiene un protocolo dueño; cada protocolo de cada empresa itera por separado

> Estado: `accepted` · Fecha: 2026-11-22 · Aceptado el 2026-11-22: Francisco lo pidió («implementalo así y testea») y entró a `main` con el PR #74

## Contexto

Hasta acá las mejoras se proponían y se revisaban por empresa, pero la versión de una pauta era una sola para todas: la tabla `pautas (id, version)` es global y `catalogo.generar_ot` toma la última aprobada. Si una empresa aprobaba la v2 del cambio de polín, todas las que la tenían habilitada pasaban a ejecutarla, y la propuesta de otra empresa sobre esa pauta quedaba «superada» sin que nadie la hubiera pedido.

Pancho lo planteó el 2026-11-22: cada cliente es distinto, y dentro de una empresa también; cada iteración mejora a cada cliente en paralelo, y por eso el informe pasa por Factum. La unidad no es la empresa sino el protocolo: el cambio de polín de la planta A y el de la planta B se iteran por separado, y es por protocolo donde las métricas le sirven al dueño del proceso.

## Decisión

**El protocolo es de una empresa, o de la biblioteca de Factum.** `protocolos.cliente_id` dice de qué empresa es; sin empresa, es de la biblioteca (los de `datos/`). Al entrar a una operación, el equipo copia el protocolo de la biblioteca para la empresa, `POST /interno/clientes/{cliente_id}/protocolos` con `{"base", "actor", "sufijo"}` (`catalogo.instanciar`). La copia dice «adaptado de <base>» en su origen y trae los controles críticos de la base, aprobados por quien la copia.

**Cada pauta tiene un protocolo dueño, uno solo** (`pauta_duena`, `catalogo.fijar_duena` y `protocolo_dueno`): el de la tarea que ejecuta. Sus versiones, sus OT, sus propuestas, su validación y sus métricas son de ese protocolo. La copia de un protocolo trae una copia de cada pauta que la base tiene como propia (`propias` en `datos/protocolos.json`), en su versión 1, aprobada y habilitada solo para esa empresa.

**Dos relaciones, con significados distintos:**

| Relación | Cuántas | Qué significa | Para qué sirve |
|---|---|---|---|
| Dueño (`pauta_duena`) | Una | El protocolo de la empresa cuya tarea ejecuta la pauta | Iterar: versiones, OT, propuestas y métricas |
| Aplica a (`pauta_protocolo`, ADR-0016) | Varias | Protocolos cuyo peligro existe en la tarea | La conformidad: qué controles se le exigen |

No es la alternativa C que descartó el ADR-0016. Esa separaba «aplica a» de «se derivó de», dos lecturas de lo mismo que cabían en una frase del protocolo. El dueño no es trazabilidad: dice quién itera la pauta, y sin él no hay forma de que dos protocolos que parten de la misma base avancen por separado. La derivación sigue contándose en el texto, como decidió el ADR-0016.

**Los ids llevan la empresa y, si hace falta, el área**, separados por `--`: `prot-correa-01--oculta--planta-a`, y sus pautas `pauta-polin-ct-01--oculta--planta-a`. Ni el cliente ni el sufijo pueden llevar `--` ni `:`, porque `:` separa protocolo y control en `cumple`.

**Los protocolos que solo aplican se copian una vez por empresa y se comparten dentro de ella.** El de aislamiento de Oculta (`prot-aislamiento-01--oculta`) les aplica a las dos plantas; el de otra empresa es otro. Al copiar una pauta, su `cumple` se reescribe a las copias, así que la conformidad se calcula contra los controles de esa empresa.

**El informe pasa por Factum.** El supervisor de cada empresa recibe el aviso y revisa las propuestas de sus protocolos; el equipo ve las de todas en `/interno/mejoras`, arma cada versión nueva y decide si una mejora que funcionó en un protocolo se ofrece a otro, que la adopta en su propia copia. Las métricas, por protocolo dueño: `GET /cliente/metricas/protocolos` (`metricas.por_protocolo`).

**Lo que hace converger el ciclo.** Iterar sin fin no sirve si cada vuelta puede sacar una versión por ruido o insistir con una causa que la pauta no arregla. Dos reglas, medidas en la [simulación de la mejora continua](../projects/mejora-continua/simulacion.md), sección «Convergencia»:

- **Escalar en vez de versionar.** Si un paso vuelve a ser recurrente en la versión nueva después de que se aplicó un cambio sobre él, y ese cambio no lo bajó (la validación no dice «mejoro»), la propuesta trae `escalar` y Factum no escribe otra versión: lo lleva a la supervisión (presión de tiempo, equipo). Si el cambio lo bajó y queda un resto, otra vuelta sí tiene sentido (`mejora._escalar`).
- **El α repartido entre las miradas.** El aviso al supervisor, la versión que escribe Factum y la escalada se deciden mirando una y otra vez los mismos datos. La k-ésima OT de una versión gasta `ALFA_VIDA·6/(π²k²)` (`mejora.alfa_en_vivo`); como esa serie suma `ALFA_VIDA` (0,05), la probabilidad de un aviso falso en toda la vida de una versión no pasa de 5 %, por muchas OT que se ejecuten. Con un α fijo, mirar sin fin termina dando un falso positivo seguro.

## Alternativas consideradas

- **A — Una copia por empresa, no por protocolo:** más simple, pero dos plantas de la misma empresa compartirían versiones, y Pancho pidió que dentro de una empresa también se itere por separado.
- **B — `cliente_id` en las versiones de una misma pauta:** sin ids nuevos, pero toca la tabla de pautas, todas las rutas y la semilla, y mezcla bajo un mismo id historias de empresas distintas.
- **C — Pautas globales y solo las propuestas por empresa (lo que había):** la versión de una empresa le cambiaba la pauta a las demás.

## Consecuencias

- Tres protocolos que parten de la misma base avanzan cada uno a su ritmo: lo prueba `tests/test_protocolo_por_empresa.py` (la v2 de la planta A no cambia la versión que ejecutan la planta B ni otra empresa, ni supera sus propuestas).
- Cada propuesta trae `protocolo_dueno` y `escalar`, y las métricas se pueden pedir por protocolo.
- La conformidad, la aprobación que no deja sacar un control, la recurrencia, el aviso en vivo y la validación con Fisher funcionan igual sobre cada copia, porque cada copia es una pauta más.
- Cargar una empresa nueva es copiar sus protocolos desde la biblioteca, no escribir pautas a mano.

## Pendientes y no verificado

- **Versionar los protocolos.** Sin versiones, un hallazgo no se reproduce contra el texto del protocolo de ese momento (ADR-0016). `Brecha`.
- **La semilla y el demo siguen usando las pautas de la biblioteca directamente.** La VM, «Nueva demo» y el front piden `pauta-polin-estacion`, no una copia por empresa. Pasarlos a copias cambia ids que usan varias pantallas. `Brecha`.
- **El front no tiene una vista por protocolo.** La pantalla de mejoras y las métricas de `web/` no agrupan por `protocolo_dueno` todavía. `Brecha`.
- **Un salto, dos señales.** Cuando el paso saltado es un control crítico, el mismo incidente deja seguridad en ese paso y orden en el que se adelantó, y el aviso tarda más (6 OT en `tests/test_recorrido_interno.py`). Contarlas como un incidente no se decidió. `Candidata a validar`.
- Ofrecer a otro protocolo una mejora que funcionó en uno no tiene ruta: hoy es una decisión del equipo, a mano.

### Nota del 2026-11-22: la versión siguiente la arma el código

Desde el PR #74, «escribe cada versión nueva» es `POST /interno/pautas/{id}/version-siguiente` (`app/sugerencias.py`): junta los cambios de las propuestas aceptadas de la última versión aprobada, la guarda sin aprobar con los mismos protocolos que aplican y el mismo protocolo dueño, y una persona del equipo la aprueba. Una propuesta con `escalar` no trae cambio (`aplicable` false), así que la regla que hace converger el ciclo también rige ahí: lo escalado no entra a la versión siguiente.

Desde el PR #78 el supervisor también la dispara: «Aplicar los N cambios» en el aviso (`POST /cliente/pautas/{id}/mejoras/aplicar`) acepta todas las propuestas avisadas de la pauta y llama a la misma función. La versión queda sin aprobar y la aprobación sigue siendo del equipo, con el rechazo si pierde un control crítico.

## Referencias

- [ADR-0011](./0011-protocolos-y-pautas-por-servicio-interno-ot-por-servicio-al-cliente.md), [ADR-0014](./0014-mejora-continua-por-evidencia-y-metricas-por-pauta.md) y [ADR-0016](./0016-una-pauta-sale-del-protocolo-que-aplica-a-su-tarea.md).
- [Simulación de la mejora continua](../projects/mejora-continua/simulacion.md), sección «Convergencia».
- Código: `app/catalogo.py` (`instanciar`, `fijar_duena`, `protocolo_dueno`), `app/mejora.py` (`_escalar`, `alfa_en_vivo`), `app/metricas.py` (`por_protocolo`), `app/simulacion.py` (`iterar_en_paralelo`).
- Tests: `tests/test_protocolo_por_empresa.py`, `tests/test_recorrido_interno.py`.
