# ADR-0016 — Una pauta sale del protocolo que aplica a su tarea; cumplirlo se verifica aparte

> Estado: `proposed` · Fecha: 2026-11-22

## Contexto

El [ADR-0011](./0011-protocolos-y-pautas-por-servicio-interno-ot-por-servicio-al-cliente.md) dice que una pauta «sale» de uno o más protocolos, pero no dice qué significa. Al revisar las atribuciones el 2026-11-22 aparecieron tres lecturas mezcladas:

- **Derivación:** los pasos de la pauta se sacaron de ese documento.
- **Aplicabilidad:** el peligro que el protocolo controla existe en la tarea de la pauta.
- **Conformidad:** la pauta cumple los controles críticos del protocolo.

Con la tercera se sacaron del protocolo de aislamiento las tres pautas de la maqueta (PR #65), y con la misma regla habría que sacar también `pauta-correa-ct-01`, que junta aislar y bloquear en un paso y no comprueba energía cero. Esa regla no tiene respaldo: la inventamos al revisar. Las fuentes dicen otra cosa.

- **El alcance se define por el peligro, no por el cumplimiento.** 29 CFR 1910.147 cubre toda mantención donde una energización inesperada puede herir (REFERENCIAS 78); el DS 132 art. 52 aplica a toda mantención o reparación (44), y MSHA 56.12016 y 56.14105 a todo trabajo mecánico o eléctrico (45). ICMM define cada control crítico respecto del evento no deseado que previene (79).
- **Un procedimiento que no cumple se corrige; no deja de estar cubierto.** 1910.147 pide que el procedimiento de cada equipo traiga los pasos de aislar, bloquear y probar que el bloqueo funciona, y que una inspección periódica corrija las desviaciones o insuficiencias que encuentre (78). ICMM pide investigar y mejorar un control crítico que rinde menos de lo requerido (79).
- **El protocolo no es el control.** Para ICMM los procedimientos y las reglas no son controles: el control es el acto que mandan hacer (79). Una pauta que omite el acto no deja de pertenecer al procedimiento; tiene una brecha.

## Decisión

**La atribución significa aplicabilidad.** Una pauta se atribuye a un protocolo cuando el alcance que el protocolo declara cubre la tarea de la pauta: el peligro que controla existe en esa tarea. Cada protocolo declara su alcance (su sección «Alcance») y sus controles críticos.

**La conformidad se verifica aparte y una falta es un hallazgo.** Una pauta atribuida tiene que traer un paso por cada control crítico del protocolo, en su orden. Si le falta uno, la atribución se mantiene y la falta queda registrada como hallazgo de esa versión de la pauta; se corrige con una versión nueva, por el flujo de mejora del [ADR-0014](./0014-mejora-continua-por-evidencia-y-metricas-por-pauta.md). Nunca se resuelve quitando la atribución, porque eso esconde la brecha.

**La derivación se cuenta en el texto, no en la relación.** Que una pauta se haya adaptado de otro documento lo dice el protocolo al que pertenece (por ejemplo, «adaptada de `prot-correa-01`»). La relación pauta–protocolo tiene un solo significado.

**Una maqueta tiene su propio protocolo de ejemplos.** Una pauta que corre sobre una maqueta o un caso de prueba no interviene un equipo con el peligro real, así que los protocolos de ese peligro no le aplican. Sale del protocolo de ejemplos que la describe (`prot-maqueta-01`, `prot-botella-01`), redactado por el equipo y declarado como tal.

### Qué se guarda y qué se calcula

Se guardan los hechos y las decisiones de las personas; se calcula lo que sale de ellos. Es el patrón que ya rige para la bitácora ([ADR-0003](./0003-patrones-de-arquitectura-para-el-mvp.md)) y para las propuestas de mejora, que se calculan de la bitácora mientras sus revisiones se guardan en `mejora_revisiones` ([ADR-0014](./0014-mejora-continua-por-evidencia-y-metricas-por-pauta.md), `app/mejora.py`). 29 CFR 1910.147 dice qué tiene que quedar de una revisión de procedimiento: el equipo, la fecha, quiénes participaron y quién revisó, (c)(6)(ii) (78). ICMM pide definir para cada control crítico cómo se verifica y quién es su dueño, pasos 5 y 6 (79).

| Qué | Se guarda o se calcula | Dónde |
|---|---|---|
| El protocolo, **por versión** | Se guarda | Hoy `protocolos` no tiene versiones: `PUT /interno/protocolos/{id}` reescribe el texto. Un hallazgo es «la pauta v3 contra el protocolo v2», y sin versiones no se puede reproducir. El protocolo se versiona como la pauta |
| Los controles críticos de cada versión del protocolo | Se guardan y los aprueba una persona | Una tabla por versión de protocolo: id del control, qué exige, en qué orden y con qué evidencia se comprueba |
| Qué control cumple cada paso de la pauta | Se guarda | Un campo del paso en el JSON de la pauta, que ya está versionado. Reemplaza a `control_critico: true`, que no dice cuál |
| El hallazgo (qué control le falta a qué pauta) | **Se calcula** | Lo da el validador de pautas (`/interno/pautas/validar`) a partir de la pauta, los protocolos que le aplican y sus controles. Es determinístico: guardarlo sería duplicarlo |
| La revisión del hallazgo (se corrige, o se acepta con su justificación) | Se guarda, sin borrar nada | La misma tabla y la misma pantalla de las propuestas de mejora (`mejora_revisiones`, `/supervisor/mejoras`, PR #66): un hallazgo es una propuesta de tipo `conformidad`, con quién la revisó, cuándo y su nota |

Los controles de un protocolo los propone la skill que lee el protocolo (`reconocer-proceso`) y **los aprueba una persona del equipo**, una vez por versión del protocolo, como se aprueba una pauta. Para ICMM, elegir los controles críticos y asignarles un dueño son pasos deliberados del proceso, no un resultado automático (pasos 4 a 6, 79).

### Lo que se construyó, el 2026-11-22

- **Los controles como datos.** Cada protocolo guarda sus controles críticos (`controles`, con id, nombre y orden) y quién los aprobó y cuándo (`PUT /interno/protocolos/{id}/controles`). `prot-aislamiento-01` declara A1 aislar, A2 bloquear y A3 comprobar energía cero; `prot-maqueta-01`, los tres que imita (M1 apagar el motor, M2 trabar la parada, M3 esperar a que se enfríe).
- **`cumple` en el paso**, como `prot-aislamiento-01:A3`. Se anota sobre la versión que ya existe: no cambia nada de lo que se ejecuta, y la semilla lo pone solo si es lo único que cambia. Una pauta que no anota ningún control de un protocolo recibe un aviso, no hallazgos: se escribió antes de que existiera el campo.
- **La revisión de conformidad**, en `analisis.conformidad` y en el validador (C1 falta, C2 dos controles en un paso, C3 fuera de orden, C4 un control que el protocolo no declara). Sobre la semilla da 5 hallazgos: los 2 del cambio de rodillo y uno por cada pauta de la maqueta.
- **El hallazgo como propuesta** de tipo `conformidad` en `GET /cliente/mejoras`, con la clave `conformidad:<pauta>@<versión>:<protocolo>:<control>:<tipo>`. Aparece apenas la pauta se habilita, sin ninguna OT; el supervisor lo acepta o lo descarta en la misma pantalla, y con una versión aprobada más nueva `validacion` dice si se cerró.
- **La aprobación no deja sacar un control.** Una versión nueva no se aprueba si le falta un control crítico que la anterior cumplía (409). Lo que ya le faltaba a la anterior no bloquea: es un hallazgo abierto.
- **Probado de punta a punta** en `tests/test_recorrido_interno.py`, por HTTP y con la clave del equipo: protocolo con controles, pauta sin A3 que el validador marca, aprobación, hallazgo visible sin OT, OT que se desvían hasta el aviso, revisión del supervisor, versión que saca el candado rechazada, versión con la prueba aprobada, y las dos propuestas en «mejoró» con las OT nuevas.

## Alternativas consideradas

- **A — La atribución significa conformidad** (lo que se aplicó en el PR #65): una pauta que no cumple sale del protocolo. Es simple de leer, pero sin respaldo en las fuentes y con un efecto malo: la pauta defectuosa deja de parecer cubierta por el control que le falta, que es justo lo que hay que ver.
- **B — La atribución significa derivación:** la pauta sale del documento del que se copiaron sus pasos. Es trazabilidad pura, pero deja dentro de `prot-correa-01` a las pautas de la maqueta, que no tienen el peligro de una correa real, y no dice qué controles se le pueden exigir a una pauta.
- **C — Dos relaciones, «aplica a» y «se derivó de»:** es la más precisa, pero duplica el modelo, las rutas y la semilla para distinguir algo que hoy cabe en una frase del protocolo. Se puede volver a ella si un cliente necesita auditar la derivación por separado.

## Consecuencias

- Aplicado a la semilla de hoy:

  | Pauta | Hoy | Con esta decisión |
  |---|---|---|
  | `pauta-loto-escritorio`, `pauta-polin-demo`, `pauta-polin-estacion` | maqueta (y las dos de polín, también correa) | Solo `prot-maqueta-01`: la correa a escala no tiene el peligro de una correa real. `prot-maqueta-01` dice de qué protocolo se adaptó cada una |
  | `pauta-correa-ct-01` | aislamiento y correa | Igual. Queda registrado el hallazgo: junta aislar y bloquear y no comprueba energía cero (ya está en `Brecha` en el ADR-0011) |
  | Las demás | — | Sin cambio |

- La conformidad se vuelve comprobable: el validador lista qué control le falta a cada pauta atribuida, y el supervisor lo ve donde ya revisa las propuestas de mejora. Hoy esos controles están solo en el texto del protocolo.
- Cuesta tres cambios de datos: versionar los protocolos, una tabla de controles por versión con su aprobación y un campo nuevo en el paso. La migración tiene que llevar los protocolos actuales a su versión 1.
- `prot-aislamiento-01` deja de citar 29 CFR 1910.147 por REFERENCIAS 55, que solo dice que es la tercera norma más citada. Lo cita por la 78, y como modelo: 1910.147 no rige la minería ni la construcción.
- Un protocolo nuevo tiene que declarar su alcance y sus controles críticos para que se le puedan atribuir pautas.

## Pendientes y no verificado

- **ISO 45001:2018, cláusula 10.2** (no conformidad y acción correctiva) respaldaría lo mismo, pero no se leyó: la norma es de pago. No se cita.
- **Quién revisa un hallazgo**: decidido el 2026-11-22. Lo revisa el supervisor del cliente, que recibe el aviso; el equipo de Factum sigue cómo van las mejoras de todas las empresas en `/interno/mejoras`. 1910.147 pide que revise alguien distinto de quien usa el procedimiento, (c)(6)(i)(A) (78).
- **`propuesta_id` de un hallazgo**: `mejora_revisiones` hoy guarda revisiones de propuestas calculadas por paso; un hallazgo necesita una clave estable con pauta, versión, protocolo, versión y control. No se probó.
- **La norma de celdas robotizadas**: ISO 10218-2:2025 (REFERENCIAS 80). Su alcance cubre la mantención y trae cláusulas de energía peligrosa y de partida y rearranque inesperados, pero el texto de sus requisitos es de pago y no se leyó; `prot-brazo-01` no declara controles propios por eso. `Brecha`.
- **`prot-inspeccion-correa-01`** existe solo en la base de la VM. Decidido el 2026-11-22: no se trae al repo, porque ningún protocolo documentado lo necesita. Borrarlo de la base pide quitarle antes su pauta.
- ICMM se leyó en las definiciones, la tabla de pasos y la sección de qué es un control; el resto del documento, no.

- **Un salto, dos señales.** Cuando el paso saltado es un control crítico, acercarse con la energía viva deja seguridad en ese paso y orden en el que se adelantó. Las dos se inflan la tasa de referencia de la prueba de recurrencia, y el aviso llega a la quinta OT en vez de la tercera. Contarlas como un incidente no se decidió.
- **Los protocolos no tienen versiones todavía.** Sin ellas, un hallazgo no se reproduce contra el texto del protocolo de ese momento. `Brecha`.

## Referencias

- REFERENCIAS 44, 45, 56, 78, 79 y 80.
- PR #66 (Daniel Godoy): `/supervisor/mejoras` y la revisión de propuestas en la web.
- [ADR-0011](./0011-protocolos-y-pautas-por-servicio-interno-ot-por-servicio-al-cliente.md) y [ADR-0014](./0014-mejora-continua-por-evidencia-y-metricas-por-pauta.md).
- Código: `datos/protocolos.json`, `app/protocolos.py` (`cargar_semilla`), `app/catalogo.py` (atribuciones).
