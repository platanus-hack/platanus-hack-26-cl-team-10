# ADR-0013 — Factum se presenta como el copiloto del operario, y no como un supervisor que mira todo el tiempo

> Estado: `proposed` · Fecha: 2026-11-21 · Precisa el pitch del [ADR-0009](./0009-flujo-operacional-verificable-mantenimiento-como-caso-de-uso.md)

## Contexto

El 2026-11-21 Francisco propuso un pitch de venta nuevo ([transcripción](../domain/fuentes/2026-11-21-pitch-del-copiloto.md)). Lo central ya estaba en el [planteamiento del equipo](../domain/fuentes/2026-11-21-planteamiento-del-equipo.md): Factum es el copiloto del operario. Pero la propuesta suma tres promesas que el knowledge no tenía:

- que el operario genere conocimiento mientras ejecuta;
- que los reportes no omitan información;
- que la operación saque APIs, métricas y datos.

Además dice que Factum «es lo mismo que tener un supervisor en todo momento visualizando la operación».

Esa última frase choca con una regla de [LOGICA](../architecture/LOGICA.md#cuándo-el-sistema-propone-cambiar-la-pauta): la vista del supervisor agrupa por pauta y por área antes que por persona. La razón es que muchas desviaciones nacen de la presión de la jefatura (REFERENCIAS 33), y un sistema que se vende como vigilancia la aumenta. El jurado ya hizo esa pregunta en el tour: «¿cómo evitas que el jefe use la cámara para vigilarme?» ([preguntas](../projects/research/tour-platanus.md#las-preguntas-que-nos-van-a-hacer)).

## Decisión

Factum se presenta como **el copiloto del operario**. El valor para la operación se dice así: **cada trabajo queda verificado sin poner un supervisor encima de cada uno.** No se dice que reemplaza a un supervisor ni que mira la operación todo el tiempo.

La frase de referencia del pitch es:

> Factum es el copiloto de tus operarios. Los acompaña mientras ejecutan: comprueba cada paso de la orden de trabajo con sensores y cámara, y les avisa en el momento si se saltan uno. Como está en cada trabajo, todo queda registrado con su evidencia: el reporte no se escribe ni omite nada, el turno siguiente retoma sin depender de quien se fue y la pauta mejora con cada ejecución. La operación sabe que cada trabajo se hizo bien sin poner un supervisor encima de cada uno. Y todo sale por API hacia tus sistemas.

Cada promesa del pitch se dice según lo que hay detrás:

| Promesa | Cómo se dice | Qué la sostiene |
|---|---|---|
| Copiloto que verifica cada paso y avisa | Como algo que funciona | La verificación en tres capas y el aviso, construidos ([ADR-0004](./0004-verificacion-por-capas.md)) |
| El reporte no omite nada | Como algo que funciona, en lo que se verifica | La bitácora de pasos verificados con su evidencia, que solo agrega |
| La pauta mejora con cada ejecución | Como algo que funciona | Propuestas por paso desde la evidencia, validadas por el supervisor y comprobadas con la versión nueva ([ADR-0014](./0014-mejora-continua-por-evidencia-y-metricas-por-pauta.md)) |
| El operario genera conocimiento | Como algo que funciona | El operario deja observaciones en la bitácora, y las de `pauta` y `seguridad` alimentan las propuestas ([ADR-0014](./0014-mejora-continua-por-evidencia-y-metricas-por-pauta.md)) |
| Métricas y datos por API | Como algo que funciona | Cinco GET de métricas por pauta, equipo, paso y día, además del servicio para clientes ([ADR-0012](./0012-login-y-clientes-cada-empresa-ve-lo-suyo.md), [ADR-0014](./0014-mejora-continua-por-evidencia-y-metricas-por-pauta.md)) |

En el knowledge, quien ejecuta es el **operario**. «Operador» es su rol en la API.

## Alternativas consideradas

- **A — «Es como tener un supervisor viendo la operación todo el tiempo»:** es lo que más entiende un gerente, pero le vende vigilancia y contradice la regla de agrupar por pauta. Además deja sin respuesta la pregunta del jurado sobre privacidad.
- **B — Seguir solo con «AI Augmented Operator»:** es el lema actual y no promete nada que no esté construido. Pero no dice qué gana la operación además de la seguridad: el reporte, el relevo y los datos.

## Consecuencias

- El pitch suma el reporte que no omite nada y la API, que ya existen, sin prometer lo que falta.
- El conocimiento del operario y las métricas quedaban como visión. Francisco decidió construirlos el mismo día ([ADR-0014](./0014-mejora-continua-por-evidencia-y-metricas-por-pauta.md)), y la tabla de arriba ya lo dice.
- La respuesta a «¿me van a vigilar?» parte de esta decisión: Factum mira el paso y la pauta, no a la persona.

## Pendientes y no verificado

- La postura de privacidad completa: qué se graba, quién lo ve y cuánto dura. Esta decisión solo fija que no se agrupa por persona. `Brecha`.
- Que «el reporte no omite nada» vale para lo que la pauta verifica. Lo que pasa fuera de un paso no queda registrado. `Candidata a validar`.

## Referencias

- [Transcripción del pitch](../domain/fuentes/2026-11-21-pitch-del-copiloto.md) y [planteamiento del equipo](../domain/fuentes/2026-11-21-planteamiento-del-equipo.md).
- REFERENCIAS 33 (presión de la jefatura), 40 (verificar el control crítico), 3 y 4 (los errores del texto libre de las OT).
- [LOGICA](../architecture/LOGICA.md), [CONTEXTO](../domain/CONTEXTO.md) y [research](../projects/research/research.md#evidencia-frente-al-planteamiento-del-equipo).
