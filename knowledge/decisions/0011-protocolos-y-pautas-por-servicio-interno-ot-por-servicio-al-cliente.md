# ADR-0011 — Los protocolos y las pautas se cargan por un servicio interno; el cliente pide OT

> Estado: `proposed` · Fecha: 2026-11-21

## Contexto

El [ADR-0006](./0006-la-ot-nace-del-protocolo.md) dice que la OT nace del protocolo del cliente, pero en el código el protocolo no existía: `app/protocolos.py` devolvía una pauta escrita a mano y la pauta no decía de qué documento salió. Tampoco había una forma de pedir una OT sin conocer el número de versión de la pauta ni inventar el id de la OT.

Francisco planteó el 2026-11-21 cómo se va a prestar el servicio: Factum carga el protocolo y arma las pautas una sola vez, al poner en marcha una estación, y después el cliente solo pide órdenes de trabajo de esas pautas.

## Decisión

Separamos dos servicios sobre la misma API.

**El servicio interno (`/interno/...`) es del equipo de Factum.** Ahí el protocolo es un recurso con CRUD: su nombre, la industria, de dónde salió y su texto. Las pautas se crean atribuidas a uno o más protocolos, y la relación es de muchos a muchos: un protocolo da varias pautas (una por tarea) y una pauta puede salir de más de un protocolo (el de la tarea y el transversal de aislamiento de energías, por ejemplo). Cuando `CLAVE_EQUIPO` está definida, todo este servicio pide la cabecera `X-Clave-Equipo`.

**El servicio del cliente (`/cliente/...`) solo genera OT.** El cliente ve las pautas que tienen una versión aprobada y al menos un protocolo, y pide una OT nombrando la pauta. El servicio elige la última versión aprobada, le pone el id a la OT y devuelve de qué protocolos sale.

Se mantiene lo que ya regía: una pauta nueva nace sin aprobar y la aprueba una persona ([ADR-0003](./0003-patrones-de-arquitectura-para-el-mvp.md)), y la OT guarda la versión de la pauta que ejecuta.

Los casos que el equipo ya tiene quedan cargados como semilla en `datos/protocolos.json`, con un documento por protocolo en `datos/protocolos/`.

Las pautas nuevas separan tres pasos que antes iban juntos o faltaban: aislar la energía, bloquear y comprobar energía cero, en ese orden (REFERENCIAS 56). El candado va en el punto de bloqueo, no en el mando con que se opera el equipo. Así están escritas la del polín (`pauta-polin-ct-01`) y la del brazo (`pauta-brazo-01`).

## Alternativas consideradas

- **A — Guardar el protocolo como un campo de la pauta:** es más simple, pero obliga a una pauta por protocolo y repite el mismo documento en cada pauta que sale de él. El protocolo transversal de aislamiento quedaría copiado en cinco pautas.
- **B — Que el cliente cargue sus protocolos y arme sus pautas:** es el producto de autoservicio. Hoy armar una pauta comprobable exige conocer los sensores de la estación y las reglas de capa 1, y eso lo sabe el equipo. Queda para después.
- **C — Poner todo detrás de la clave del equipo:** deja sin servicio al cliente, que es justamente quien tiene que pedir las OT.

## Consecuencias

- Una OT se puede rastrear hasta el documento del cliente: OT → versión de la pauta → protocolos.
- Sumar un proceso nuevo es cargar un protocolo y sus pautas, sin tocar el código, mientras sus señales ya existan en la estación.
- El borrado tiene reglas: un protocolo con pautas no se borra, y una pauta con OT no queda sin protocolo.
- La puesta en marcha de un cliente es trabajo del equipo. Eso limita cuántos clientes se pueden atender a la vez.

## Pendientes y no verificado

- La extracción de pasos la hace el equipo con la skill `reconocer-proceso` y su comprobador ([ADR-0015](./0015-reconocer-procesos-con-skills-de-agente-y-un-criterio.md)), no una ruta de la API. El stub `protocolos.extraer_pasos` se borró el 2026-11-21: el cliente no convierte protocolos, eso es parte del servicio.
- El servicio del cliente no identifica al cliente: cualquiera que llegue a la API puede pedir una OT, y `solicitante` es un texto libre. Falta una credencial por cliente. `Brecha`.
- Las rutas públicas anteriores (`POST /pautas`, `POST /ot`) siguen abiertas y permiten crear pautas sin protocolo. No se cerraron para no romper la pantalla del demo ni el banco de casos. `Brecha`.
- Los seis protocolos de la semilla los redactó el equipo, con la estructura de los manuales de REFERENCIAS 56 a 66; ninguno es el documento real de un cliente. El del camión rígido resume una guía pública de un tercero y guarda su enlace, sin copiar su texto. `Candidata a validar` con un protocolo real.
- La comprobación de energía cero la cierra hoy la palabra del operario: ninguna estación mide el intento de partida. Es un control crítico cerrado sin sensor. `Brecha`.
- `pauta-correa-ct-01`, la del demo anterior, sigue juntando aislar y bloquear en un paso y no trae la comprobación. No se cambió porque la usan las pruebas de minería, el recorrido del demo y la pantalla. `Brecha`.
- Las señales de la pauta del polín (`correa`, `energia`, `bloqueo`, `guarda`) no las mide ninguna estación del equipo. `Brecha`.
- La estrategia de controles de REFERENCIAS 56 abre con una nota de confidencialidad, aunque está publicada en el sitio de la compañía. Se enlaza y se resume con palabras propias; no se copia su texto. `Candidata a validar` con el equipo si alcanza.
- La pauta del camión usa señales (`inclinacion`, `marcha`, `freno_estacionamiento`, `enfriamiento`, `motor`) que ninguna estación del equipo mide hoy. `Brecha`.

## Referencias

- Código: `app/catalogo.py` (sección Protocolos), `app/api.py` (rutas `/interno` y `/cliente`), `app/protocolos.py` (`cargar_semilla`), `tests/test_protocolos.py`.
- [ADR-0006](./0006-la-ot-nace-del-protocolo.md) y [ADR-0003](./0003-patrones-de-arquitectura-para-el-mvp.md).
- Guía tomada como ejemplo de protocolo de un tercero: [Rigid Haul Truck, Learner Guide](https://nationalcourses.edu.au/wp-content/uploads/2025/02/2.14.5-Rigid-Haul-Truck-LG.docx.pdf).
