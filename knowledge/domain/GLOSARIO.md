# Glosario

| Término | Definición en este proyecto | Fuente |
|---|---|---|
| **Operario aumentado con IA** | La premisa del producto: la IA acompaña al operario como copiloto, comprueba cada paso y le avisa en el momento. No lo reemplaza | [Planteamiento del equipo](./fuentes/2026-11-21-planteamiento-del-equipo.md) |
| **ICP** | Perfil de cliente ideal: una operación con equipos críticos, de cualquier rubro, que ya tiene procedimientos estandarizados y no tiene cómo verificarlos | [CONTEXTO](./CONTEXTO.md) |
| **OT** | Orden de trabajo de mantenimiento. Tiene campos estructurados (equipo, fechas, estado) y un texto libre que escribe el técnico. En este proyecto es la instancia ejecutable de la pauta vigente, y se genera por calendario, por pedido o por una falla | Uso en SAP PM y CMMS; [ADR-0006](../decisions/0006-la-ot-nace-del-protocolo.md) |
| **Bitácora** | Registro de lo que se hizo en una OT. En este proyecto es la lista de pasos verificados con su evidencia, no un texto escrito después | [CONTEXTO](./CONTEXTO.md) |
| **Pauta** | Procedimiento paso a paso para ejecutar una tarea de mantenimiento. El equipo también le dice protocolo o procedimiento estandarizado | — |
| **Pauta comprobable** | Pauta en la que cada paso declara qué evidencia lo cierra: un sensor, la cámara o la confirmación del operario | [ADR-0004](../decisions/0004-verificacion-por-capas.md) |
| **Pauta matriz** | La versión aprobada de una pauta, de la que salen las pautas de cada OT. Se versiona | [ADR-0003](../decisions/0003-patrones-de-arquitectura-para-el-mvp.md) |
| **Bloqueo y etiquetado** (LOTO, *lockout/tagout*) | Aislar las fuentes de energía de un equipo con candado y tarjeta antes de intervenirlo. Es el paso de seguridad más concreto del mantenimiento | OSHA 29 CFR 1910.147 |
| **Relevo de turno** | Traspaso de un trabajo que dura más de un turno. El turno siguiente lo retoma desde el último paso verificado | [FLUJO](../architecture/FLUJO.md#5-bitácora-y-relevo-de-turno) |
| **Capa determinista** | La parte de la verificación que decide con señales de sensores y reglas, sin un modelo. Un modelo nunca la contradice | [ADR-0004](../decisions/0004-verificacion-por-capas.md) |
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

## Fuentes

- Números de referencia: ver [REFERENCIAS](../projects/research/REFERENCIAS.md).
- OSHA, 29 CFR 1910.147, *The control of hazardous energy (lockout/tagout)*. Sin enlace verificado.
