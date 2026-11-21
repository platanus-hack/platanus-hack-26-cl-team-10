# Glosario

| Término | Definición en este proyecto | Fuente |
|---|---|---|
| **Operario aumentado con IA** | La premisa del producto: la IA acompaña al operario como copiloto, comprueba cada paso y le avisa en el momento. No lo reemplaza | [Planteamiento del equipo](./fuentes/2026-11-21-planteamiento-del-equipo.md) |
| **Flujo operacional** | Cualquier procedimiento que una operación ejecuta paso a paso. Es lo que el producto vuelve verificable; el mantenimiento de maquinaria es el caso de uso | [ADR-0009](../decisions/0009-flujo-operacional-verificable-mantenimiento-como-caso-de-uso.md) |
| **ICP** | Perfil de cliente ideal: una operación con equipos críticos, de cualquier rubro, que ya tiene procedimientos estandarizados y no tiene cómo verificarlos | [CONTEXTO](./CONTEXTO.md) |
| **OT** | Orden de trabajo de mantenimiento. Tiene campos estructurados (equipo, fechas, estado) y un texto libre que escribe el técnico. En este proyecto es la instancia ejecutable de la pauta vigente, y se genera por calendario, por pedido o por una falla | Uso en SAP PM y CMMS; [ADR-0006](../decisions/0006-la-ot-nace-del-protocolo.md) |
| **Bitácora** | Registro de lo que se hizo en una OT. En este proyecto es la lista de pasos verificados con su evidencia, no un texto escrito después | [CONTEXTO](./CONTEXTO.md) |
| **Pauta** | Procedimiento paso a paso para ejecutar un flujo operacional; en el caso de uso, una tarea de mantenimiento. El equipo también le dice protocolo o procedimiento estandarizado | — |
| **Pauta comprobable** | Pauta en la que cada paso declara qué evidencia lo cierra: un sensor, la cámara o la confirmación del operario | [ADR-0004](../decisions/0004-verificacion-por-capas.md) |
| **Pauta matriz** | La versión aprobada de una pauta, de la que salen las pautas de cada OT. Se versiona | [ADR-0003](../decisions/0003-patrones-de-arquitectura-para-el-mvp.md) |
| **Bloqueo y etiquetado** (LOTO, *lockout/tagout*) | Aislar las fuentes de energía de un equipo con candado y tarjeta antes de intervenirlo. Es el paso de seguridad más concreto del mantenimiento | OSHA 29 CFR 1910.147 |
| **Relevo de turno** | Traspaso de un trabajo que dura más de un turno. El turno siguiente lo retoma desde el último paso verificado | [FLUJO](../architecture/FLUJO.md#5-bitácora-y-relevo-de-turno) |
| **Capa determinista** | La parte de la verificación que decide con señales de sensores y reglas, sin un modelo. Un modelo nunca la contradice | [ADR-0004](../decisions/0004-verificacion-por-capas.md) |
| **Capa 1, 2 y 3** | Las tres formas de comprobar un paso, en orden: sensores y reglas (1), un modelo sobre señales o sobre la imagen, como el detector de objetos (2), y un VLM que responde una pregunta sobre la foto (3). Decide la primera que puede, y solo la capa 1 interrumpe al operario | [ADR-0004](../decisions/0004-verificacion-por-capas.md), [LOGICA](../architecture/LOGICA.md#quién-decide-que-un-paso-está-hecho) |
| **Edge** | La estación junto al equipo: sensores y cámara que mandan lecturas y video a la API. No sabe de OT | [ADR-0007](../decisions/0007-servicios-en-vivo-sesion-stream-y-calificacion.md) |
| **Sesión** | Lo que une un edge con la OT que se está ejecutando. Desde que se abre, cada lectura de ese edge entra a esa OT y solo a esa | [ADR-0007](../decisions/0007-servicios-en-vivo-sesion-stream-y-calificacion.md) |
| **Calificación** | Qué tan grave es lo que pasa en una OT: `ok`, `warning` o `error`, con su certeza y sus motivos. Se calcula al leer, no se guarda | [ADR-0007](../decisions/0007-servicios-en-vivo-sesion-stream-y-calificacion.md) |
| **Clave del equipo** | La cabecera `X-Clave-Equipo`, que el servidor pide para quitarle un edge a la OT que ejecuta o para soltarlo | [PRD de servicios](../projects/servicios-en-vivo/PRD.md#5-datos-y-reglas) |
| **SAP PM** | Módulo de mantenimiento de SAP, habitual en minería. De ahí sale el archivo exportado de OT | — |
| **CMMS / EAM** | Sistemas de gestión del mantenimiento y de los activos | — |
| **PLC / SCADA** | El control del equipo y la supervisión de la planta. El producto no los toca | — |
| **PdM** | Mantenimiento predictivo: anticipar la falla con datos de condición | — |
| **RUL** | Vida útil remanente de un equipo o componente | ISO 13381-1 |
| **MTBF** | Tiempo medio entre fallas | — |
| **FMEA** | Análisis de modos de falla y sus efectos | — |
| **TLP** (*Technical Language Processing*) | Procesamiento de lenguaje adaptado al texto técnico de las OT: jerga, abreviaturas, errores | REFERENCIAS 1 |
| **VLM** | Modelo de visión y lenguaje: recibe imagen o video y texto, y responde en texto | REFERENCIAS 9 |
| **Video egocéntrico** | Grabado desde la cabeza o el pecho de quien ejecuta la tarea | REFERENCIAS 16 |
| **Grafo de tarea** | Los pasos de una pauta y sus precedencias: qué tiene que estar hecho antes de cada paso | REFERENCIAS 15 |
| ***Zero-shot*** | Usar un modelo sin entrenarlo con datos de la tarea | REFERENCIAS 9 |
| **Paso saltado** | Un paso de la pauta que no aparece en la ejecución. Un VLM general lo detecta bien | REFERENCIAS 9 |
| **Cambio de orden** | Pasos hechos en otro orden que el de la pauta. Un VLM general lo detecta mal | REFERENCIAS 9 |
| **Control crítico** | La barrera cuya falla permite que ocurra un evento de alta consecuencia. ICMM pide identificarlos, implementarlos y **verificarlos**; verificarlos es lo que hace este producto | [REFERENCIAS 40](../projects/research/REFERENCIAS.md) |
| **Ejecución inefectiva del control** | El control existía y se ejecutó mal. Fue la falla más común en los incidentes fatales de los miembros de ICMM en 2025: 19 de 26. Es el problema que el flujo ataca | [REFERENCIAS 40](../projects/research/REFERENCIAS.md) |
| **Aislamiento de energía** | Cómo ICMM nombra al bloqueo y etiquetado al listar los peligros de alta consecuencia. Es el paso central del demo | [REFERENCIAS 40](../projects/research/REFERENCIAS.md) |

## Fuentes

- Números de referencia: ver [REFERENCIAS](../projects/research/REFERENCIAS.md).
- OSHA, 29 CFR 1910.147, *The control of hazardous energy (lockout/tagout)*. Sin enlace verificado.
