# ADR-0014 — La pauta mejora con la evidencia de cada ejecución y lo que observa el operario; las métricas se leen de la bitácora, nunca por persona

> Estado: `proposed` · Fecha: 2026-11-21 · Construye lo que el [ADR-0013](./0013-el-pitch-copiloto-del-operario-sin-supervisor-encima.md) dejaba como visión

## Contexto

El pitch del copiloto ([ADR-0013](./0013-el-pitch-copiloto-del-operario-sin-supervisor-encima.md)) promete tres cosas que no existían:

- que el operario genere conocimiento mientras ejecuta;
- que la pauta mejore con cada ejecución;
- que la empresa reciba métricas.

Lo que había era `GET /supervisor/propuestas`: contaba los pasos en conflicto en dos o más OT, sin login, sin empresa y sin forma de validar ni de saber si el cambio sirvió. En la semilla no aparecía ninguna propuesta, porque ningún paso quedaba en conflicto.

El 2026-11-21 Francisco decidió construir las dos piezas como servicios: la mejora continua de las pautas, a partir de la validación de cada ejecución, y los GET de métricas que la empresa cliente necesita para ver el valor del producto.

## Decisión

**El operario deja observaciones.** Es un tipo de evento nuevo en el contrato, `observacion` (`app/contratos.py`), con una categoría: `pauta`, `seguridad`, `equipo` u `otra`. No cierra ni abre ningún paso. Queda en la bitácora con quién la dijo y cuándo, como todo lo demás. La deja el operario que tiene la OT o el supervisor de su empresa (`POST /cliente/ots/{ot_id}/observaciones`).

**Una propuesta de mejora nace de señales repetidas en el mismo paso.** Las señales son cinco:

- una alerta de orden;
- una alerta de control perdido;
- un conflicto entre la palabra y la evidencia;
- un paso que confirmó una persona porque la evidencia no lo vio;
- una observación de `pauta` o de `seguridad`.

Cuando el mismo paso de la misma versión tiene señales en dos o más OT distintas, nace la propuesta. Una sola OT no basta: una desviación suelta no es una propuesta ([LOGICA](../architecture/LOGICA.md#cuándo-el-sistema-propone-cambiar-la-pauta)). La propuesta dice el protocolo de origen, el paso, cuántas OT y cuántos operarios distintos dieron señales, lo que observaron y una sugerencia según la señal que domina.

**El ciclo se cierra con validación de personas y con evidencia** (`app/mejora.py`):

1. El supervisor de la empresa acepta o descarta cada propuesta en `POST /cliente/mejoras/{id}/revision`. Descartar pide una nota, y se puede cambiar de opinión: queda la última revisión.
2. El equipo de Factum ve las aceptadas de todas las empresas en `GET /interno/mejoras`, escribe la versión siguiente de la pauta y una persona la aprueba (ADR-0003).
3. La propuesta pasa a `aplicada`. Con las OT de la versión nueva que ya pasaron por ese paso, `validacion` dice si dejó de desviarse (`mejoro`), si se sigue desviando (`se_repite`) o si todavía no hay ejecuciones (`sin_datos`).

**Las métricas se leen de la bitácora al pedirlas** (`app/metricas.py`), como la calificación: no hay un número guardado que se desfase. Son cinco GET para el supervisor, con `desde`, `hasta`, `orden` y `limite`:

| Ruta | Qué entrega |
|---|---|
| `GET /cliente/metricas` | OT por estado, cuántas completas sin desviaciones, con qué evidencia se cerraron los pasos, las desviaciones por clase y cuánto tardan en resolverse, el tiempo de ejecución, los relevos, las observaciones y las propuestas |
| `GET /cliente/metricas/pautas` | Lo mismo por pauta, con el paso que más se desvía |
| `GET /cliente/metricas/pautas/{pauta_id}/pasos` | Cada paso de una versión: evidencia, desviaciones y observaciones |
| `GET /cliente/metricas/equipos` | Lo mismo por equipo, más lo que se observó de la máquina |
| `GET /cliente/metricas/serie` | Por día o por semana, sin huecos, para graficar |

**Qué cuenta como desviación:**

- una alerta de seguridad, de orden o de control perdido;
- un paso en conflicto;
- un paso que confirmó una persona.

Las alertas de señal y de sensor pegado hablan del sensor, no de cómo se ejecutó, y van aparte. **Cumplimiento** es la fracción de las OT completas que terminaron sin ninguna desviación.

**Nada se agrupa por persona.** Las métricas van por pauta, equipo, paso y día. De las propuestas solo sale cuántos operarios distintos dieron señales, nunca quiénes. Así lo piden LOGICA y el ADR-0013, y una prueba comprueba que ninguna de estas respuestas nombra a un operario.

## Alternativas consideradas

- **A — Guardar las métricas en una tabla que se actualiza con cada evento:** responde más rápido, pero es un segundo registro que se puede desfasar de la bitácora. Con decenas de OT por empresa, calcular al pedir tarda milisegundos. Se revisa cuando una empresa tenga miles.
- **B — Que la observación sea una declaración con otra marca:** evita tocar el contrato, pero mezcla lo que cierra un paso con lo que no lo cierra, y cada lector tendría que saber distinguirlas.
- **C — Que la propuesta cambie la pauta sola:** contradice el ADR-0003. El sistema propone, una persona aprueba.
- **D — Métricas por operario:** es lo que más se pide en una planta, y es justamente lo que el ADR-0013 descarta.

## Consecuencias

- La empresa cliente ve el valor del producto con sus propios datos: cumplimiento, desviaciones y tiempos, más un ciclo de mejora que se puede mostrar en el demo con la semilla. La propuesta de la semilla es `pauta-polin-demo:v1:p3`: una alerta de orden y una observación sobre «Acercarte a la correa».
- La pauta deja de ser un documento fijo: cada versión se mide contra la anterior en el paso que se cambió.
- El contrato cambió: hay un tipo de evento nuevo. La interfaz de `web/` lo muestra sin título hasta que agregue `observacion` a sus tipos.

## Pendientes y no verificado

- La comprobación compara la fracción de OT con señal antes y después, sin un mínimo de ejecuciones. Con dos o tres OT por versión, «mejoró» puede ser azar. `Candidata a validar`.
- La versión nueva la escribe a mano el equipo. Que un modelo redacte el cambio a partir de la propuesta es el siguiente paso. `Brecha`.
- `GET /supervisor/propuestas`, la ruta anterior, sigue abierta y sin empresa. Queda hasta que la pantalla del demo use `/cliente/mejoras`. `Brecha`.
- El tiempo de ejecución se mide del primer evento después de asignar la OT al último paso verificado. Una OT que espera entre pasos cuenta esa espera. `Candidata a validar`.
- Las métricas no paginan más allá de `limite`, y `GET /cliente/metricas` lee todas las OT de la empresa en cada llamada. `Brecha` cuando una empresa tenga miles.
- La semilla trae las observaciones solo en una base nueva: en la VM, las OT de la semilla ya existían y no se vuelven a ejecutar. `Brecha` del despliegue.

## Referencias

- Código: `app/mejora.py`, `app/metricas.py`, `Servicios.observar` en `app/servicios.py`, las rutas de `app/api.py` y `tests/test_mejora_y_metricas.py`.
- [ADR-0003](./0003-patrones-de-arquitectura-para-el-mvp.md), [ADR-0012](./0012-login-y-clientes-cada-empresa-ve-lo-suyo.md) y [ADR-0013](./0013-el-pitch-copiloto-del-operario-sin-supervisor-encima.md).
- REFERENCIAS 33: un paso que se saltan muchos operarios apunta a la pauta, no a ellos.
