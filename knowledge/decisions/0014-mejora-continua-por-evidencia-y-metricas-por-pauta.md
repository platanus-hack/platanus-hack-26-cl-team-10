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
3. La propuesta pasa a `aplicada`. Con las OT de la versión nueva que ya pasaron por ese paso, `validacion` dice si dejó de desviarse (`mejoro`), si bajó pero con tan pocas OT que puede ser azar (`sin_evidencia`), si se sigue desviando (`se_repite`) o si todavía no hay ejecuciones (`sin_datos`). Desde el 2026-11-21, «mejoro» pide Fisher exacta con α = 0,05, y cada propuesta trae `recurrencia`, que dice si el paso se desvía más que el resto de su pauta (`app/recurrencia.py`). La [simulación](../projects/mejora-continua/simulacion.md) mostró por qué: con 20 OT y ruido al 5 %, la regla de 2 OT deja alguna propuesta falsa en el 91 % de las pautas, y una versión sin efecto «mejoraba» el 42 % de las veces.

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

### Lo que cambió el 2026-11-22

La regla de las dos OT sigue decidiendo cuándo existe una propuesta de desviación (`mejora.MINIMO`), pero ya no decide qué se le muestra al supervisor como patrón:

- **El aviso.** Al supervisor le llega «Factum sugiere una mejora a tus pautas» apenas el paso es recurrente **en vivo**: la prueba binomial con el α repartido entre las OT de la versión (`en_vivo`, `mejora.alfa_en_vivo`, [ADR-0018](./0018-la-pauta-tiene-un-protocolo-dueno-y-cada-protocolo-itera-por-separado.md)). Queda en la bitácora de la OT que lo destapó (`detectada`). Una propuesta de dos OT que no es recurrente se ve en la lista, pero no avisa.
- **Las señales son seis.** Se sumó la alerta de seguridad atribuida al paso que seguía abierto (`mejora.SENALES`).
- **Hay propuestas de conformidad**, que nacen de la pauta misma y no de las OT ([ADR-0016](./0016-una-pauta-sale-del-protocolo-que-aplica-a-su-tarea.md)).
- **Cada propuesta trae su cambio** (`app/sugerencias.py`, PR #74). `GET /cliente/mejoras/{id}/borrador` devuelve qué pasos agrega, separa o reescribe la versión siguiente, con el antes, el después y las OT que lo respaldan (`ots`), comprobado contra los controles del protocolo. Lo arma el código; si hay key, Claude Opus 5.5 puede reescribir solo el título, la instrucción y el porqué, y el código descarta su texto si cita una OT ajena o toca otra cosa. Las que no traen un cambio de pauta (domina la confirmación por persona o las observaciones, se escaló, o son de conformidad por orden o por un control desconocido) lo dicen en `aplicable` y `por_que_no`.
- **El reporte de la OT** trae `mejoras`: las propuestas de su pauta y versión en que esa OT aportó, más las de conformidad, con su cambio en una línea por paso, y la sección «Mejoras sugeridas» en markdown. El texto del reporte lo sigue armando solo el código.
- **El paso 2 del ciclo cambió.** «Aplicar», en la pantalla del supervisor, es aceptar. El equipo ya no escribe la versión siguiente a mano: `POST /interno/pautas/{id}/version-siguiente` junta los borradores de todas las aceptadas de la última versión aprobada y la guarda sin aprobar; una persona del equipo la aprueba con la ruta de siempre, que la rechaza si pierde un control crítico. Sigue valiendo la alternativa C descartada: el sistema propone, una persona aprueba.

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

- La comprobación compara la fracción de OT con señal antes y después, sin un mínimo de ejecuciones. Con dos o tres OT por versión, «mejoró» puede ser azar. `Candidata a validar`. Resuelto el 2026-11-21: «mejoro» pide Fisher exacta con α = 0,05, y si la baja puede ser azar dice `sin_evidencia`.
- La versión nueva la escribe a mano el equipo. Que un modelo redacte el cambio a partir de la propuesta es el siguiente paso. `Brecha`. Resuelto el 2026-11-22 de otra forma: el cambio lo arma el código con reglas fijas y un modelo solo puede reescribir su texto (`app/sugerencias.py`); la versión la junta `version-siguiente` y la aprueba una persona.
- `GET /supervisor/propuestas`, la ruta anterior, sigue abierta y sin empresa. Queda hasta que la pantalla del demo use `/cliente/mejoras`. `Brecha`. Al 2026-11-22, la web del supervisor ya usa `/cliente/mejoras`; la ruta anterior la sigue leyendo `app/estatico/simulador.html`.
- El tiempo de ejecución se mide del primer evento después de asignar la OT al último paso verificado. Una OT que espera entre pasos cuenta esa espera. `Candidata a validar`.
- Las métricas no paginan más allá de `limite`, y `GET /cliente/metricas` lee todas las OT de la empresa en cada llamada. `Brecha` cuando una empresa tenga miles.
- La semilla trae las observaciones solo en una base nueva: en la VM, las OT de la semilla ya existían y no se vuelven a ejecutar. `Brecha` del despliegue.

## Referencias

- Código: `app/mejora.py`, `app/recurrencia.py`, `app/sugerencias.py`, `app/metricas.py`, `Servicios.observar` en `app/servicios.py`, las rutas de `app/api.py`, `tests/test_mejora_y_metricas.py` y `tests/test_sugerencias.py`.
- [ADR-0003](./0003-patrones-de-arquitectura-para-el-mvp.md), [ADR-0012](./0012-login-y-clientes-cada-empresa-ve-lo-suyo.md) y [ADR-0013](./0013-el-pitch-copiloto-del-operario-sin-supervisor-encima.md).
- REFERENCIAS 33: un paso que se saltan muchos operarios apunta a la pauta, no a ellos.
